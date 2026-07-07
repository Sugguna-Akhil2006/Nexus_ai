"""Sorts plugins topologically and detects missing or circular dependencies."""

from typing import Dict, List, Set
from backend.plugins.models import PluginManifest


class DependencyResolver:
    """Verifies dependency constraints and calculates plugin load order."""

    def resolve_load_order(self, manifests: Dict[str, PluginManifest]) -> List[str]:
        """Calculates topological load order. Throws ValueError on cycles or missing links."""
        load_order: List[str] = []
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def dfs(name: str) -> None:
            if name in visiting:
                raise ValueError(f"Circular dependency detected involving plugin '{name}'.")
            if name in visited:
                return

            # Retrieve manifest
            manifest = manifests.get(name)
            if not manifest:
                raise ValueError(f"Missing dependency plugin: '{name}'.")

            visiting.add(name)

            # Visit all dependencies
            for dep_name in manifest.dependencies.keys():
                dfs(dep_name)

            visiting.remove(name)
            visited.add(name)
            load_order.append(name)

        for name in manifests.keys():
            dfs(name)

        return load_order
