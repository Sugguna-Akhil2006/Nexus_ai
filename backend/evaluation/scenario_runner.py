"""Scenario runner executing evaluation cases against selected models and settings."""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any, Dict

from backend.evaluation.models import EvalMetrics, ScenarioResult, TestCase


class ScenarioRunner:
    """Executes single benchmark scenario cases using mock/real gateway modules."""

    def execute_case(
        self,
        case: TestCase,
        model_name: str,
        provider_name: str,
        prompt_version: str,
    ) -> ScenarioResult:
        """Executes a single test case query and records results.

        Args:
            case: The TestCase being validated.
            model_name: Name of target model (e.g. gpt-4o, gemini-1.5-pro).
            provider_name: Name of the provider.
            prompt_version: Active system prompt version under test.

        Returns:
            ScenarioResult containing final scores and text response.
        """
        start_time = time.perf_counter()

        # Simulate execution logic and compile mock output matching expectations
        time.sleep(0.02)  # simulate API latency
        output = f"Completed run using model {model_name} on provider {provider_name}. " \
                 f"Evaluated input: '{case.input_query}'. Reference match: {case.reference_output}"

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Basic mock evaluation scoring based on mock attributes
        accuracy = 0.95 if "expected" in output.lower() else 0.85
        if "gpt-4" in model_name.lower() or "gemini" in model_name.lower():
            accuracy += 0.03
        accuracy = min(accuracy, 1.0)

        metrics = EvalMetrics(
            accuracy=accuracy,
            completeness=0.92,
            hallucination_rate=0.04,
            citation_quality=0.90,
            latency_ms=round(duration_ms, 2),
            cost_usd=0.0015 if "gpt" in model_name.lower() else 0.0005,
            confidence=0.88,
            consistency=0.95,
        )

        return ScenarioResult(
            scenario_id=f"scen-{uuid.uuid4().hex[:8]}",
            case_id=case.case_id,
            model_name=model_name,
            provider_name=provider_name,
            prompt_version=prompt_version,
            output_content=output,
            metrics=metrics,
            timestamp=datetime.utcnow().isoformat(),
        )
