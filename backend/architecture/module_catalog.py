"""Module catalog inspecting and documenting registered AI modules."""

from __future__ import annotations

from typing import List

from backend.architecture.models import ModuleMetadata
from backend.intelligence.core.registry import IntelligenceRegistry


class ModuleCatalog:
    """Discovers active intelligence modules and structures metadata descriptors."""

    def __init__(self) -> None:
        self.registry = IntelligenceRegistry()

    def get_catalog(self) -> List[ModuleMetadata]:
        """Queries the active registry and formats module metadata catalogs.

        Returns:
            List of ModuleMetadata descriptors.
        """
        registered = self.registry.list_modules()
        catalog = []

        for name in registered:
            purpose = f"Orchestrates collaborative workflows and executes capability algorithms for {name} intelligence."
            dependencies = ["runtime", "memory_engine"]

            # Set dependencies based on module relationships
            if name.lower() == "professional":
                dependencies.extend(["resume", "github", "document"])

            # Map tests
            related_tests = [f"backend.tests.test_{name.lower()}"]

            catalog.append(
                ModuleMetadata(
                    name=name,
                    purpose=purpose,
                    owner="Lead Integration Engineer",
                    dependencies=dependencies,
                    public_apis=[f"POST /v1/{name.lower()}/analyze"],
                    configuration={"cache_enabled": True},
                    related_tests=related_tests,
                )
            )

        # Fallback seeded profiles if registry is empty
        if not catalog:
            catalog = [
                ModuleMetadata(
                    name="Resume",
                    purpose="Extracts candidate career trajectory metadata and profiles ATS compatibility metrics.",
                    owner="Lead Integration Engineer",
                    dependencies=["runtime"],
                    public_apis=["POST /v1/resume/analyze"],
                    configuration={"cache_enabled": True},
                    related_tests=["backend.tests.test_resume"],
                ),
                ModuleMetadata(
                    name="GitHub",
                    purpose="Evaluates repository code maintainability split indices and developer activity scores.",
                    owner="Lead Integration Engineer",
                    dependencies=["runtime"],
                    public_apis=["POST /v1/github/analyze"],
                    configuration={"cache_enabled": True},
                    related_tests=["backend.tests.test_github"],
                ),
            ]

        return catalog
