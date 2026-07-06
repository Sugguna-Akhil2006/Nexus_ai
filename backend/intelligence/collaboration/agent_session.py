"""Tracks lifecycle metrics of an individual agent execution run in a session."""

import time
from typing import List


class AgentSession:
    """Manages active executing state and log history trace for a single agent."""

    def __init__(self, agent_name: str, session_id: str) -> None:
        self.agent_name = agent_name
        self.session_id = session_id
        self.status = "IDLE"  # IDLE, RUNNING, COMPLETED, FAILED
        self.logs: List[str] = []
        self.start_time = 0.0

    def start(self) -> None:
        """Starts timer and sets status to RUNNING."""
        self.status = "RUNNING"
        self.start_time = time.perf_counter()
        self.log("Agent execution started.")

    def complete(self) -> None:
        """Transitions status to COMPLETED."""
        self.status = "COMPLETED"
        duration = round(time.perf_counter() - self.start_time, 4)
        self.log(f"Agent execution completed in {duration}s.")

    def fail(self, error: str) -> None:
        """Transitions status to FAILED, logging details."""
        self.status = "FAILED"
        self.log(f"Agent execution crashed: {error}")

    def log(self, message: str) -> None:
        """Saves trace logs."""
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {message}")
