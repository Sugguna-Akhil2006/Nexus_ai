"""Report generator compiling formatted benchmark summaries (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List

from backend.evaluation.models import BenchmarkRun, ModelRank


class ReportGenerator:
    """Compiles benchmark runs and regression summaries into developer-facing formats."""

    @staticmethod
    def generate_benchmark_markdown(run: BenchmarkRun) -> str:
        """Formats a BenchmarkRun into a Markdown table layout."""
        lines = [
            f"# Benchmark Evaluation Report: {run.dataset_name}",
            f"- **Run ID**: `{run.run_id}`",
            f"- **Start Time**: {run.start_time}",
            f"- **End Time**: {run.end_time}\n",
            "## Summary Metrics",
            f"- **Average Accuracy**: {run.avg_metrics.accuracy:.2f}",
            f"- **Average Completeness**: {run.avg_metrics.completeness:.2f}",
            f"- **Average Latency**: {run.avg_metrics.latency_ms:.1f} ms",
            f"- **Average Cost**: ${run.avg_metrics.cost_usd:.6f}\n",
            "## Scenario Details",
            "| Case ID | Model | Provider | Accuracy | Latency (ms) | Output Snapshot |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for r in run.results:
            lines.append(
                f"| `{r.case_id}` | {r.model_name} | {r.provider_name} | "
                f"{r.metrics.accuracy:.2f} | {r.metrics.latency_ms:.1f} | {r.output_content[:40]}... |"
            )
        return "\n".join(lines)

    @staticmethod
    def generate_leaderboard_markdown(ranks: List[ModelRank]) -> str:
        """Formats ModelRanks into a leaderboard Markdown table."""
        lines = [
            "# AI Model Leaderboard Rankings\n",
            "| Rank | Model Name | Provider | Avg Accuracy | Avg Latency (ms) | Score |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for r in ranks:
            lines.append(
                f"| **{r.rank}** | {r.model_name} | {r.provider_name} | "
                f"{r.avg_accuracy:.2%} | {r.avg_latency_ms:.1f} | {r.overall_score:.2f} |"
            )
        return "\n".join(lines)
