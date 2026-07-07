"""Pydantic models for the Intelligence Composition Layer.

These are composition-specific types — they wrap contract-level
``IntelligenceResponse`` objects without duplicating their fields.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.intelligence.contracts.response_models import (
    Artifact,
    Citation,
    ExecutionMetrics,
    Recommendation,
    ResponseStatus,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ConflictSeverity(str, Enum):
    """How significant a detected conflict is."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceStrategy(str, Enum):
    """Algorithm used to aggregate per-module confidence scores."""

    AVERAGE = "average"
    WEIGHTED_AVERAGE = "weighted_average"
    MIN = "min"
    MAX = "max"


class CompositionStatus(str, Enum):
    """Overall outcome of a composition run."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Intermediate composition objects
# ---------------------------------------------------------------------------


class ModuleContribution(BaseModel):
    """Records what a single module contributed to the composition."""

    module: str
    execution_id: str
    status: ResponseStatus
    confidence: float
    summary: str = ""
    structured_output: Dict[str, Any] = Field(default_factory=dict)
    citation_ids: List[str] = Field(default_factory=list)
    artifact_ids: List[str] = Field(default_factory=list)
    recommendation_ids: List[str] = Field(default_factory=list)


class ConflictRecord(BaseModel):
    """Describes a conflict detected between two module outputs."""

    conflict_id: str = Field(default_factory=lambda: f"conf-{uuid.uuid4().hex[:8]}")
    field: str
    module_a: str
    module_b: str
    value_a: Any
    value_b: Any
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    explanation: str = ""
    resolved: bool = False
    resolution_note: str = ""


class AggregatedConfidence(BaseModel):
    """Result of a multi-module confidence aggregation."""

    overall: float
    strategy: ConfidenceStrategy
    per_module: Dict[str, float] = Field(default_factory=dict)
    weights: Dict[str, float] = Field(default_factory=dict)
    min_confidence: float = 0.0
    max_confidence: float = 0.0


class FindingSummary(BaseModel):
    """One discrete finding surfaced during composition."""

    finding_id: str = Field(default_factory=lambda: f"find-{uuid.uuid4().hex[:8]}")
    source_modules: List[str] = Field(default_factory=list)
    category: str
    title: str
    description: str
    confidence: float = 1.0
    supporting_evidence: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Composite response
# ---------------------------------------------------------------------------


class ComposedResponse(BaseModel):
    """The unified output produced by the Composition Engine.

    Aggregates contributions from every participating intelligence module
    into a single coherent report ready for frontend / SDK consumption.
    """

    composition_id: str = Field(default_factory=lambda: f"comp-{uuid.uuid4().hex[:10]}")
    request_id: str
    status: CompositionStatus = CompositionStatus.COMPLETED

    # Per-module provenance
    participating_modules: List[str] = Field(default_factory=list)
    module_contributions: List[ModuleContribution] = Field(default_factory=list)

    # Merged outputs
    executive_summary: str = ""
    detailed_findings: List[FindingSummary] = Field(default_factory=list)
    structured_output: Dict[str, Any] = Field(default_factory=dict)
    citations: List[Citation] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)

    # Quality signals
    aggregated_confidence: Optional[AggregatedConfidence] = None
    conflicts: List[ConflictRecord] = Field(default_factory=list)

    # Aggregate metrics
    total_duration_ms: float = 0.0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    estimated_cost_usd: float = 0.0

    completed_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
