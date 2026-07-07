"""Core Pydantic data schemas for the Career Intelligence Engine."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SkillLevel(str, Enum):
    """Proficiency level descriptors for a skill."""
    NONE = "NONE"
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class RecommendationType(str, Enum):
    """Category of a career recommendation."""
    PROJECT = "PROJECT"
    LEARNING = "LEARNING"
    CERTIFICATION = "CERTIFICATION"


class CareerLevel(str, Enum):
    """Broad career stage classification."""
    STUDENT = "STUDENT"
    JUNIOR = "JUNIOR"
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    PRINCIPAL = "PRINCIPAL"


# ---------------------------------------------------------------------------
# Profile & input
# ---------------------------------------------------------------------------

class CareerProfile(BaseModel):
    """Aggregated professional profile derived from resume, GitHub, and documents."""
    profile_id: str = Field(default_factory=lambda: f"cp-{uuid.uuid4().hex[:8]}")
    workspace_id: str = ""
    name: str = ""
    current_role: str = ""
    years_experience: float = 0.0
    skills: List[str] = Field(default_factory=list)
    github_languages: List[str] = Field(default_factory=list)
    github_projects: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    document_topics: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CareerAnalysisRequest(BaseModel):
    """Input payload for a career analysis request."""
    workspace_id: str
    profile: CareerProfile
    target_role: str = ""
    target_skills: List[str] = Field(default_factory=list)
    job_description: str = ""


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------

class SkillGap(BaseModel):
    """A single identified skill gap between current and target profile."""
    skill: str
    current_level: SkillLevel = SkillLevel.NONE
    target_level: SkillLevel = SkillLevel.INTERMEDIATE
    priority: int = 1  # 1 = highest priority
    rationale: str = ""


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

class CareerRoadmapStep(BaseModel):
    """A single step in a personalized career development roadmap."""
    step_number: int
    skill: str
    action: str
    resources: List[str] = Field(default_factory=list)
    estimated_weeks: int = 4
    expected_outcome: str = ""


class CareerRoadmap(BaseModel):
    """Ordered collection of development steps forming a career roadmap."""
    roadmap_id: str = Field(default_factory=lambda: f"rm-{uuid.uuid4().hex[:8]}")
    profile_id: str = ""
    target_role: str = ""
    steps: List[CareerRoadmapStep] = Field(default_factory=list)
    total_estimated_weeks: int = 0
    summary: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Job matching
# ---------------------------------------------------------------------------

class JobMatchResult(BaseModel):
    """Result of comparing a career profile against a job description."""
    match_id: str = Field(default_factory=lambda: f"jm-{uuid.uuid4().hex[:8]}")
    profile_id: str = ""
    job_title: str = ""
    skill_match_pct: float = 0.0
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    resume_improvements: List[str] = Field(default_factory=list)
    github_improvements: List[str] = Field(default_factory=list)
    recommended_projects: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

class CareerRecommendation(BaseModel):
    """A single actionable career development recommendation."""
    rec_id: str = Field(default_factory=lambda: f"rec-{uuid.uuid4().hex[:8]}")
    rec_type: RecommendationType
    title: str
    rationale: str = ""
    priority: int = 1
    estimated_hours: int = 0


# ---------------------------------------------------------------------------
# Full career report
# ---------------------------------------------------------------------------

class CareerReport(BaseModel):
    """Comprehensive career intelligence report produced for a single analysis."""
    report_id: str = Field(default_factory=lambda: f"rpt-{uuid.uuid4().hex[:8]}")
    workspace_id: str = ""
    profile_id: str = ""
    career_level: CareerLevel = CareerLevel.JUNIOR
    executive_summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    skill_gaps: List[SkillGap] = Field(default_factory=list)
    roadmap: Optional[CareerRoadmap] = None
    recommendations: List[CareerRecommendation] = Field(default_factory=list)
    job_match: Optional[JobMatchResult] = None
    career_timeline: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
