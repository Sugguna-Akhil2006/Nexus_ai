"""Pipeline Context carrying candidate documents and structured analysis payloads."""

from typing import Optional
from pydantic import BaseModel, Field

from backend.intelligence.resume.models import (
    ResumeData,
    Resume,
    SkillProfile,
    ATSReport,
    JobDescription,
    JDMatchReport,
    ResumeAnalysisReport,
    UnifiedResumeReport
)


class WorkflowContext(BaseModel):
    """Execution context containing input arguments and structured intermediate models."""
    workspace_id: str = "default-ws"
    document_id: str = "doc-default"
    filename: str = "resume.txt"
    contents: bytes = b""

    # Intermediate structured data models
    parsed_resume_data: Optional[ResumeData] = None
    canonical_resume: Optional[Resume] = None
    skill_profile: Optional[SkillProfile] = None
    ats_report: Optional[ATSReport] = None

    # Job description match variables
    raw_job_description: Optional[str] = None
    job_description: Optional[JobDescription] = None
    jd_match_report: Optional[JDMatchReport] = None

    # Analysis and consolidated reports
    analysis_report: Optional[ResumeAnalysisReport] = None
    final_report: Optional[UnifiedResumeReport] = None

    class Config:
        arbitrary_types_allowed = True
