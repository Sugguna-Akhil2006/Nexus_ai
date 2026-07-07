"""Reasoning history tracker recording AI teammate's cognitive steps and confidence levels."""

import threading
from typing import List, Optional
from backend.session.models import ReasoningHistoryModel, ReasoningStepModel


class ReasoningHistory:
    """Thread-safe storage for reasoning steps, evidence, and recommendations."""

    def __init__(self, data: Optional[ReasoningHistoryModel] = None) -> None:
        self._lock = threading.RLock()
        self._model = data or ReasoningHistoryModel()

    def record_question(self, question: str) -> None:
        """Records a user question or self-inquiry."""
        with self._lock:
            self._model.questions_asked.append(question)

    def record_evidence(self, evidence: str) -> None:
        """Records evidence or context used in decision making."""
        with self._lock:
            self._model.evidence_used.append(evidence)

    def record_step(self, description: str, confidence: float = 1.0) -> ReasoningStepModel:
        """Records a distinct reasoning step and adjusts confidence evolution."""
        with self._lock:
            step = ReasoningStepModel(description=description, confidence=confidence)
            self._model.reasoning_steps.append(step)
            self._model.confidence_evolution.append(confidence)
            return step

    def record_report(self, report_name: str) -> None:
        """Records a report generated during the reasoning process."""
        with self._lock:
            self._model.generated_reports.append(report_name)

    def record_recommendation(self, recommendation: str) -> None:
        """Records a recommendation provided to the user."""
        with self._lock:
            self._model.recommendations.append(recommendation)

    def get_snapshot(self) -> ReasoningHistoryModel:
        """Returns a copy of the reasoning history model."""
        with self._lock:
            return self._model.model_copy(deep=True)

    def load_snapshot(self, model: ReasoningHistoryModel) -> None:
        """Loads state from a snapshot model."""
        with self._lock:
            self._model = model.model_copy(deep=True)
