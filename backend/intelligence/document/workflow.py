"""Pipeline stage definitions and workflow exceptions for Document Intelligence."""

class DocumentStageNames:
    """Canonical stage names for the Document Intelligence workflow pipeline."""
    LOADER = "Document Ingestion & Parsing"
    PROCESSING = "Intelligent Document Processing"
    CITATION = "Citation Resolution"
    SUMMARIZATION = "Document Summarization"
    PROFILE = "Knowledge Profile Integration"
    PERSISTENCE = "Database Log Storage"


class StageExecutionError(Exception):
    """Exception raised when a specific workflow stage fails completely."""
    def __init__(self, stage_name: str, message: str) -> None:
        super().__init__(f"Stage '{stage_name}' failed: {message}")
        self.stage_name = stage_name
