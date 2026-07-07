"""Dependency validator checking Python module dependencies and registry state."""

from __future__ import annotations

import sys
from typing import List

from backend.intelligence.core.registry import IntelligenceRegistry


class DependencyValidator:
    """Verifies that all core packages import cleanly and registry duplicates are absent."""

    @staticmethod
    def audit_dependencies() -> List[str]:
        """Scans python imports and registered module names.

        Returns:
            List of detected failure warning messages.
        """
        warnings = []

        # 1. Standard module imports
        required_modules = ["fastapi", "pydantic", "uvicorn", "sqlite3", "concurrent.futures"]
        for m in required_modules:
            if m not in sys.modules and m not in sys.builtin_module_names:
                try:
                    __import__(m)
                except ImportError:
                    warnings.append(f"Required package {m} could not be imported.")

        # 2. Duplicate registrations check
        try:
            registry = IntelligenceRegistry()
            modules = registry.list_modules()
            if len(modules) != len(set(modules)):
                warnings.append("Duplicate intelligence module names detected in the registry.")
        except Exception as e:
            warnings.append(f"Intelligence Registry check failed: {e}")

        return warnings
