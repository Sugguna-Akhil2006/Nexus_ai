"""FastAPI router exposing policy CRUD, evaluation, and history routes."""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.policy.models import Policy, PolicyType
from backend.policy.policy_engine import PolicyEngine
from backend.product.serialization import ProductResponse

router = APIRouter(prefix="/policy", tags=["Policy & Governance"])

_engine = PolicyEngine()


class EvaluatePayload(BaseModel):
    """Payload to trigger policy evaluation against context attributes."""

    context: dict = {}


@router.post("", summary="Create a new governance policy")
def create_policy(policy: Policy) -> Any:
    """Adds a new policy rule configuration block to the governance registry."""
    _engine.add_policy(policy)
    return ProductResponse.ok(data=policy)


@router.put("/{policy_id}", summary="Update an existing policy configuration")
def update_policy(policy_id: str, policy: Policy) -> Any:
    """Updates an existing policy inside the governance registry."""
    if not _engine.get_policy(policy_id):
        raise HTTPException(status_code=404, detail="Policy not found.")
    _engine.add_policy(policy)
    return ProductResponse.ok(data=policy)


@router.delete("/{policy_id}", summary="Delete a policy from the registry")
def delete_policy(policy_id: str) -> Any:
    """Removes a policy definition from the governance registry."""
    _engine.remove_policy(policy_id)
    return ProductResponse.ok(message="Policy deleted successfully.")


@router.post("/evaluate", summary="Evaluate policy rules against runtime context")
def evaluate_policy(payload: EvaluatePayload) -> Any:
    """Resolves and enforces applicable policy chains for the given user action query context."""
    result = _engine.evaluate(payload.context)
    return ProductResponse.ok(data=result)


@router.get("/history", summary="List policy evaluation audit logs")
def get_audit_history(workspace_id: Optional[str] = Query(None, description="Filter logs by workspace")) -> Any:
    """Returns log events of past policy evaluations."""
    logs = _engine.list_audit_history(workspace_id)
    return ProductResponse.ok(data=logs)


@router.get("/statistics", summary="Get policy matching metrics")
def get_statistics() -> Any:
    """Returns policy matching counts and warning frequencies."""
    stats = _engine.get_statistics()
    return ProductResponse.ok(data=stats)
