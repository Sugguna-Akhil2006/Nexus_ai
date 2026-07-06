"""Registers the career analysis pipeline as a named WorkflowDefinition."""

from backend.workflows.models import StepType, WorkflowDefinition
from backend.workflows.workflow_builder import WorkflowBuilder
from backend.workflows.workflow_engine import WorkflowEngine

CAREER_WORKFLOW_NAME = "career_analysis_workflow"


def build_career_workflow() -> WorkflowDefinition:
    """Constructs the career analysis workflow definition.

    Steps mirror the CareerService pipeline so the workflow can be
    executed, monitored, and cancelled via the Workflow Engine.

    Returns:
        A ``WorkflowDefinition`` ready for registration.
    """
    return (
        WorkflowBuilder(
            name=CAREER_WORKFLOW_NAME,
            description="End-to-end career analysis: gap analysis, roadmap, recommendations, and report.",
        )
        .add_step(
            "Resume Intelligence",
            StepType.RESUME,
            parameters={"action": "analyze"},
            max_retries=1,
        )
        .add_step(
            "GitHub Intelligence",
            StepType.GITHUB,
            parameters={"action": "analyze"},
            max_retries=1,
        )
        .add_step(
            "Career Gap Analysis",
            StepType.REASONING,
            parameters={"action": "gap_analysis"},
        )
        .add_step(
            "Roadmap Generation",
            StepType.REASONING,
            parameters={"action": "roadmap"},
        )
        .add_step(
            "Knowledge Profile Update",
            StepType.KNOWLEDGE_GRAPH,
            parameters={"action": "update_ukp"},
        )
        .add_step(
            "Career Report Assembly",
            StepType.NO_OP,
            parameters={"action": "assemble_report"},
        )
        .add_tag("career")
        .add_tag("template")
        .build()
    )


class CareerWorkflow:
    """Registers and exposes the career analysis workflow via WorkflowEngine."""

    def __init__(self, engine: WorkflowEngine) -> None:
        self._engine = engine
        self._definition = build_career_workflow()
        self._engine.create_workflow(self._definition)

    @property
    def workflow_id(self) -> str:
        """Returns the registered workflow's ID."""
        return self._definition.workflow_id

    def execute(self, workspace_id: str = "default") -> str:
        """Runs the career workflow and returns the execution ID.

        Args:
            workspace_id: The workspace context for this run.

        Returns:
            The ``execution_id`` of the completed run.
        """
        result = self._engine.execute_workflow(
            self._definition.workflow_id,
            workspace_id=workspace_id,
        )
        return result.execution_id
