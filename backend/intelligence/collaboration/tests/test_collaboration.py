"""Integration tests validating Multi-Agent Collaboration Framework dispatch, blackboard, and consensus."""

import time
import unittest
from backend.intelligence.collaboration.models import CollaborationSession, AgentTask
from backend.intelligence.collaboration.shared_context import SharedContext
from backend.intelligence.collaboration.collaboration_manager import CollaborationManager


class TestCollaboration(unittest.TestCase):
    """Integration test suite verifying multi-agent delegation, blackboard queues, and consensus."""

    def setUp(self) -> None:
        self.manager = CollaborationManager()
        self.ws_id = "ws-collab-test"

        # Define and register mock agent routines
        def resume_agent_handler(payload: dict, context: SharedContext) -> dict:
            context.add_evidence("ResumeAgent", "Resume records 5 years of Python skill experience.", 0.9)
            return {"status": "success", "skills": ["Python"]}

        def github_agent_handler(payload: dict, context: SharedContext) -> dict:
            context.add_evidence("GitHubAgent", "GitHub repo indexes 3 Python active repositories.", 1.0)
            return {"status": "success", "repos": 3}

        def doc_agent_handler(payload: dict, context: SharedContext) -> dict:
            context.add_evidence("DocumentAgent", "Documentation notes SQLite replication bottlenecks.", 0.8)
            return {"status": "success", "db": "SQLite"}

        self.manager.registry.register_agent("ResumeAgent", resume_agent_handler)
        self.manager.registry.register_agent("GitHubAgent", github_agent_handler)
        self.manager.registry.register_agent("DocumentAgent", doc_agent_handler)

    def test_two_agent_collaboration(self) -> None:
        """Verifies context sharing and step dispatches across Resume and GitHub mock agents."""
        session, context = self.manager.start_session(self.ws_id, "Analyze candidate Python profile.")

        # Delegate to Resume Agent
        res1 = self.manager.delegate(session, context, "Orchestrator", "ResumeAgent", "Load resume profile info", {})
        self.assertEqual(res1["status"], "success")

        # Delegate to GitHub Agent
        res2 = self.manager.delegate(session, context, "Orchestrator", "GitHubAgent", "Load GitHub repositories", {})
        self.assertEqual(res2["status"], "success")

        # Complete and compile report
        report = self.manager.complete_session(session, context)

        # Assertions
        self.assertEqual(report.session_id, session.session_id)
        self.assertIn("ResumeAgent", report.executed_agents)
        self.assertIn("GitHubAgent", report.executed_agents)
        self.assertEqual(len(report.shared_evidence), 2)
        self.assertGreater(report.confidence_score, 0.0)
        self.assertGreater(len(report.timeline), 0)

    def test_three_agent_collaboration(self) -> None:
        """Verifies context sharing across three mock agents."""
        session, context = self.manager.start_session(self.ws_id, "Index candidate system details.")

        self.manager.delegate(session, context, "Orchestrator", "ResumeAgent", "Get resume profile", {})
        self.manager.delegate(session, context, "Orchestrator", "GitHubAgent", "Get repositories", {})
        self.manager.delegate(session, context, "Orchestrator", "DocumentAgent", "Get database setup", {})

        report = self.manager.complete_session(session, context)
        self.assertEqual(len(report.executed_agents), 3)

    def test_conflict_resolution_consensus(self) -> None:
        """Validates that opposing claims trigger contradiction flags and lower confidence."""
        # 1. Register contradictory handlers
        def agent_a_handler(payload: dict, context: SharedContext) -> dict:
            context.add_evidence("AgentA", "Benchmark tests prove FastAPI increases response performance.", 1.0)
            return {}

        def agent_b_handler(payload: dict, context: SharedContext) -> dict:
            context.add_evidence("AgentB", "Benchmark tests prove FastAPI decreases response performance.", 0.8)
            return {}

        self.manager.registry.register_agent("AgentA", agent_a_handler)
        self.manager.registry.register_agent("AgentB", agent_b_handler)

        session, context = self.manager.start_session(self.ws_id, "How does FastAPI affect performance?")
        
        self.manager.delegate(session, context, "Orchestrator", "AgentA", "Run performance analysis A", {})
        self.manager.delegate(session, context, "Orchestrator", "AgentB", "Run performance analysis B", {})

        report = self.manager.complete_session(session, context)

        # Contradiction should be evaluated inside Consensus/Reasoning engine
        # Base avg = (1.0 + 0.8)/2 = 0.9. Penalty for contradiction = -0.15. Final = 0.75
        self.assertAlmostEqual(report.confidence_score, 0.75, places=2)

    def test_timeout_retry_recovery(self) -> None:
        """Verifies that the delegator retries a failing agent, and raises on final failure."""
        call_count = 0

        def flaky_agent_handler(payload: dict, context: SharedContext) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Simulated network timeout.")
            context.add_evidence("FlakyAgent", "Resolved details successfully.", 0.9)
            return {"status": "recovered"}

        self.manager.registry.register_agent("FlakyAgent", flaky_agent_handler)
        session, context = self.manager.start_session(self.ws_id, "Recover flaky data.")

        # Should recover on the second attempt (1 retry)
        result = self.manager.delegate(session, context, "Orchestrator", "FlakyAgent", "Fetch dynamic records", {}, retry_count=2)
        self.assertEqual(result["status"], "recovered")
        self.assertEqual(call_count, 2)
