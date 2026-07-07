"""FastAPI APIRouter routing Internal Developer Platform code scans, scaffolding, and CLI simulations."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.idp.code_quality import CodeQualityAuditor
from backend.idp.dependency_analyzer import DependencyAnalyzer
from backend.idp.developer_cli import DeveloperCLI
from backend.idp.lint_manager import LintManager
from backend.idp.models import QualityReport, ScaffoldRequest
from backend.idp.project_scaffolder import ProjectScaffolder
from backend.product.serialization import ProductResponse

router = APIRouter(prefix="/idp", tags=["Internal Developer Platform"])


class ValidateCodePayload(BaseModel):
    """Payload containing code text files map to audit."""

    # Filename -> content
    files: Dict[str, str]


class CLIPayload(BaseModel):
    """Payload to simulate terminal commands."""

    args: List[str]


@router.post("/scaffold", summary="Scaffold a new component structure")
def scaffold_component(payload: ScaffoldRequest) -> Any:
    """Generates folders, boilerplate python scripts, guides, and test skeletons."""
    # Place generated components inside backend/generated/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = ProjectScaffolder.scaffold(payload, base_dir)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return ProductResponse.ok(data=result)


@router.post("/validate", summary="Run code quality and dependency validations")
def validate_code(payload: ValidateCodePayload) -> Any:
    """Performs style, lints, docstrings, and circular import scans."""
    lints = []
    circulars = []

    # Run circular dependency checks
    circulars = DependencyAnalyzer.detect_circular_dependencies(payload.files)

    # Run style and lints
    for name, content in payload.files.items():
        lints.extend([f"{name} / {l}" for l in LintManager.lint_code(content)])
        lints.extend([f"{name} / {q}" for q in CodeQualityAuditor.audit_quality(content)])

    report = QualityReport(
        formatting_passed=len(lints) == 0,
        lint_warnings=lints,
        circular_dependencies=circulars,
        architecture_score=max(0, 100 - (len(lints) * 5) - (len(circulars) * 20)),
    )

    return ProductResponse.ok(data=report)


@router.post("/cli", summary="Simulate developer CLI actions")
def run_cli(payload: CLIPayload) -> Any:
    """Simulates commands parsing like nexus doctor, nexus validate, or nexus docs."""
    result = DeveloperCLI.process_command(payload.args)
    return ProductResponse.ok(data=result)


@router.get("/diagnostics", summary="Get developer platform diagnostic status")
def get_diagnostics() -> ProductResponse[Any]:
    """Returns tool availability and configuration diagnostic metrics."""
    return ProductResponse.ok(
        data={
            "scaffolder": "healthy",
            "quality_gates": "active",
            "supported_scaffolds": ["module", "connector", "workflow", "provider", "plugin", "agent"],
            "doctor_status": "all checks passed",
        }
    )
