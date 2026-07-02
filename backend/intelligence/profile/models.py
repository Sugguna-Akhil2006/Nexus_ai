"""Pydantic schemas for the Unified Knowledge Profile."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProfileSource(BaseModel):
    """Source attribution for a profile field."""
    source_name: str  # "Resume", "GitHub", "Meeting", etc.
    confidence_score: float = 1.0
    extracted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    evidence: Optional[str] = None


class ProfilePersonalInfo(BaseModel):
    """Personal contact information in the profile."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    source_attribution: Dict[str, ProfileSource] = Field(default_factory=dict)


class ProfileSkill(BaseModel):
    """Deduplicated skill with source tracking and confidence scoring."""
    name: str
    category: Optional[str] = None
    confidence_score: float = 1.0
    sources: List[str] = Field(default_factory=list)  # list of source names
    evidence: List[str] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TimelineEvent(BaseModel):
    """Chronological event representation for education, employment, certifications, and research."""
    title: str
    event_type: str  # "Education", "Experience", "Project", "Certification", "Research"
    organization: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    sources: List[str] = Field(default_factory=list)


class ProfileProject(BaseModel):
    """Structured project entry in the profile."""
    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    sources: List[str] = Field(default_factory=list)


class ProfileExperience(BaseModel):
    """Structured work experience entry in the profile."""
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class ProfileEducation(BaseModel):
    """Structured educational background entry in the profile."""
    institution: str
    degree: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[str] = None
    sources: List[str] = Field(default_factory=list)


class KnowledgeProfile(BaseModel):
    """Canonical single source of truth for user professional identity."""
    workspace_id: str
    user_id: str
    personal_info: ProfilePersonalInfo = Field(default_factory=ProfilePersonalInfo)
    skills: Dict[str, ProfileSkill] = Field(default_factory=dict)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    projects: List[ProfileProject] = Field(default_factory=list)
    experience: List[ProfileExperience] = Field(default_factory=list)
    education: List[ProfileEducation] = Field(default_factory=list)
    
    # Platform contributions
    repositories: List[Dict[str, Any]] = Field(default_factory=list)
    publications: List[Dict[str, Any]] = Field(default_factory=list)
    research_interests: List[str] = Field(default_factory=list)
    
    # Skill relations
    knowledge_graph: Dict[str, List[str]] = Field(default_factory=dict)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
