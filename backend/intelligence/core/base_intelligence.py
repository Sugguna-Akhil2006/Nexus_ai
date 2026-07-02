"""Abstract base class interface for pluggable intelligence modules."""

from abc import ABC, abstractmethod
from typing import Set

from backend.intelligence.core.context import IntelligenceContext
from backend.intelligence.core.report import IntelligenceExecutionReport


class BaseIntelligenceModule(ABC):
    """Abstract class that all intelligence modules (Resume, GitHub, etc.) subclass."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the module's unique registered name."""

    @property
    @abstractmethod
    def capabilities(self) -> Set[str]:
        """Returns the capabilities set supported by this module."""

    @abstractmethod
    def execute_workflow(self, context: IntelligenceContext) -> IntelligenceExecutionReport:
        """Main entry point to execute the pipeline stages on the context.

        Args:
            context: Context containing workspaces and input documents.

        Returns:
            IntelligenceExecutionReport: Standardized summary report.
        """
