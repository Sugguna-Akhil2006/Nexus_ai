"""Unit tests for the canonical Resume Data Model, validators, and normalizers."""

import json
import unittest
from unittest.mock import MagicMock, patch
import uuid

from backend.api.sqlite_mock import DBStorage
from backend.intelligence.resume.models import (
    Resume,
    SocialLink,
    PersonalInformation,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Skill,
    CertificationEntry,
    Language,
    Award,
    Publication,
    VolunteerExperience,
    CustomSection,
    ParsedResume,
    SkillsCategory,
)
from backend.intelligence.resume.validators import ResumeValidator, ResumeNormalizer, parse_date_safely
from backend.intelligence.resume.exceptions import ResumeValidationError
from backend.intelligence.resume.services import ResumeService
from backend.runtime.event import EventBus, Event, EventType


class TestResumeDataModel(unittest.TestCase):
    """Verifies parsing validations, text normalizations, events, and database storage."""

    def test_canonical_resume_creation(self) -> None:
        """Verifies instantiating a Resume with defaults populated."""
        resume = Resume(
            personal_info=PersonalInformation(full_name="Alice Smith", email="alice@example.com")
        )
        self.assertEqual(resume.personal_info.full_name, "Alice Smith")
        self.assertEqual(resume.personal_info.email, "alice@example.com")
        # Assert other sections are correctly instantiated as default lists
        self.assertEqual(resume.education, [])
        self.assertEqual(resume.experience, [])
        self.assertEqual(resume.projects, [])
        self.assertEqual(resume.skills, [])
        self.assertEqual(resume.languages, [])
        self.assertEqual(resume.awards, [])
        self.assertEqual(resume.publications, [])
        self.assertEqual(resume.volunteer, [])
        self.assertEqual(resume.custom_sections, [])

    def test_validators_email(self) -> None:
        """Verifies that the validator checks email addresses structure."""
        validator = ResumeValidator()
        # Correct email
        validator.validate_email("candidate@nexus.ai")
        # Empty email
        validator.validate_email(None)
        validator.validate_email("")

        # Malformed email
        with self.assertRaises(ResumeValidationError):
            validator.validate_email("malformed_email")
        with self.assertRaises(ResumeValidationError):
            validator.validate_email("malformed@com")

    def test_validators_url(self) -> None:
        """Verifies protocol and domain validator for links."""
        validator = ResumeValidator()
        validator.validate_url("https://github.com/alex", "github")
        validator.validate_url("http://alex.portfolio.me", "portfolio")
        validator.validate_url("alex.portfolio.me", "portfolio")  # valid scheme-less URL
        validator.validate_url(None, "website")

        # Invalid protocol/syntax
        with self.assertRaises(ResumeValidationError):
            validator.validate_url("not_a_valid_url", "portfolio")
        with self.assertRaises(ResumeValidationError):
            validator.validate_url("ftp://github.com/alex", "github")

    def test_validators_date_range(self) -> None:
        """Verifies date ranges comparison checks consistency."""
        validator = ResumeValidator()
        
        # Valid cases
        validator.validate_date_range("2020", "2022", "test")
        validator.validate_date_range("January 2018", "December 2020", "test")
        validator.validate_date_range("05/2019", "Present", "test")
        validator.validate_date_range("2021", None, "test")
        validator.validate_date_range(None, "2021", "test")

        # Invalid cases where start > end
        with self.assertRaises(ResumeValidationError):
            validator.validate_date_range("2022", "2020", "test")
        with self.assertRaises(ResumeValidationError):
            validator.validate_date_range("December 2020", "January 2018", "test")

    def test_parse_date_safely(self) -> None:
        """Verifies helper extracts dates appropriately from various patterns."""
        self.assertIsNotNone(parse_date_safely("Present"))
        self.assertIsNotNone(parse_date_safely("2020"))
        self.assertIsNotNone(parse_date_safely("June 2021"))
        self.assertIsNotNone(parse_date_safely("01/2022"))
        self.assertIsNone(parse_date_safely(None))

    def test_validator_required_fields(self) -> None:
        """Verifies full_name validation requirement raises if missing."""
        validator = ResumeValidator()
        
        resume_ok = Resume(personal_info=PersonalInformation(full_name="Bob"))
        validator.validate(resume_ok)

        resume_bad = Resume(personal_info=PersonalInformation(full_name=""))
        with self.assertRaises(ResumeValidationError):
            validator.validate(resume_bad)

        resume_missing = Resume(personal_info=PersonalInformation(full_name=None))
        with self.assertRaises(ResumeValidationError):
            validator.validate(resume_missing)

    def test_normalizer_company(self) -> None:
        """Verifies stripping standard suffixes from companies names."""
        norm = ResumeNormalizer()
        self.assertEqual(norm.normalize_company("Google Inc."), "Google")
        self.assertEqual(norm.normalize_company("OpenAI LLC."), "OpenAI")
        self.assertEqual(norm.normalize_company("Stripe, Corp"), "Stripe")
        self.assertEqual(norm.normalize_company("Microsoft Corporation"), "Microsoft")
        self.assertEqual(norm.normalize_company(None), None)

    def test_normalizer_degree(self) -> None:
        """Verifies standard degree mappings normalization."""
        norm = ResumeNormalizer()
        self.assertEqual(norm.normalize_degree("BS"), "Bachelor of Science")
        self.assertEqual(norm.normalize_degree("B.S."), "Bachelor of Science")
        self.assertEqual(norm.normalize_degree("bachelor of science"), "Bachelor of Science")
        self.assertEqual(norm.normalize_degree("B.Tech"), "Bachelor of Technology")
        self.assertEqual(norm.normalize_degree("M.S."), "Master of Science")
        self.assertEqual(norm.normalize_degree("Ph.D."), "Doctor of Philosophy")
        self.assertEqual(norm.normalize_degree("Self-Taught"), "Self-Taught")

    def test_normalizer_url(self) -> None:
        """Verifies prepending https:// prefix to URLs."""
        norm = ResumeNormalizer()
        self.assertEqual(norm.normalize_url("github.com/test"), "https://github.com/test")
        self.assertEqual(norm.normalize_url("https://github.com/test"), "https://github.com/test")
        self.assertEqual(norm.normalize_url(None), None)

    def test_normalizer_tech(self) -> None:
        """Verifies technological keywords standardized casing and spelling."""
        norm = ResumeNormalizer()
        self.assertEqual(norm.normalize_tech("postgres"), "PostgreSQL")
        self.assertEqual(norm.normalize_tech("k8s"), "Kubernetes")
        self.assertEqual(norm.normalize_tech("aws"), "AWS")
        self.assertEqual(norm.normalize_tech("python"), "Python")
        self.assertEqual(norm.normalize_tech("rust"), "rust")

    def test_normalizer_duplicate_removals(self) -> None:
        """Verifies deduplication of list categories during normalization."""
        resume = Resume(
            personal_info=PersonalInformation(full_name="Duplicate Tester"),
            skills=[
                Skill(name="python", category="Programming Languages"),
                Skill(name="Python", category="Programming Languages"),
                Skill(name="python", category="Tools"),  # Different category, should keep
                Skill(name="k8s", category="DevOps"),
            ],
            certifications=[
                CertificationEntry(certification_name="AWS Solutions Architect", organization="AWS"),
                CertificationEntry(certification_name="AWS Solutions Architect", organization="Amazon"), # duplicate name
            ],
            languages=[
                Language(name="English", proficiency="Native"),
                Language(name="english", proficiency="Fluent"),
            ]
        )
        normalized = ResumeNormalizer().normalize(resume)
        
        # Verify skills (Python in Programming, python in Tools, and k8s in DevOps)
        self.assertEqual(len(normalized.skills), 3)
        self.assertEqual(normalized.skills[0].name, "Python")
        self.assertEqual(normalized.skills[1].name, "Python")
        self.assertEqual(normalized.skills[1].category, "Tools")
        self.assertEqual(normalized.skills[2].name, "Kubernetes")
        
        # Verify certifications deduplicated by name
        self.assertEqual(len(normalized.certifications), 1)
        self.assertEqual(normalized.certifications[0].certification_name, "AWS Solutions Architect")
        
        # Verify languages deduplicated
        self.assertEqual(len(normalized.languages), 1)
        self.assertEqual(normalized.languages[0].name, "English")

    def test_service_mapping_and_orchestration(self) -> None:
        """Tests map_parsed_to_canonical and full pipeline with DB storage."""
        parsed_mvp = ParsedResume(
            personal_info=PersonalInformation(
                full_name="Charlie Brown",
                email="charlie@peanuts.com",
                phone="123456",
                linkedin="linkedin.com/in/charlie",
                github="github.com/charlie",
                portfolio="charlie.com"
            ),
            education=[
                EducationEntry(institution="School", degree="B.S.", graduation_year="2020")
            ],
            experience=[
                ExperienceEntry(company="DogHouse LLC", role="Dog Feeder", start_date="2020", end_date="Present")
            ],
            projects=[
                ProjectEntry(project_name="Kite Flyer", description="Flys kites", technologies=["wind"])
            ],
            skills=SkillsCategory(
                programming_languages=["python"],
                frameworks=["fastapi"],
                databases=["postgres"]
            ),
            certifications=[
                CertificationEntry(certification_name="Good Boy Cert", organization="Snoopy")
            ]
        )

        service = ResumeService()
        
        # Test mapping
        canonical = service.map_parsed_to_canonical(parsed_mvp)
        self.assertEqual(canonical.personal_info.full_name, "Charlie Brown")
        self.assertEqual(canonical.education[0].graduation_year, "2020")
        self.assertEqual(canonical.education[0].end_year, "2020")
        self.assertEqual(canonical.experience[0].company, "DogHouse LLC")
        self.assertEqual(len(canonical.skills), 3)

        # Test full orchestrator pipeline with event bus and persistence Mocking parser
        event_bus = EventBus()
        events_fired = []

        def event_listener(event: Event) -> None:
            events_fired.append(event.payload.get("event"))

        event_bus.subscribe(EventType.CUSTOM_EVENT, event_listener)

        with patch.object(service.parser, "parse_resume", return_value=parsed_mvp):
            doc_id, normalized_res = service.parse_validate_normalize(
                contents=b"dummy content",
                filename="charlie_resume.pdf",
                workspace_id="test-workspace"
            )

        # Dispatch events
        event_bus.dispatch_all()

        # Verify event publishing
        self.assertIn("resume.parsed", events_fired)
        self.assertIn("resume.validated", events_fired)
        self.assertIn("resume.normalized", events_fired)

        # Verify DB Persistence
        retrieved = service.get_resume(doc_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.personal_info.full_name, "Charlie Brown")
        
        # Verify Normalization took place in persistent storage
        self.assertEqual(retrieved.experience[0].company, "DogHouse")
        self.assertEqual(retrieved.personal_info.linkedin, "https://linkedin.com/in/charlie")
        self.assertEqual(retrieved.education[0].degree, "Bachelor of Science")

        # Clean up event subscription
        event_bus.unsubscribe(EventType.CUSTOM_EVENT, event_listener)
