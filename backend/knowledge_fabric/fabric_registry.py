"""Fabric Registry holding registered categories and schema definitions."""

from __future__ import annotations

from typing import Set


class FabricRegistry:
    """Manages active entity classification schemas."""

    def __init__(self) -> None:
        self._categories: Set[str] = {"skill", "framework", "organization", "language", "document"}

    def is_category_registered(self, category: str) -> bool:
        return category.lower() in self._categories

    def register_category(self, category: str) -> None:
        self._categories.add(category.lower())
