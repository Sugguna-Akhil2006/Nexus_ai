"""Registry catalog storing available collaborative agent execution handlers."""

from typing import Dict, List, Optional, Callable


class AgentRegistry:
    """Thread-safe catalog directory mapping names to handler function routines."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}

    def register_agent(self, name: str, handler: Callable) -> None:
        """Registers a handler function under an agent name."""
        self._handlers[name] = handler

    def get_agent_handler(self, name: str) -> Optional[Callable]:
        """Fetches the registered handler by agent name."""
        return self._handlers.get(name)

    def list_agents(self) -> List[str]:
        """Lists registered agent name tags."""
        return list(self._handlers.keys())
