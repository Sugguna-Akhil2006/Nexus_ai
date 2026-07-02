"""Registry to manage and discover registered intelligence modules."""

import threading
from typing import Dict, List, Set

from backend.intelligence.core.base_intelligence import BaseIntelligenceModule
from backend.intelligence.core.exceptions import RegistryError


class IntelligenceRegistry:
    """Thread-safe singleton registry allowing modules to register and be searched by capability."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "IntelligenceRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._modules = {}
            return cls._instance

    def register(self, module: BaseIntelligenceModule) -> None:
        """Registers an intelligence module.

        Args:
            module: Subclass of BaseIntelligenceModule.
        """
        with self._lock:
            self._modules[module.name] = module

    def get_module(self, name: str) -> BaseIntelligenceModule:
        """Retrieves a registered module by name.

        Args:
            name: Unique module identifier name.

        Returns:
            BaseIntelligenceModule: Target module instance.

        Raises:
            RegistryError: If module is not found.
        """
        with self._lock:
            if name not in self._modules:
                raise RegistryError(f"Module '{name}' is not registered.")
            return self._modules[name]

    def get_modules_by_capability(self, capability: str) -> List[BaseIntelligenceModule]:
        """Finds all modules matching a capability name.

        Args:
            capability: Capability string search key.

        Returns:
            List[BaseIntelligenceModule]: Matches.
        """
        with self._lock:
            return [m for m in self._modules.values() if capability in m.capabilities]

    def list_modules(self) -> List[str]:
        """Lists all registered modules names."""
        with self._lock:
            return list(self._modules.keys())
