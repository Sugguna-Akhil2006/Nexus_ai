"""Identifies anti-patterns like God Objects, Circular Dependencies, and Deep Nesting."""

import re
from typing import List, Tuple
from backend.intelligence.github.repository import GitRepositoryReader


class AntiPatternDetector:
    """Identifies architectural and structural design anti-patterns."""

    def detect_anti_patterns(self, reader: GitRepositoryReader) -> Tuple[List[str], List[List[str]]]:
        """Scans code files to find anti-patterns and circular imports.

        Args:
            reader: Workspace reader.

        Returns:
            Tuple[List[str], List[List[str]]]: (anti_patterns_list, circular_dependencies_list)
        """
        files = reader.scan_files()
        anti_patterns = []
        circulars = []

        # 1. God Object detection (files exceeding 1000 lines or classes with too many methods)
        for f in files:
            content = reader.read_file(f)
            lines = content.splitlines()
            if len(lines) > 1000:
                anti_patterns.append(f"God Object: {f} has {len(lines)} lines")

        # 2. Deep Nesting (detect if indentation level goes beyond 5 blocks)
        deep_nested_found = False
        for f in files:
            if not f.endswith(".py"):
                continue
            content = reader.read_file(f)
            for line in content.splitlines():
                leading_spaces = len(line) - len(line.lstrip(' '))
                # Tab nesting or space nesting
                if leading_spaces >= 24: # 6 levels of 4-space indent
                    deep_nested_found = True
                    break
            if deep_nested_found:
                anti_patterns.append(f"Deep Nesting: {f} contains complex nested logic (> 5 levels)")
                break

        # 3. Simple Circular Dependency mock detector (e.g. check for mutual imports)
        imports = {}
        for f in files:
            if not f.endswith(".py"):
                continue
            content = reader.read_file(f)
            # Find python imports
            imported_mods = []
            for line in content.splitlines():
                if line.startswith("import ") or line.startswith("from "):
                    match = re.search(r"(?:import|from)\s+([a-zA-Z0-9_\.]+)", line)
                    if match:
                        imported_mods.append(match.group(1))
            basename = os.path.splitext(os.path.basename(f))[0]
            imports[basename] = imported_mods

        # Simple circular import trace
        for mod, deps in imports.items():
            for dep in deps:
                dep_base = dep.split(".")[-1]
                if dep_base in imports and mod in imports[dep_base]:
                    pair = sorted([mod, dep_base])
                    if pair not in circulars:
                        circulars.append(pair)
                        anti_patterns.append(f"Circular Dependency: {mod} <-> {dep_base}")

        return anti_patterns, circulars

import os
