"""Workspace History service aggregating historical analyses from all domains."""

import json
from typing import Any, Dict, List
from backend.api.sqlite_mock import DBStorage
from backend.product.history_service import HistoryService, HistoryRecord


class WorkspaceHistoryService:
    """Consolidates analysis histories from Resume, GitHub, Document, and custom report domains."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._history = HistoryService()

    def get_consolidated_history(self, workspace_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieves and parses history entries across all supported domains, sorted newest-first."""
        # Query product_history table managed by the history_service
        records = self._history.list(workspace_id=workspace_id, limit=limit, offset=offset)
        history_list = []
        for r in records:
            history_list.append(r.model_dump())
        
        # Pull any old legacy tables if needed, or simply return product_history records
        # since everything now saves to the unified product_history table.
        return history_list
