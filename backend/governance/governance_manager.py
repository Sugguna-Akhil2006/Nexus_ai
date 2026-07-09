"""Central AI governance manager coordinating audit, compliance, and model registries."""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from backend.governance.approval_workflow import ApprovalWorkflow
from backend.governance.audit_manager import AuditManager
from backend.governance.compliance_engine import ComplianceEngine
from backend.governance.model_registry import ModelRegistry
from backend.governance.models import (
    ApprovalState,
    AuditTrailEntry,
    ComplianceStatusReport,
    ModelRecord,
    RiskReport,
)
from backend.governance.report_generator import ReportGenerator
from backend.governance.retention_manager import RetentionManager
from backend.governance.risk_assessor import RiskAssessor


class GovernanceManager:
    """Thread-safe singleton managing model governance, auditing, and risk analysis."""

    _instance: Optional["GovernanceManager"] = None

    def __new__(cls) -> "GovernanceManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_ready", False):
            return
        self._lock = threading.RLock()
        self._model_registry = ModelRegistry()
        self._audit_manager = AuditManager()
        self._approvals = ApprovalWorkflow()
        self._ready = True

    # ------------------------------------------------------------------
    # Model Registry
    # ------------------------------------------------------------------

    def register_model(self, model: ModelRecord) -> None:
        """Adds a model details block to the active model inventory registry."""
        self._model_registry.register(model)
        self._approvals.submit(model.model_id)

    def list_models(self) -> List[ModelRecord]:
        """Returns all registered models."""
        return self._model_registry.list_all()

    # ------------------------------------------------------------------
    # Auditing
    # ------------------------------------------------------------------

    def audit_event(
        self,
        category: str,
        actor: str,
        action: str,
        context: Optional[Dict] = None,
    ) -> AuditTrailEntry:
        """Records an event log entry in the audit trail."""
        with self._lock:
            entry = self._audit_manager.record_event(category, actor, action, context)
            # Enforce retention (max 200 logs for test speed)
            logs = self._audit_manager.list_history()
            truncated = RetentionManager.enforce_retention(logs, max_count=200)
            if len(truncated) < len(logs):
                self._audit_manager.clear()
                for l in truncated:
                    self._audit_manager.record_event(l.category, l.actor, l.action, l.context)
            return entry

    def list_audit_history(self, category: Optional[str] = None) -> List[AuditTrailEntry]:
        """Lists collected audit trail records."""
        return self._audit_manager.list_history(category)

    # ------------------------------------------------------------------
    # Compliance & Risk
    # ------------------------------------------------------------------

    def check_compliance(self) -> ComplianceStatusReport:
        """Evaluates operational activity history logs against compliance rule sets."""
        logs = self._audit_manager.list_history()
        return ComplianceEngine.evaluate(logs)

    def assess_risk(self) -> RiskReport:
        """Evaluates model list statuses and logging trends to score platform risk levels."""
        models = self._model_registry.list_all()
        logs = self._audit_manager.list_history()
        return RiskAssessor.assess(models, logs)

    # ------------------------------------------------------------------
    # Workflow approvals
    # ------------------------------------------------------------------

    def get_approval_state(self, model_id: str) -> ApprovalState:
        """Fetches status of the ticket."""
        return self._approvals.get_status(model_id)

    def approve_model(self, model_id: str) -> None:
        """Approves a pending ticket."""
        self._approvals.approve(model_id)
        self._model_registry.update_state(model_id, ApprovalState.APPROVED)

    def reject_model(self, model_id: str) -> None:
        """Rejects a pending ticket."""
        self._approvals.reject(model_id)
        self._model_registry.update_state(model_id, ApprovalState.REJECTED)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def generate_report(self, fmt: str = "json") -> str:
        """Formats the aggregate governance and compliance status report."""
        comp = self.check_compliance()
        risk = self.assess_risk()
        f = fmt.lower()
        if f == "markdown":
            return ReportGenerator.to_markdown(comp, risk)
        if f == "html":
            return ReportGenerator.to_html(comp, risk)
        return ReportGenerator.to_json(comp, risk)

    def cleanup(self) -> None:
        """Wipes registry and logs for isolation."""
        with self._lock:
            self._model_registry.clear()
            self._audit_manager.clear()
            self._approvals.clear()
            self._ready = True
            GovernanceManager._instance = None
