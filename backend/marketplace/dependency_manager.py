"""Dependency manager resolving packages, conflicts, trees, and circular references."""

from typing import Dict, List, Set, Optional, Union, Callable
from backend.marketplace.models import PackageMetadata
from backend.marketplace.version_manager import VersionManager


class DependencyResolutionError(Exception):
    """Exception raised when dependency resolution fails."""
    pass


class DependencyManager:
    """Solves installation dependencies, validating constraints and tree hierarchies."""

    def __init__(self, available_packages: Union[Dict[str, List[PackageMetadata]], Callable[[], Dict[str, List[PackageMetadata]]]]) -> None:
        self._available_packages_source = available_packages

    @property
    def available_packages(self) -> Dict[str, List[PackageMetadata]]:
        """Returns the dictionary mapping of available packages."""
        if callable(self._available_packages_source):
            return self._available_packages_source()
        return self._available_packages_source

    def resolve_dependencies(
        self,
        package_id: str,
        version: str,
        installed_packages: Optional[Dict[str, str]] = None
    ) -> List[PackageMetadata]:
        """Resolves dependency tree for a package. Returns a topologically sorted install order.

        Args:
            package_id: Target package ID.
            version: Target version.
            installed_packages: Dict of currently installed package_id -> version.

        Returns:
            List[PackageMetadata]: Installation sequence (dependencies first, target last).

        Raises:
            DependencyResolutionError: On circular dependency, conflict, or missing package.
        """
        # Track path for circular dependency detection
        path: List[str] = []
        # Final ordered list of packages to install/update
        resolved_sequence: List[PackageMetadata] = []
        # Package ID -> resolved version metadata
        resolved_map: Dict[str, PackageMetadata] = {}

        # Merge installed packages as initial state to avoid re-resolving unless needed
        current_state = dict(installed_packages or {})

        def dfs(p_id: str, ver_constraint: str) -> None:
            if p_id in path:
                cycle = " -> ".join(path + [p_id])
                raise DependencyResolutionError(f"Circular dependency detected: {cycle}")

            # Find matching package version
            candidates = self.available_packages.get(p_id, [])
            if not candidates:
                raise DependencyResolutionError(f"Missing package: '{p_id}' required by dependencies.")

            # Filter candidates by version constraint
            matching_metadata = None
            # Search highest version first
            sorted_candidates = sorted(
                candidates,
                key=lambda m: VersionManager.parse_version(m.version),
                reverse=True
            )
            for cand in sorted_candidates:
                if VersionManager.matches_all_constraints(cand.version, ver_constraint):
                    matching_metadata = cand
                    break

            if not matching_metadata:
                raise DependencyResolutionError(
                    f"No matching version found for '{p_id}' satisfying '{ver_constraint}'."
                )

            # Check if this package is already resolved
            existing_resolved = resolved_map.get(p_id)
            if existing_resolved:
                # Validate compatibility of new constraint with already resolved version
                if not VersionManager.matches_all_constraints(existing_resolved.version, ver_constraint):
                    raise DependencyResolutionError(
                        f"Version conflict: '{p_id}' already resolved to '{existing_resolved.version}', "
                        f"but constraint '{ver_constraint}' is required."
                    )
                return

            # Check if already installed version matches the constraint
            already_installed_ver = current_state.get(p_id)
            if already_installed_ver:
                if VersionManager.matches_all_constraints(already_installed_ver, ver_constraint):
                    # No need to reinstall or update
                    return

            # Resolve its dependencies first
            path.append(p_id)
            for dep_id, dep_constraint in matching_metadata.dependencies.items():
                dfs(dep_id, dep_constraint)
            path.pop()

            resolved_map[p_id] = matching_metadata
            resolved_sequence.append(matching_metadata)

        # Kickoff DFS
        dfs(package_id, f"=={version}")
        return resolved_sequence
