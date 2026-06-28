"""FastAPI routers for Workflow Automation Engine.

Exposes endpoints matching Prompt 40 specifications exactly.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.workflow.automation_engine import WorkflowExecutor, WorkflowStep, WorkflowCondition
from backend.api.sqlite_mock import DBStorage

router = APIRouter(prefix="/workflows", tags=["Workflows"])

# =====================================================================
# Request / Response Schemas
# =====================================================================

class StepSchema(BaseModel):
    step_id: str
    name: str
    step_type: str
    config: Dict[str, Any]
    dependencies: List[str] = []


class ConditionSchema(BaseModel):
    condition_id: str
    expression: str
    true_step_id: str
    false_step_id: str


class CreateWorkflowRequest(BaseModel):
    name: str
    description: str
    steps: List[StepSchema]
    conditions: Optional[List[ConditionSchema]] = None


class ExecuteRequest(BaseModel):
    variables: Optional[Dict[str, Any]] = None


class ApproveRequest(BaseModel):
    approval_id: str
    approver: str
    decision: str  # APPROVED, REJECTED
    comments: Optional[str] = ""


# =====================================================================
# REST routes
# =====================================================================

@router.post("")
def create_workflow(req: CreateWorkflowRequest):
    """Creates a new workflow definition."""
    executor = WorkflowExecutor()
    steps = [WorkflowStep(s.step_id, s.name, s.step_type, s.config, s.dependencies) for s in req.steps]
    conds = []
    if req.conditions:
        conds = [WorkflowCondition(c.condition_id, c.expression, c.true_step_id, c.false_step_id) for c in req.conditions]

    try:
        def_id = executor.create_definition(req.name, req.description, steps, conds)
        return {"status": "success", "definition_id": def_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow definition: {e}")


@router.get("/history")
def get_workflow_history():
    """Lists all history execution logs."""
    db = DBStorage()
    try:
        rows = db.list_workflow_history()
        return {"history": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list history: {e}")


@router.get("/{id}")
def get_workflow(id: str):
    """Retrieves a specific workflow definition details."""
    db = DBStorage()
    row = db.get_workflow_definition(id)
    if not row:
        raise HTTPException(status_code=404, detail="Workflow definition not found.")
    
    steps = db.list_workflow_steps(id)
    conds = db.list_workflow_conditions(id)
    return {
        "definition_id": id,
        "name": row["name"],
        "description": row["description"],
        "created_at": row["created_at"],
        "steps": steps,
        "conditions": conds
    }


@router.post("/{id}/execute")
def execute_workflow(id: str, req: Optional[ExecuteRequest] = None):
    """Triggers background execution of a workflow."""
    executor = WorkflowExecutor()
    db = DBStorage()
    row = db.get_workflow_definition(id)
    if not row:
        raise HTTPException(status_code=404, detail="Workflow definition not found.")

    try:
        instance_id = executor.execute(id, (req.variables if req else {}))
        return {"status": "success", "instance_id": instance_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger execution: {e}")


@router.post("/{id}/approve")
def approve_workflow(id: str, req: ApproveRequest):
    """Approves or rejects a pending human validation checkpoint step."""
    executor = WorkflowExecutor()
    try:
        success = executor.approve_step(req.approval_id, req.approver, req.decision, req.comments or "")
        if not success:
            raise HTTPException(status_code=400, detail="Invalid approval request or already decided.")
        return {"status": "success", "message": "Approval step resolved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {e}")
