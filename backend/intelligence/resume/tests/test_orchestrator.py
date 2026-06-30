"""Integration tests for Resume Intelligence Orchestrator pipeline, retries, and failures."""

import unittest
from unittest.mock import patch, MagicMock

from backend.intelligence.resume.models import (
    Resume,
    PersonalInformation,
    EducationEntry,
    ExperienceEntry,
    Skill,
    JobDescription,
    UnifiedResumeReport
)
from backend.intelligence.resume.resume_agent import ResumeAgent
from backend.intelligence.resume.workflow import StageNames, StageExecutionError
from backend.runtime.event import Event, EventBus


class TestOrchestrator(unittest.TestCase):
    """Verifies modular pipeline execution, timed telemetry, error isolation, and retry loops."""

    def setUp(self) -> None:
        self.agent = ResumeAgent()
        self.event_bus = EventBus()
        self.events_fired = []
        self.event_bus.subscribe("*", self.catch_event)

        # Mock the LLM queries for deterministic test speeds
        self.llm_patcher = patch("backend.intelligence.resume.jd_parser.run_resume_llm_query")
        self.mock_llm_query = self.llm_patcher.start()
        
        # Simple mock return for Job Description parsing
        self.mock_llm_query.return_value = {
            "job_title": "AI Engineer",
            "company": "TechCorp",
            "experience_required": "3 years",
            "education_requirements": ["BS in Computer Science"],
            "required_skills": ["Python", "PyTorch"],
            "preferred_skills": [],
            "responsibilities": ["Deploy models"],
            "technologies": ["Python"],
            "certifications": [],
            "soft_skills": [],
            "location": "Remote",
            "employment_type": "Full-time"
        }

    def tearDown(self) -> None:
        self.llm_patcher.stop()
        self.event_bus.unsubscribe("*", self.catch_event)

    def catch_event(self, event: Event) -> None:
        self.events_fired.append(event)

    def _create_test_resume(self) -> Resume:
        return Resume(
            personal_info=PersonalInformation(
                full_name="Alice Smith",
                email="alice@smith.com",
                phone="987654",
                github="https://github.com/alicesmith"
            ),
            education=[
                EducationEntry(
                    institution="Stanford",
                    degree="BS",
                    branch="CS",
                    graduation_year="2021"
                )
            ],
            experience=[
                ExperienceEntry(
                    company="AppCorp",
                    role="Developer",
                    start_date="2021-06",
                    end_date="2023-06",
                    responsibilities=["Created REST backend services in Python.", "Optimized DB queries, saving 15% latency."]
                )
            ],
            skills=[
                Skill(name="Python"),
                Skill(name="FastAPI"),
                Skill(name="PostgreSQL")
            ]
        )

    def test_student_orchestration(self) -> None:
        """Verifies parsing and analysis routing for student profile inputs (no JD)."""
        resume = self._create_test_resume()
        resume.experience = []
        
        report = self.agent.analyze_resume(resume=resume, workspace_id="ws-student")
        
        self.assertIsInstance(report, UnifiedResumeReport)
        self.assertEqual(report.resume_summary["career_stage"], "Student Backend Engineer")
        self.assertIsNone(report.jd_match_report)
        self.assertIsNotNone(report.ats_report)

        self.event_bus.dispatch_all()
        event_types = [e.payload.get("event") for e in self.events_fired if e.payload]
        self.assertIn("resume.workflow.started", event_types)
        self.assertIn("resume.parser.completed", event_types)
        self.assertIn("resume.analysis.completed", event_types)
        self.assertIn("resume.workflow.completed", event_types)

    def test_experienced_orchestration_with_jd(self) -> None:
        """Verifies standard matching and analysis routing for experienced resume + JD inputs."""
        resume = self._create_test_resume()
        jd_text = "We are seeking an AI Engineer who knows Python and PyTorch."
        
        report = self.agent.analyze_resume(
            resume=resume,
            job_description=jd_text,
            workspace_id="ws-exp-jd"
        )
        
        self.assertIsInstance(report, UnifiedResumeReport)
        self.assertIsNotNone(report.jd_match_report)
        self.assertEqual(report.jd_match_report.overall_score, 47.0) # Alice has Python, lacks PyTorch
        
        self.event_bus.dispatch_all()
        event_types = [e.payload.get("event") for e in self.events_fired if e.payload]
        self.assertIn("resume.jd.completed", event_types)

    @patch("backend.intelligence.resume.pipeline.PipelineExecutionRunner.run_ats_stage")
    def test_partial_failures_tolerance(self, mock_ats_run: MagicMock) -> None:
        """Verifies that if a non-critical module (e.g. ATS Engine) fails, the pipeline still completes."""
        mock_ats_run.side_effect = Exception("ATS Engine consistently unavailable")
        
        resume = self._create_test_resume()
        report = self.agent.analyze_resume(resume=resume, workspace_id="ws-fail")
        
        self.assertIsInstance(report, UnifiedResumeReport)
        self.assertIsNone(report.ats_report)  # ATS failed, so report has none
        self.assertIsNotNone(report.resume_summary)
        
        # Verify metadata recorded the failed stage and error message
        meta = report.pipeline_metadata
        self.assertEqual(meta["pipeline_status"], "completed")
        self.assertEqual(meta["failed_stage"], StageNames.ATS_ENGINE)
        self.assertIn("ATS Engine consistently unavailable", meta["errors"][StageNames.ATS_ENGINE])

    @patch("backend.intelligence.resume.pipeline.PipelineExecutionRunner.run_parser_stage")
    def test_module_retry_success(self, mock_parser_run: MagicMock) -> None:
        """Verifies that stage runner retries on transient errors and succeeds when next call works."""
        # 1st call raises transient error, 2nd call succeeds (simulates normal run)
        def mock_side_effect(context, state):
            if mock_parser_run.call_count == 1:
                raise Exception("Database transaction locked temporarily")
            # Success side effect: mimic baseline behavior
            from backend.intelligence.resume.pipeline import PipelineExecutionRunner
            PipelineExecutionRunner().run_parser_stage(context, state)

        mock_parser_run.side_effect = mock_side_effect
        
        resume_bytes = b"Jane Doe\nSkills: Python"
        report = self.agent.analyze_resume(resume=resume_bytes, workspace_id="ws-retry")
        
        self.assertIsInstance(report, UnifiedResumeReport)
        self.assertEqual(report.pipeline_metadata["pipeline_status"], "completed")
        
        # Verify retries recorded in execution metrics
        metrics = report.execution_metrics
        self.assertEqual(metrics["retry_counts"][StageNames.PARSER], 1)

    def test_large_resume(self) -> None:
        """Verifies system handles large resume input text strings successfully."""
        large_text = "Alice Large\n" + ("Experience: Senior Developer.\n" * 200) + "Skills: Python, Go."
        report = self.agent.analyze_resume(resume=large_text.encode("utf-8"), workspace_id="ws-large")
        self.assertIsInstance(report, UnifiedResumeReport)
        self.assertEqual(report.pipeline_metadata["pipeline_status"], "completed")

    def test_corrupted_resume(self) -> None:
        """Verifies that completely corrupted inputs result in workflow failure event."""
        # A completely empty content bytes will cause parser extraction to fail
        report = self.agent.analyze_resume(resume=b"", workspace_id="ws-corrupted")
        
        self.assertIsInstance(report, UnifiedResumeReport)
        self.assertEqual(report.pipeline_metadata["pipeline_status"], "failed")
        self.assertEqual(report.pipeline_metadata["failed_stage"], StageNames.PARSER)
        
        self.event_bus.dispatch_all()
        event_types = [e.payload.get("event") for e in self.events_fired if e.payload]
        self.assertIn("resume.workflow.failed", event_types)
