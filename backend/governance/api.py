"""FastAPI router exposing AI governance model registries and audit timeline routes."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.governance.governance_manager import GovernanceManager
from backend.governance.models import ApprovalState, ModelRecord
from backend.product.serialization import ProductResponse

router = APIRouter(prefix="/governance", tags=["AI Governance"])

_manager = GovernanceManager()


class ModelPayload(BaseModel):
    """Payload to register a new LLM model."""

    model_id: str
    name: str
    version: str
    provider: str


class AuditPayload(BaseModel):
    """Payload to manually log an audit event."""

    category: str
    actor: str
    action: str
    context: dict = {}


@router.post("/model", summary="Register an LLM model in the inventory")
def register_model(payload: ModelPayload) -> Any:
    """Adds a new model registration details to the governance inventory registry."""
    model = ModelRecord(
        model_id=payload.model_id,
        name=payload.name,
        version=payload.version,
        provider=payload.provider,
    )
    _manager.register_model(model)
    return ProductResponse.ok(data=model)


@router.post("/model/{model_id}/approve", summary="Approve a pending model registration")
def approve_model(model_id: str) -> Any:
    """Approves a pending model deployment and updates its registration state to approved."""
    _manager.approve_model(model_id)
    return ProductResponse.ok(message="Model registration approved.")


@router.post("/model/{model_id}/reject", summary="Reject a pending model registration")
def reject_model(model_id: str) -> Any:
    """Rejects a pending model deployment and blocks it from platform registrations."""
    _manager.reject_model(model_id)
    return ProductResponse.ok(message="Model registration rejected.")


@router.post("/audit", summary="Log an operational event in the audit trail")
def audit_event(payload: AuditPayload) -> Any:
    """Manually appends an event to the security audit trail logs."""
    entry = _manager.audit_event(
        category=payload.category,
        actor=payload.actor,
        action=payload.action,
        context=payload.context,
    )
    return ProductResponse.ok(data=entry)


@router.get("/summary", summary="Get platform governance and risk summary")
def get_summary() -> Any:
    """Returns the compiled risk scores, warnings, and compliance checks status."""
    compliance = _manager.check_compliance()
    risk = _manager.assess_risk()
    return ProductResponse.ok(
        data={
            "overall_compliant": compliance.overall_passed,
            "risk_level": risk.risk_level.value,
            "risk_score": risk.score,
            "alerts": risk.alerts,
        }
    )


@router.get("/report", summary="Get governance report in chosen format")
def get_report(format: str = Query("json", description="markdown | json | html")) -> Any:
    """Generates the latest compliance and risk assessment report."""
    content = _manager.generate_report(fmt=format.lower())
    return ProductResponse.ok(data={"format": format, "content": content})


@router.get("/models", summary="List registered model inventory")
def list_models() -> Any:
    """Returns all models registered inside the governance inventory."""
    models = _manager.list_models()
    return ProductResponse.ok(data=models)


@router.get("/history", summary="List audit history logs")
def get_audit_history(category: Optional[str] = Query(None, description="Filter logs by category")) -> Any:
    """Returns chronological audit timeline logs."""
    history = _manager.list_audit_history(category)
    return ProductResponse.ok(data=history)
