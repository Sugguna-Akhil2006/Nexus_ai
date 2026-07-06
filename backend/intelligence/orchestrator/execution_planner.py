"""Formulates parallel and sequential execution plans for orchestrated steps."""

import uuid
from typing import List, Dict, Any
from backend.intelligence.orchestrator.models import OrchestrationPlan, ExecutionStep


class ExecutionPlanner:
    """Constructs step sequences and maps concurrency execution modes."""

    def create_plan(
        self,
        modules: List[str],
        options: Dict[str, Any]
    ) -> OrchestrationPlan:
        """Formulates execution plans mapping step sequences and dependencies."""
        steps = []
        for mod in modules:
            steps.append(ExecutionStep(
                step_id=f"step-{mod.lower()}-{str(uuid.uuid4())[:4]}",
                module_name=mod,
                action="analyze"
            ))

        # Default concurrency mode
        mode = "PARALLEL"
        if options.get("sequential", False) or options.get("execution_mode") == "SEQUENTIAL":
            mode = "SEQUENTIAL"

        return OrchestrationPlan(
            plan_id=f"plan-orch-{str(uuid.uuid4())[:8]}",
            steps=steps,
            execution_mode=mode
        )
