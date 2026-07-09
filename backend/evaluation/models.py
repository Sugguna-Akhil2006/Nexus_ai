"""Pydantic data models for the AI Evaluation & Benchmarking Suite."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """A single evaluation test case containing input query and expected outputs."""

    case_id: str
    category: str  # "resume" | "github" | "document" | "mixed"
    input_query: str
    reference_output: str
    document_ids: List[str] = Field(default_factory=list)


class Dataset(BaseModel):
    """A named collection of evaluation test cases."""

    dataset_id: str
    name: str
    cases: List[TestCase] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class EvalMetrics(BaseModel):
    """Quality, latency, cost, and reliability metrics scored for an execution."""

    accuracy: float = 1.0  # [0.0, 1.0]
    completeness: float = 1.0  # [0.0, 1.0]
    hallucination_rate: float = 0.0  # [0.0, 1.0]
    citation_quality: float = 1.0  # [0.0, 1.0]
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    confidence: float = 1.0
    consistency: float = 1.0


class ScenarioResult(BaseModel):
    """The outcome of running a single TestCase against specific settings."""

    scenario_id: str
    case_id: str
    model_name: str
    provider_name: str
    prompt_version: str
    output_content: str
    metrics: EvalMetrics = Field(default_factory=EvalMetrics)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BenchmarkRun(BaseModel):
    """Detailed summary of a completed benchmark evaluation run."""

    run_id: str
    dataset_name: str
    start_time: str
    end_time: str
    results: List[ScenarioResult] = Field(default_factory=list)
    avg_metrics: EvalMetrics = Field(default_factory=EvalMetrics)
    completed: bool = False


class ModelRank(BaseModel):
    """Comparative standing data for a model in the leaderboard."""

    model_name: str
    provider_name: str
    avg_accuracy: float = 0.0
    avg_latency_ms: float = 0.0
    avg_cost_usd: float = 0.0
    overall_score: float = 0.0
    rank: int = 1
