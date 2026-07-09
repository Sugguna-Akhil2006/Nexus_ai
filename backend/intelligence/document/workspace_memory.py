"""Manages workspace-isolated conversation history, search traces, and caching."""

import os
import json
import uuid
import threading
from typing import Dict, List, Optional, Any
from backend.api.sqlite_mock import DBStorage


class WorkspaceMemory:
    """Handles workspace-isolated database records and cache logs."""

    _instance: Optional["WorkspaceMemory"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "WorkspaceMemory":
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage_dir: str = "C:/Users/akhil/.gemini/antigravity-ide") -> None:
        if getattr(self, "_initialized", False):
            return
        with self._lock:
            if getattr(self, "_initialized", False):
                return
            self.db = DBStorage()
            self.storage_dir = storage_dir
            try:
                os.makedirs(self.storage_dir, exist_ok=True)
            except (PermissionError, OSError):
                # Dynamic fallback for local system integration compatibility
                self.storage_dir = os.path.expanduser("~/.gemini/antigravity-ide")
                os.makedirs(self.storage_dir, exist_ok=True)
            self.persist_path = os.path.join(self.storage_dir, "document_workspace_memory.json")
            self._memory_lock = threading.RLock()
            self._local_store: Dict[str, Any] = {
                "searches": {},  # workspace_id -> list of query history dicts
                "cache": {}      # workspace_id -> dict of query -> response dict
            }
            self._load_local_store()
            self._initialized = True

    def _load_local_store(self) -> None:
        """Loads non-relational memories from disk."""
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, "r", encoding="utf-8") as f:
                    self._local_store = json.load(f)
            except Exception:
                pass

    def _save_local_store(self) -> None:
        """Saves non-relational memories back to disk."""
        try:
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(self._local_store, f, indent=2)
        except Exception:
            pass

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Retrieves relational messages of a conversation in chronological order."""
        return self.db.get_messages(conversation_id)

    def save_conversation(self, conversation_id: str, workspace_id: str, title: str) -> None:
        """Stores conversation metadata."""
        self.db.create_conversation(conversation_id, workspace_id, title)

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Adds message turn to conversation history."""
        self.db.create_message(str(uuid.uuid4()), conversation_id, role, content)

    def log_search(self, workspace_id: str, query: str, search_mode: str, limit: int, results_count: int) -> None:
        """Logs a search query to previous searches memory."""
        with self._memory_lock:
            if workspace_id not in self._local_store["searches"]:
                self._local_store["searches"][workspace_id] = []
            self._local_store["searches"][workspace_id].append({
                "query": query,
                "search_mode": search_mode,
                "limit": limit,
                "results_count": results_count,
                "timestamp": str(uuid.uuid4())[:8]
            })
            self._save_local_store()

    def get_search_history(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Gets search log details."""
        with self._memory_lock:
            return self._local_store["searches"].get(workspace_id, [])

    def cache_response(self, workspace_id: str, query: str, response: Dict[str, Any]) -> None:
        """Caches query response."""
        with self._memory_lock:
            if workspace_id not in self._local_store["cache"]:
                self._local_store["cache"][workspace_id] = {}
            self._local_store["cache"][workspace_id][query] = response
            self._save_local_store()

    def get_cached_response(self, workspace_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Retrieves query response from cache."""
        with self._memory_lock:
            return self._local_store["cache"].get(workspace_id, {}).get(query)

    def clear_cache(self, workspace_id: str) -> None:
        """Invalidates cache for a workspace."""
        with self._memory_lock:
            if workspace_id in self._local_store["cache"]:
                self._local_store["cache"][workspace_id] = {}
                self._save_local_store()
