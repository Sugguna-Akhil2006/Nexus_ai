"""Pydantic data models for GitHub Repository, Quality, and Activity Intelligence."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# --- Prompt 2: Repository Analysis Models ---

class TechnologyInfo(BaseModel):
    """Details of detected language or framework."""
    name: str
    version: Optional[str] = None
    category: str  # Language, Framework, Database, Queue, DevOps, etc.
    confidence: float


class DependencyNode(BaseModel):
    """A single library package or module import dependency."""
    name: str
    version: Optional[str] = None
    license: Optional[str] = None
    vulnerabilities_count: int = 0
    dependencies: List[str] = Field(default_factory=list)


class ArchitectureStyle(BaseModel):
    """Detected architecture pattern or structure style."""
    name: str
    confidence: float
    evidence: List[str] = Field(default_factory=list)


class DocumentationMetric(BaseModel):
    """Quality and completeness scores of README and guides."""
    has_readme: bool
    has_contributing_guide: bool
    has_changelog: bool
    has_license: bool
    readability_score: float
    freshness_days: int


class RepositoryAnalysisReport(BaseModel):
    """Unified Repository Analysis report containing structures and detectors."""
    report_id: str
    repository_url: str
    branch: str
    detected_technologies: List[TechnologyInfo] = Field(default_factory=list)
    dependencies: Dict[str, DependencyNode] = Field(default_factory=dict)
    architecture: Optional[ArchitectureStyle] = None
    documentation: Optional[DocumentationMetric] = None
    file_count: int = 0
    total_lines: int = 0
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# --- Prompt 3: Code Quality & Architecture Models ---

class QualityImprovement(BaseModel):
    """Specific concrete suggestions for improvements."""
    rule_id: str
    priority: str  # High, Medium, Low
    file_path: str
    line_number: Optional[int] = None
    issue_type: str
    description: str
    suggested_fix: str


class EngineeringAnalysisReport(BaseModel):
    """Report detailing modules design, anti-patterns, and metrics."""
    report_id: str
    maintainability_score: float  # 0 to 100
    complexity_score: float  # 0 to 100
    detected_patterns: List[str] = Field(default_factory=list)
    detected_anti_patterns: List[str] = Field(default_factory=list)
    circular_dependencies: List[List[str]] = Field(default_factory=list)
    improvements: List[QualityImprovement] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# --- Prompt 4: Engineering Activity & Repository Health Models ---

class InactivePeriod(BaseModel):
    """Represents a period of development inactivity."""
    start_date: datetime
    end_date: datetime
    duration_days: int


class BurstActivity(BaseModel):
    """Represents a short burst period of high development velocity."""
    date: datetime
    commit_count: int
    impact_description: str


class ReleaseInfo(BaseModel):
    """Summary representation of a software release."""
    tag_name: str
    published_at: datetime
    commit_count: int
    changelog_summary: Optional[str] = None


class HealthScores(BaseModel):
    """Aggregated health score values."""
    maintenance_score: float  # 0 to 100
    activity_score: float  # 0 to 100
    release_cadence_score: float  # 0 to 100
    issue_resolution_score: float  # 0 to 100
    documentation_freshness_score: float  # 0 to 100
    community_health_score: float  # 0 to 100
    overall_health_score: float  # 0 to 100


class EngineeringInsight(BaseModel):
    """Evidence-based observation of project behavior and health."""
    insight_type: str  # Activity, Maintenance, Collaboration, Quality
    description: str
    evidence: str
    priority: str  # High, Medium, Low


class RecommendationItem(BaseModel):
    """Actionable recommendation suggestion."""
    action: str
    rationale: str
    expected_impact: str
    difficulty: str  # Easy, Medium, Hard


class RepositoryHealthReport(BaseModel):
    """Unified report on commit timelines, releases, health scores and collaboration."""
    report_id: str
    repository_url: str
    total_commits: int = 0
    active_contributors: int = 0
    bus_factor: int = 1
    inactive_periods: List[InactivePeriod] = Field(default_factory=list)
    burst_activities: List[BurstActivity] = Field(default_factory=list)
    releases: List[ReleaseInfo] = Field(default_factory=list)
    health_scores: HealthScores
    insights: List[EngineeringInsight] = Field(default_factory=list)
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    confidence_score: float
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# --- Prompt 5: GitHub Intelligence Product Models ---

class DeveloperSkillEvidence(BaseModel):
    """Evidence of a specific developer skill identified during analysis."""
    skill_name: str
    experience_level: str  # Beginner, Intermediate, Expert
    evidence_description: str
    associated_files: List[str] = Field(default_factory=list)


class GitHubIntelligenceReport(BaseModel):
    """Consolidated product-level engineering and health report for GitHub repositories."""
    report_id: str
    repository: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    knowledge_profile_version: str = "1.0"
    
    # Report Sections
    executive_summary: str
    repository_overview: Dict[str, Any] = Field(default_factory=dict)
    technology_stack: Dict[str, Any] = Field(default_factory=dict)
    architecture_style: str
    engineering_quality: Dict[str, Any] = Field(default_factory=dict)
    repository_health: Dict[str, Any] = Field(default_factory=dict)
    documentation_quality: Dict[str, Any] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    engineering_risks: List[str] = Field(default_factory=list)
    improvement_roadmap: List[str] = Field(default_factory=list)
    developer_skill_evidence: List[DeveloperSkillEvidence] = Field(default_factory=list)
    knowledge_profile_updates: Dict[str, Any] = Field(default_factory=dict)
    
    # Telemetry and Console Details
    pipeline_stage: str = "Completed"
    execution_metrics: Dict[str, float] = Field(default_factory=dict)

