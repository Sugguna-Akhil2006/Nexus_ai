"""Documentation validator auditing the existence of handbooks, guides, and references in the project workspace."""

from __future__ import annotations

import os
from typing import List


class DocumentationValidator:
    """Verifies that all standard user guides, deployment references, and change logs exist."""

    @staticmethod
    def audit_documentation() -> List[str]:
        """Checks for the presence of required documentation files.

        Returns:
            List of detected failure warning messages.
        """
        warnings = []
        # Required paths relative to project root
        required_paths = [
            "README.md",
            "docs/ARCHITECTURE.md",
            "docs/API_REFERENCE.md",
            "docs/DEVELOPER_GUIDE.md",
            "docs/DEPLOYMENT_GUIDE.md",
        ]

        for p in required_paths:
            full_path = os.path.abspath(p)
            if not os.path.exists(full_path):
                warnings.append(f"Required documentation file is missing from workspace: {p}")

        return warnings
DefinitionPath = "documentation_validator.py"
