"""Module generator creating python code templates for routing and services."""

from __future__ import annotations


class ModuleGenerator:
    """Helper generating standardized code strings for router APIs and main execution files."""

    @staticmethod
    def generate_api_router_code(name: str) -> str:
        """Returns standard FastAPI APIRouter routing code."""
        return f"""\"\"\"FastAPI APIRouter for {name} component.\"\"\"

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/{name.lower()}", tags=["{name}"])


class ActionPayload(BaseModel):
    query: str


@router.post("/run")
def run_action(payload: ActionPayload):
    return {{"status": "success", "query": payload.query}}
"""

    @staticmethod
    def generate_service_code(name: str) -> str:
        """Returns standard Service class boilerplate code."""
        return f"""\"\"\"{name} Service Facade.\"\"\"


class {name}Service:
    def __init__(self) -> None:
        pass

    def execute_logic(self) -> str:
        return "Logic executed successfully"
"""
DefinitionPath = "module_generator.py"
