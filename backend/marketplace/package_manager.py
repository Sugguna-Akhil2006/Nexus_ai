"""Local package manager tracking installed packages, enabled states, and backups."""

import threading
from datetime import datetime
from typing import Dict, List, Optional
from backend.marketplace.models import InstalledPackage, PackageMetadata, PackageType


class PackageManager:
    """Manages the state and lifecycles of locally installed extensions."""

    def __init__(self) -> None:
        self._installed: Dict[str, InstalledPackage] = {}  # package_id -> InstalledPackage
        self._lock = threading.RLock()

    def install_local(self, metadata: PackageMetadata, package_type: PackageType) -> InstalledPackage:
        """Registers a package as locally installed, managing backups if updating."""
        with self._lock:
            p_id = metadata.package_id
            now = datetime.utcnow().isoformat()
            
            if p_id in self._installed:
                existing = self._installed[p_id]
                # Archive current version to backups before updating
                backups = list(existing.backup_versions)
                if existing.metadata.version not in backups:
                    backups.append(existing.metadata.version)
                
                installed = InstalledPackage(
                    metadata=metadata,
                    package_type=package_type,
                    enabled=existing.enabled,
                    installed_at=existing.installed_at,
                    updated_at=now,
                    backup_versions=backups
                )
            else:
                installed = InstalledPackage(
                    metadata=metadata,
                    package_type=package_type,
                    enabled=True,
                    installed_at=now
                )

            self._installed[p_id] = installed
            return installed

    def uninstall_local(self, package_id: str) -> Optional[InstalledPackage]:
        """Removes a package from the local registry."""
        with self._lock:
            return self._installed.pop(package_id, None)

    def enable_local(self, package_id: str) -> bool:
        """Enables an installed package."""
        with self._lock:
            if package_id in self._installed:
                self._installed[package_id].enabled = True
                return True
            return False

    def disable_local(self, package_id: str) -> bool:
        """Disables an installed package."""
        with self._lock:
            if package_id in self._installed:
                self._installed[package_id].enabled = False
                return True
            return False

    def get_installed(self, package_id: str) -> Optional[InstalledPackage]:
        """Gets an installed package record by ID."""
        with self._lock:
            return self._installed.get(package_id)

    def list_installed(self) -> List[InstalledPackage]:
        """Returns all installed packages."""
        with self._lock:
            return list(self._installed.values())

    def get_installed_versions(self) -> Dict[str, str]:
        """Returns package_id -> active version mappings for all installed packages."""
        with self._lock:
            return {p_id: pkg.metadata.version for p_id, pkg in self._installed.items()}
