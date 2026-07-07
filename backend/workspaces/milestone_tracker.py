"""Milestone tracker tracking completion metrics for collaborative project phases."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.workspaces.models import ProjectTask, TaskState


class MilestoneTracker:
    """Computes project progress metrics based on task board states."""

    @staticmethod
    def calculate_progress(tasks: List[ProjectTask]) -> Dict[str, Any]:
        """Calculates completed vs total tasks percentages.

        Args:
            tasks: List of ProjectTasks.

        Returns:
            Dict containing progress_pct, total_tasks, and completed_tasks.
        """
        total = len(tasks)
        if total == 0:
            return {
                "progress_pct": 100.0,
                "total_tasks": 0,
                "completed_tasks": 0,
            }

        completed = sum(1 for t in tasks if t.status == TaskState.COMPLETED)
        pct = (completed / total) * 100.0

        return {
            "progress_pct": round(pct, 2),
            "total_tasks": total,
            "completed_tasks": completed,
        }
DefinitionPath = "milestone_tracker.py"
