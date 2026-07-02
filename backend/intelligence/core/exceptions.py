"""Core exceptions for the Intelligence Orchestrator Framework."""

class IntelligenceError(Exception):
    """Base exception class for all intelligence framework errors."""


class RegistryError(IntelligenceError):
    """Raised when a module fails to register or search in the registry."""


class WorkflowError(IntelligenceError):
    """Raised when workflow execution violates dependencies or fails validation."""


class StageExecutionError(WorkflowError):
    """Raised when a specific pipeline stage fails to execute."""
