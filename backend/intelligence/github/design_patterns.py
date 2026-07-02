"""Identifies code design patterns like Factory, Singleton, Strategy, and Builder."""

from typing import List
from backend.intelligence.github.repository import GitRepositoryReader


class DesignPatternDetector:
    """Identifies structural and behavioral patterns in source code."""

    def detect_patterns(self, reader: GitRepositoryReader) -> List[str]:
        """Scans codebase to discover design patterns.

        Args:
            reader: Repository reader context.

        Returns:
            List[str]: Names of detected patterns.
        """
        files = reader.scan_files()
        patterns = set()

        for f in files:
            content = reader.read_file(f).lower()
            
            # Simple keyword checks in code content
            if "class" in content and "singleton" in content or "instance" in content and "get_instance" in content:
                patterns.add("Singleton Pattern")
            if "class" in content and ("factory" in content or "create_" in content and "type" in content):
                patterns.add("Factory Pattern")
            if "class" in content and ("builder" in content or "with_" in content or ".build()" in content):
                patterns.add("Builder Pattern")
            if "class" in content and ("strategy" in content or "interface" in content or "execute" in content and "context" in content):
                patterns.add("Strategy Pattern")

        return list(patterns)
