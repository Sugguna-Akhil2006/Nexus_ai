"""Central certification manager orchestrating all domain certifiers."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.certification.integration_certifier import IntegrationCertifier
from backend.certification.knowledge_certifier import KnowledgeCertifier
from backend.certification.models import CertificationRun, DomainReport
from backend.certification.performance_certifier import PerformanceCertifier
from backend.certification.provider_certifier import ProviderCertifier
from backend.certification.report_generator import ReportGenerator
from backend.certification.runtime_certifier import RuntimeCertifier
from backend.certification.scorecard import Scorecard
from backend.certification.security_certifier import SecurityCertifier
from backend.certification.workflow_certifier import WorkflowCertifier


class CertificationManager:
    """Orchestrates the full platform certification pipeline.

    The manager runs each domain certifier, scores all results via the
    :class:`Scorecard`, stores history, and generates reports on demand.

    Thread Safety:
        ``run()`` is guarded by a reentrant lock so only one certification
        can execute at a time.  History reads are always safe.
    """

    _instance: Optional["CertificationManager"] = None

    def __new__(cls) -> "CertificationManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._lock: threading.RLock = threading.RLock()
        self._history: List[CertificationRun] = []
        self._initialized = True

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def run(self) -> CertificationRun:
        """Executes the full certification suite and returns the scored run.

        Returns:
            Completed and scored :class:`CertificationRun`.
        """
        with self._lock:
            run_id = str(uuid.uuid4())[:8]
            run = CertificationRun(
                run_id=run_id,
                started_at=datetime.now(timezone.utc).isoformat(),
            )

            # Execute all domain certifiers
            certifiers = [
                RuntimeCertifier,
                WorkflowCertifier,
                ProviderCertifier,
                KnowledgeCertifier,
                SecurityCertifier,
                PerformanceCertifier,
                IntegrationCertifier,
            ]
            for certifier in certifiers:
                domain_report: DomainReport = certifier.certify()
                run.domain_reports.append(domain_report)

            run.completed_at = datetime.now(timezone.utc).isoformat()

            # Score and award level
            run = Scorecard.finalize(run)

            self._history.append(run)
            return run

    # ------------------------------------------------------------------
    # History and reporting
    # ------------------------------------------------------------------

    def get_latest(self) -> Optional[CertificationRun]:
        """Returns the most recent certification run or None."""
        with self._lock:
            return self._history[-1] if self._history else None

    def get_history(self) -> List[CertificationRun]:
        """Returns all past certification runs."""
        with self._lock:
            return list(self._history)

    def generate_markdown_report(self, run: Optional[CertificationRun] = None) -> str:
        """Generates a Markdown report for the given run (or latest).

        Args:
            run: Target run, or None to use the latest.

        Returns:
            Markdown string.
        """
        target = run or self.get_latest()
        if not target:
            return "# No certification runs found."
        return ReportGenerator.to_markdown(target)

    def generate_json_report(self, run: Optional[CertificationRun] = None) -> str:
        """Generates a JSON report for the given run (or latest)."""
        target = run or self.get_latest()
        if not target:
            return "{}"
        return ReportGenerator.to_json(target)

    def generate_html_report(self, run: Optional[CertificationRun] = None) -> str:
        """Generates an HTML report for the given run (or latest)."""
        target = run or self.get_latest()
        if not target:
            return "<html><body>No certification runs found.</body></html>"
        return ReportGenerator.to_html(target)
