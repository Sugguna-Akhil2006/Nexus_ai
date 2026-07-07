"""Provenance Manager tracking validation and evidence arguments."""

from __future__ import annotations

from datetime import datetime
from typing import Dict


class ProvenanceManager:
    """Tracks validations and reasoning arguments for semantic facts."""

    def __init__(self) -> None:
        self._provenance: Dict[str, Dict[str, Any]] = {}

    def log_provenance(self, entity_id: str, reasoning_chain: str) -> None:
        """Stores evidence reasoning chain."""
        self._provenance[entity_id] = {
            "reasoning_chain": reasoning_chain,
            "last_validation": datetime.utcnow().isoformat()
        }

    def get_provenance(self, entity_id: str) -> Dict[str, Any]:
        return self._provenance.get(entity_id, {
            "reasoning_chain": "Default resolved canonical entity fact.",
            "last_validation": datetime.utcnow().isoformat()
        })
