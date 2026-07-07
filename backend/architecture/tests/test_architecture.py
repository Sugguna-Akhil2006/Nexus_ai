"""Unit and integration tests for the Architecture Knowledge Center."""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.architecture.architecture_service import ArchitectureService
from backend.architecture.decision_log import DecisionLog
from backend.architecture.dependency_mapper import DependencyMapper
from backend.architecture.documentation_generator import DocumentationGenerator
from backend.architecture.models import DecisionRecord, ModuleMetadata
from backend.architecture.module_catalog import ModuleCatalog
from backend.architecture.sequence_generator import SequenceGenerator


class TestModuleCatalog(unittest.TestCase):
    """Verifies module catalog documentation extraction."""

    def setUp(self) -> None:
        self.catalog = ModuleCatalog()

    def test_extract_catalog(self) -> None:
        items = self.catalog.get_catalog()
        self.assertGreater(len(items), 0)
        self.assertTrue(any(m.name.lower() == "resume" for m in items))


class TestDependencyMapper(unittest.TestCase):
    """Verifies dependency DAG nodes and edges mapping."""

    def test_mapper_graph(self) -> None:
        graph = DependencyMapper.get_map()
        self.assertGreater(len(graph.nodes), 0)
        self.assertGreater(len(graph.edges), 0)
        self.assertIn("graph TD", graph.mermaid_diagram)


class TestSequenceGenerator(unittest.TestCase):
    """Verifies Mermaid sequence diagram generation."""

    def test_resume_sequence(self) -> None:
        flow = SequenceGenerator.generate_flow("resume")
        self.assertIn("Sequence", flow.flow_name)
        self.assertGreater(len(flow.steps), 0)
        self.assertIn("sequenceDiagram", flow.mermaid_diagram)


class TestDecisionLog(unittest.TestCase):
    """Verifies ADR logs pre-seeding and insertions."""

    def setUp(self) -> None:
        self.log = DecisionLog()

    def test_default_adrs(self) -> None:
        decisions = self.log.list_decisions()
        self.assertEqual(len(decisions), 2)
        self.assertEqual(decisions[0].decision_id, "ADR-001")


class TestDocumentationGenerator(unittest.TestCase):
    """Verifies handbooks markdown/HTML/JSON compiles."""

    def test_compiles_handbook(self) -> None:
        modules = [
            ModuleMetadata(
                name="Test",
                purpose="Testing purpose",
                dependencies=[],
            )
        ]
        decisions = [
            DecisionRecord(
                decision_id="ADR-0",
                title="Test ADR",
                reason="For tests",
                consequences="Consequences",
                owner="Admin",
            )
        ]
        diagram = "graph TD\n A --> B"

        md = DocumentationGenerator.generate_markdown_handbook(modules, decisions, diagram)
        self.assertIn("Developer Handbook", md)
        self.assertIn("Test ADR", md)

        html = DocumentationGenerator.generate_html_handbook(md)
        self.assertIn("<!DOCTYPE html>", html)

        js = DocumentationGenerator.generate_json_handbook(modules, decisions)
        self.assertIn("Testing purpose", js)
