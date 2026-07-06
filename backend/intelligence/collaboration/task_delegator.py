"""Coordinates task dispatches between agents, applying retries and timeout wrappers."""

import time
from typing import Dict, Any, Optional
from backend.intelligence.collaboration.models import AgentTask
from backend.intelligence.collaboration.shared_context import SharedContext
from backend.intelligence.collaboration.agent_registry import AgentRegistry


class TaskDelegator:
    """Invokes agent handler functions, reporting progress and executing retries."""

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    def delegate_task(
        self,
        task: AgentTask,
        context: SharedContext,
        retry_count: int = 2
    ) -> Optional[Dict[str, Any]]:
        """Invokes target receiver agent handler, running retries on exception throw."""
        handler = self.registry.get_agent_handler(task.receiver_agent)
        if not handler:
            task.status = "FAILED"
            raise ValueError(f"Receiver agent '{task.receiver_agent}' not registered in catalog.")

        task.status = "RUNNING"
        last_err = None

        for attempt in range(retry_count + 1):
            try:
                # Add receiver to execution tracking in shared context
                context.add_executed_agent(task.receiver_agent)
                
                # Execute agent routine
                start = time.perf_counter()
                result = handler(task.payload, context)
                duration = round(time.perf_counter() - start, 4)
                
                # Record timeline
                context.record_timeline_step(task.receiver_agent, f"execute_task:{task.description}", duration)
                
                task.status = "COMPLETED"
                task.result = result
                return result
            except Exception as e:
                last_err = e
                time.sleep(0.05)

        task.status = "FAILED"
        raise RuntimeError(
            f"Delegation to agent '{task.receiver_agent}' failed after {retry_count} retries. "
            f"Last error: {str(last_err)}"
        ) from last_err
