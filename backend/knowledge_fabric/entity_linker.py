"""Entity Linker resolving variations of names into canonical entity IDs."""

from __future__ import annotations

import re
from typing import Dict


class EntityLinker:
    """Matches text keywords against canonical names, resolving duplicates."""

    def __init__(self) -> None:
        self._canonical_map: Dict[str, str] = {
            "fastapi": "FastAPI",
            "fast-api": "FastAPI",
            "python3": "Python",
            "python": "Python",
            "sqlite3": "SQLite",
            "sqlite": "SQLite",
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL"
        }

    def resolve_canonical_name(self, raw_name: str) -> str:
        """Standardizes name casing and mappings."""
        clean = re.sub(r"\s+", "", raw_name).lower()
        return self._canonical_map.get(clean, raw_name.strip())

    def generate_entity_id(self, canonical_name: str) -> str:
        """Builds clean identifier string."""
        return f"ent-{re.sub(r'[^a-zA-Z0-9]', '', canonical_name).lower()}"
