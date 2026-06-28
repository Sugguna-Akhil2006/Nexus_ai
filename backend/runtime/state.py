from typing import Any, Dict


class State:
    """Represents the runtime state of agents and workflows."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """Set a state variable."""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state variable."""
        return self._data.get(key, default)

    def clear(self) -> None:
        """Clear all state variables."""
        self._data.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return self._data.copy()
