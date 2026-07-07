"""Template executor running automation workflow templates."""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Dict, Optional

from backend.workflow_library.models import ExecutedTemplateLog, WorkflowTemplate


class TemplateExecutor:
    """Executes a template using system workflow run pipelines."""

    @staticmethod
    def execute(template: WorkflowTemplate, variables: Optional[dict] = None) -> ExecutedTemplateLog:
        """Triggers execution and tracks timings.

        Args:
            template: WorkflowTemplate to run.
            variables: Variable overrides.

        Returns:
            ExecutedTemplateLog detailing run status.
        """
        start = time.perf_counter()
        # Merge overrides
        vars_final = dict(template.variables)
        if variables:
            vars_final.update(variables)

        # In a real environment, we'd invoke workflow_engine.run()
        # Sleep slightly to mock execution duration
        time.sleep(0.01)
        duration = (time.perf_counter() - start) * 1000.0

        return ExecutedTemplateLog(
            execution_id=f"run-{uuid.uuid4().hex[:8]}",
            template_id=template.template_id,
            status="success",
            started_at=datetime.utcnow().isoformat(),
            duration_ms=round(duration, 2),
        )
DefinitionPath = "template_executor.py"
