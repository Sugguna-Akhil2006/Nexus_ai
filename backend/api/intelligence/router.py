"""FastAPI APIRouter routing intelligence gateway requests and listing modules."""

import time
from fastapi import APIRouter, status

from backend.api.intelligence.requests import GatewayExecutionRequest
from backend.api.intelligence.responses import GatewayExecutionResponse
from backend.api.intelligence.gateway import IntelligenceGateway
from backend.api.intelligence.registry import GatewayRegistry


router = APIRouter(prefix="/api/intelligence", tags=["Intelligence Gateway"])


@router.post("/execute", response_model=GatewayExecutionResponse)
def execute_module(request: GatewayExecutionRequest) -> GatewayExecutionResponse:
    """Executes target module dynamically resolved from request capability."""
    gateway = IntelligenceGateway()
    return gateway.route_and_execute(request)


@router.post("/resume", response_model=GatewayExecutionResponse)
def execute_resume(request: GatewayExecutionRequest) -> GatewayExecutionResponse:
    """Executes Resume Intelligence module specifically."""
    request.capability = "RESUME_PARSING"
    gateway = IntelligenceGateway()
    return gateway.route_and_execute(request)


@router.post("/github", response_model=GatewayExecutionResponse)
def execute_github(request: GatewayExecutionRequest) -> GatewayExecutionResponse:
    """Gateway route for future GitHub Intelligence execution."""
    request.capability = "GITHUB_INTELLIGENCE"
    gateway = IntelligenceGateway()
    return gateway.route_and_execute(request)


@router.post("/research", response_model=GatewayExecutionResponse)
def execute_research(request: GatewayExecutionRequest) -> GatewayExecutionResponse:
    """Gateway route for future Research Intelligence execution."""
    request.capability = "RESEARCH_INTELLIGENCE"
    gateway = IntelligenceGateway()
    return gateway.route_and_execute(request)


@router.post("/meeting", response_model=GatewayExecutionResponse)
def execute_meeting(request: GatewayExecutionRequest) -> GatewayExecutionResponse:
    """Gateway route for future Meeting Intelligence execution."""
    request.capability = "MEETING_INTELLIGENCE"
    gateway = IntelligenceGateway()
    return gateway.route_and_execute(request)


@router.get("/modules", status_code=status.HTTP_200_OK)
def list_modules() -> dict:
    """Lists registered modules and all supported capability keywords."""
    registry = GatewayRegistry()
    return {
        "modules": registry.list_modules(),
        "capabilities": registry.list_capabilities()
    }


@router.get("/status", status_code=status.HTTP_200_OK)
def get_gateway_status() -> dict:
    """Verifies gateway health and returns current uptime."""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }
