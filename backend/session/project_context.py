"""Project context tracking goals, milestones, decisions, and technical debt."""

import threading
from typing import List, Optional
from backend.session.models import ProjectContextModel, Decision, DecisionType


class ProjectContext:
    """Thread-safe context store for project metadata and design decisions."""

    def __init__(self, data: Optional[ProjectContextModel] = None) -> None:
        self._lock = threading.RLock()
        self._model = data or ProjectContextModel()

    def add_goal(self, goal: str) -> None:
        """Adds a project goal."""
        with self._lock:
            if goal not in self._model.goals:
                self._model.goals.append(goal)

    def add_milestone(self, milestone: str) -> None:
        """Adds a project milestone."""
        with self._lock:
            if milestone not in self._model.milestones:
                self._model.milestones.append(milestone)

    def record_decision(self, title: str, description: str, decision_type: DecisionType) -> Decision:
        """Records a new architectural or implementation decision."""
        with self._lock:
            decision = Decision(
                title=title,
                description=description,
                decision_type=decision_type
            )
            if decision_type == DecisionType.ARCHITECTURE:
                self._model.architecture_decisions.append(decision)
            else:
                self._model.implementation_decisions.append(decision)
            return decision

    def add_known_issue(self, issue: str) -> None:
        """Adds a known issue."""
        with self._lock:
            if issue not in self._model.known_issues:
                self._model.known_issues.append(issue)

    def resolve_known_issue(self, issue: str) -> None:
        """Resolves/removes a known issue."""
        with self._lock:
            if issue in self._model.known_issues:
                self._model.known_issues.remove(issue)

    def add_technical_debt(self, debt: str) -> None:
        """Adds technical debt item."""
        with self._lock:
            if debt not in self._model.technical_debt:
                self._model.technical_debt.append(debt)

    def get_snapshot(self) -> ProjectContextModel:
        """Returns a copy of the project context model."""
        with self._lock:
            return self._model.model_copy(deep=True)

    def load_snapshot(self, model: ProjectContextModel) -> None:
        """Loads state from a snapshot model."""
        with self._lock:
            self._model = model.model_copy(deep=True)
