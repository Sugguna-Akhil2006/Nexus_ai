"""Comprehensive E2E Integration tests for the GitHub Intelligence Product."""

import os
import time
import shutil
import tempfile
import unittest
import subprocess
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.intelligence.github.repository import GitRepositoryReader
from backend.intelligence.github.product import GitHubProduct
from backend.intelligence.github.service import GitHubProductService
from backend.intelligence.github.history import GitHubHistoryManager
from backend.intelligence.github.cache import GitHubCache


class TestGitHubProduct(unittest.TestCase):
    """End-to-end integration tests validating sync/async flows, different stacks, and concurrency."""

    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=True)
        self.test_dirs = []
        self.history_manager = GitHubHistoryManager()
        self.cache = GitHubCache()

    def tearDown(self) -> None:
        for d in self.test_dirs:
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)

    def _create_temp_git_repo(self) -> str:
        """Helper to create a temporary directory and initialize it as a git repository."""
        d = tempfile.mkdtemp()
        self.test_dirs.append(d)
        subprocess.run(["git", "init", "-b", "main"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "Test Dev"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "dev@test.com"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return d

    def _commit_file(self, repo_path: str, filename: str, content: str, msg: str) -> None:
        """Helper to write a file and commit it to git."""
        full_path = os.path.join(repo_path, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["git", "add", filename], cwd=repo_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", msg], cwd=repo_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_sync_python_project_with_readme_and_cicd(self) -> None:
        """Validates a standard Python project with README and CI/CD workflow files."""
        repo = self._create_temp_git_repo()
        self._commit_file(repo, "README.md", "# Sample Python Project\nFor testing CI/CD workflow.", "initial commit")
        self._commit_file(repo, "main.py", "def add(a, b):\n    return a + b\n", "feat: add main function")
        self._commit_file(repo, "requirements.txt", "fastapi==0.100.0\nuvicorn>=0.20.0\n", "add requirements")
        self._commit_file(repo, ".github/workflows/ci.yml", "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n", "add CI workflow")

        # Call endpoint
        payload = {
            "repository_url": repo,
            "workspace_id": "ws-py",
            "user_id": "tester-1",
            "options": {"workspace_path": repo}
        }
        response = self.client.post("/github/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        report = response.json()

        self.assertIn("report_id", report)
        self.assertEqual(report["repository"], repo)
        self.assertEqual(report["technology_stack"]["languages"], ["Python"])
        self.assertIn("FastAPI", report["technology_stack"]["frameworks"])
        self.assertGreater(report["repository_health"]["overall_health_score"], 0)
        self.assertTrue(report["documentation_quality"]["has_readme"])
        self.assertGreaterEqual(len(report["strengths"]), 1)

    def test_java_project_and_docker_configurations(self) -> None:
        """Validates Java project detection with Maven pom.xml and Docker setup."""
        repo = self._create_temp_git_repo()
        self._commit_file(repo, "README.md", "# Java App", "init")
        self._commit_file(repo, "pom.xml", "<project></project>", "add maven config")
        self._commit_file(repo, "Main.java", "public class Main {}", "add java code")
        self._commit_file(repo, "Dockerfile", "FROM openjdk:17\nCOPY . /app\nUSER appuser\n", "add dockerfile")

        payload = {
            "repository_url": repo,
            "workspace_id": "ws-java",
            "options": {"workspace_path": repo}
        }
        response = self.client.post("/github/repository", json=payload)
        self.assertEqual(response.status_code, 200)
        report = response.json()

        self.assertIn("Java", report["technology_stack"]["languages"])
        self.assertIn("Docker Containerization", report["technology_stack"]["frameworks"])

    def test_nodejs_and_ai_ml_project(self) -> None:
        """Validates Node.js package.json detection with AI/ML requirements."""
        repo = self._create_temp_git_repo()
        self._commit_file(repo, "package.json", '{"dependencies": {"react": "^18.0.0"}}', "add package json")
        self._commit_file(repo, "requirements.txt", "torch==2.0.0\n", "add torch requirements")

        payload = {
            "repository_url": repo,
            "workspace_id": "ws-ai",
            "options": {"workspace_path": repo}
        }
        response = self.client.post("/github/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        report = response.json()

        self.assertIn("React", report["technology_stack"]["frameworks"])
        self.assertIn("AI/ML Stack", report["technology_stack"]["frameworks"])

    def test_no_readme_documentation_penalty(self) -> None:
        """Verifies documentation penalty for repositories missing a README file."""
        repo = self._create_temp_git_repo()
        self._commit_file(repo, "main.go", "package main\n", "init go project")

        payload = {
            "repository_url": repo,
            "workspace_id": "ws-noreadme",
            "options": {"workspace_path": repo}
        }
        response = self.client.post("/github/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        report = response.json()

        self.assertFalse(report["documentation_quality"]["has_readme"])
        self.assertTrue(any("readme" in risk.lower() for risk in report["engineering_risks"]))

    def test_async_workflow_for_large_repository(self) -> None:
        """Validates the asynchronous flow with worker thread tracking and status checks."""
        repo = self._create_temp_git_repo()
        self._commit_file(repo, "README.md", "# Large repo", "init")

        # Query with forced async option
        payload = {
            "repository_url": repo,
            "workspace_id": "ws-async",
            "options": {"workspace_path": repo, "async": True}
        }
        response = self.client.post("/github/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "processing")
        job_id = data["job_id"]

        # Poll status until completed
        completed = False
        for i in range(300):
            status_resp = self.client.get(f"/github/status/{job_id}")
            self.assertEqual(status_resp.status_code, 200)
            status_data = status_resp.json()
            print(f"POLL ITER {i}: STATUS={status_data['status']} PROGRESS={status_data['progress']}")
            if status_data["status"] in ["completed", "failed"]:
                completed = True
                self.assertEqual(status_data["status"], "completed")
                self.assertIsNotNone(status_data["report_id"])
                break
            time.sleep(0.1)

        self.assertTrue(completed)

        # Retrieve report by report ID
        report_id = status_data["report_id"]
        report_resp = self.client.get(f"/github/report/{report_id}")
        self.assertEqual(report_resp.status_code, 200)
        self.assertEqual(report_resp.json()["report_id"], report_id)

    def test_concurrent_requests_thread_safety(self) -> None:
        """Verifies concurrent report requests run safely without database lock collisions."""
        repo = self._create_temp_git_repo()
        self._commit_file(repo, "README.md", "# Concurrent tests", "init")

        payloads = [
            {
                "repository_url": repo,
                "workspace_id": f"ws-concurrent-{i}",
                "options": {"workspace_path": repo}
            }
            for i in range(5)
        ]

        def post_request(payload):
            return self.client.post("/github/analyze", json=payload)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(post_request, p) for p in payloads]
            responses = [f.result() for f in futures]

        for resp in responses:
            self.assertEqual(resp.status_code, 200)
            self.assertIn("report_id", resp.json())

    def test_pipeline_recovery_and_history_comparison(self) -> None:
        """Verifies database history list and delta metric comparison of two versions."""
        repo = self._create_temp_git_repo()
        self._commit_file(repo, "main.py", "print('hello')", "first version")

        # Run first analysis
        p1 = {"repository_url": repo, "workspace_id": "ws-history", "options": {"workspace_path": repo}}
        r1 = self.client.post("/github/analyze", json=p1).json()
        report_id_1 = r1["report_id"]

        # Change codebase (e.g. increase lines of code)
        self._commit_file(repo, "helper.py", "\n".join("print('line')" for _ in range(50)), "second version")

        # Run second analysis
        r2 = self.client.post("/github/analyze", json=p1).json()
        report_id_2 = r2["report_id"]

        # Query history
        hist_resp = self.client.get("/github/history?workspace_id=ws-history")
        self.assertEqual(hist_resp.status_code, 200)
        history = hist_resp.json()["history"]
        self.assertGreaterEqual(len(history), 2)

        # Retrieve reports and compare
        rep_1 = self.history_manager.get_report(report_id_1)
        rep_2 = self.history_manager.get_report(report_id_2)
        comparison = self.history_manager.compare_reports(rep_1, rep_2)

        self.assertEqual(comparison["comparison"]["lines_of_code"]["base"], 1)
        self.assertEqual(comparison["comparison"]["lines_of_code"]["target"], 51)
        self.assertEqual(comparison["comparison"]["lines_of_code"]["delta"], 50)
