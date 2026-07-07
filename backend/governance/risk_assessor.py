"""Risk assessor auditing model states, failures, and policy alerts."""

from __future__ import annotations

from typing import List

from backend.governance.models import (
    AuditTrailEntry,
    ModelRecord,
    RiskLevel,
    RiskReport,
)


class RiskAssessor:
    """Evaluates operations logs and registered models to calculate risk scores."""

    @staticmethod
    def assess(models: List[ModelRecord], logs: List[AuditTrailEntry]) -> RiskReport:
        """Determines platform risk scoring, identifying deprecated tools or policy alarms."""
        alerts = []
        score = 0.0

        # Rule 1: Check for deprecated models in use
        deprecated = [m for m in models if m.status == "deprecated"]
        if deprecated:
            score += 0.3
            alerts.append(f"{len(deprecated)} deprecated model(s) active in the registry.")

        # Rule 2: Check for administrator warnings
        failures = sum(
            1 for l in logs if l.category == "provider" and l.context.get("status") == "failed"
        )
        if failures > 3:
            score += 0.4
            alerts.append(f"High frequency provider invocation failures detected ({failures}).")

        # Cap score at 1.0
        score = min(1.0, score)

        if score >= 0.7:
            level = RiskLevel.CRITICAL
        elif score >= 0.4:
            level = RiskLevel.HIGH
        elif score >= 0.2:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskReport(
            risk_level=level,
            score=score,
            alerts=alerts,
        )
