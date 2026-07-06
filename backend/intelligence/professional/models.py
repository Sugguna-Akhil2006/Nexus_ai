"""Core Pydantic data schemas for the Unified Professional Intelligence Engine."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProfessionalTier(str, Enum):
    """Broad professional maturity tier derived from the overall score."""
    EMERGING = "EMERGING"          # 0–20
    DEVELOPING = "DEVELOPING"      # 21–40
    PROFICIENT = "PROFICIENT"      # 41–60
    EXPERT = "EXPERT"              # 61–80
    PRINCIPAL = "PRINCIPAL"        # 81–100


class EvidenceSource(str, Enum):
    """Data source that provides evidence for a skill or project."""
    RESUME = "RESUME"
    GITHUB = "GITHUB"
    DOCUMENT = "DOCUMENT"


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class ProfessionalAnalysisRequest(BaseModel):
    """Input payload for a unified professional analysis."""
    workspace_id: str
    # Raw data strings — parsed by existing intelligence modules upstream
    resume_text: str = ""
    github_username: str = ""
    github_repos: List[str] = Field(default_factory=list)
    github_languages: List[str] = Field(default_factory=list)
    github_projects: List[str] = Field(default_factory=list)
    document_texts: List[str] = Field(default_factory=list)
    document_topics: List[str] = Field(default_factory=list)
    # Structured data (may be pre-populated by Resume / GitHub agents upstream)
    resume_skills: List[str] = Field(default_factory=list)
    resume_years_experience: float = 0.0
    resume_name: str = ""
    resume_current_role: str = ""
    resume_certifications: List[str] = Field(default_factory=list)
    resume_education: List[str] = Field(default_factory=list)
    # Target context
    target_role: str = ""
    target_skills: List[str] = Field(default_factory=list)
    job_description: str = ""


# ---------------------------------------------------------------------------
# Cross-source skill verification
# ---------------------------------------------------------------------------

class SkillEvidence(BaseModel):
    """Verification record for a single claimed skill across data sources."""
    skill: str
    verified: bool = False
    sources: List[EvidenceSource] = Field(default_factory=list)
    confidence: float = 0.0  # 0.0 – 1.0
    discrepancy: str = ""    # non-empty when sources conflict


# ---------------------------------------------------------------------------
# Portfolio analysis
# ---------------------------------------------------------------------------

class PortfolioStrength(BaseModel):
    """Dimension scores representing portfolio completeness and depth."""
    completeness_score: float = 0.0   # 0–100
    project_depth_score: float = 0.0  # 0–100
    documentation_score: float = 0.0  # 0–100
    breadth_score: float = 0.0        # 0–100
    overall_portfolio_score: float = 0.0  # weighted average
    summary: str = ""


# ---------------------------------------------------------------------------
# Professional score
# ---------------------------------------------------------------------------

class ScoreComponents(BaseModel):
    """Individual weighted dimensions of the professional score."""
    resume_quality: float = 0.0       # 0–100
    github_quality: float = 0.0       # 0–100
    project_depth: float = 0.0        # 0–100
    documentation: float = 0.0        # 0–100
    skill_evidence: float = 0.0       # 0–100
    technology_breadth: float = 0.0   # 0–100
    consistency: float = 0.0          # 0–100
    career_readiness: float = 0.0     # 0–100
    confidence_score: float = 0.0     # 0–100


# Default component weights (must sum to 1.0)
DEFAULT_SCORE_WEIGHTS: Dict[str, float] = {
    "resume_quality": 0.20,
    "github_quality": 0.20,
    "project_depth": 0.15,
    "documentation": 0.10,
    "skill_evidence": 0.15,
    "technology_breadth": 0.10,
    "consistency": 0.05,
    "career_readiness": 0.05,
    "confidence_score": 0.00,  # informational only, not in weighted total
}


class ProfessionalScore(BaseModel):
    """Overall professional score and tier classification."""
    score_id: str = Field(default_factory=lambda: f"ps-{uuid.uuid4().hex[:8]}")
    overall: float = 0.0             # 0–100
    tier: ProfessionalTier = ProfessionalTier.EMERGING
    components: ScoreComponents = Field(default_factory=ScoreComponents)
    weights_used: Dict[str, float] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Growth prediction
# ---------------------------------------------------------------------------

class GrowthProjection(BaseModel):
    """Short- and medium-term professional growth estimates."""
    current_level: str = ""
    projection_6m: str = ""
    projection_12m: str = ""
    milestones: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    growth_velocity: str = ""  # "slow" | "moderate" | "fast"


# ---------------------------------------------------------------------------
# Full professional report
# ---------------------------------------------------------------------------

class ProfessionalReport(BaseModel):
    """Comprehensive professional intelligence report."""
    report_id: str = Field(default_factory=lambda: f"pr-{uuid.uuid4().hex[:8]}")
    workspace_id: str = ""
    executive_summary: str = ""
    professional_score: Optional[ProfessionalScore] = None
    verified_skills: List[SkillEvidence] = Field(default_factory=list)
    verified_projects: List[str] = Field(default_factory=list)
    career_readiness: str = ""
    portfolio_analysis: Optional[PortfolioStrength] = None
    growth_prediction: Optional[GrowthProjection] = None
    recommendations: List[Any] = Field(default_factory=list)
    learning_roadmap: str = ""
    evidence_summary: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
