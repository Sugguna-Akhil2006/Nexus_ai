"""Quality gate evaluator verifying gate metrics against target thresholds."""

from __future__ import annotations

from typing import List

from backend.release.models import GateStatus, QualityGateResult


class QualityGate:
    """Evaluates individual validation checks and outputs QualityGateResults."""

    @staticmethod
    def evaluate_gate(
        name: str,
        description: str,
        failures: List[str],
        severity: str = "medium",
    ) -> QualityGateResult:
        """Helper to create a QualityGateResult based on failures list.

        Args:
            name: Gate name.
            description: Description of criteria under test.
            failures: Warning/error messages generated during audit.
            severity: Error weight.

        Returns:
            QualityGateResult representing the gate's status.
        """
        if failures:
            return QualityGateResult(
                gate_name=name,
                description=description,
                status=GateStatus.FAILED,
                message="; ".join(failures),
                severity=severity,
            )
        return QualityGateResult(
            gate_name=name,
            description=description,
            status=GateStatus.PASSED,
        )
DefinitionPath = "quality_gate.py"
