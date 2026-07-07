"""Marketplace client searching packages and fetching details from the registry."""

from typing import List, Optional
from backend.marketplace.models import MarketplacePackage, PackageType
from backend.marketplace.package_registry import PackageRegistry


class MarketplaceClient:
    """Client API interface querying package catalog metadata."""

    def __init__(self, registry: PackageRegistry) -> None:
        self.registry = registry

    def search(self, query: Optional[str] = None, package_type: Optional[PackageType] = None) -> List[MarketplacePackage]:
        """Queries extensions filtering by text search and package type."""
        return self.registry.search_packages(query, package_type)

    def get_details(self, package_id: str, version: Optional[str] = None) -> Optional[MarketplacePackage]:
        """Gets full metadata details of a specific extension version (or latest if unspecified)."""
        if version:
            return self.registry.get_package_metadata(package_id, version)
        return self.registry.get_latest_package_metadata(package_id)
