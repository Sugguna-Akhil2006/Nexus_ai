"""Integration tests validating Research Intelligence metadata parses, comparisons, and profile syncs."""

import os
import uuid
import unittest
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.profile.models import KnowledgeProfile
from backend.intelligence.research.research_service import ResearchService


class TestResearchFoundation(unittest.TestCase):
    """Integration test suite validating literature review, comparisons, and citation manager pipelines."""

    def setUp(self) -> None:
        self.db_name = f"test_research_{str(uuid.uuid4())[:8]}.db"
        self.service = ResearchService(db_path=self.db_name)
        self.cache = DocumentCache()
        self.ws_id = "ws-res-test"
        
        # Clear document cache
        self.cache._documents.clear()

    def tearDown(self) -> None:
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except Exception:
                pass

    def test_multi_paper_analysis_and_synthesis(self) -> None:
        """Processes multiple papers to verify synthesis, evidence matrices, and bibliography listings."""
        # 1. Store mock document 1: Vance CRM Paper
        doc1_text = (
            "CRM Performance Benchmarks\n"
            "By Bob Vance and Phyllis Lapin.\n"
            "Abstract: This study demonstrates that Python FastAPI backends improve CRM response latency.\n"
            "1. Introduction\n"
            "We conclude that FastAPI increases performance by 40% compared to REST API baselines under standard loads.\n"
            "Keywords: Python, FastAPI, CRM, Performance\n"
            "References:\n"
            "[1] Vance, B. (2025). refrigerator scaling benchmarks.\n"
            "[2] Lapin, P. (2026). cloud data latency."
        )
        doc1_id = "doc-vance-crm"
        self.cache.save_document(doc1_id, "vance_crm.md", doc1_text)

        # 2. Store mock document 2: Vance DB Paper
        doc2_text = (
            "Database Replication Bottlenecks\n"
            "By Dwight Schrute.\n"
            "Abstract: This paper investigates SQLite clustering. We speculate that network latency slows down SQLite synchronization.\n"
            "1. Introduction\n"
            "Our results prove that network sync decreases performance of replicate databases.\n"
            "Keywords: Python, SQLite, Replication, Database\n"
            "References:\n"
            "[1] Schrute, D. (2024). beet farm data logistics."
        )
        doc2_id = "doc-dwight-db"
        self.cache.save_document(doc2_id, "dwight_db.md", doc2_text)

        # 3. Initialize profile
        profile = KnowledgeProfile(workspace_id=self.ws_id, user_id="bob")

        # 4. Trigger Research Service
        report = self.service.analyze_papers(self.ws_id, [doc1_id, doc2_id], profile)

        # 5. Assertions
        self.assertIsNotNone(report.executive_summary)
        self.assertGreater(len(report.key_findings), 0)
        self.assertGreater(len(report.evidence_matrix), 0)
        
        # Check evidence items
        claims = [e["claim"] for e in report.evidence_matrix]
        self.assertTrue(any("increases performance by 40%" in c for c in claims))
        self.assertTrue(any("sync decreases performance" in c for c in claims))

        # Check contradictions detection
        comp = report.source_comparison
        self.assertIsNotNone(comp)
        self.assertIn("Python", comp["consensus_keywords"])
        self.assertGreater(len(comp["detected_contradictions"]), 0)
        self.assertEqual(comp["detected_contradictions"][0]["keyword"], "performance")

        # Check citations and bibliography listing
        self.assertGreater(len(report.citations), 0)
        self.assertIn("[1]", [c["citation_key"] for c in report.citations])
        self.assertGreater(len(report.suggested_reading), 0)
        self.assertTrue(any("refrigerator scaling benchmarks" in r for r in report.suggested_reading))

        # Check UKP graph sync
        self.assertIn("research paper:CRM Performance Benchmarks", profile.knowledge_graph)
        self.assertIn("topic:Python", profile.knowledge_graph["research paper:CRM Performance Benchmarks"])
        self.assertIn("research paper:Database Replication Bottlenecks", profile.knowledge_graph)
        self.assertIn("topic:Python", profile.knowledge_graph["research paper:Database Replication Bottlenecks"])
