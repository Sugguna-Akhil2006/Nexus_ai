"""Low-latency knowledge cache manager handling invalidation gates on workspace changes."""

from typing import Dict, Any, Optional
from backend.intelligence.document.workspace_memory import WorkspaceMemory


class KnowledgeCache:
    """Wrapper coordinating query response cache hits."""

    def __init__(self) -> None:
        self.memory = WorkspaceMemory()

    def lookup(self, workspace_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached response matching query context."""
        return self.memory.get_cached_response(workspace_id, query)

    def store(self, workspace_id: str, query: str, response: Dict[str, Any]) -> None:
        """Saves generated responses to low-latency memory store."""
        self.memory.cache_response(workspace_id, query, response)

    def invalidate(self, workspace_id: str) -> None:
        """Clears all cached queries on modifying document status."""
        self.memory.clear_cache(workspace_id)
