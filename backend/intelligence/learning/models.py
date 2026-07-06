"""Pydantic data schemas representing Feedback Types and Correction Logs."""

from enum import Enum
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    """Supported user feedback rating type classifiers."""
    THUMBS_UP = "THUMBS_UP"
    THUMBS_DOWN = "THUMBS_DOWN"
    MANUAL_EDIT = "MANUAL_EDIT"
    CORRECTION = "CORRECTION"
    IGNORED_SUGGESTION = "IGNORED_SUGGESTION"
    ACCEPTED_SUGGESTION = "ACCEPTED_SUGGESTION"
    CUSTOM_RATING = "CUSTOM_RATING"


class FeedbackEntry(BaseModel):
    """Metadata logged for a single thumbs or rating feedback action."""
    feedback_id: str
    workspace_id: str
    target_type: str  # "reasoning", "module", "recommendation", etc.
    target_id: str
    feedback_type: FeedbackType
    rating: float = 0.0  # Optional numeric value
    comments: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CorrectionEntry(BaseModel):
    """Tracks manual correction overrides entered by users."""
    correction_id: str
    workspace_id: str
    source_module: str  # "Resume", "GitHub", "Document", etc.
    field_name: str
    original_value: str
    corrected_value: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
