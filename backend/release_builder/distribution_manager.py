"""Distribution manager tracking distribution publishing parameters."""

from __future__ import annotations

from typing import Dict, List


class DistributionManager:
    """Manages Docker registry uploads and PyPI release distribution configurations."""

    @staticmethod
    def get_publishing_details(version: str) -> Dict[str, str]:
        """Returns target URLs and image tag settings for the version."""
        return {
            "docker_image": f"nexus-ai/platform:{version}",
            "docker_registry": "registry.hub.docker.com",
            "pypi_package": f"nexus-ai-platform=={version}",
            "distribution_url": f"https://github.com/Sugguna-Akhil2006/Nexus_ai/releases/tag/v{version}",
        }
DefinitionPath = "distribution_manager.py"
