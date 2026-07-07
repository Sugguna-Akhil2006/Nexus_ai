"""Workspace memory management to track files, workflows, projects, and active objectives."""

import threading
from typing import Any, Dict, List, Optional
from backend.session.models import WorkspaceMemoryModel


class WorkspaceMemory:
    """Thread-safe manager for session-scoped workspace states."""

    def __init__(self, data: Optional[WorkspaceMemoryModel] = None) -> None:
        self._lock = threading.RLock()
        self._model = data or WorkspaceMemoryModel()

    def update_project(self, project_name: Optional[str]) -> None:
        """Sets the current active project name."""
        with self._lock:
            self._model.current_project = project_name

    def add_recent_file(self, file_path: str) -> None:
        """Adds a file to the top of recent files list, maintaining unique values."""
        with self._lock:
            if file_path in self._model.recent_files:
                self._model.recent_files.remove(file_path)
            self._model.recent_files.insert(0, file_path)

    def add_recent_workflow(self, workflow_id: str) -> None:
        """Adds a workflow run to the recent list."""
        with self._lock:
            if workflow_id in self._model.recent_workflows:
                self._model.recent_workflows.remove(workflow_id)
            self._model.recent_workflows.insert(0, workflow_id)

    def add_recent_analysis(self, analysis_id: str) -> None:
        """Adds an analysis to the recent list."""
        with self._lock:
            if analysis_id in self._model.recent_analyses:
                self._model.recent_analyses.remove(analysis_id)
            self._model.recent_analyses.insert(0, analysis_id)

    def set_objective(self, objective: Optional[str]) -> None:
        """Sets the current high-level objective."""
        with self._lock:
            self._model.current_objective = objective

    def add_pending_task(self, task: str) -> None:
        """Appends a task to the pending list."""
        with self._lock:
            if task not in self._model.pending_tasks:
                self._model.pending_tasks.append(task)

    def remove_pending_task(self, task: str) -> None:
        """Removes a task from the pending list."""
        with self._lock:
            if task in self._model.pending_tasks:
                self._model.pending_tasks.remove(task)

    def get_snapshot(self) -> WorkspaceMemoryModel:
        """Returns a copy of the workspace memory state."""
        with self._lock:
            return self._model.model_copy(deep=True)

    def load_snapshot(self, model: WorkspaceMemoryModel) -> None:
        """Loads/restores the state from a snapshot model."""
        with self._lock:
            self._model = model.model_copy(deep=True)
