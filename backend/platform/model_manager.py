"""Model Manager managing registered LLMs list and defaults."""

from __future__ import annotations

import json
import threading
from typing import Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.runtime.event import Event, EventBus, EventType
from backend.platform.models import ModelProfile


class ModelManager:
    """Thread-safe manager for dynamic model routing mappings."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._event_bus = EventBus()
        self._lock = threading.Lock()
        self._init_db()
        self._seed_models()

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS platform_models (
                model_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                version TEXT NOT NULL,
                capabilities TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                is_default INTEGER NOT NULL,
                metadata TEXT NOT NULL
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def _seed_models(self) -> None:
        defaults = [
            ("gpt-4", "GPT-4", "openai", "1.0", ["chat", "extraction"], True),
            ("claude-3-opus", "Claude 3 Opus", "anthropic", "1.0", ["chat"], False),
            ("gemini-1.5", "Gemini 1.5", "gemini", "1.5", ["chat", "multimodal"], False),
            ("phi3:mini", "Phi 3 Mini", "ollama", "3.0", ["chat", "local"], False)
        ]
        for mid, name, pid, ver, tags, is_def in defaults:
            if not self.get_model(mid):
                self.register_model(ModelProfile(
                    model_id=mid, name=name, provider_id=pid,
                    version=ver, capabilities=tags, is_default=is_def
                ))

    def register_model(self, profile: ModelProfile) -> None:
        """Registers a new model and handles default selections."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                # If default is selected, reset previous defaults
                if profile.is_default:
                    conn.execute("UPDATE platform_models SET is_default = 0")
                
                conn.execute("""
                INSERT INTO platform_models (
                    model_id, name, provider_id, version, capabilities, is_active, is_default, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(model_id) DO UPDATE SET
                    name=excluded.name,
                    provider_id=excluded.provider_id,
                    version=excluded.version,
                    capabilities=excluded.capabilities,
                    is_active=excluded.is_active,
                    is_default=excluded.is_default,
                    metadata=excluded.metadata
                """, (
                    profile.model_id,
                    profile.name,
                    profile.provider_id,
                    profile.version,
                    ",".join(profile.capabilities),
                    1 if profile.is_active else 0,
                    1 if profile.is_default else 0,
                    json.dumps(profile.metadata)
                ))
                conn.commit()
            finally:
                conn.close()

            # Emit events
            if profile.is_default:
                self._event_bus.publish(Event(
                    event_type=EventType.CUSTOM_EVENT,
                    source="ModelManager",
                    payload={"event": "model.selected", "model_id": profile.model_id}
                ))

    def get_model(self, model_id: str) -> Optional[ModelProfile]:
        """Retrieves model profile metadata."""
        conn = self._db._get_connection()
        try:
            r = conn.execute("SELECT * FROM platform_models WHERE model_id = ?", (model_id,)).fetchone()
            if r:
                return ModelProfile(
                    model_id=r["model_id"],
                    name=r["name"],
                    provider_id=r["provider_id"],
                    version=r["version"],
                    capabilities=r["capabilities"].split(",") if r["capabilities"] else [],
                    is_active=bool(r["is_active"]),
                    is_default=bool(r["is_default"]),
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {}
                )
            return None
        finally:
            conn.close()

    def get_default_model(self) -> Optional[ModelProfile]:
        """Retrieves default routing model."""
        conn = self._db._get_connection()
        try:
            r = conn.execute("SELECT * FROM platform_models WHERE is_default = 1").fetchone()
            if r:
                return ModelProfile(
                    model_id=r["model_id"],
                    name=r["name"],
                    provider_id=r["provider_id"],
                    version=r["version"],
                    capabilities=r["capabilities"].split(",") if r["capabilities"] else [],
                    is_active=bool(r["is_active"]),
                    is_default=bool(r["is_default"]),
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {}
                )
            return None
        finally:
            conn.close()

    def list_models(self) -> List[ModelProfile]:
        """Lists registered models."""
        conn = self._db._get_connection()
        try:
            rows = conn.execute("SELECT * FROM platform_models").fetchall()
            return [
                ModelProfile(
                    model_id=r["model_id"],
                    name=r["name"],
                    provider_id=r["provider_id"],
                    version=r["version"],
                    capabilities=r["capabilities"].split(",") if r["capabilities"] else [],
                    is_active=bool(r["is_active"]),
                    is_default=bool(r["is_default"]),
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {}
                ) for r in rows
            ]
        finally:
            conn.close()

    def set_active_status(self, model_id: str, is_active: bool) -> bool:
        profile = self.get_model(model_id)
        if not profile:
            return False
        profile.is_active = is_active
        self.register_model(profile)
        return True

    def clear(self) -> None:
        """Clears model DB for testing."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM platform_models")
                conn.commit()
            finally:
                conn.close()
