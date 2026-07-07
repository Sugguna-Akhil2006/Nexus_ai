"""Captures intermediate reasoning steps and links them to execution spans."""

from typing import Any, Dict, Optional
from backend.observability.models import ReasoningStep
from backend.observability.execution_trace import ExecutionTracer


class ReasoningTracer:
    """Wraps an ``ExecutionTracer`` to record Reasoning Engine steps."""

    def __init__(self, tracer: ExecutionTracer) -> None:
        self._tracer = tracer

    def record_step(
        self,
        description: str,
        span_id: str = "",
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> ReasoningStep:
        """Records a reasoning step and links it to a parent span.

        Args:
            description: Human-readable step description.
            span_id: Parent span that triggered this step.
            inputs: Input facts/evidence fed into the step.
            outputs: Conclusions produced by the step.
            confidence: Confidence score for the step output.

        Returns:
            The recorded ``ReasoningStep`` instance.
        """
        step = ReasoningStep(
            span_id=span_id,
            description=description,
            inputs=inputs or {},
            outputs=outputs or {},
            confidence=confidence,
        )
        self._tracer.record_reasoning_step(step)
        return step
