"""Thread-safe blackboard repository sharing parameters and facts between agents."""

import threading
from datetime import datetime
from typing import Dict, List, Any


class SharedContext:
    """Synchronized shared memory board accessible by collaborating agents."""

    def __init__(self, objective: str) -> None:
        self.objective = objective
        self._lock = threading.RLock()
        self.evidence_list: List[Dict[str, Any]] = []
        self.timeline: List[Dict[str, Any]] = []
        self.intermediate_results: Dict[str, Any] = {}
        self.executed_agents: List[str] = []

    def add_evidence(self, agent_name: str, fact: str, confidence: float) -> None:
        """Saves a fact extracted by an agent to the shared blackboard."""
        with self._lock:
            self.evidence_list.append({
                "source": agent_name,
                "fact": fact,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            })

    def get_evidence(self) -> List[Dict[str, Any]]:
        """Retrieves all collected evidence logs."""
        with self._lock:
            return list(self.evidence_list)

    def add_executed_agent(self, agent_name: str) -> None:
        """Appends to the executed agent list."""
        with self._lock:
            if agent_name not in self.executed_agents:
                self.executed_agents.append(agent_name)

    def get_executed_agents(self) -> List[str]:
        """Returns the completed list of active collaborator agents."""
        with self._lock:
            return list(self.executed_agents)

    def record_timeline_step(self, agent_name: str, action: str, duration: float) -> None:
        """Appends step duration details into the execution timeline."""
        with self._lock:
            self.timeline.append({
                "agent_name": agent_name,
                "action": action,
                "duration_s": duration,
                "timestamp": datetime.utcnow().isoformat()
            })

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Returns the completed timeline metrics list."""
        with self._lock:
            return list(self.timeline)

    def set_result(self, key: str, value: Any) -> None:
        """Saves intermediate agent calculation state values."""
        with self._lock:
            self.intermediate_results[key] = value

    def get_result(self, key: str) -> Any:
        """Fetches intermediate value by keyword."""
        with self._lock:
            return self.intermediate_results.get(key)
