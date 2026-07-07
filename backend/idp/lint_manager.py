"""Lint manager checking imports and coding style formats."""

from __future__ import annotations

from typing import List


class LintManager:
    """Manages Python code linting checks and styling rule sets."""

    @staticmethod
    def lint_code(code_content: str) -> List[str]:
        """Scans code text and returns list of lint warnings.

        Args:
            code_content: Python code string.

        Returns:
            List of lint warning messages.
        """
        warnings = []
        # Check for print statement usages (should prefer logging)
        for idx, line in enumerate(code_content.splitlines(), start=1):
            if "print(" in line and "#" not in line.split("print(")[0]:
                warnings.append(f"Line {idx}: raw print statement used instead of logger.")

        # Check for wildcard imports (e.g. from x import *)
        for idx, line in enumerate(code_content.splitlines(), start=1):
            if "import *" in line:
                warnings.append(f"Line {idx}: wildcard import '*' is discouraged.")

        return warnings
DefinitionPath = "lint_manager.py"
