"""Flagship ResumeAgent orchestrating parsing, ATS scoring, matching, and general analysis."""

from typing import Any, List, Optional, Union
import uuid

from backend.runtime.base import BaseAgent
from backend.runtime.task import Task
from backend.runtime.exceptions import TaskValidationError
from backend.intelligence.resume.exceptions import ResumeIntelligenceError
from backend.intelligence.resume.models import (
    Resume,
    ResumeData,
    JobDescription,
    UnifiedResumeReport,
    ContactInfo,
    EducationInfo,
    WorkExperience,
    ProjectInfo,
    CertificationInfo
)
from backend.intelligence.resume.context import WorkflowContext
from backend.intelligence.resume.coordinator import WorkflowCoordinator


class ResumeAgent(BaseAgent):
    """Flagship Resume Intelligence Agent coordinating candidate profile analysis."""

    def __init__(
        self,
        name: str = "ResumeAgent",
        description: str = "Evaluates candidate resumes, structures skills taxonomies, scores ATS compliance, and matches JDs.",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ) -> None:
        caps = capabilities or ["RESUME_PARSING", "ATS_ANALYSIS", "SKILL_EXTRACTION", "JD_MATCHING"]
        super().__init__(name=name, description=description, version=version, capabilities=caps)
        self.coordinator = WorkflowCoordinator()

    def validate_task(self, task: Task) -> None:
        """Validates incoming tasks.

        Args:
            task: Task to run.

        Raises:
            TaskValidationError: If validation fails.
        """
        super().validate_task(task)
        if not task.metadata or "action" not in task.metadata:
            raise TaskValidationError("Task metadata must contain an 'action' field.")

        action = task.metadata["action"]
        if action not in ["parse", "analyze", "match_jd"]:
            raise TaskValidationError(f"Unsupported action: '{action}'.")

        # Parameter validation
        if action == "parse":
            if "contents" not in task.metadata or "filename" not in task.metadata:
                raise TaskValidationError("Parsing requires 'contents' (bytes) and 'filename' (str).")
        elif action == "analyze":
            if any(k not in task.metadata for k in ["contents", "filename", "workspace_id", "document_id"]):
                raise TaskValidationError("Analysis requires 'contents', 'filename', 'workspace_id', and 'document_id'.")
        elif action == "match_jd":
            if any(k not in task.metadata for k in ["contents", "filename", "job_description"]):
                raise TaskValidationError("JD Matching requires 'contents', 'filename', and 'job_description'.")

    def execute(self, task: Task) -> Any:
        """Executes targeted resume actions inside the pipeline (backwards compatible).

        Args:
            task: Task to run.

        Returns:
            Any: Structured result of parsing, matching, or analysis.

        Raises:
            ResumeIntelligenceError: On execution failures.
        """
        self.validate_task(task)
        action = task.metadata["action"]
        
        try:
            if action == "parse":
                from backend.intelligence.resume.parser import ResumeParser
                parser = ResumeParser()
                return parser.parse(
                    contents=task.metadata["contents"],
                    filename=task.metadata["filename"]
                )
            elif action == "analyze":
                report = self.analyze_resume(
                    resume=task.metadata["contents"],
                    workspace_id=task.metadata["workspace_id"],
                    document_id=task.metadata["document_id"],
                    filename=task.metadata["filename"]
                )
                return report
            elif action == "match_jd":
                from backend.intelligence.resume.jd_matcher import JDMatcher
                from backend.intelligence.resume.ats_engine import ATSEngine
                
                # Run matching using legacy method
                parser = ResumeParser()
                resume_data = parser.parse(task.metadata["contents"], task.metadata["filename"])
                raw_text = task.metadata["contents"].decode("utf-8", errors="ignore")
                
                matcher = JDMatcher()
                return matcher.match(
                    resume_data=resume_data,
                    raw_text=raw_text,
                    job_description=task.metadata["job_description"]
                )
        except Exception as e:
            if isinstance(e, ResumeIntelligenceError):
                raise
            raise ResumeIntelligenceError(f"ResumeAgent failed to execute action '{action}': {e}") from e

    def analyze_resume(
        self,
        resume: Union[Resume, bytes, ResumeData],
        job_description: Optional[Union[str, JobDescription]] = None,
        workspace_id: str = "default-ws",
        document_id: Optional[str] = None,
        filename: str = "resume.txt"
    ) -> UnifiedResumeReport:
        """Orchestrates structured resume analysis pipeline, retries, and events.

        Args:
            resume: Raw file contents (bytes), parsed legacy ResumeData, or canonical Resume model.
            job_description: Optional job description plaintext or structured model.
            workspace_id: Associated workspace ID.
            document_id: Associated candidate document ID.
            filename: Uploaded file name string.

        Returns:
            UnifiedResumeReport: Consolidated suitabilities and analysis.

        Raises:
            ResumeIntelligenceError: If processing fails.
        """
        try:
            doc_id = document_id or f"doc-{str(uuid.uuid4())[:8]}"
            context = WorkflowContext(
                workspace_id=workspace_id,
                document_id=doc_id,
                filename=filename
            )

            # Map raw resume input
            if isinstance(resume, bytes):
                context.contents = resume
            elif isinstance(resume, ResumeData):
                context.parsed_resume_data = resume
                # Map to canonical
                from backend.intelligence.resume.ats_engine import ATSEngine
                ats = ATSEngine()
                context.canonical_resume = ats._map_data_to_canonical(resume)
                
                # Mock contents representation
                context.contents = f"Name: {resume.contact_info.name or 'Candidate'}\nSkills: {', '.join(resume.skills)}".encode("utf-8")
            elif isinstance(resume, Resume):
                context.canonical_resume = resume
                context.parsed_resume_data = self._map_canonical_to_legacy(resume)
                
                # Mock contents representation
                skills_str = ", ".join(s.name for s in resume.skills if s.name)
                context.contents = f"Name: {resume.personal_info.full_name or 'Candidate'}\nSkills: {skills_str}".encode("utf-8")

            # Map job description input
            if job_description:
                if isinstance(job_description, str):
                    context.raw_job_description = job_description
                elif isinstance(job_description, JobDescription):
                    context.job_description = job_description
                    context.raw_job_description = f"Title: {job_description.job_title}\nRequired: {', '.join(job_description.required_skills)}"

            # Run coordinator execution
            self.coordinator.coordinate_execution(context)

            if not context.final_report:
                raise ResumeIntelligenceError("Consolidation stage failed to produce the final report.")

            return context.final_report
        except Exception as e:
            if isinstance(e, ResumeIntelligenceError):
                raise
            raise ResumeIntelligenceError(f"Failed to orchestrate resume analysis: {e}") from e

    def _map_canonical_to_legacy(self, resume: Resume) -> ResumeData:
        """Converts canonical Resume model back to legacy ResumeData format."""
        info = resume.personal_info
        contact = ContactInfo(
            name=info.full_name,
            email=info.email,
            phone=info.phone
        )
        
        education = []
        for edu in resume.education:
            education.append(EducationInfo(
                institution=edu.institution,
                degree=edu.degree,
                field_of_study=edu.branch
            ))
            
        experience = []
        for exp in resume.experience:
            experience.append(WorkExperience(
                company=exp.company,
                role=exp.role,
                start_date=exp.start_date,
                end_date=exp.end_date
            ))
            
        projects = []
        for proj in resume.projects:
            projects.append(ProjectInfo(
                project_name=proj.project_name or proj.name,
                description=proj.description,
                technologies=proj.technologies
            ))
            
        skills = [s.name for s in resume.skills if s.name]

        return ResumeData(
            contact_info=contact,
            education=education,
            experience=experience,
            projects=projects,
            skills=skills
        )
