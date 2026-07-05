"""Pytest and unit test coverage for GitHub Activity, Health, and Code Quality reviews."""

import os
import shutil
import tempfile
import unittest
import subprocess
from datetime import datetime, timedelta
from typing import Optional

from backend.intelligence.github.repository import GitRepositoryReader
from backend.intelligence.github.activity_analyzer import EngineeringActivityAnalyzer
from backend.intelligence.github.code_quality import CodeQualityEngine
from backend.intelligence.github.services import GitHubIntelligenceService


class TestGitHubActivity(unittest.TestCase):
    """Verifies repository scans, commit logs analysis, release progression, and health scorers."""

    def setUp(self) -> None:
        self.test_dirs = []

    def tearDown(self) -> None:
        # Cleanup temporary folders
        for d in self.test_dirs:
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)

    def _create_temp_git_repo(self) -> str:
        """Helper to create a temporary directory and initialize it as a git repository."""
        d = tempfile.mkdtemp()
        self.test_dirs.append(d)
        
        # Init Git
        subprocess.run(["git", "init", "-b", "main"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Configure local dummy user
        subprocess.run(["git", "config", "user.name", "Test Developer"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "dev@test.com"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return d

    def _commit_file(self, repo_path: str, filename: str, content: str, msg: str, author: Optional[str] = None, email: Optional[str] = None, date_str: Optional[str] = None) -> None:
        """Helper to write a file and commit it, optionally setting author and date."""
        full_path = os.path.join(repo_path, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        subprocess.run(["git", "add", filename], cwd=repo_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        cmd = ["git", "commit", "-m", msg]
        env = os.environ.copy()
        
        if author and email:
            env["GIT_AUTHOR_NAME"] = author
            env["GIT_AUTHOR_EMAIL"] = email
            env["GIT_COMMITTER_NAME"] = author
            env["GIT_COMMITTER_EMAIL"] = email
            
        if date_str:
            env["GIT_AUTHOR_DATE"] = date_str
            env["GIT_COMMITTER_DATE"] = date_str
            
        subprocess.run(cmd, cwd=repo_path, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_active_repository_with_releases(self) -> None:
        """Verifies active repository with multiple commits and release tags."""
        repo = self._create_temp_git_repo()
        
        # Write README.md and python files
        self._commit_file(repo, "README.md", "# Test Project\nInstall and run tools.", "feat: initial commit")
        self._commit_file(repo, "main.py", "print('hello')", "feat: add main function")
        
        # Add release tag
        subprocess.run(["git", "tag", "v1.0.0"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Run analyzers
        reader = GitRepositoryReader(repo)
        analyzer = EngineeringActivityAnalyzer()
        report = analyzer.analyze_activity(reader, repository_url="https://github.com/test/repo")
        
        self.assertEqual(report.total_commits, 2)
        self.assertEqual(report.active_contributors, 1)
        self.assertEqual(len(report.releases), 1)
        self.assertEqual(report.releases[0].tag_name, "v1.0.0")
        
        # Verify scores and insights
        self.assertGreater(report.health_scores.overall_health_score, 0.0)
        self.assertTrue(any("readme" in i.description.lower() or "documentation" in i.description.lower() or "active" in i.description.lower() or "activity" in i.description.lower() for i in report.insights))

    def test_inactive_repository_without_releases(self) -> None:
        """Verifies inactive repository commits parsing gaps detection."""
        repo = self._create_temp_git_repo()
        
        # Make a commit long ago
        ago = (datetime.utcnow() - timedelta(days=40)).isoformat()
        self._commit_file(repo, "main.py", "print('old')", "feat: old commit", date_str=ago)
        
        reader = GitRepositoryReader(repo)
        analyzer = EngineeringActivityAnalyzer()
        report = analyzer.analyze_activity(reader, repository_url="https://github.com/test/inactive", has_readme=False)
        
        self.assertEqual(report.total_commits, 1)
        self.assertEqual(len(report.releases), 0)
        
        # Check overall health matches inactive penalty
        self.assertLess(report.health_scores.overall_health_score, 80.0)
        self.assertTrue(any("missing readme" in i.description.lower() or "slipped" in i.description.lower() or "slowed" in i.description.lower() or "no active" in i.description.lower() for i in report.insights))

    def test_team_project_bus_factor(self) -> None:
        """Verifies collaborator metrics, contributor distribution and Bus Factor calculation."""
        repo = self._create_temp_git_repo()
        
        # Commits from different authors
        self._commit_file(repo, "a.py", "a = 1", "feat: commit a", author="Alice", email="alice@test.com")
        self._commit_file(repo, "b.py", "b = 2", "feat: commit b", author="Bob", email="bob@test.com")
        self._commit_file(repo, "c.py", "c = 3", "feat: commit c", author="Charlie", email="charlie@test.com")
        
        reader = GitRepositoryReader(repo)
        analyzer = EngineeringActivityAnalyzer()
        report = analyzer.analyze_activity(reader)
        
        self.assertEqual(report.active_contributors, 3)
        self.assertGreaterEqual(report.bus_factor, 1)

    def test_large_commit_history_and_bursts(self) -> None:
        """Verifies burst activity checks and conventional commits formatting ratios."""
        repo = self._create_temp_git_repo()
        
        # Push 6 commits on the same day to trigger a burst
        for i in range(6):
            self._commit_file(repo, f"file_{i}.py", f"x = {i}", f"feat: conventional commit {i}")
            
        reader = GitRepositoryReader(repo)
        analyzer = EngineeringActivityAnalyzer()
        report = analyzer.analyze_activity(reader)
        
        self.assertEqual(report.total_commits, 6)
        self.assertEqual(len(report.burst_activities), 1)
        self.assertEqual(report.burst_activities[0].commit_count, 6)

    def test_code_quality_and_circular_dependencies(self) -> None:
        """Verifies Design Patterns, God Objects, and Circular dependencies detection."""
        repo = self._create_temp_git_repo()
        
        # 1. Circular dependency python files (mod_a imports mod_b and vice-versa)
        self._commit_file(repo, "mod_a.py", "import mod_b\nclass Singleton:\n    pass", "feat: add mod_a")
        self._commit_file(repo, "mod_b.py", "import mod_a", "feat: add mod_b")
        
        # 2. Large lines file (God Object)
        god_content = "\n".join(f"line_{i} = {i}" for i in range(1100))
        self._commit_file(repo, "god_object.py", god_content, "feat: add god_object")
        
        reader = GitRepositoryReader(repo)
        quality_engine = CodeQualityEngine()
        report = quality_engine.analyze_quality(reader)
        
        # Verify detected anti-patterns
        self.assertTrue(any("God Object" in ap for ap in report.detected_anti_patterns))
        self.assertTrue(any("Circular" in ap or "mod_a" in ap for ap in report.detected_anti_patterns))
        self.assertLessEqual(report.maintainability_score, 80.0)

    def test_service_level_run(self) -> None:
        """Verifies complete end-to-end workspace execution and SQLite report persistence."""
        repo = self._create_temp_git_repo()
        self._commit_file(repo, "README.md", "# Hello", "feat: init")
        
        svc = GitHubIntelligenceService()
        results = svc.analyze_workspace(repo, workspace_id="ws-123", repository_url="test-repo")
        
        self.assertIn("repo_report", results)
        self.assertIn("quality_report", results)
        self.assertIn("health_report", results)
        
        # Query saved reports from DB
        fetched = svc.get_reports("ws-123", "test-repo")
        self.assertIsNotNone(fetched.get("repo_report"))
        self.assertIsNotNone(fetched.get("quality_report"))
        self.assertIsNotNone(fetched.get("health_report"))


