"""Package installer executing installs, updates, rollbacks, and repairs."""

import threading
from datetime import datetime
from typing import Dict, List, Optional
from backend.marketplace.models import InstalledPackage, PackageMetadata, PackageType, MarketplacePackage
from backend.marketplace.package_manager import PackageManager
from backend.marketplace.dependency_manager import DependencyManager
from backend.marketplace.signature_verifier import SignatureVerifier
from backend.marketplace.compatibility_checker import CompatibilityChecker
from backend.runtime.event import Event, EventBus, EventType, EventPriority


class PackageInstaller:
    """Orchestrates package installations, rollbacks, repairs, and emits system events."""

    def __init__(
        self,
        package_manager: PackageManager,
        dependency_manager: DependencyManager,
        signature_verifier: SignatureVerifier,
        compatibility_checker: CompatibilityChecker
    ) -> None:
        self.package_manager = package_manager
        self.dependency_manager = dependency_manager
        self.signature_verifier = signature_verifier
        self.compatibility_checker = compatibility_checker
        self._event_bus = EventBus()
        self._lock = threading.RLock()

    def install(self, package: MarketplacePackage, content_bytes: bytes) -> InstalledPackage:
        """Installs a package and its dependencies, verifying signatures and compatibility."""
        with self._lock:
            metadata = package.metadata
            p_id = metadata.package_id

            try:
                # 1. Verify publisher and signature
                if not self.signature_verifier.verify_signature(metadata, package.publisher):
                    raise ValueError(f"Invalid signature for package '{p_id}' from publisher '{package.publisher}'.")

                # 2. Verify checksum integrity
                if not self.signature_verifier.verify_checksum(metadata, content_bytes):
                    raise ValueError(f"Checksum mismatch for package '{p_id}'. Content may be corrupted.")

                # 3. Check framework compatibility
                if not self.compatibility_checker.is_compatible(metadata):
                    raise ValueError(f"Package '{p_id}' is incompatible with the core system/OS.")

                # 4. Resolve dependencies
                installed_versions = self.package_manager.get_installed_versions()
                # Determine resolution order (dependencies first)
                resolution_order = self.dependency_manager.resolve_dependencies(
                    p_id, metadata.version, installed_versions
                )

                # 5. Install resolved dependencies (we mock contents since they are sub-installations)
                for dep_meta in resolution_order:
                    # In a real environment, we would download the dependency bytes.
                    # Here we register them directly in the package manager.
                    is_update = dep_meta.package_id in installed_versions
                    installed_dep = self.package_manager.install_local(dep_meta, PackageType.PLUGIN)

                    event_type = EventType.PACKAGE_UPDATED if is_update else EventType.PACKAGE_INSTALLED
                    self._event_bus.publish(Event(
                        event_type=event_type,
                        priority=EventPriority.NORMAL,
                        payload={"package_id": dep_meta.package_id, "version": dep_meta.version}
                    ))

                # Get final installed metadata for target package
                is_update = p_id in installed_versions
                target_installed = self.package_manager.get_installed(p_id)
                if not target_installed:
                    raise ValueError("Failed to retrieve installed package record.")

                return target_installed

            except Exception as e:
                self._event_bus.publish(Event(
                    event_type=EventType.PACKAGE_FAILED,
                    priority=EventPriority.HIGH,
                    payload={"package_id": p_id, "error": str(e), "operation": "install"}
                ))
                raise

    def update(self, package: MarketplacePackage, content_bytes: bytes) -> InstalledPackage:
        """Updates an existing package. Syntactic sugar over install."""
        return self.install(package, content_bytes)

    def uninstall(self, package_id: str) -> None:
        """Removes a package from the local environment and publishes package.removed."""
        with self._lock:
            removed = self.package_manager.uninstall_local(package_id)
            if not removed:
                raise ValueError(f"Package '{package_id}' is not installed.")

            self._event_bus.publish(Event(
                event_type=EventType.PACKAGE_REMOVED,
                priority=EventPriority.NORMAL,
                payload={"package_id": package_id, "version": removed.metadata.version}
            ))

    def rollback(self, package_id: str) -> InstalledPackage:
        """Rolls back the package to its previous cached backup version."""
        with self._lock:
            installed = self.package_manager.get_installed(package_id)
            if not installed:
                raise ValueError(f"Package '{package_id}' is not installed.")

            if not installed.backup_versions:
                raise ValueError(f"No rollback target version exists for package '{package_id}'.")

            # Pop the latest backup version
            previous_version = installed.backup_versions.pop()
            
            # In a mock registry environment, we search for previous version details.
            # We construct a mock metadata with the previous version string for restoration.
            old_meta = installed.metadata.model_copy(deep=True)
            old_meta.version = previous_version

            # Re-register as active installed version
            rolled_back = self.package_manager.install_local(old_meta, installed.package_type)
            # Retain the modified backup versions list (minus the version we just rolled back to)
            rolled_back.backup_versions = installed.backup_versions

            self._event_bus.publish(Event(
                event_type=EventType.PACKAGE_UPDATED,
                priority=EventPriority.NORMAL,
                payload={
                    "package_id": package_id,
                    "version": previous_version,
                    "operation": "rollback"
                }
            ))

            return rolled_back

    def enable(self, package_id: str) -> None:
        """Enables a package locally."""
        with self._lock:
            if not self.package_manager.enable_local(package_id):
                raise ValueError(f"Package '{package_id}' is not installed.")

    def disable(self, package_id: str) -> None:
        """Disables a package locally."""
        with self._lock:
            if not self.package_manager.disable_local(package_id):
                raise ValueError(f"Package '{package_id}' is not installed.")

    def repair(self, package: MarketplacePackage, content_bytes: bytes) -> InstalledPackage:
        """Repairs a package installation by re-validating signature, checksum and reinstalling."""
        with self._lock:
            # Re-verify and install
            return self.install(package, content_bytes)
