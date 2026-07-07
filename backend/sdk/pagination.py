"""Pagination helpers for Nexus AI SDK."""

from __future__ import annotations

from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class Page(Generic[T]):
    """Standard list response wrapper supporting page-based pagination."""

    def __init__(
        self,
        items: List[T],
        next_page: Optional[int] = None,
        prev_page: Optional[int] = None,
        total: Optional[int] = None,
        fetch_next_fn: Optional[Callable[[int], Page[T]]] = None,
    ) -> None:
        self.items = items
        self.next_page = next_page
        self.prev_page = prev_page
        self.total = total
        self._fetch_next_fn = fetch_next_fn

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def has_next(self) -> bool:
        """Returns whether a subsequent page is available."""
        return self.next_page is not None

    def next(self) -> Optional[Page[T]]:
        """Retrieves the next page of items.

        Returns:
            The next Page[T] instance, or None if no more pages.
        """
        if not self.has_next() or not self._fetch_next_fn:
            return None
        return self._fetch_next_fn(self.next_page)  # type: ignore


class Cursor(Generic[T]):
    """Cursor-based iterator for listing entities."""

    def __init__(
        self,
        items: List[T],
        next_cursor: Optional[str] = None,
        fetch_next_fn: Optional[Callable[[str], Cursor[T]]] = None,
    ) -> None:
        self.items = items
        self.next_cursor = next_cursor
        self._fetch_next_fn = fetch_next_fn

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def has_next(self) -> bool:
        """Returns whether a subsequent batch is available."""
        return bool(self.next_cursor)

    def next(self) -> Optional[Cursor[T]]:
        """Retrieves the next batch using the cursor.

        Returns:
            The next Cursor[T] instance, or None if no more batches.
        """
        if not self.has_next() or not self._fetch_next_fn:
            return None
        return self._fetch_next_fn(self.next_cursor)  # type: ignore
