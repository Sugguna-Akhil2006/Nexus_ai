"""Provider Manager managing enabled states and endpoints mapping for AI Providers."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.runtime.event import Event, EventBus, EventType
from backend.platform.models import ProviderProfile


class ProviderManager:
    """Thread-safe manager for model provider registrations and statuses."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._event_bus = EventBus()
        self._lock = threading.Lock()
        self._init_db()
        self._seed_providers()

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS platform_providers (
                provider_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                api_url TEXT,
                health_status TEXT NOT NULL,
                error_rate REAL NOT NULL
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def _seed_providers(self) -> None:
        defaults = [
            ("openai", "OpenAI", "https://api.openai.com/v1"),
            ("anthropic", "Anthropic", "https://api.anthropic.com/v1"),
            ("gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1"),
            ("ollama", "Ollama", "http://localhost:11434"),
            ("azure", "Azure OpenAI", None),
            ("openrouter", "OpenRouter", "https://openrouter.ai/api/v1")
        ]
        for pid, name, url in defaults:
            if not self.get_provider(pid):
                self.register_provider(ProviderProfile(provider_id=pid, name=name, api_url=url))

    def register_provider(self, profile: ProviderProfile) -> None:
        """Registers or updates a provider details."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("""
                INSERT INTO platform_providers (
                    provider_id, name, is_active, api_url, health_status, error_rate
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_id) DO UPDATE SET
                    name=excluded.name,
                    is_active=excluded.is_active,
                    api_url=excluded.api_url,
                    health_status=excluded.health_status,
                    error_rate=excluded.error_rate
                """, (
                    profile.provider_id,
                    profile.name,
                    1 if profile.is_active else 0,
                    profile.api_url,
                    profile.health_status,
                    profile.error_rate
                ))
                conn.commit()
            finally:
                conn.close()
            
            # Publish event
            self._event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="ProviderManager",
                payload={"event": "provider.registered", "provider_id": profile.provider_id}
            ))

    def get_provider(self, provider_id: str) -> Optional[ProviderProfile]:
        """Retrieves provider profile metadata."""
        conn = self._db._get_connection()
        try:
            r = conn.execute("SELECT * FROM platform_providers WHERE provider_id = ?", (provider_id,)).fetchone()
            if r:
                return ProviderProfile(
                    provider_id=r["provider_id"],
                    name=r["name"],
                    is_active=bool(r["is_active"]),
                    api_url=r["api_url"],
                    health_status=r["health_status"],
                    error_rate=r["error_rate"]
                )
            return None
        finally:
            conn.close()

    def list_providers(self) -> List[ProviderProfile]:
        """Lists registered providers."""
        conn = self._db._get_connection()
        try:
            rows = conn.execute("SELECT * FROM platform_providers").fetchall()
            return [
                ProviderProfile(
                    provider_id=r["provider_id"],
                    name=r["name"],
                    is_active=bool(r["is_active"]),
                    api_url=r["api_url"],
                    health_status=r["health_status"],
                    error_rate=r["error_rate"]
                ) for r in rows
            ]
        finally:
            conn.close()

    def set_active_status(self, provider_id: str, is_active: bool) -> bool:
        """Toggles enable/disable state of a provider."""
        profile = self.get_provider(provider_id)
        if not profile:
            return False
        profile.is_active = is_active
        self.register_provider(profile)
        return True

    def clear(self) -> None:
        """Clears provider DB for testing."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM platform_providers")
                conn.commit()
            finally:
                conn.close()
