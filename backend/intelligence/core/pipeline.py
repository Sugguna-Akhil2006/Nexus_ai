"""Pipeline orchestrator resolving dependencies, running stages, and executing retries."""

import time
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.intelligence.core.context import IntelligenceContext
from backend.intelligence.core.state import ExecutionState
from backend.intelligence.core.workflow import PipelineStage
from backend.intelligence.core.exceptions import StageExecutionError


class IntelligencePipeline:
    """Orchestrates stage execution with concurrency checks, retry policies, and condition gates."""

    def __init__(self) -> None:
        self.stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> None:
        """Appends an execution stage to the pipeline.

        Args:
            stage: PipelineStage instance.
        """
        self.stages.append(stage)

    def execute(self, context: IntelligenceContext, state: ExecutionState, timeout: Optional[float] = None) -> None:
        """Runs the pipeline stages, resolving dependencies and grouping parallel execution steps.

        Args:
            context: Context details.
            state: Thread-safe metrics state tracker.
            timeout: Optional maximum seconds to wait (for cancellation/timeout).
        """
        completed = set()
        pending = list(self.stages)
        start_pipeline = time.perf_counter()

        while pending:
            # Check timeout
            if timeout and (time.perf_counter() - start_pipeline) > timeout:
                state.status = "cancelled"
                break

            # Find all stages whose dependencies are fully resolved
            runnable = [
                s for s in pending 
                if all(dep in completed or dep in state.failed_stages for dep in s.depends_on)
            ]
            if not runnable:
                # Dependency deadlock or cyclic loop
                break

            # Concurrently run stages that do not depend on each other where possible
            if len(runnable) > 1:
                with ThreadPoolExecutor(max_workers=len(runnable)) as executor:
                    futures = {
                        executor.submit(self._run_single_stage_with_retry, stage, context, state): stage
                        for stage in runnable
                    }
                    for f in as_completed(futures):
                        stage = futures[f]
                        try:
                            f.result()
                            completed.add(stage.name)
                        except Exception:
                            # Stage error is already logged inside retry wrapper
                            pass
            else:
                stage = runnable[0]
                try:
                    self._run_single_stage_with_retry(stage, context, state)
                    completed.add(stage.name)
                except Exception:
                    pass

            for s in runnable:
                pending.remove(s)

    def _run_single_stage_with_retry(self, stage: PipelineStage, context: IntelligenceContext, state: ExecutionState) -> None:
        if stage.condition and not stage.condition(context):
            # Condition returned False: skip stage execution
            state.add_warning(stage.name, f"Stage skipped due to condition gate.")
            return

        attempts = 0
        while attempts < stage.max_retries:
            start = time.perf_counter()
            state.start_stage(stage.name)
            try:
                stage.action(context, state)
                state.complete_stage(stage.name, time.perf_counter() - start)
                return
            except Exception as e:
                attempts += 1
                state.record_retry(stage.name)
                if attempts >= stage.max_retries:
                    state.fail_stage(stage.name, str(e))
                    raise StageExecutionError(stage.name, str(e)) from e
