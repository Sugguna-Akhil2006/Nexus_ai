"""Package registry containing the list of all packages in the marketplace."""

import threading
from typing import Dict, List, Optional
from backend.marketplace.models import MarketplacePackage, PackageMetadata, PackageType


class PackageRegistry:
    """Manages the catalog of available packages in the remote extension marketplace."""

    def __init__(self) -> None:
        self._packages: Dict[str, List[MarketplacePackage]] = {}  # package_id -> list of versions
        self._lock = threading.RLock()

    def register_package(self, package: MarketplacePackage) -> None:
        """Registers/publishes a package in the marketplace catalog."""
        with self._lock:
            p_id = package.metadata.package_id
            if p_id not in self._packages:
                self._packages[p_id] = []
            # Check if this exact version is already registered, if so update it
            existing_index = -1
            for i, p in enumerate(self._packages[p_id]):
                if p.metadata.version == package.metadata.version:
                    existing_index = i
                    break

            if existing_index >= 0:
                self._packages[p_id][existing_index] = package
            else:
                self._packages[p_id].append(package)

    def search_packages(
        self,
        query: Optional[str] = None,
        package_type: Optional[PackageType] = None
    ) -> List[MarketplacePackage]:
        """Searches packages by text query (ID, description, author) and type."""
        with self._lock:
            results = []
            for plist in self._packages.values():
                if not plist:
                    continue
                # Get the latest version to display in search
                latest_pkg = max(plist, key=lambda p: p.metadata.version)
                if package_type and latest_pkg.package_type != package_type:
                    continue

                if query:
                    q = query.lower()
                    meta = latest_pkg.metadata
                    matches = (
                        q in meta.package_id.lower() or
                        q in meta.description.lower() or
                        q in meta.author.lower() or
                        q in latest_pkg.publisher.lower()
                    )
                    if not matches:
                        continue

                results.append(latest_pkg)
            return results

    def get_package_versions(self, package_id: str) -> List[MarketplacePackage]:
        """Returns all registered versions of a package."""
        with self._lock:
            return list(self._packages.get(package_id, []))

    def get_package_metadata(self, package_id: str, version: str) -> Optional[MarketplacePackage]:
        """Retrieves details of a specific package version."""
        with self._lock:
            for p in self._packages.get(package_id, []):
                if p.metadata.version == version:
                    return p
            return None

    def get_latest_package_metadata(self, package_id: str) -> Optional[MarketplacePackage]:
        """Retrieves details of the latest version of a package."""
        with self._lock:
            versions = self.get_package_versions(package_id)
            if not versions:
                return None
            return max(versions, key=lambda p: p.metadata.version)

    def get_all_available_metadata(self) -> Dict[str, List[PackageMetadata]]:
        """Helper for dependency resolution: returns package_id -> list of PackageMetadata."""
        with self._lock:
            return {
                p_id: [p.metadata for p in plist]
                for p_id, plist in self._packages.items()
            }
