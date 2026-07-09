"""Release report compiler scoring readiness and summarizing passed/failed gates."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from backend.release.models import GateStatus, PerformanceAudit, QualityGateResult, ReleaseReadinessReport, SecurityAudit


class ReleaseReportCompiler:
    """Calculates release scores, separates warnings, and builds recommendations."""

    @staticmethod
    def compile_report(
        gate_results: List[QualityGateResult],
        perf: PerformanceAudit,
        sec: SecurityAudit,
    ) -> ReleaseReadinessReport:
        """Assembles the final ReleaseReadinessReport based on quality gates.

        Args:
            gate_results: Evaluated QualityGateResults.
            perf: Performance audit statistics.
            sec: Security audit details.

        Returns:
            ReleaseReadinessReport.
        """
        score = 100
        passed = []
        failed = []
        warnings = []
        critical = []
        recs = []

        for r in gate_results:
            if r.status == GateStatus.PASSED:
                passed.append(r.gate_name)
            else:
                failed.append(r.gate_name)
                # Deduct points based on severity
                if r.severity == "critical":
                    score -= 30
                    critical.append(f"{r.gate_name}: {r.message}")
                    recs.append(f"Critical Fix: Resolve system failures in {r.gate_name}.")
                elif r.severity == "high":
                    score -= 20
                    critical.append(f"{r.gate_name}: {r.message}")
                    recs.append(f"High Fix: Resolve key issues in {r.gate_name}.")
                elif r.severity == "medium":
                    score -= 10
                    warnings.append(f"{r.gate_name}: {r.message}")
                    recs.append(f"Medium Fix: Update parameters in {r.gate_name}.")
                else:
                    score -= 5
                    warnings.append(f"{r.gate_name}: {r.message}")
                    recs.append(f"Low Fix: Review documentation in {r.gate_name}.")

        score = max(0, score)
        # Deployable if score >= 80 and no critical failures exist
        is_deploy = (score >= 80) and (len(critical) == 0)

        return ReleaseReadinessReport(
            report_id=f"rep-{uuid.uuid4().hex[:8]}",
            readiness_score=score,
            is_deployable=is_deploy,
            passed_gates=passed,
            failed_gates=failed,
            warnings=warnings,
            critical_issues=critical,
            recommended_fixes=recs,
            performance=perf,
            security=sec,
            created_at=datetime.utcnow().isoformat(),
        )
DefinitionPath = "release_report.py"
