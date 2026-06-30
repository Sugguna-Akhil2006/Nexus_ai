"""Unit and integration tests for the Skill Extraction Engine."""

import unittest
from backend.intelligence.resume.models import (
    Resume,
    PersonalInformation,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Skill,
    CertificationEntry,
    Language,
    Publication,
    VolunteerExperience,
    SkillsCategory,
    ParsedResume,
)
from backend.intelligence.resume.skill_extractor import SkillExtractor
from backend.intelligence.resume.skill_taxonomy import classify_skill_by_taxonomy
from backend.intelligence.resume.normalizer import normalize_skill_name
from backend.intelligence.resume.confidence import calculate_confidence


class TestSkillExtractorEngine(unittest.TestCase):
    """Verifies taxonomy mappings, inferences, alias normalizations, and deduplications."""

    def setUp(self) -> None:
        self.extractor = SkillExtractor()

    def test_alias_normalization(self) -> None:
        """Verifies skill alias mappings to standard forms."""
        self.assertEqual(normalize_skill_name("js"), "JavaScript")
        self.assertEqual(normalize_skill_name("Py"), "Python")
        self.assertEqual(normalize_skill_name("ReactJS"), "React")
        self.assertEqual(normalize_skill_name("Tensor Flow"), "TensorFlow")
        self.assertEqual(normalize_skill_name("LLMs"), "Large Language Models")
        self.assertEqual(normalize_skill_name("node"), "Node.js")
        self.assertEqual(normalize_skill_name("kubernetes"), "Kubernetes")
        self.assertEqual(normalize_skill_name("unknown-tech"), "Unknown Tech")

    def test_taxonomy_classification(self) -> None:
        """Verifies matching skill names map to correct categories."""
        self.assertEqual(classify_skill_by_taxonomy("Python"), "Programming Languages")
        self.assertEqual(classify_skill_by_taxonomy("FastAPI"), "Frameworks")
        self.assertEqual(classify_skill_by_taxonomy("Pandas"), "Libraries")
        self.assertEqual(classify_skill_by_taxonomy("PostgreSQL"), "Databases")
        self.assertEqual(classify_skill_by_taxonomy("AWS"), "Cloud Platforms")
        self.assertEqual(classify_skill_by_taxonomy("Docker"), "DevOps")
        self.assertEqual(classify_skill_by_taxonomy("Linux"), "Operating Systems")
        self.assertEqual(classify_skill_by_taxonomy("TCP/IP"), "Networking")
        self.assertEqual(classify_skill_by_taxonomy("OAuth"), "Cybersecurity")
        self.assertEqual(classify_skill_by_taxonomy("PyTorch"), "Deep Learning")
        self.assertEqual(classify_skill_by_taxonomy("Scikit-Learn"), "Machine Learning")
        self.assertEqual(classify_skill_by_taxonomy("GPT-4"), "Generative AI")
        self.assertEqual(classify_skill_by_taxonomy("LangChain"), "LLM Frameworks")
        self.assertEqual(classify_skill_by_taxonomy("Pinecone"), "Vector Databases")
        self.assertEqual(classify_skill_by_taxonomy("Statistics"), "Data Science")
        self.assertEqual(classify_skill_by_taxonomy("Android Studio"), "Mobile Development")
        self.assertEqual(classify_skill_by_taxonomy("HTML"), "Frontend")
        self.assertEqual(classify_skill_by_taxonomy("Microservices"), "Backend")
        self.assertEqual(classify_skill_by_taxonomy("Pytest"), "Testing")
        self.assertEqual(classify_skill_by_taxonomy("Git"), "Version Control")
        self.assertEqual(classify_skill_by_taxonomy("Leadership"), "Soft Skills")
        self.assertEqual(classify_skill_by_taxonomy("Random Unmapped"), "Other")

    def test_confidence_calculations(self) -> None:
        """Verifies baseline scoring and frequency boosts logic."""
        # Explicit baseline
        self.assertAlmostEqual(calculate_confidence("Explicit Skills", "Explicit", 1), 0.95)
        # Weight boost for frequency
        self.assertAlmostEqual(calculate_confidence("Explicit Skills", "Explicit", 2), 1.0)
        # Inference baseline
        self.assertAlmostEqual(calculate_confidence("Inference", "Inferred", 1), 0.80)
        # DevOps baseline weight check
        self.assertAlmostEqual(calculate_confidence("Projects", "Explicit", 1), 0.80)

    def test_explicit_skills_extraction(self) -> None:
        """Verifies extraction of explicit skills section."""
        resume = Resume(
            personal_info=PersonalInformation(full_name="Alice"),
            skills=[Skill(name="Go", category="Programming Languages")]
        )
        profile = self.extractor.extract_skills_profile(resume)
        
        # Verify explicit match
        matching = [s for s in profile.skills if s.name == "Go"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].explicit_or_inferred, "Explicit")
        self.assertEqual(matching[0].category, "Programming Languages")
        self.assertEqual(matching[0].confidence_score, 0.95)

    def test_inferred_skills_extraction(self) -> None:
        """Verifies triggering of inferred skills with high confidence."""
        resume = Resume(
            personal_info=PersonalInformation(full_name="Bob"),
            skills=[Skill(name="FastAPI", category="Frameworks")]
        )
        profile = self.extractor.extract_skills_profile(resume)
        
        # Should infer: Python Backend, REST APIs, API Development
        inferred_names = [s.name for s in profile.skills if s.explicit_or_inferred == "Inferred"]
        self.assertIn("Python Backend", inferred_names)
        self.assertIn("REST APIs", inferred_names)
        self.assertIn("API Development", inferred_names)

        # Check confidence is high and evidence cited correctly
        python_backend = [s for s in profile.skills if s.name == "Python Backend"][0]
        self.assertEqual(python_backend.confidence_score, 0.80)
        self.assertEqual(python_backend.evidence[0].source, "Inference")
        self.assertIn("Inferred from FastAPI", python_backend.evidence[0].context)

    def test_duplicate_skills_deduplication(self) -> None:
        """Verifies merging duplicate skills, keeping strongest source and summing frequency."""
        resume = Resume(
            personal_info=PersonalInformation(full_name="Charlie"),
            skills=[Skill(name="Python", category="Programming Languages")],
            experience=[ExperienceEntry(
                company="TechCorp",
                role="Developer",
                start_date="2020",
                end_date="2022",
                technologies_used=["py"]  # py -> Python
            )]
        )
        profile = self.extractor.extract_skills_profile(resume)
        
        # Python should appear once, merging "Explicit Skills" and "Work Experience" sources
        matching = [s for s in profile.skills if s.name == "Python"]
        self.assertEqual(len(matching), 1)
        # Should sum frequency (1 from list, 1 from experience)
        self.assertEqual(matching[0].frequency, 2)
        # Strongest source: Explicit Skills (0.95) + boost for frequency (0.05) -> 1.00
        self.assertEqual(matching[0].confidence_score, 1.0)
        self.assertEqual(len(matching[0].evidence), 2)

    def test_mixed_technologies_extraction(self) -> None:
        """Verifies extracting from Education, Projects, Certifications, and Publications."""
        resume = Resume(
            personal_info=PersonalInformation(full_name="Dev"),
            education=[EducationEntry(
                institution="Stanford",
                degree="B.S.",
                branch="CS",
                description="Studied statistics and machine learning"
            )],
            projects=[ProjectEntry(
                name="Deep Search",
                description="Built a search engine with pytorch and pinecone"
            )],
            certifications=[CertificationEntry(
                certification_name="AWS Certified Developer",
                organization="Amazon"
            )],
            publications=[Publication(
                title="Paper on LangChain Agents",
                publisher="IEEE"
            )]
        )
        profile = self.extractor.extract_skills_profile(resume)
        skill_names = [s.name for s in profile.skills]
        
        # Extracted from text scanning
        self.assertIn("Machine Learning", skill_names)
        self.assertIn("PyTorch", skill_names)
        self.assertIn("Pinecone", skill_names)
        self.assertIn("AWS", skill_names)
        self.assertIn("LangChain", skill_names)

    def test_missing_skills_empty_inputs(self) -> None:
        """Verifies defaults are clean when no skills are present."""
        resume = Resume(personal_info=PersonalInformation(full_name="Empty Candidate"))
        profile = self.extractor.extract_skills_profile(resume)
        self.assertEqual(profile.skills, [])

    def test_invalid_input(self) -> None:
        """Verifies robust handling when fields contain null/invalid parameters."""
        resume = Resume(
            personal_info=PersonalInformation(full_name="Invalid Candidate"),
            skills=[Skill(name="", category="")],
            education=[EducationEntry(institution=None, degree=None)]
        )
        profile = self.extractor.extract_skills_profile(resume)
        self.assertEqual(profile.skills, [])
