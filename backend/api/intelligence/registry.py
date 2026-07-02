"""API-level registry listing active modules and capabilities."""

from typing import List

from backend.intelligence.core.registry import IntelligenceRegistry


class GatewayRegistry:
    """Proxy registry interface listing active module entries and capabilities."""

    def __init__(self) -> None:
        self.core_registry = IntelligenceRegistry()

    def list_modules(self) -> List[str]:
        """Lists active module identifiers."""
        return self.core_registry.list_modules()

    def list_capabilities(self) -> List[str]:
        """Deduplicates capabilities across all registered modules."""
        caps = set()
        for name in self.core_registry.list_modules():
            m = self.core_registry.get_module(name)
            caps.update(m.capabilities)
        return list(caps)
