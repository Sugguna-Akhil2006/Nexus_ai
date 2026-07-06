"""Registers the unified professional analysis pipeline as a WorkflowEngine definition."""

from backend.workflows.models import StepType, WorkflowDefinition
from backend.workflows.workflow_builder import WorkflowBuilder
from backend.workflows.workflow_engine import WorkflowEngine

PROFESSIONAL_WORKFLOW_NAME = "professional_analysis_workflow"


def build_professional_workflow() -> WorkflowDefinition:
    """Constructs the professional analysis workflow definition.

    Steps model the unified professional analysis pipeline:
    Profile Building -> Resume Intelligence -> GitHub Intelligence ->
    Document Intelligence -> Career Analysis -> Portfolio Analysis ->
    Skill Verification -> Scoring & Projections -> Report Assembly.

    Returns:
        A ``WorkflowDefinition`` ready for registration.
    """
    return (
        WorkflowBuilder(
            name=PROFESSIONAL_WORKFLOW_NAME,
            description="End-to-end unified professional analysis combining resume, GitHub, docs, and career engine.",
        )
        .add_step(
            "Assemble Professional Profile",
            StepType.NO_OP,
            parameters={"action": "build_profile"},
        )
        .add_step(
            "Resume Verification",
            StepType.RESUME,
            parameters={"action": "verify"},
            max_retries=1,
        )
        .add_step(
            "GitHub Repository Ingestion",
            StepType.GITHUB,
            parameters={"action": "ingest_repos"},
            max_retries=1,
        )
        .add_step(
            "Cross-Source Skill Verification",
            StepType.REASONING,
            parameters={"action": "verify_skills"},
        )
        .add_step(
            "Compute Professional Score",
            StepType.REASONING,
            parameters={"action": "calculate_score"},
        )
        .add_step(
            "Growth Projection Engine",
            StepType.REASONING,
            parameters={"action": "predict_growth"},
        )
        .add_step(
            "Flagship Report Generation",
            StepType.NO_OP,
            parameters={"action": "generate_report"},
        )
        .add_tag("professional")
        .add_tag("flagship")
        .build()
    )


class ProfessionalWorkflow:
    """Registers and executes the professional workflow via WorkflowEngine."""

    def __init__(self, engine: WorkflowEngine) -> None:
        self._engine = engine
        self._definition = build_professional_workflow()
        self._engine.create_workflow(self._definition)

    @property
    def workflow_id(self) -> str:
        """Returns the registered workflow's ID."""
        return self._definition.workflow_id

    def execute(self, workspace_id: str = "default") -> str:
        """Runs the professional workflow and returns the execution ID.

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
