"""Production-grade Repository Intelligence Engine orchestrating static codebase scans."""

import uuid
from datetime import datetime
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.github.models import RepositoryAnalysisReport
from backend.intelligence.github.repository import GitRepositoryReader
from backend.intelligence.github.technology_detector import TechnologyDetector
from backend.intelligence.github.dependency_analyzer import DependencyAnalyzer
from backend.intelligence.github.architecture_detector import ArchitectureDetector
from backend.intelligence.github.documentation_analyzer import DocumentationAnalyzer
from backend.intelligence.github.metrics import RepositoryMetricsCollector


class RepositoryAnalyzerEngine:
    """Orchestrates technology discovery, manifest parsers, docs scoring, and code structure checks."""

    def __init__(self) -> None:
        self.tech_detector = TechnologyDetector()
        self.dep_analyzer = DependencyAnalyzer()
        self.arch_detector = ArchitectureDetector()
        self.docs_analyzer = DocumentationAnalyzer()
        self.metrics_collector = RepositoryMetricsCollector()
        self.event_bus = EventBus()

    def analyze_repository(
        self,
        reader: GitRepositoryReader,
        repository_url: str = "",
        branch: str = "main",
        workspace_id: str = "default-ws"
    ) -> RepositoryAnalysisReport:
        """Runs the complete suite of repository analyzers.

        Args:
            reader: Local Git repository reader.
            repository_url: Repository URL.
            branch: Repository branch context.
            workspace_id: Workspace scope.

        Returns:
            RepositoryAnalysisReport: Structured analyzer details.
        """
        # Detect techs, deps, architecture, docs, and basic size metrics
        techs = self.tech_detector.detect_technologies(reader)
        deps = self.dep_analyzer.analyze_dependencies(reader)
        arch = self.arch_detector.detect_architecture(reader)
        docs = self.docs_analyzer.analyze_documentation(reader)
        metrics = self.metrics_collector.collect_metrics(reader)

        report = RepositoryAnalysisReport(
            report_id=f"rep-struct-{str(uuid.uuid4())[:8]}",
            repository_url=repository_url,
            branch=branch,
            detected_technologies=techs,
            dependencies=deps,
            architecture=arch,
            documentation=docs,
            file_count=metrics["file_count"],
            total_lines=metrics["total_lines"],
            analyzed_at=datetime.utcnow()
        )

        # Publish core system event
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="RepositoryAnalyzerEngine",
            payload={
                "event": "github.repository.timeline.updated",
                "workspace_id": workspace_id,
                "repository_url": repository_url,
                "report_id": report.report_id
            }
        )
        self.event_bus.publish(event)

        return report
