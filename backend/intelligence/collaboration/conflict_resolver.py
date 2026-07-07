"""Processes and reports conflicts detected across multi-agent evidence pools."""

from typing import List, Any


class ConflictResolver:
    """Formats and isolates contradictory statements for collaboration logs."""

    def identify_conflicts(self, reasoning_report: Any) -> List[str]:
        """Summarizes unresolved conflicts from the reasoning report."""
        unresolved = []
        for c in reasoning_report.detected_conflicts:
            if c.severity == "High":
                unresolved.append(f"High Conflict [{c.category}]: {c.description}")
            else:
                unresolved.append(f"Anomaly [{c.category}]: {c.description}")
        return unresolved
