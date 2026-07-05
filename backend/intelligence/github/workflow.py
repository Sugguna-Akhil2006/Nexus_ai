"""Pipeline stage definitions and workflow exceptions for GitHub Intelligence."""

class StageNames:
    """Canonical stage names for the GitHub Intelligence pipeline."""
    LOADER = "Repository Loader"
    REPOSITORY = "Repository Intelligence"
    ENGINEERING = "Engineering Intelligence"
    HEALTH = "Repository Health"
    PROFILE = "Knowledge Profile Update"
    GENERATOR = "Engineering Report Generator"


class StageExecutionError(Exception):
    """Exception raised when a specific workflow stage fails completely."""
    def __init__(self, stage_name: str, message: str) -> None:
        super().__init__(f"Stage '{stage_name}' failed: {message}")
        self.stage_name = stage_name
