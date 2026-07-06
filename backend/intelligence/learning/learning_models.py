"""Data structures stashing statistical preferences and source reliability scores."""

from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ConfidenceCalibration(BaseModel):
    """Calibrated reliability score values for an intelligence module."""
    source_key: str  # E.g. "Resume", "GitHub", "Document"
    success_count: int = 0
    correction_count: int = 0
    reliability_score: float = 1.0
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UserPreference(BaseModel):
    """Aggregated preference scores computed for output styles or settings."""
    workspace_id: str
    category: str  # E.g. "output_style", "template_preference"
    value: str
    frequency: int = 1
    last_used: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
