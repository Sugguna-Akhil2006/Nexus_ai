"""Data models representing the structured parsed resume outputs."""

from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field


# =====================================================================
# Backwards-Compatibility MVP Models
# =====================================================================

class ContactInfo(BaseModel):
    """MVP ContactInfo model."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    links: List[str] = Field(default_factory=list)


class EducationInfo(BaseModel):
    """MVP EducationInfo model."""
    degree: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[float] = None


class WorkExperience(BaseModel):
    """MVP WorkExperience model."""
    job_title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)


class ProjectInfo(BaseModel):
    """MVP ProjectInfo model."""
    name: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    links: List[str] = Field(default_factory=list)


class CertificationInfo(BaseModel):
    """MVP CertificationInfo model."""
    name: Optional[str] = None
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None


class ResumeData(BaseModel):
    """MVP ResumeData model."""
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    education: List[EducationInfo] = Field(default_factory=list)
    experience: List[WorkExperience] = Field(default_factory=list)
    projects: List[ProjectInfo] = Field(default_factory=list)
    certifications: List[CertificationInfo] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)


class CategorizedSkills(BaseModel):
    """MVP CategorizedSkills model."""
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud: List[str] = Field(default_factory=list)
    devops: List[str] = Field(default_factory=list)
    ai_ml: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    explicit_skills: List[str] = Field(default_factory=list)
    inferred_skills: List[str] = Field(default_factory=list)


class ATSResult(BaseModel):
    """MVP ATSResult model."""
    score: float = 0.0
    completeness_score: float = 0.0
    formatting_score: float = 0.0
    keyword_density_score: float = 0.0
    verb_metric_score: float = 0.0
    quantification_score: float = 0.0
    missing_keywords: List[str] = Field(default_factory=list)
    action_verbs_found: List[str] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)
    readability_level: str = "Standard"


class JDMatchResult(BaseModel):
    """MVP JDMatchResult model."""
    match_percentage: float = 0.0
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    gap_analysis: str = ""
    recommendations: List[str] = Field(default_factory=list)
    section_specific_feedback: Dict[str, str] = Field(default_factory=dict)


class ResumeAnalysis(BaseModel):
    """MVP ResumeAnalysis model."""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    career_readiness: str = "Mid-level Engineer"
    interview_preparation_tips: List[str] = Field(default_factory=list)


class ResumeReport(BaseModel):
    """MVP ResumeReport model."""
    report_id: str
    workspace_id: str
    document_id: str
    resume_data: ResumeData
    categorized_skills: CategorizedSkills
    ats_analysis: ATSResult
    general_analysis: Union[ResumeAnalysis, "ResumeAnalysisReport"]
    created_at: str


# =====================================================================
# Prompt 43 New Structured Models
# =====================================================================

class SocialLink(BaseModel):
    """Platform and link URL representation."""
    platform: str
    url: str


class PersonalInformation(BaseModel):
    """Personal and contact details extracted from the resume."""
    full_name: Optional[str] = Field(None, description="Candidate's full name")
    email: Optional[str] = Field(None, description="Candidate's email address")
    phone: Optional[str] = Field(None, description="Candidate's contact phone number")
    linkedin: Optional[str] = Field(None, description="Candidate's LinkedIn profile URL")
    github: Optional[str] = Field(None, description="Candidate's GitHub profile URL")
    portfolio: Optional[str] = Field(None, description="Candidate's personal website or portfolio URL")
    location: Optional[str] = Field(None, description="Candidate's physical location or address")
    address: Optional[str] = Field(None, description="Detailed physical mailing address")
    website: Optional[str] = Field(None, description="Personal website/portfolio URL alias")
    social_links: List[SocialLink] = Field(default_factory=list, description="List of social link profiles")


class EducationEntry(BaseModel):
    """Educational qualifications details entry."""
    institution: Optional[str] = Field(None, description="University, college or school name")
    degree: Optional[str] = Field(None, description="Degree name (e.g. B.Tech, M.S., Ph.D.)")
    branch: Optional[str] = Field(None, description="Field of study or branch (e.g. Computer Science)")
    gpa_cgpa: Optional[str] = Field(None, description="GPA or CGPA score")
    graduation_year: Optional[str] = Field(None, description="Graduation year (or expected)")
    start_year: Optional[str] = Field(None, description="Start year of study")
    end_year: Optional[str] = Field(None, description="End year of study")
    description: Optional[str] = Field(None, description="Description of studies or achievements")


class ExperienceEntry(BaseModel):
    """Professional work history experience details entry."""
    company: Optional[str] = Field(None, description="Company or organization name")
    role: Optional[str] = Field(None, description="Role or position title")
    start_date: Optional[str] = Field(None, description="Start date (Month/Year)")
    end_date: Optional[str] = Field(None, description="End date (Month/Year or 'Present')")
    duration: Optional[str] = Field(None, description="Total duration of employment")
    responsibilities: List[str] = Field(default_factory=list, description="Responsibilities and achievements bullet list")
    location: Optional[str] = Field(None, description="Physical location of company")
    technologies_used: List[str] = Field(default_factory=list, description="Technologies used in this role")
    achievements: List[str] = Field(default_factory=list, description="Specific achievements in this role")


class ProjectEntry(BaseModel):
    """Engineering or academic project details entry."""
    project_name: Optional[str] = Field(None, description="Project title name")
    name: Optional[str] = Field(None, description="Canonical project name")
    description: Optional[str] = Field(None, description="Description of project accomplishments")
    technologies: List[str] = Field(default_factory=list, description="Tech stack technologies used")
    github_url: Optional[str] = Field(None, description="Project repository GitHub URL link")
    live_url: Optional[str] = Field(None, description="Project demonstration URL link")
    github_link: Optional[str] = Field(None, description="Social platform GitHub repository link")
    live_demo: Optional[str] = Field(None, description="Live demonstration URL link")
    duration: Optional[str] = Field(None, description="Total project timeframe duration")
    contributions: List[str] = Field(default_factory=list, description="Candidate specific contributions")
    team_size: Optional[int] = Field(None, description="Total engineering team size")


class SkillsCategory(BaseModel):
    """Candidate skills organized into specialized technology categories."""
    programming_languages: List[str] = Field(default_factory=list, description="Languages (e.g., Python, C++, Go)")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks (e.g., FastAPI, React, PyTorch)")
    databases: List[str] = Field(default_factory=list, description="Databases (e.g., PostgreSQL, MongoDB, Redis)")
    cloud: List[str] = Field(default_factory=list, description="Cloud providers (e.g., AWS, GCP, Azure)")
    ai_ml: List[str] = Field(default_factory=list, description="Artificial Intelligence / Machine Learning (e.g., LLMs, PyTorch)")
    devops: List[str] = Field(default_factory=list, description="CI/CD & DevOps tools (e.g., Docker, Kubernetes)")
    tools: List[str] = Field(default_factory=list, description="Development tools & IDEs (e.g., Git, VSCode)")
    soft_skills: List[str] = Field(default_factory=list, description="Interpersonal attributes (e.g., Leadership, Teamwork)")


class CertificationEntry(BaseModel):
    """Professional certification details entry."""
    certification_name: Optional[str] = Field(None, description="Certification title (e.g. AWS Solutions Architect)")
    organization: Optional[str] = Field(None, description="Issuing organization name")
    year: Optional[str] = Field(None, description="Year of issuance")
    issuer: Optional[str] = Field(None, description="Issuing organization name alias")
    credential_id: Optional[str] = Field(None, description="Credential identifier string")
    verification_url: Optional[str] = Field(None, description="Credential verification link URL")


class ParsedResume(BaseModel):
    """Fully parsed structured representation of a resume."""
    personal_info: PersonalInformation = Field(default_factory=PersonalInformation, description="Personal info data")
    education: List[EducationEntry] = Field(default_factory=list, description="Educational background entries list")
    experience: List[ExperienceEntry] = Field(default_factory=list, description="Work experience entries list")
    projects: List[ProjectEntry] = Field(default_factory=list, description="Projects entries list")
    skills: SkillsCategory = Field(default_factory=SkillsCategory, description="Categorized skills list details")
    certifications: List[CertificationEntry] = Field(default_factory=list, description="Certifications entries list")


class Skill(BaseModel):
    """Canonical Skill model with category, confidence, and experience details."""
    name: str
    category: str = "Other"
    confidence_score: float = 1.0
    explicit_or_inferred: str = "Explicit"
    years_of_experience: Optional[float] = None


class Language(BaseModel):
    """Canonical Language entry."""
    name: str
    proficiency: Optional[str] = None


class Award(BaseModel):
    """Canonical Award entry."""
    title: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class Publication(BaseModel):
    """Canonical Publication entry."""
    title: str
    publisher: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None


class VolunteerExperience(BaseModel):
    """Canonical Volunteer Experience entry."""
    organization: str
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class CustomSection(BaseModel):
    """Canonical Custom Section entry."""
    title: str
    content: List[str] = Field(default_factory=list)


class SkillEvidence(BaseModel):
    """Evidence citation for an extracted skill."""
    source: str
    context: str
    evidence_text: str


class ExtractedSkill(BaseModel):
    """Extracted skill with metadata, confidence, and source citations."""
    name: str
    category: str
    confidence_score: float
    explicit_or_inferred: str  # "Explicit" or "Inferred"
    frequency: int
    evidence: List[SkillEvidence] = Field(default_factory=list)


class SkillProfile(BaseModel):
    """Deduplicated profile containing all extracted and inferred skills."""
    skills: List[ExtractedSkill] = Field(default_factory=list)


class ATSCategoryScore(BaseModel):
    """Specific scoring details for an ATS evaluation category."""
    name: str
    weight: float
    max_score: int
    current_score: float
    reason: str
    improvement_suggestions: List[str] = Field(default_factory=list)


class ATSReport(BaseModel):
    """ applicant tracking system compatibility evaluation report structure."""
    overall_score: float
    category_scores: List[ATSCategoryScore] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    priority_improvements: List[str] = Field(default_factory=list)
    detailed_recommendations: List[str] = Field(default_factory=list)


class Resume(BaseModel):
    """Canonical Resume Data Model serving as the single source of truth."""
    personal_info: PersonalInformation = Field(default_factory=PersonalInformation)
    education: List[EducationEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    volunteer: List[VolunteerExperience] = Field(default_factory=list)
    custom_sections: List[CustomSection] = Field(default_factory=list)
    skill_profile: Optional[SkillProfile] = None
    ats_report: Optional[ATSReport] = None


class JobDescription(BaseModel):
    """Canonical Job Description data model."""
    job_title: str
    company: Optional[str] = None
    experience_required: Optional[str] = None
    education_requirements: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    employment_type: Optional[str] = None


class JDCategoryMatch(BaseModel):
    """Specific matching evaluation score details for a category."""
    category_name: str
    score: float
    weight: float
    confidence: float
    matching_evidence: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)


class JDMatchReport(BaseModel):
    """Canonical Job Description Suitability Match Report."""
    overall_score: float
    category_scores: List[JDCategoryMatch] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    matching_skills: List[str] = Field(default_factory=list)
    gap_analysis: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence: float


class AnalysisRecommendation(BaseModel):
    """Structured evidence-based analysis recommendation."""
    priority: str  # Critical, Important, Optional
    description: str
    evidence: str


class CareerReadiness(BaseModel):
    """Calculated career readiness evaluation scoring and improvement checklist."""
    score: float
    confidence: float
    reasoning: str
    improvement_areas: List[str] = Field(default_factory=list)


class ResumeAnalysisReport(BaseModel):
    """Canonical Resume Analysis Report with strengths, weaknesses, readiness and prioritised tasks."""
    report_id: str
    document_id: str
    workspace_id: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommendations: List[AnalysisRecommendation] = Field(default_factory=list)
    career_stage: str
    career_readiness: CareerReadiness
    confidence: float


class UnifiedResumeReport(BaseModel):
    """Consolidated Unified Resume Intelligence Report containing parsing, ATS, matching, and analysis."""
    resume_summary: Optional[Dict[str, Any]] = None
    skills: List[str] = Field(default_factory=list)
    ats_report: Optional[ATSReport] = None
    jd_match_report: Optional[JDMatchReport] = None
    resume_analysis: Optional[ResumeAnalysisReport] = None
    recommendations: List[AnalysisRecommendation] = Field(default_factory=list)
    pipeline_metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_metrics: Dict[str, Any] = Field(default_factory=dict)
