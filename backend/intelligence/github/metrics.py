"""Computes code size, file counts, and overall metrics for a codebase."""

from typing import Dict, Any
from backend.intelligence.github.repository import GitRepositoryReader


class RepositoryMetricsCollector:
    """Collects repository volumes and metrics (lines, file counts)."""

    def collect_metrics(self, reader: GitRepositoryReader) -> Dict[str, Any]:
        """Scans code files and sums total files and line counts.

        Args:
            reader: Repository reader context.

        Returns:
            Dict[str, Any]: Collected metrics dictionary.
        """
        files = reader.scan_files()
        total_lines = 0
        file_count = 0

        for f in files:
            # Only count lines of common source files
            content = reader.read_file(f)
            lines = content.count("\n") + 1 if content else 0
            total_lines += lines
            file_count += 1

        return {
            "file_count": file_count,
            "total_lines": total_lines
        }
