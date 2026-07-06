"""Pre-built workflow templates for common Nexus AI use cases."""

from backend.workflows.models import StepType, WorkflowDefinition
from backend.workflows.workflow_builder import WorkflowBuilder

# Registry mapping template names to factory callables
_TEMPLATE_REGISTRY: dict = {}


def _register(name: str):
    """Decorator that registers a template factory function by name."""
    def decorator(fn):
        _TEMPLATE_REGISTRY[name] = fn
        return fn
    return decorator


@_register("resume_analysis_workflow")
def resume_analysis_workflow() -> WorkflowDefinition:
    """Builds the Resume Analysis pipeline workflow.

    Pipeline:
        Upload Resume → Resume Analysis → Knowledge Profile Update
        → Generate ATS Report → Export PDF

    Returns:
        A ``WorkflowDefinition`` for the resume analysis pipeline.
    """
    return (
        WorkflowBuilder(
            name="Resume Analysis Pipeline",
            description="End-to-end resume upload, analysis, KP update, and ATS report generation.",
        )
        .add_step("Upload Resume", StepType.RESUME, parameters={"action": "upload"})
        .add_step("Analyze Resume", StepType.RESUME, parameters={"action": "analyze"}, max_retries=1)
        .add_step("Update Knowledge Profile", StepType.KNOWLEDGE_GRAPH, parameters={"action": "update_ukp"})
        .add_step("Generate ATS Report", StepType.REASONING, parameters={"action": "ats_report"})
        .add_step("Export PDF", StepType.NO_OP, parameters={"action": "export_pdf"})
        .add_tag("resume")
        .add_tag("template")
        .build()
    )


@_register("github_engineering_workflow")
def github_engineering_workflow() -> WorkflowDefinition:
    """Builds the GitHub Engineering Report pipeline workflow.

    Pipeline:
        GitHub Repository Analysis → Engineering Report
        → Knowledge Profile Update

    Returns:
        A ``WorkflowDefinition`` for the GitHub engineering pipeline.
    """
    return (
        WorkflowBuilder(
            name="GitHub Engineering Report",
            description="Repository analysis followed by engineering report generation and KP update.",
        )
        .add_step("Analyse Repository", StepType.GITHUB, parameters={"action": "analyze"}, max_retries=1)
        .add_step("Generate Engineering Report", StepType.REASONING, parameters={"action": "engineering_report"})
        .add_step("Update Knowledge Profile", StepType.KNOWLEDGE_GRAPH, parameters={"action": "update_ukp"})
        .add_tag("github")
        .add_tag("template")
        .build()
    )


@_register("document_research_workflow")
def document_research_workflow() -> WorkflowDefinition:
    """Builds the Document + Research Intelligence pipeline workflow.

    Pipeline:
        Upload Documents → Document Intelligence
        → Research Intelligence → Unified Summary

    Returns:
        A ``WorkflowDefinition`` for the document research pipeline.
    """
    return (
        WorkflowBuilder(
            name="Document Research Pipeline",
            description="Multi-document ingestion, analysis, research synthesis, and unified summary.",
        )
        .add_step("Upload Documents", StepType.DOCUMENT, parameters={"action": "upload"})
        .add_step("Document Intelligence", StepType.DOCUMENT, parameters={"action": "analyze"}, max_retries=1)
        .add_step("Research Intelligence", StepType.RESEARCH, parameters={"action": "synthesize"})
        .add_step("Generate Unified Summary", StepType.REASONING, parameters={"action": "unified_summary"})
        .add_tag("document")
        .add_tag("research")
        .add_tag("template")
        .build()
    )


def get_template(name: str) -> WorkflowDefinition:
    """Builds and returns a named template workflow.

    Args:
        name: The template identifier string.

    Returns:
        A freshly constructed ``WorkflowDefinition``.

    Raises:
        KeyError: If no template with the given name is registered.
    """
    if name not in _TEMPLATE_REGISTRY:
        raise KeyError(f"No workflow template named '{name}'. Available: {list_templates()}")
    return _TEMPLATE_REGISTRY[name]()


def list_templates() -> list:
    """Returns the names of all registered workflow templates.

    Returns:
        List of template name strings.
    """
    return list(_TEMPLATE_REGISTRY.keys())
