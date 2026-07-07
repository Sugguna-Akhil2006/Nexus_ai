"""Workflow Inspector visualizer DAG and execution routes."""

from __future__ import annotations

from typing import List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.studio.models import WorkflowInspection, WorkflowNode


class WorkflowInspector:
    """Inspects and builds graphical DAG nodes for workflows."""

    def __init__(self) -> None:
        self._db = DBStorage()

    def inspect_workflow(self, workflow_id: str) -> Optional[WorkflowInspection]:
        """Resolves workflow schema structure and converts it to displayable nodes/edges."""
        conn = self._db._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM workflow_definitions WHERE definition_id = ?",
                (workflow_id,)
            ).fetchone()
            if not row:
                return None

            # Build mock nodes representing standard DAG execution steps
            nodes = [
                WorkflowNode("start", "Trigger Event", "task", "completed", 5.0),
                WorkflowNode("step1", "Extract Parameters", "task", "completed", 12.0),
                WorkflowNode("decision1", "Validate Constraints", "decision", "completed", 2.0),
                WorkflowNode("step2", "Run Agent Process", "parallel", "completed", 120.0),
                WorkflowNode("end", "Compile Final Report", "end", "completed", 10.0)
            ]

            edges = [
                {"source": "start", "target": "step1"},
                {"source": "step1", "target": "decision1"},
                {"source": "decision1", "target": "step2"},
                {"source": "step2", "target": "end"}
            ]

            return WorkflowInspection(
                workflow_id=row["definition_id"],
                name=row["name"],
                nodes=nodes,
                edges=edges,
                total_execution_time_ms=149.0
            )
        except Exception:
            return None
        finally:
            conn.close()
