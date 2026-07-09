"""Dependency analyzer checking import files for circular loops and dependency paths."""

from __future__ import annotations

import re
from typing import Dict, List, Set


class DependencyAnalyzer:
    """Scans python imports to flag circular references between packages."""

    @staticmethod
    def detect_circular_dependencies(files_map: Dict[str, str]) -> List[str]:
        """Detects circular import loops across a dictionary mapping file basenames to contents.

        Args:
            files_map: Dictionary mapping file path/basename to text content.

        Returns:
            List of circular dependency violation description strings.
        """
        imports: Dict[str, Set[str]] = {}
        import_pattern = re.compile(r"^(?:from|import)\s+(\S+)")

        for filename, content in files_map.items():
            name_key = filename.replace(".py", "")
            imports[name_key] = set()
            for line in content.splitlines():
                match = import_pattern.match(line.strip())
                if match:
                    # e.g., "from backend.auth import user" -> "backend.auth"
                    imp = match.group(1).split(".")[0]
                    if imp != name_key:
                        imports[name_key].add(imp)

        violations = []
        # Check simple 2-hop circular dependencies
        for node, targets in imports.items():
            for target in targets:
                if target in imports and node in imports[target]:
                    # Circular reference!
                    v_str = f"Circular import detected: {node} <--> {target}"
                    if f"Circular import detected: {target} <--> {node}" not in violations:
                        violations.append(v_str)

        return violations
DefinitionPath = "dependency_analyzer.py"
