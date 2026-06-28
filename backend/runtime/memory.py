from typing import Any, List


class Memory:
    """Memory base class to store agent context and history."""

    def __init__(self) -> None:
        self.short_term: List[Any] = []

    def add(self, item: Any) -> None:
        """Add an item to memory."""
        self.short_term.append(item)

    def clear(self) -> None:
        """Clear memory."""
        self.short_term.clear()

    def get_all(self) -> List[Any]:
        """Retrieve all items in memory."""
        return self.short_term
