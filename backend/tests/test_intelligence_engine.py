"""Tests for the Nexus Intelligence Engine.

Verifies the 7 services, 6 tools, EventBus notifications, and performance benchmarks.
"""

import json
import time
import unittest

from backend.services.intelligence import (
    SummaryService, EntityExtractionService, ClassificationService,
    ComparisonService, RecommendationService, ConfidenceService, ReportService
)
from backend.tools.tool import ToolRegistry, ToolRequest
from backend.runtime.event import Event, EventBus, EventType

class TestIntelligenceEngine(unittest.TestCase):
    """Test suite covering stateless intelligence services, EventBus events, and performance tests."""

    def setUp(self) -> None:
        self.tool_registry = ToolRegistry()
        self.workspace_id = "ws-intel-test"
        self.user_id = "admin"

        # Setup Mock Model Provider
        from backend.interfaces.model import ModelRegistry
        from backend.agents.chat import MockChatModelProvider
        self.model_registry = ModelRegistry()
        with self.model_registry._lock:
            self.model_registry._providers.clear()
        self.model_provider = MockChatModelProvider()
        self.model_registry.register_provider("mock_chat", self.model_provider)

        # Setup Event Listener to catch custom events
        self.event_bus = EventBus()
        self.caught_events = []
        self.event_bus.subscribe("*", self.catch_event)

        self.mock_text = "Jane Doe has 5 years of software engineering experience."

    def catch_event(self, event: Event) -> None:
        """Callback to store published events."""
        if event.event_type == EventType.CUSTOM_EVENT:
            self.caught_events.append(event.payload.get("event_name"))

    def test_tools_registration(self) -> None:
        """Verifies the 6 reusable intelligence tools are registered in the registry."""
        expected_tools = [
            "summary_tool", "entity_extraction_tool", "classification_tool", 
            "comparison_tool", "recommendation_tool", "report_tool"
        ]
        registered = [t.schema.tool_id for t in self.tool_registry.list_tools()]
        for t in expected_tools:
            self.assertIn(t, registered, f"Tool '{t}' is not registered in the ToolRegistry.")

    def test_services_execution(self) -> None:
        """Verifies each service executes successfully, triggers events, and yields correct outputs."""
        self.caught_events.clear()

        # 1. SummaryService
        summary_srv = SummaryService()
        sum_out = summary_srv.summarize(self.mock_text, self.workspace_id)
        self.assertIsNotNone(sum_out)
        self.assertIn("Summarized", sum_out)

        # 2. EntityExtractionService
        entity_srv = EntityExtractionService()
        ent_out = entity_srv.extract_entities(self.mock_text, {"name": "string"}, self.workspace_id)
        self.assertEqual(ent_out.get("name"), "Jane Doe")

        # 3. ClassificationService
        class_srv = ClassificationService()
        class_out = class_srv.classify(self.mock_text, ["tech", "finance"], self.workspace_id)
        self.assertEqual(class_out.get("primary_category"), "tech")

        # 4. ComparisonService
        comp_srv = ComparisonService()
        comp_out = comp_srv.compare([{"v1": self.mock_text}], self.workspace_id)
        self.assertIn("deltas", comp_out)

        # 5. RecommendationService
        rec_srv = RecommendationService()
        rec_out = rec_srv.generate_recommendations(self.mock_text, ["improve"], self.workspace_id)
        self.assertGreater(len(rec_out), 0)

        # 6. ConfidenceService
        conf_srv = ConfidenceService()
        conf_out = conf_srv.evaluate_confidence(self.mock_text, self.mock_text, self.workspace_id)
        self.assertGreater(conf_out.get("confidence_score", 0.0), 0.5)

        # 7. ReportService
        rep_srv = ReportService()
        rep_out = rep_srv.generate_report_formats({"analysis": "done"}, "E2E Report")
        self.assertIn("markdown", rep_out)
        self.assertIn("pdf_data_model", rep_out)

        # Assert custom EventBus publications are generated
        self.assertIn("analysis.started", self.caught_events)
        self.assertIn("analysis.completed", self.caught_events)
        self.assertIn("report.generated", self.caught_events)

    def test_performance_benchmark(self) -> None:
        """Measures the latency of running services to benchmark performance metrics."""
        summary_srv = SummaryService()
        start = time.perf_counter()
        
        # Run 5 fast iterations to evaluate average execution timings
        for _ in range(5):
            summary_srv.summarize(self.mock_text, self.workspace_id)
            
        duration = time.perf_counter() - start
        avg_latency = duration / 5
        
        # In a mock local configuration, this should be sub-second
        self.assertLess(avg_latency, 1.0, f"Average latency {avg_latency}s exceeded benchmark threshold of 1.0s.")
