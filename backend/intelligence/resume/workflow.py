"""Pipeline stage definitions and workflow exceptions."""

class StageNames:
    """Canonical stage names for the Resume Intelligence pipeline."""
    PARSER = "Parser"
    SKILL_EXTRACTION = "Skill Extraction"
    ATS_ENGINE = "ATS Engine"
    JD_MATCHING = "JD Matching"
    ANALYSIS = "Analysis"
    CONSOLIDATOR = "Consolidator"


class StageExecutionError(Exception):
    """Exception raised when a specific workflow stage fails completely after retries."""
    def __init__(self, stage_name: str, message: str) -> None:
        super().__init__(f"Stage '{stage_name}' failed: {message}")
        self.stage_name = stage_name
