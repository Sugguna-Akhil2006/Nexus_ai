"""Definitions for modular pipeline stages."""

from typing import Any, Callable, List, Optional
from pydantic import BaseModel, Field

from backend.intelligence.core.context import IntelligenceContext


class PipelineStage(BaseModel):
    """Represents a single stage in the intelligence processing pipeline."""
    name: str
    action: Callable[[Any, Any], None]
    condition: Optional[Callable[[IntelligenceContext], bool]] = None
    depends_on: List[str] = Field(default_factory=list)
    max_retries: int = 3

    class Config:
        arbitrary_types_allowed = True
