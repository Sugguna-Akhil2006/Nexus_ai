"""Database storage tables mapper and workflows runner for GitHub reports."""

import json
from datetime import datetime
from typing import Optional, Dict, Any

from backend.api.sqlite_mock import DBStorage
from backend.intelligence.github.models import (
    RepositoryAnalysisReport,
    EngineeringAnalysisReport,
    RepositoryHealthReport
)
from backend.intelligence.github.repository import GitRepositoryReader
from backend.intelligence.github.repository_analyzer import RepositoryAnalyzerEngine
from backend.intelligence.github.code_quality import CodeQualityEngine
from backend.intelligence.github.activity_analyzer import EngineeringActivityAnalyzer


class GitHubIntelligenceService:
    """Service handling repository clones, static parsing, code audits, and SQLite persistency."""

    def __init__(self) -> None:
        self.repo_analyzer = RepositoryAnalyzerEngine()
        self.quality_analyzer = CodeQualityEngine()
        self.activity_analyzer = EngineeringActivityAnalyzer()
        self._init_db()

    def _init_db(self) -> None:
        """Configures database schemas for repository metrics, design audits, and timelines."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS github_reports (
                    workspace_id TEXT NOT NULL,
                    repository_url TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    repo_report TEXT,
                    quality_report TEXT,
                    health_report TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (workspace_id, repository_url, branch)
                )
                """)
                conn.commit()
        finally:
            conn.close()

    def save_reports(
        self,
        workspace_id: str,
        repository_url: str,
        branch: str,
        repo_rep: Optional[RepositoryAnalysisReport] = None,
        qual_rep: Optional[EngineeringAnalysisReport] = None,
        health_rep: Optional[RepositoryHealthReport] = None
    ) -> None:
        """Stores or merges calculated reports into SQLite.

        Args:
            workspace_id: Workspace key.
            repository_url: Repository URL or local workspace path key.
            branch: Repository branch context.
            repo_rep: Repository structure report.
            qual_rep: Code quality audit report.
            health_rep: Engineering activity report.
        """
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                # First, check if row exists to keep un-updated columns
                row = conn.execute(
                    "SELECT repo_report, quality_report, health_report FROM github_reports WHERE workspace_id = ? AND repository_url = ? AND branch = ?",
                    (workspace_id, repository_url, branch)
                ).fetchone()
                
                existing_repo = row["repo_report"] if row else None
                existing_qual = row["quality_report"] if row else None
                existing_health = row["health_report"] if row else None

                repo_json = repo_rep.model_dump_json() if repo_rep else existing_repo
                qual_json = qual_rep.model_dump_json() if qual_rep else existing_qual
                health_json = health_rep.model_dump_json() if health_rep else existing_health

                conn.execute(
                    """
                    INSERT OR REPLACE INTO github_reports 
                    (workspace_id, repository_url, branch, repo_report, quality_report, health_report, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workspace_id,
                        repository_url,
                        branch,
                        repo_json,
                        qual_json,
                        health_json,
                        datetime.utcnow().isoformat()
                    )
                )
                conn.commit()
        finally:
            conn.close()

    def get_reports(self, workspace_id: str, repository_url: str, branch: str = "main") -> Dict[str, Any]:
        """Retrieves active stored reports.

        Args:
            workspace_id: Target workspace context.
            repository_url: Repository URL path identifier.
            branch: Branch key.

        Returns:
            Dict[str, Any]: Mapped reports or None.
        """
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                row = conn.execute(
                    "SELECT repo_report, quality_report, health_report FROM github_reports WHERE workspace_id = ? AND repository_url = ? AND branch = ?",
                    (workspace_id, repository_url, branch)
                ).fetchone()
                
                if not row:
                    return {}
                
                res = {}
                if row["repo_report"]:
                    res["repo_report"] = RepositoryAnalysisReport.model_validate_json(row["repo_report"])
                if row["quality_report"]:
                    res["quality_report"] = EngineeringAnalysisReport.model_validate_json(row["quality_report"])
                if row["health_report"]:
                    res["health_report"] = RepositoryHealthReport.model_validate_json(row["health_report"])
                return res
        finally:
            conn.close()

    def analyze_workspace(
        self,
        workspace_path: str,
        workspace_id: str = "default-ws",
        repository_url: str = "",
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Runs complete parsing, quality audits, and commit logs checks synchronously.

        Args:
            workspace_path: Path on local disk.
            workspace_id: Current workspace ID.
            repository_url: Repository URL identifier.
            branch: Branch context.

        Returns:
            Dict[str, Any]: Collected execution reports.
        """
        reader = GitRepositoryReader(workspace_path)
        
        # 1. Run Repository static parsing (Prompt 2)
        repo_rep = self.repo_analyzer.analyze_repository(reader, repository_url, branch, workspace_id)
        
        # 2. Run Code Quality check (Prompt 3)
        qual_rep = self.quality_analyzer.analyze_quality(reader)
        
        # 3. Run Engineering Activity evaluation (Prompt 4)
        doc_read = repo_rep.documentation.readability_score if repo_rep.documentation else 50.0
        has_read = repo_rep.documentation.has_readme if repo_rep.documentation else False
        health_rep = self.activity_analyzer.analyze_activity(
            reader=reader,
            repository_url=repository_url,
            workspace_id=workspace_id,
            doc_readability=doc_read,
            has_readme=has_read
        )

        # 4. Save results to DB
        self.save_reports(
            workspace_id=workspace_id,
            repository_url=repository_url or workspace_path,
            branch=branch,
            repo_rep=repo_rep,
            qual_rep=qual_rep,
            health_rep=health_rep
        )

        return {
            "repo_report": repo_rep,
            "quality_report": qual_rep,
            "health_report": health_rep
        }
