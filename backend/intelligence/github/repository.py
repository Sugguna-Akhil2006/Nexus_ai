"""Local Git repository file manager and structure crawler."""

import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
from backend.intelligence.github.exceptions import InvalidRepositoryError


class GitRepositoryReader:
    """Reads repository structures, files, and git metadata logs from local workspace directories."""

    def __init__(self, workspace_path: str) -> None:
        """Initializes reader.

        Args:
            workspace_path: Absolute directory path.

        Raises:
            InvalidRepositoryError: If path does not exist or is not a directory.
        """
        if not os.path.exists(workspace_path) or not os.path.isdir(workspace_path):
            raise InvalidRepositoryError(f"Workspace path does not exist or is not a directory: {workspace_path}")
        self.workspace_path = os.path.abspath(workspace_path)

    def scan_files(self) -> List[str]:
        """Crawl workspace files skipping typical build/lock files.

        Returns:
            List[str]: Relative file paths.
        """
        excluded_dirs = {
            ".git", "node_modules", "venv", ".venv", "build", "dist",
            "__pycache__", "target", "bin", "obj", ".idea", ".vscode"
        }
        
        file_paths = []
        for root, dirs, files in os.walk(self.workspace_path):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.workspace_path)
                file_paths.append(rel_path.replace("\\", "/"))
        return file_paths

    def read_file(self, relative_path: str) -> str:
        """Reads file contents.

        Args:
            relative_path: Target relative path.

        Returns:
            str: Content text.
        """
        full_path = os.path.join(self.workspace_path, relative_path)
        if not os.path.exists(full_path):
            return ""
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    def run_git_cmd(self, args: List[str]) -> str:
        """Runs a git command inside the workspace directory.

        Args:
            args: Command line arguments.

        Returns:
            str: Standard output.
        """
        try:
            # Use shell=True for windows safety if command needs routing
            res = subprocess.run(
                ["git"] + args,
                cwd=self.workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return res.stdout
        except Exception:
            return ""

    def get_commit_history(self) -> List[Dict[str, Any]]:
        """Parses git log commits into dictionary structures.

        Returns:
            List[Dict[str, Any]]: List of commit info maps.
        """
        raw_log = self.run_git_cmd([
            "log", 
            '--pretty=format:%H||%an||%ae||%aI||%s'
        ])
        
        commits = []
        if not raw_log:
            # Fallback to simulated commit history if not a git repo
            return []
            
        for line in raw_log.splitlines():
            parts = line.strip().split("||")
            if len(parts) == 5:
                commit_hash, author, email, timestamp, subject = parts
                try:
                    dt = datetime.fromisoformat(timestamp)
                except Exception:
                    dt = datetime.utcnow()
                commits.append({
                    "hash": commit_hash,
                    "author": author,
                    "email": email,
                    "timestamp": dt,
                    "message": subject
                })
        return commits
