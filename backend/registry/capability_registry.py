"""Centralized Capability Registry managing discovers, persistence, and lifecycle event loops."""

from __future__ import annotations

from datetime import datetime
import json
import threading
from typing import Any, Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.runtime.event import Event, EventBus, EventType
from backend.registry.registry_models import CapabilityMetadata, CapabilityType, CapabilityHealth


class CapabilityRegistry:
    """Thread-safe control plane registry managing all AI capabilities."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "CapabilityRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._lock:
            if getattr(self, "_initialized", False):
                return
            self._db = DBStorage()
            self._event_bus = EventBus()
            self._capabilities: Dict[str, CapabilityMetadata] = {}
            self._init_db()
            self._load_from_db()
            self._discover_local_capabilities()
            self._initialized = True

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS registry_capabilities (
                capability_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT NOT NULL,
                author TEXT NOT NULL,
                tags TEXT NOT NULL,
                dependencies TEXT NOT NULL,
                compatibilities TEXT NOT NULL,
                is_deprecated INTEGER NOT NULL,
                upgrade_path TEXT,
                is_available INTEGER NOT NULL,
                latency_ms REAL NOT NULL,
                error_rate REAL NOT NULL,
                last_execution TEXT NOT NULL,
                usage_count INTEGER NOT NULL,
                failure_count INTEGER NOT NULL,
                extra TEXT NOT NULL
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def _load_from_db(self) -> None:
        conn = self._db._get_connection()
        try:
            rows = conn.execute("SELECT * FROM registry_capabilities").fetchall()
            for r in rows:
                health = CapabilityHealth(
                    is_available=bool(r["is_available"]),
                    latency_ms=r["latency_ms"],
                    error_rate=r["error_rate"],
                    last_execution=r["last_execution"],
                    usage_count=r["usage_count"],
                    failure_count=r["failure_count"]
                )
                meta = CapabilityMetadata(
                    capability_id=r["capability_id"],
                    name=r["name"],
                    type=CapabilityType(r["type"]),
                    version=r["version"],
                    description=r["description"],
                    author=r["author"],
                    tags=r["tags"].split(",") if r["tags"] else [],
                    dependencies=r["dependencies"].split(",") if r["dependencies"] else [],
                    compatibilities=r["compatibilities"].split(",") if r["compatibilities"] else [],
                    is_deprecated=bool(r["is_deprecated"]),
                    upgrade_path=r["upgrade_path"],
                    health=health,
                    extra=json.loads(r["extra"]) if r["extra"] else {}
                )
                self._capabilities[meta.capability_id] = meta
        finally:
            conn.close()

    def register_capability(self, meta: CapabilityMetadata) -> None:
        """Registers a capability dynamically and persists it."""
        with self._lock:
            self._capabilities[meta.capability_id] = meta
            conn = self._db._get_connection()
            try:
                conn.execute("""
                INSERT INTO registry_capabilities (
                    capability_id, name, type, version, description, author, tags,
                    dependencies, compatibilities, is_deprecated, upgrade_path,
                    is_available, latency_ms, error_rate, last_execution,
                    usage_count, failure_count, extra
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(capability_id) DO UPDATE SET
                    name=excluded.name,
                    type=excluded.type,
                    version=excluded.version,
                    description=excluded.description,
                    author=excluded.author,
                    tags=excluded.tags,
                    dependencies=excluded.dependencies,
                    compatibilities=excluded.compatibilities,
                    is_deprecated=excluded.is_deprecated,
                    upgrade_path=excluded.upgrade_path,
                    is_available=excluded.is_available,
                    latency_ms=excluded.latency_ms,
                    error_rate=excluded.error_rate,
                    last_execution=excluded.last_execution,
                    usage_count=excluded.usage_count,
                    failure_count=excluded.failure_count,
                    extra=excluded.extra
                """, (
                    meta.capability_id,
                    meta.name,
                    meta.type.value,
                    meta.version,
                    meta.description,
                    meta.author,
                    ",".join(meta.tags),
                    ",".join(meta.dependencies),
                    ",".join(meta.compatibilities),
                    1 if meta.is_deprecated else 0,
                    meta.upgrade_path,
                    1 if meta.health.is_available else 0,
                    meta.health.latency_ms,
                    meta.health.error_rate,
                    meta.health.last_execution,
                    meta.health.usage_count,
                    meta.health.failure_count,
                    json.dumps(meta.extra)
                ))
                conn.commit()
            finally:
                conn.close()

            # Emit registration lifecycle events
            self._publish_event(f"{meta.type.value}.registered", {"capability_id": meta.capability_id})
            self._publish_event("registry.updated", {"action": "register", "capability_id": meta.capability_id})

    def update_health(self, capability_id: str, is_available: bool, latency_ms: float, is_error: bool) -> None:
        """Updates runtime performance metrics of a capability."""
        with self._lock:
            meta = self._capabilities.get(capability_id)
            if not meta:
                return
            h = meta.health
            h.is_available = is_available
            h.latency_ms = (h.latency_ms * 9.0 + latency_ms) / 10.0  # EMA latency
            h.last_execution = datetime.utcnow().isoformat()
            h.usage_count += 1
            if is_error:
                h.failure_count += 1
            h.error_rate = h.failure_count / h.usage_count

            # Update DB
            conn = self._db._get_connection()
            try:
                conn.execute("""
                UPDATE registry_capabilities SET
                    is_available = ?, latency_ms = ?, error_rate = ?,
                    last_execution = ?, usage_count = ?, failure_count = ?
                WHERE capability_id = ?
                """, (
                    1 if h.is_available else 0,
                    h.latency_ms,
                    h.error_rate,
                    h.last_execution,
                    h.usage_count,
                    h.failure_count,
                    capability_id
                ))
                conn.commit()
            finally:
                conn.close()

    def get_capability(self, capability_id: str) -> Optional[CapabilityMetadata]:
        """Retrieves a capability by ID."""
        with self._lock:
            return self._capabilities.get(capability_id)

    def list_capabilities(self, cap_type: Optional[CapabilityType] = None) -> List[CapabilityMetadata]:
        """Lists registered capabilities. Filterable by type."""
        with self._lock:
            if cap_type:
                return [c for c in self._capabilities.values() if c.type == cap_type]
            return list(self._capabilities.values())

    def search(self, query: str) -> List[CapabilityMetadata]:
        """Performs simple search matching query string to tags, name or author."""
        with self._lock:
            q = query.lower()
            results = []
            for c in self._capabilities.values():
                if (
                    q in c.name.lower() or
                    q in c.description.lower() or
                    q in c.author.lower() or
                    any(q in tag.lower() for tag in c.tags)
                ):
                    results.append(c)
            return results

    def _discover_local_capabilities(self) -> None:
        """Autodetects core system capabilities on startup without manual configuration."""
        # 1. Discover registered intelligence gateway modules
        from backend.intelligence.core.registry import IntelligenceRegistry
        gateway_registry = IntelligenceRegistry()
        for m_name in gateway_registry.list_modules():
            module = gateway_registry.get_module(m_name)
            self.register_capability(CapabilityMetadata(
                capability_id=f"module-{m_name.lower()}",
                name=m_name,
                type=CapabilityType.MODULE,
                version="1.0.0",
                description=f"Core Intelligence Gateway Module: {m_name}",
                tags=list(module.capabilities) + ["intelligence", "gateway"]
            ))

        # 2. Discover workflows
        # Register a few default capability templates
        self.register_capability(CapabilityMetadata(
            capability_id="workflow-resume-profile",
            name="Resume Ingestion Workflow",
            type=CapabilityType.WORKFLOW,
            version="1.0.0",
            description="End-to-end resume scanning, skills extraction, and profile creation pipeline.",
            tags=["resume", "profile", "automation"],
            dependencies=["module-resumeintelligence"]
        ))
        self.register_capability(CapabilityMetadata(
            capability_id="workflow-github-audit",
            name="GitHub Code Quality Audit",
            type=CapabilityType.WORKFLOW,
            version="1.0.0",
            description="GitHub engineering audit, code health check, and repository health check.",
            tags=["github", "audit", "automation"],
            dependencies=["module-githubintelligence"]
        ))

    def _publish_event(self, event_name: str, payload: dict) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CapabilityRegistry",
            payload={
                "event": event_name,
                "timestamp": datetime.utcnow().isoformat(),
                **payload
            }
        )
        self.event_bus.publish(event)

    def clear(self) -> None:
        """Clears registry database and cache (test helper)."""
        with self._lock:
            self._capabilities.clear()
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM registry_capabilities")
                conn.commit()
            finally:
                conn.close()
