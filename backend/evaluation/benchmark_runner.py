"""Benchmark runner coordinating datasets, execution concurrency, and leaderboard rankings."""

from __future__ import annotations

import concurrent.futures
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from backend.evaluation.dataset_manager import DatasetManager
from backend.evaluation.leaderboard import Leaderboard
from backend.evaluation.metrics_engine import MetricsEngine
from backend.evaluation.models import BenchmarkRun, EvalMetrics, ScenarioResult, TestCase
from backend.evaluation.scenario_runner import ScenarioRunner


class BenchmarkRunner:
    """Central engine running evaluation benchmarks across configurations and providers."""

    def __init__(self) -> None:
        self.dataset_manager = DatasetManager()
        self.scenario_runner = ScenarioRunner()
        self.leaderboard = Leaderboard()
        self._lock = threading.RLock()
        self._history: Dict[str, BenchmarkRun] = {}

    def run_benchmark(
        self,
        dataset_name: str,
        models: List[str],
        provider: str = "ollama",
        prompt_version: str = "v1.0",
    ) -> BenchmarkRun:
        """Executes the test cases in a dataset against multiple models in parallel.

        Args:
            dataset_name: Target dataset (Resume, GitHub, or documents).
            models: List of model identifiers.
            provider: Provider name.
            prompt_version: Prompts version identifier.

        Returns:
            Completed BenchmarkRun report.
        """
        dataset = self.dataset_manager.get_dataset(dataset_name)
        if not dataset:
            # Fallback to generating synthetic cases if dataset isn't pre-configured
            dataset = self.dataset_manager.generate_synthetic_dataset()

        start_time = datetime.utcnow().isoformat()
        run_id = f"bench-{uuid.uuid4().hex[:8]}"

        results: List[ScenarioResult] = []

        # Run combinations of cases and models concurrently
        tasks = []
        for case in dataset.cases:
            for model in models:
                tasks.append((case, model))

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = {
                pool.submit(
                    self.scenario_runner.execute_case, case, model, provider, prompt_version
                ): (case, model)
                for case, model in tasks
            }

            for fut in concurrent.futures.as_completed(futures):
                try:
                    res = fut.result()
                    results.append(res)
                except Exception:
                    pass

        # Calculate average metrics
        avg_metrics = MetricsEngine.calculate_averages(results)

        run = BenchmarkRun(
            run_id=run_id,
            dataset_name=dataset.name,
            start_time=start_time,
            end_time=datetime.utcnow().isoformat(),
            results=results,
            avg_metrics=avg_metrics,
            completed=True,
        )

        with self._lock:
            self._history[run_id] = run

        # Update leaderboard rankings
        self.leaderboard.update_rankings(results)

        return run

    def get_run(self, run_id: str) -> Optional[BenchmarkRun]:
        """Retrieves a past run log."""
        with self._lock:
            return self._history.get(run_id)

    def list_runs(self) -> List[BenchmarkRun]:
        """Returns all completed benchmark runs."""
        with self._lock:
            return list(self._history.values())
