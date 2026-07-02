"""Flagship agent coordinating static scanning, design auditing, and activity analysis."""

import os
from typing import Dict, Any, Optional
from backend.runtime.logger import StructuredLogger
from backend.intelligence.github.services import GitHubIntelligenceService


class GitHubAgent:
    """Flagship agent coordinating code scans, anti-pattern detectors, and health scoring."""

    def __init__(self) -> None:
        self.logger = StructuredLogger()
        self.service = GitHubIntelligenceService()

    def run_analysis(
        self,
        workspace_path: str,
        workspace_id: str = "default-ws",
        repository_url: str = "",
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Runs static crawls, audits, and timelines checks over local repository path.

        Args:
            workspace_path: Target directory path.
            workspace_id: Workspace scope.
            repository_url: Repository URL or path.
            branch: Target branch.

        Returns:
            Dict[str, Any]: Combined structured analytical reports.
        """
        self.logger.info(f"GitHubAgent: Starting execution run for workspace path {workspace_path}")
        
        # Verify folder path
        if not os.path.exists(workspace_path):
            raise FileNotFoundError(f"Target workspace path not found: {workspace_path}")
            
        results = self.service.analyze_workspace(
            workspace_path=workspace_path,
            workspace_id=workspace_id,
            repository_url=repository_url,
            branch=branch
        )
        
        self.logger.info("GitHubAgent: Execution run completed successfully.")
        return results
