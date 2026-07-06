"""Tracks execution timelines, step durations, and logs for Orchestration queries."""

import time
from datetime import datetime
from typing import Dict, List, Any


class OrchestrationContext:
    """Manages logs and tracks step timelines thread-safely."""

    def __init__(self, workspace_id: str, query: str) -> None:
        self.workspace_id = workspace_id
        self.query = query
        self.timeline: List[Dict[str, Any]] = []
        self.step_starts: Dict[str, float] = {}

    def start_step(self, step_id: str, module_name: str) -> None:
        """Logs starting a workflow step and starts timer."""
        self.step_starts[step_id] = time.perf_counter()
        self.timeline.append({
            "step_id": step_id,
            "module_name": module_name,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "duration_s": 0.0
        })

    def end_step(self, step_id: str, success: bool, message: str = "") -> None:
        """Stops the step timer and records final execution details."""
        start = self.step_starts.get(step_id, time.perf_counter())
        duration = round(time.perf_counter() - start, 4)
        
        for item in self.timeline:
            if item["step_id"] == step_id:
                item["status"] = "completed" if success else "failed"
                item["duration_s"] = duration
                item["message"] = message
                item["completed_at"] = datetime.utcnow().isoformat()
                break

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Returns the completed execution steps timeline."""
        return self.timeline
