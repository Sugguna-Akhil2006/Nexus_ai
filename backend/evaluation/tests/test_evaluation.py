"""Unit and integration tests for the AI Evaluation & Benchmarking Suite."""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.evaluation.benchmark_runner import BenchmarkRunner
from backend.evaluation.dataset_manager import DatasetManager
from backend.evaluation.leaderboard import Leaderboard
from backend.evaluation.model_comparator import ModelComparator
from backend.evaluation.models import EvalMetrics, ScenarioResult, TestCase
from backend.evaluation.prompt_evaluator import PromptEvaluator
from backend.evaluation.rag_evaluator import RAGEvaluator
from backend.evaluation.workflow_comparator import WorkflowComparator


class TestDatasetManager(unittest.TestCase):
    """Verifies dataset seeding and synthetic dataset generation."""

    def setUp(self) -> None:
        self.mgr = DatasetManager()

    def test_default_datasets_exist(self) -> None:
        datasets = self.mgr.list_datasets()
        self.assertGreaterEqual(len(datasets), 4)
        names = {ds.name for ds in datasets}
        self.assertIn("Resume Analysis", names)
        self.assertIn("GitHub Repositories", names)

    def test_synthetic_generation(self) -> None:
        syn = self.mgr.generate_synthetic_dataset(size=10)
        self.assertEqual(len(syn.cases), 10)
        self.assertEqual(syn.cases[0].category, "synthetic")


class TestRAGEvaluator(unittest.TestCase):
    """Verifies retrieval precision, recall, and chunk relevance scoring."""

    def test_rag_precision_recall(self) -> None:
        retrieved = [{"chunk_id": "c1"}, {"chunk_id": "c2"}, {"chunk_id": "c3"}]
        ground = ["c1", "c3", "c5"]

        scores = RAGEvaluator.evaluate_retrieval(retrieved, ground)
        self.assertAlmostEqual(scores["retrieval_precision"], 2 / 3, places=3)
        self.assertAlmostEqual(scores["retrieval_recall"], 2 / 3, places=3)
        self.assertEqual(scores["chunk_relevance"], 0.90)


class TestPromptEvaluator(unittest.TestCase):
    """Verifies A/B testing compare parameters and regression flags."""

    def test_detects_regression(self) -> None:
        results_a = [{"accuracy": 0.95}, {"accuracy": 0.93}]
        # Significant drop in version B
        results_b = [{"accuracy": 0.85}, {"accuracy": 0.82}]

        comp = PromptEvaluator.compare_prompts(results_a, results_b)
        self.assertTrue(comp["regression_detected"])
        self.assertLess(comp["accuracy_improvement"], 0.0)

    def test_detects_improvement(self) -> None:
        results_a = [{"accuracy": 0.80}]
        results_b = [{"accuracy": 0.90}]

        comp = PromptEvaluator.compare_prompts(results_a, results_b)
        self.assertFalse(comp["regression_detected"])
        self.assertEqual(comp["accuracy_improvement"], 0.10)


class TestLeaderboard(unittest.TestCase):
    """Verifies model sorting score formulas."""

    def test_leaderboard_rankings(self) -> None:
        results = [
            ScenarioResult(
                scenario_id="s1",
                case_id="tc1",
                model_name="model-fast",
                provider_name="ollama",
                prompt_version="v1",
                output_content="res",
                metrics=EvalMetrics(accuracy=0.90, latency_ms=100.0),
            ),
            ScenarioResult(
                scenario_id="s2",
                case_id="tc1",
                model_name="model-slow",
                provider_name="ollama",
                prompt_version="v1",
                output_content="res",
                metrics=EvalMetrics(accuracy=0.92, latency_ms=1500.0),
            ),
        ]
        lb = Leaderboard()
        ranks = lb.update_rankings(results)

        self.assertEqual(len(ranks), 2)
        # model-fast has lower latency and high accuracy, so overall score should rank it first
        self.assertEqual(ranks[0].model_name, "model-fast")
        self.assertEqual(ranks[0].rank, 1)
        self.assertEqual(ranks[1].model_name, "model-slow")
        self.assertEqual(ranks[1].rank, 2)


class TestBenchmarkRunner(unittest.TestCase):
    """Full workflow evaluation validation run."""

    def test_run_benchmark(self) -> None:
        runner = BenchmarkRunner()
        run = runner.run_benchmark(
            dataset_name="ds-resume",
            models=["gpt-4", "llama3"],
            provider="ollama",
            prompt_version="v1.0",
        )
        self.assertTrue(run.completed)
        self.assertEqual(len(run.results), 2)
        self.assertGreater(run.avg_metrics.accuracy, 0.0)
        self.assertEqual(len(runner.list_runs()), 1)
