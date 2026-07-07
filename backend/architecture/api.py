"""FastAPI APIRouter routing architecture cataloging and handbook generation queries."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response

from backend.architecture.architecture_service import ArchitectureService
from backend.architecture.documentation_generator import DocumentationGenerator
from backend.product.serialization import ProductResponse

router = APIRouter(prefix="/architecture", tags=["Architecture Knowledge Center"])

# Singleton service
_service = ArchitectureService()


@router.get("/modules", summary="Get intelligence modules catalog details")
def get_modules() -> ProductResponse[List[Any]]:
    """Returns documentation catalog entries for all registered modules."""
    mods = _service.get_modules()
    return ProductResponse.ok(data=mods)


@router.get("/dependencies", summary="Get component dependency graphs")
def get_dependencies() -> ProductResponse[Any]:
    """Returns nodes, edges, and Mermaid structure layouts."""
    graph = _service.get_dependency_graph()
    return ProductResponse.ok(data=graph)


@router.get("/sequences", summary="Get Mermaid sequence diagrams")
def get_sequences(
    scenario: str = Query("resume", regex="^(resume|github|document|professional)$"),
) -> ProductResponse[Any]:
    """Compiles chronological message flow diagrams in Mermaid format."""
    flow = _service.get_sequence(scenario)
    return ProductResponse.ok(data=flow)


@router.get("/decisions", summary="Get Architecture Decision Records (ADRs)")
def get_decisions() -> ProductResponse[List[Any]]:
    """Returns the historical design decision log entries."""
    decisions = _service.get_decisions()
    return ProductResponse.ok(data=decisions)


@router.get("/handbook", summary="Generate system developer and architecture handbooks")
def get_handbook(
    format: str = Query("markdown", regex="^(markdown|html|json)$"),
) -> Any:
    """Generates complete documentation handbooks in Markdown, HTML, or JSON formats."""
    modules = _service.get_modules()
    decisions = _service.get_decisions()
    diagram = _service.get_component_diagram()

    md_content = DocumentationGenerator.generate_markdown_handbook(modules, decisions, diagram)

    if format == "html":
        html_content = DocumentationGenerator.generate_html_handbook(md_content)
        return Response(content=html_content, media_type="text/html")

    if format == "json":
        json_content = DocumentationGenerator.generate_json_handbook(modules, decisions)
        return Response(content=json_content, media_type="application/json")

    # Default Markdown
    return Response(content=md_content, media_type="text/markdown")
