"""AgentPackager - package, export, and version management for ADK agents."""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sdk.adk.models import AgentConfig


@dataclass
class PackageManifest:
    """Metadata for a packaged ADK agent.

    Attributes:
        agent_name: Agent identifier.
        version: Semantic version of the package.
        created_at: ISO timestamp of packaging time.
        runtime_version: Target Nexus Runtime version.
        sdk_version: ADK SDK version.
        dependencies: External package dependencies.
        checksum: SHA256 hex digest of the archive.
    """

    agent_name: str
    version: str
    created_at: str
    runtime_version: str = "1.0.0"
    sdk_version: str = "1.0.0"
    dependencies: List[str] = None  # type: ignore[assignment]
    checksum: str = ""

    def __post_init__(self) -> None:
        if self.dependencies is None:
            self.dependencies = []


class AgentPackager:
    """Packages ADK agent configurations into distributable archives.

    Supports:
    - Packing agent config into a versioned ``.nxpkg`` zip archive.
    - Exporting plugin manifests.
    - Listing available versions.

    Example::

        packager = AgentPackager()
        path = packager.package(agent_config, output_dir="/dist")
        manifest = packager.inspect(path)
    """

    PACKAGE_EXTENSION = ".nxpkg"

    def package(
        self,
        config: AgentConfig,
        output_dir: str = ".",
        dependencies: Optional[List[str]] = None,
    ) -> str:
        """Packages the agent configuration into a ``.nxpkg`` archive.

        Args:
            config: Agent configuration to package.
            output_dir: Target directory for the output archive.
            dependencies: Optional list of ``requirements.txt``-style dep strings.

        Returns:
            Absolute path to the generated ``.nxpkg`` archive.
        """
        os.makedirs(output_dir, exist_ok=True)

        safe_name = config.name.lower().replace(" ", "_")
        archive_name = f"{safe_name}-{config.version}{self.PACKAGE_EXTENSION}"
        archive_path = os.path.join(output_dir, archive_name)

        manifest = PackageManifest(
            agent_name=config.name,
            version=config.version,
            created_at=datetime.utcnow().isoformat(),
            dependencies=list(dependencies or []),
        )

        # Serialize config (excluding non-serializable callables)
        config_dict = {
            "name": config.name,
            "description": config.description,
            "version": config.version,
            "model_id": config.model_id,
            "provider_id": config.provider_id,
            "memory_backend": config.memory_backend,
            "system_prompt": config.system_prompt,
            "metadata": config.metadata,
            "tools": [t.name for t in config.tools],
            "workflow_steps": [s.name for s in config.workflow_steps],
        }

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(asdict(manifest), indent=2))
            zf.writestr("agent_config.json", json.dumps(config_dict, indent=2))

        # Compute checksum
        import hashlib
        sha = hashlib.sha256()
        with open(archive_path, "rb") as f:
            sha.update(f.read())
        manifest.checksum = sha.hexdigest()

        # Re-write manifest with checksum
        with zipfile.ZipFile(archive_path, "a") as zf:
            zf.writestr("checksum.txt", manifest.checksum)

        return os.path.abspath(archive_path)

    def inspect(self, archive_path: str) -> PackageManifest:
        """Reads and returns the manifest from a ``.nxpkg`` archive.

        Args:
            archive_path: Path to the archive file.

        Returns:
            PackageManifest extracted from the archive.

        Raises:
            FileNotFoundError: If the archive does not exist.
            KeyError: If manifest.json is missing from the archive.
        """
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Package archive not found: {archive_path}")

        with zipfile.ZipFile(archive_path, "r") as zf:
            manifest_data = json.loads(zf.read("manifest.json"))

        return PackageManifest(**manifest_data)

    def list_packages(self, search_dir: str = ".") -> List[str]:
        """Lists all ``.nxpkg`` archives in the given directory.

        Args:
            search_dir: Directory to scan.

        Returns:
            List of absolute archive file paths.
        """
        packages = []
        for fname in os.listdir(search_dir):
            if fname.endswith(self.PACKAGE_EXTENSION):
                packages.append(os.path.abspath(os.path.join(search_dir, fname)))
        return sorted(packages)
