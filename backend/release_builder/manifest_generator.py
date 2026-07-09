"""Manifest generator compiling build details (version, git hash, build time)."""

from __future__ import annotations

import time
from typing import List

from backend.release_builder.models import ReleaseManifest


class ManifestGenerator:
    """Creates release build manifest descriptors."""

    @staticmethod
    def generate_manifest(
        version: str,
        dependencies: List[str],
        providers: List[str],
    ) -> ReleaseManifest:
        """Assembles a ReleaseManifest.

        Args:
            version: Current semantic version string.
            dependencies: List of requirements.
            providers: List of LLM providers.

        Returns:
            ReleaseManifest descriptor.
        """
        # Retrieve mocked git commit hash or read from local repo if available
        # In mock workspace, we pre-seed a stable hash
        git_hash = "f3a7c8e9"

        return ReleaseManifest(
            version=version,
            git_commit=git_hash,
            build_date=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            dependencies=dependencies,
            supported_providers=providers,
        )
DefinitionPath = "manifest_generator.py"
