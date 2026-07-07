"""ToolBuilder - decorator-based tool registration for ADK agents."""

from __future__ import annotations

import functools
import threading
from typing import Any, Callable, Dict, List, Optional

from sdk.adk.models import ToolDefinition


class ToolRegistry:
    """Thread-safe singleton registry holding all registered ADK tools.

    Attributes:
        _tools: Internal mapping of tool name to ToolDefinition.
    """

    _instance: Optional["ToolRegistry"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._tools: Dict[str, ToolDefinition] = {}
                    instance._rlock = threading.RLock()
                    cls._instance = instance
        return cls._instance

    def register(self, tool_def: ToolDefinition) -> None:
        """Registers a tool definition.

        Args:
            tool_def: Fully constructed ToolDefinition.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        with self._rlock:
            if tool_def.name in self._tools:
                raise ValueError(f"Tool '{tool_def.name}' is already registered.")
            self._tools[tool_def.name] = tool_def

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Retrieves a tool by name.

        Args:
            name: Tool name.

        Returns:
            ToolDefinition or None if not found.
        """
        with self._rlock:
            return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """Lists all registered tools.

        Returns:
            List of ToolDefinition instances.
        """
        with self._rlock:
            return list(self._tools.values())

    def clear(self) -> None:
        """Clears the registry (primarily for tests)."""
        with self._rlock:
            self._tools.clear()


def tool(
    name: Optional[str] = None,
    description: str = "",
    parameters: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that registers a function as an ADK tool.

    Can be used with or without arguments::

        @tool
        def search_docs(query: str) -> str:
            ...

        @tool(name="doc_search", description="Searches documentation")
        def search_docs(query: str) -> str:
            ...

    Args:
        name: Optional tool name override (defaults to function name).
        description: Short human-readable description.
        parameters: Parameter schema hints dict.

    Returns:
        Decorated callable registered in the global ToolRegistry.
    """
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name if name else fn.__name__
        tool_description = description or (fn.__doc__ or "").strip()

        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_description,
            fn=fn,
            parameters=parameters or {},
        )

        # Register globally - skip if already registered (idempotent for reloads)
        registry = ToolRegistry()
        try:
            registry.register(tool_def)
        except ValueError:
            pass  # already registered

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **kwargs)

        wrapper._tool_definition = tool_def  # type: ignore[attr-defined]
        return wrapper

    # Allow bare @tool usage (no parentheses)
    if callable(name):
        fn = name
        name = None
        return decorator(fn)

    return decorator
