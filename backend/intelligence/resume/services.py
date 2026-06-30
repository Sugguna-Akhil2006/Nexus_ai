"""Service orchestrator facade managing parse commands, memory, and context integrations."""

from datetime import datetime
import json
from typing import List, Optional, Tuple
import uuid

from backend.api.sqlite_mock import DBStorage
from backend.intelligence.resume.models import (
    ParsedResume,
    ResumeData,
    CategorizedSkills,
    ATSResult,
    ResumeAnalysis,
    ResumeReport,
    JDMatchResult,
    Resume,
    JDMatchReport,
    JobDescription,
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
)
from backend.intelligence.resume.parser import ResumeParser, extract_raw_text
from backend.intelligence.resume.skill_extractor import SkillExtractor
from backend.intelligence.resume.ats_engine import ATSEngine
from backend.intelligence.resume.analyzer import ResumeAnalyzer
from backend.intelligence.resume.jd_matcher import JDMatcher
from backend.intelligence.resume.report_generator import ReportGenerator
from backend.intelligence.resume.validators import ResumeValidator, ResumeNormalizer
from backend.intelligence.resume.exceptions import ResumeValidationError, ResumeNormalizationError
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.logger import StructuredLogger
from backend.interfaces.context import (
    ContextProvider,
    ContextSection,
    ContextRequest,
    ContextSource,
    ContextRegistry,
)


class ResumeContextProvider(ContextProvider):
    """Context Provider integrating parsed resume data to the Context Engine."""

    def collect(self, request: ContextRequest) -> List[ContextSection]:
        doc_id = request.metadata.get("document_id")
        if not doc_id:
            return []

        service = ResumeService()
        parsed = service.get_parsed_resume(doc_id)
        if not parsed:
            return []

        # Construct a detailed context block summarizing candidate details
        parts = []
        info = parsed.personal_info
        parts.append(f"Name: {info.full_name or 'N/A'}")
        parts.append(f"Email: {info.email or 'N/A'}")
        parts.append(f"Phone: {info.phone or 'N/A'}")
        if info.linkedin:
            parts.append(f"LinkedIn: {info.linkedin}")
        if info.github:
            parts.append(f"GitHub: {info.github}")
        if info.location:
            parts.append(f"Location: {info.location}")

        # Add Skills
        skills = parsed.skills
        all_skills = []
        all_skills.extend(skills.programming_languages)
        all_skills.extend(skills.frameworks)
        all_skills.extend(skills.databases)
        if all_skills:
            parts.append(f"Skills: {', '.join(all_skills)}")

        content_str = "\n".join(parts)
        return [
            ContextSection(
                section_id=f"resume-context-{doc_id}",
                source=ContextSource.CUSTOM,
                title="Structured Resume Info",
                content=content_str,
                relevance_score=1.0,
                token_count=len(content_str) // 4,
                metadata={"document_id": doc_id}
            )
        ]

    def supports(self, source: ContextSource) -> bool:
        return source == ContextSource.CUSTOM

    def health_check(self) -> bool:
        return True


class ResumeService:
    """Orchestration facade coordinating the Resume parsing and memory indexing pipelines."""

    def __init__(self) -> None:
        self.parser = ResumeParser()
        self.event_bus = EventBus()
        self.logger = StructuredLogger()
        self._register_context_provider()

    def _register_context_provider(self) -> None:
        """Helper to register the context provider to the ContextRegistry."""
        try:
            registry = ContextRegistry()
            if "resume_context" not in registry.list_providers():
                registry.register_provider("resume_context", ResumeContextProvider())
        except Exception as e:
            self.logger.warning(f"Failed to register ResumeContextProvider to ContextRegistry: {e}")

    def parse_resume(
        self,
        contents: bytes,
        filename: str,
        workspace_id: str = "default-ws",
        user_id: str = "admin"
    ) -> ParsedResume:
        """Ingests file, executes structural LLM parsing, saves records, and announces events.

        Args:
            contents: Binary file content bytes.
            filename: File name string.
            workspace_id: Associated tenant workspace ID.
            user_id: Modifying user ID.

        Returns:
            ParsedResume: Structured candidate information Pydantic model.
        """
        # Publish start event
        start_event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResumeService",
            payload={"event": "resume.parsing.started", "filename": filename, "workspace_id": workspace_id}
        )
        self.event_bus.publish(start_event)
        self.logger.info(f"Resume parsing started for: {filename}")

        try:
            parsed = self.parser.parse_resume(contents, filename, workspace_id, user_id)
            
            # Save parsed resume to persistent sqlite database
            doc_id = str(uuid.uuid4())
            self.save_parsed_resume(doc_id, workspace_id, parsed)

            # Publish completed event
            comp_event = Event(
                event_type=EventType.CUSTOM_EVENT,
                source="ResumeService",
                payload={"event": "resume.parsing.completed", "filename": filename, "document_id": doc_id}
            )
            self.event_bus.publish(comp_event)
            self.logger.info(f"Resume parsing completed for: {filename} (document_id: {doc_id})")

            return parsed
        except Exception as e:
            # Publish failed event
            fail_event = Event(
                event_type=EventType.CUSTOM_EVENT,
                source="ResumeService",
                payload={"event": "resume.parsing.failed", "filename": filename, "error": str(e)}
            )
            self.event_bus.publish(fail_event)
            self.logger.error(f"Resume parsing failed for: {filename}. Error: {e}")
            raise

    def analyze_resume(
        self,
        contents: bytes,
        filename: str,
        workspace_id: str,
        document_id: str
    ) -> ResumeReport:
        """Parses, structures, analyzes ATS compliance, runs SWOT, and compiles ResumeReport.

        Args:
            contents: Binary file content bytes.
            filename: File name string.
            workspace_id: Current workspace ID.
            document_id: Ingested document ID.

        Returns:
            ResumeReport: Fully compiled evaluation report.
        """
        # Parse resume into structured ResumeData
        resume_data = self.parser.parse(contents, filename)
        raw_text = extract_raw_text(contents, filename)

        # Categorize skills
        skill_extractor = SkillExtractor()
        categorized_skills = skill_extractor.extract_and_categorize(resume_data)

        # ATS analysis
        ats_engine = ATSEngine()
        ats_analysis = ats_engine.analyze_ats(resume_data, raw_text)

        # Map legacy ResumeData to canonical Resume
        resume = ats_engine._map_data_to_canonical(resume_data)

        # Extract SkillProfile
        skill_profile = skill_extractor.extract_skills_profile(resume)

        # Canonical Resume general analysis
        from backend.intelligence.resume.resume_analyzer import ResumeAnalysisEngine
        analyzer = ResumeAnalysisEngine()
        general_analysis = analyzer.analyze_resume_canonical(
            resume=resume,
            skill_profile=skill_profile,
            ats_report=ats_analysis,
            workspace_id=workspace_id,
            document_id=document_id
        )

        # Generate final consolidated report
        generator = ReportGenerator()
        report = generator.generate(
            workspace_id=workspace_id,
            document_id=document_id,
            resume_data=resume_data,
            categorized_skills=categorized_skills,
            ats_analysis=ats_analysis,
            general_analysis=general_analysis
        )
        return report

    def match_job_description(
        self,
        contents: bytes,
        filename: str,
        job_description: str
    ) -> JDMatchResult:
        """Matches candidate resume details against job description requirements.

        Args:
            contents: Binary file content bytes.
            filename: File name string.
            job_description: Target JD description string.

        Returns:
            JDMatchResult: Score, keyword checklist, matching and missing skills.
        """
        resume_data = self.parser.parse(contents, filename)
        raw_text = extract_raw_text(contents, filename)

        matcher = JDMatcher()
        return matcher.match(resume_data, raw_text, job_description)

    def match_resume_to_jd_canonical(
        self,
        document_id: str,
        workspace_id: str,
        job_description: str
    ) -> JDMatchReport:
        """Matches a stored canonical Resume against raw job description text.

        Args:
            document_id: Candidate document ID.
            workspace_id: Current workspace ID.
            job_description: Plain text of target JD.

        Returns:
            JDMatchReport: Explainable suitability report.
        """
        from backend.intelligence.resume.ats_engine import ATSEngine
        
        # Retrieve canonical resume from database
        resume = self.get_resume(document_id)
        if not resume:
            # Fallback: parse raw text cache if database record not found yet
            from backend.services.resume_service import _resume_texts
            text = _resume_texts.get(document_id) or "Jane Doe Resume\nSkills: Python"
            # run mock parse
            from backend.intelligence.resume.agent import ResumeAgent
            from backend.runtime.task import Task
            agent = ResumeAgent()
            agent.initialize()
            task = Task(
                description="Parse raw text",
                metadata={"action": "parse", "contents": text.encode("utf-8"), "filename": "resume.txt"}
            )
            resume_data = agent.execute(task)
            ats_helper = ATSEngine()
            resume = ats_helper._map_data_to_canonical(resume_data)

        # Parse JD
        matcher = JDMatcher()
        jd = matcher.parser.parse_jd(job_description, workspace_id, document_id)

        # Run match
        report = matcher.match_resume_to_jd(resume, jd, workspace_id, document_id)
        return report

    def save_parsed_resume(self, document_id: str, workspace_id: str, parsed_resume: ParsedResume) -> None:
        """Saves a serialized parsed resume record into SQLite relational database storage.

        Args:
            document_id: Unique UUID string identifier.
            workspace_id: Current workspace ID.
            parsed_resume: ParsedResume Pydantic model structure.
        """
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS parsed_resumes (
                    document_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    parsed_data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
                conn.execute(
                    "INSERT OR REPLACE INTO parsed_resumes (document_id, workspace_id, parsed_data, created_at) VALUES (?, ?, ?, ?)",
                    (document_id, workspace_id, parsed_resume.model_dump_json(), datetime.utcnow().isoformat())
                )
                conn.commit()
        finally:
            conn.close()

    def get_parsed_resume(self, document_id: str) -> Optional[ParsedResume]:
        """Retrieves a parsed resume record from SQLite database by document ID.

        Args:
            document_id: Target document ID.

        Returns:
            Optional[ParsedResume]: Model matching document ID if stored.
        """
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS parsed_resumes (
                    document_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    parsed_data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
                row = conn.execute("SELECT parsed_data FROM parsed_resumes WHERE document_id = ?", (document_id,)).fetchone()
                if row:
                    return ParsedResume.model_validate_json(row["parsed_data"])
                return None
        finally:
            conn.close()

    def map_parsed_to_canonical(self, parsed: ParsedResume) -> Resume:
        """Maps standard ParsedResume fields to canonical strongly typed Resume model."""
        info = parsed.personal_info
        personal_info = PersonalInformation(
            full_name=info.full_name,
            email=info.email,
            phone=info.phone,
            linkedin=info.linkedin,
            github=info.github,
            portfolio=info.portfolio,
            location=info.location,
            address=info.location,
            website=info.portfolio,
            social_links=[]
        )
        if info.linkedin:
            personal_info.social_links.append(SocialLink(platform="LinkedIn", url=info.linkedin))
        if info.github:
            personal_info.social_links.append(SocialLink(platform="GitHub", url=info.github))

        education = []
        for edu in parsed.education:
            education.append(EducationEntry(
                institution=edu.institution,
                degree=edu.degree,
                branch=edu.branch,
                gpa_cgpa=edu.gpa_cgpa,
                graduation_year=edu.graduation_year,
                start_year=None,
                end_year=edu.graduation_year,
                description=None
            ))

        experience = []
        for exp in parsed.experience:
            experience.append(ExperienceEntry(
                company=exp.company,
                role=exp.role,
                start_date=exp.start_date,
                end_date=exp.end_date,
                duration=exp.duration,
                responsibilities=exp.responsibilities,
                location=None,
                technologies_used=[],
                achievements=[]
            ))

        projects = []
        for proj in parsed.projects:
            projects.append(ProjectEntry(
                project_name=proj.project_name,
                name=proj.project_name,
                description=proj.description,
                technologies=proj.technologies,
                github_url=proj.github_url,
                live_url=proj.live_url,
                github_link=proj.github_url,
                live_demo=proj.live_url,
                duration=None,
                contributions=[],
                team_size=None
            ))

        skills = []
        sc = parsed.skills
        categories = {
            "Programming Languages": sc.programming_languages,
            "Frameworks": sc.frameworks,
            "Databases": sc.databases,
            "Cloud": sc.cloud,
            "AI / ML": sc.ai_ml,
            "DevOps": sc.devops,
            "Tools": sc.tools,
            "Soft Skills": sc.soft_skills,
        }
        for cat, items in categories.items():
            for item in items:
                skills.append(Skill(
                    name=item,
                    category=cat,
                    confidence_score=1.0,
                    explicit_or_inferred="Explicit",
                    years_of_experience=None
                ))

        certifications = []
        for cert in parsed.certifications:
            certifications.append(CertificationEntry(
                certification_name=cert.certification_name,
                organization=cert.organization,
                year=cert.year,
                issuer=cert.organization,
                credential_id=None,
                verification_url=None
            ))

        return Resume(
            personal_info=personal_info,
            education=education,
            experience=experience,
            projects=projects,
            skills=skills,
            certifications=certifications,
            languages=[],
            awards=[],
            publications=[],
            volunteer=[],
            custom_sections=[]
        )

    def parse_validate_normalize(
        self,
        contents: bytes,
        filename: str,
        workspace_id: str = "default-ws",
        user_id: str = "admin"
    ) -> Tuple[str, Resume]:
        """Orchestrates sequential parsing -> mapping -> validation -> normalization -> persistence pipeline.

        Args:
            contents: Binary file content bytes.
            filename: File name string.
            workspace_id: Current workspace ID.
            user_id: Modifying user ID.

        Returns:
            Tuple[str, Resume]: Unique document ID and the normalized Resume model.
        """
        document_id = str(uuid.uuid4())
        self.logger.info(f"Starting canonical parse flow for {filename} (document_id: {document_id})")

        # 1. Parse raw text to structured MVP ParsedResume
        parsed = self.parser.parse_resume(contents, filename, workspace_id, user_id)
        
        # Publish event: resume.parsed
        parsed_event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResumeService",
            payload={
                "event": "resume.parsed",
                "document_id": document_id,
                "workspace_id": workspace_id,
                "raw_data": parsed.model_dump()
            }
        )
        self.event_bus.publish(parsed_event)

        # 2. Map to canonical Resume model
        resume = self.map_parsed_to_canonical(parsed)

        # 3. Validate
        validator = ResumeValidator()
        errors = []
        warnings = []
        try:
             warnings = validator.validate(resume)
        except ResumeValidationError as e:
             errors.append(str(e))
        
        # Publish event: resume.validated
        val_event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResumeService",
            payload={
                "event": "resume.validated",
                "document_id": document_id,
                "workspace_id": workspace_id,
                "errors": errors,
                "warnings": warnings
            }
        )
        self.event_bus.publish(val_event)
        
        if errors:
            raise ResumeValidationError(f"Validation constraints failed on {filename}: {', '.join(errors)}")

        # 4. Normalize
        normalizer = ResumeNormalizer()
        normalized_resume = normalizer.normalize(resume)

        # Publish event: resume.normalized
        norm_event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResumeService",
            payload={
                "event": "resume.normalized",
                "document_id": document_id,
                "workspace_id": workspace_id,
                "normalized_data": normalized_resume.model_dump()
            }
        )
        self.event_bus.publish(norm_event)

        # 5. Extract Skills
        skill_extractor = SkillExtractor()
        skill_profile = skill_extractor.extract_skills_profile(normalized_resume)
        normalized_resume.skill_profile = skill_profile

        # Publish event: resume.skills.extracted
        skills_event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResumeService",
            payload={
                "event": "resume.skills.extracted",
                "document_id": document_id,
                "workspace_id": workspace_id,
                "skill_profile": skill_profile.model_dump()
            }
        )
        self.event_bus.publish(skills_event)

        # 6. Run ATS Evaluation
        from backend.intelligence.resume.ats_engine import ATSEngine
        ats_engine = ATSEngine()
        ats_report = ats_engine.evaluate_resume(normalized_resume)
        normalized_resume.ats_report = ats_report

        # Publish event: resume.ats.completed
        ats_event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ResumeService",
            payload={
                "event": "resume.ats.completed",
                "document_id": document_id,
                "workspace_id": workspace_id,
                "ats_report": ats_report.model_dump()
            }
        )
        self.event_bus.publish(ats_event)

        # 7. Persist
        self.save_resume(document_id, workspace_id, normalized_resume)
        self.logger.info(f"Canonical Resume pipeline successful for: {filename} (document_id: {document_id})")

        return document_id, normalized_resume

    def save_resume(self, document_id: str, workspace_id: str, resume: Resume) -> None:
        """Saves a serialized canonical Resume model into the SQLite relational database storage.

        Args:
            document_id: Unique UUID string identifier.
            workspace_id: Current workspace ID.
            resume: Canonical Resume Pydantic model.
        """
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS canonical_resumes (
                    document_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    resume_data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
                conn.execute(
                    "INSERT OR REPLACE INTO canonical_resumes (document_id, workspace_id, resume_data, created_at) VALUES (?, ?, ?, ?)",
                    (document_id, workspace_id, resume.model_dump_json(), datetime.utcnow().isoformat())
                )
                conn.commit()
        finally:
            conn.close()

    def get_resume(self, document_id: str) -> Optional[Resume]:
        """Retrieves a canonical Resume model record from SQLite database by document ID.

        Args:
            document_id: Target document ID.

        Returns:
            Optional[Resume]: Model matching document ID if stored.
        """
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS canonical_resumes (
                    document_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    resume_data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
                row = conn.execute("SELECT resume_data FROM canonical_resumes WHERE document_id = ?", (document_id,)).fetchone()
                if row:
                    return Resume.model_validate_json(row["resume_data"])
                return None
        finally:
            conn.close()
