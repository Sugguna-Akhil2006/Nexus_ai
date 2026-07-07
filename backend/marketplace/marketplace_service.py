"""Marketplace service orchestrating registry, installer, client, and developer console views."""

import threading
from typing import Any, Dict, List, Optional
from backend.marketplace.models import (
    InstalledPackage,
    MarketplacePackage,
    PackageMetadata,
    PackageType,
)
from backend.marketplace.package_registry import PackageRegistry
from backend.marketplace.package_manager import PackageManager
from backend.marketplace.dependency_manager import DependencyManager
from backend.marketplace.signature_verifier import SignatureVerifier
from backend.marketplace.compatibility_checker import CompatibilityChecker
from backend.marketplace.package_installer import PackageInstaller
from backend.marketplace.rating_service import RatingService
from backend.marketplace.marketplace_client import MarketplaceClient
from backend.marketplace.version_manager import VersionManager


class MarketplaceService:
    """Core facade coordinating Extension Marketplace operations and console displays."""

    def __init__(self, core_version: str = "1.0.0") -> None:
        self._lock = threading.RLock()
        self.registry = PackageRegistry()
        self.package_manager = PackageManager()
        
        self.verifier = SignatureVerifier()
        self.compat_checker = CompatibilityChecker(core_version=core_version)
        
        # Build dependency resolver referencing registry catalog
        self.dependency_manager = DependencyManager(self.registry.get_all_available_metadata)
        
        self.installer = PackageInstaller(
            package_manager=self.package_manager,
            dependency_manager=self.dependency_manager,
            signature_verifier=self.verifier,
            compatibility_checker=self.compat_checker
        )
        
        self.rating_service = RatingService(self.registry)
        self.client = MarketplaceClient(self.registry)

    # ------------------------------------------------------------------
    # Public APIs
    # ------------------------------------------------------------------

    def search_marketplace(
        self,
        query: Optional[str] = None,
        package_type: Optional[PackageType] = None
    ) -> List[MarketplacePackage]:
        """Queries extensions on the remote marketplace."""
        with self._lock:
            return self.client.search(query, package_type)

    def get_package_details(self, package_id: str, version: Optional[str] = None) -> Optional[MarketplacePackage]:
        """Retrieves details of a package."""
        with self._lock:
            return self.client.get_details(package_id, version)

    def install_package(self, package_id: str, version: str) -> InstalledPackage:
        """Downloads, verifies, and installs a package from the marketplace."""
        with self._lock:
            pkg = self.registry.get_package_metadata(package_id, version)
            if not pkg:
                raise ValueError(f"Package '{package_id}' version '{version}' not found in registry.")

            # Simulate package file bytes for checksum check
            # Hash of (package_id + version) is stored in mock packages for verification
            simulated_content = f"{package_id}-{version}-data".encode()
            
            # Execute installation flow
            installed = self.installer.install(pkg, simulated_content)
            
            # Increment downloads on success
            self.rating_service.increment_downloads(package_id)
            return installed

    def update_package(self, package_id: str) -> InstalledPackage:
        """Updates an installed package to its latest available version."""
        with self._lock:
            installed = self.package_manager.get_installed(package_id)
            if not installed:
                raise ValueError(f"Package '{package_id}' is not installed locally.")

            latest = self.registry.get_latest_package_metadata(package_id)
            if not latest:
                raise ValueError(f"No marketplace metadata found for package '{package_id}'.")

            # Check if already up-to-date
            if VersionManager.compare_versions(latest.metadata.version, installed.metadata.version) <= 0:
                return installed

            simulated_content = f"{package_id}-{latest.metadata.version}-data".encode()
            return self.installer.update(latest, simulated_content)

    def remove_package(self, package_id: str) -> None:
        """Uninstalls a package."""
        with self._lock:
            self.installer.uninstall(package_id)

    def rollback_package(self, package_id: str) -> InstalledPackage:
        """Rolls back an update to the previously cached backup version."""
        with self._lock:
            return self.installer.rollback(package_id)

    def list_installed_packages(self) -> List[InstalledPackage]:
        """Lists all locally installed packages."""
        with self._lock:
            return self.package_manager.list_installed()

    # ------------------------------------------------------------------
    # Developer Console Data Display
    # ------------------------------------------------------------------

    def get_console_display_data(self, search_query: Optional[str] = None) -> Dict[str, Any]:
        """Compiles package list data specifically formatted for the developer console tab."""
        with self._lock:
            installed = self.list_installed_packages()
            
            # 1. Installed packages display
            installed_display = []
            updates_available = []
            for pkg in installed:
                p_id = pkg.metadata.package_id
                latest = self.registry.get_latest_package_metadata(p_id)
                has_update = False
                latest_version = pkg.metadata.version

                if latest:
                    latest_version = latest.metadata.version
                    if VersionManager.compare_versions(latest_version, pkg.metadata.version) > 0:
                        has_update = True

                pkg_info = {
                    "package_id": p_id,
                    "version": pkg.metadata.version,
                    "package_type": pkg.package_type.value,
                    "author": pkg.metadata.author,
                    "enabled": pkg.enabled,
                    "installed_at": pkg.installed_at,
                    "updated_at": pkg.updated_at,
                    "latest_version": latest_version,
                    "has_update": has_update,
                    "compatibility": self.compat_checker.is_compatible(pkg.metadata)
                }
                installed_display.append(pkg_info)
                if has_update:
                    updates_available.append(pkg_info)

            # 2. Marketplace search results
            search_results = self.search_marketplace(search_query)
            search_display = [
                {
                    "package_id": p.metadata.package_id,
                    "version": p.metadata.version,
                    "package_type": p.package_type.value,
                    "author": p.metadata.author,
                    "publisher": p.publisher,
                    "average_rating": p.average_rating,
                    "ratings_count": p.ratings_count,
                    "downloads": p.downloads,
                    "compatibility": self.compat_checker.is_compatible(p.metadata)
                }
                for p in search_results
            ]

            return {
                "installed_packages": installed_display,
                "updates_available": updates_available,
                "marketplace_search": search_display
            }
