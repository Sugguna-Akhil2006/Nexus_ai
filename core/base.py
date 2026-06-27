from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Self
import uuid

from core.exceptions import (
    AgentInitializationError,
    AgentStateError,
    TaskValidationError,
)
from core.memory import Memory
from core.state import State
from core.task import Task


class AgentState(Enum):
    """Lifecycle states of the AI agent."""
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZED = "INITIALIZED"
    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class AgentStatus(Enum):
    """Health status of the AI agent."""
    UNINITIALIZED = "UNINITIALIZED"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


@dataclass
class BaseAgent(ABC):
    """Abstract base class representing the foundation for all Nexus Core AI agents.

    This class manages the lifecycle, state, memory, and telemetry hooks of
    an agent, following the SOLID principles. It contains no business or AI logic,
    acting purely as a lifecycle orchestration parent class.

    Attributes:
        name: The human-readable name of the agent.
        description: A brief summary of the agent's purpose and function.
        version: Semantic versioning string of the agent.
        id: Unique identifier for the agent instance.
        created_at: Datetime stamp when the agent was instantiated.
        updated_at: Datetime stamp of the last agent state change.
        status: The health status of the agent.
        state: The lifecycle state of the agent.
        memory: The memory buffer storing context and execution history.
        metadata: Key-value metadata dictionary for customization.
        capabilities: A list of capability strings supported by this agent.
        logger: Logger instance for telemetry and logging.
    """
    name: str
    description: str
    version: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: AgentStatus = AgentStatus.UNINITIALIZED
    state: AgentState = AgentState.UNINITIALIZED
    memory: Memory = field(default_factory=Memory)
    metadata: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    logger: logging.Logger = field(init=False)

    def __post_init__(self) -> None:
        """Post-initialization to set up the agent-specific logger."""
        self.logger = logging.getLogger(f"nexus_core.agent.{self.name}.{self.id}")

    def initialize(self) -> None:
        """Initializes the agent, preparing it for task processing.

        Transitions the agent state to INITIALIZED and status to HEALTHY.

        Raises:
            AgentStateError: If the agent is not in UNINITIALIZED state.
            AgentInitializationError: If initialization fails during setup.
        """
        if self.state != AgentState.UNINITIALIZED:
            raise AgentStateError(
                f"Cannot initialize agent '{self.name}' from state {self.state.value}. "
                "Expected state: UNINITIALIZED."
            )

        try:
            self.state = AgentState.INITIALIZED
            self.status = AgentStatus.HEALTHY
            self.updated_at = datetime.utcnow()
            self.logger.info("Agent '%s' (%s) initialized successfully.", self.name, self.id)
            # Move immediately to IDLE to indicate readiness
            self.state = AgentState.IDLE
        except Exception as e:
            self.handle_error(e)
            raise AgentInitializationError(
                f"Failed to initialize agent '{self.name}': {e}"
            ) from e

    def validate_task(self, task: Task) -> None:
        """Validates that the given task is formatted correctly and executable.

        Args:
            task: The task instance to validate.

        Raises:
            TaskValidationError: If the task fails criteria checks.
            AgentStateError: If the agent is not currently IDLE.
        """
        if self.state != AgentState.IDLE:
            raise AgentStateError(
                f"Cannot validate task in state {self.state.value}. "
                "Agent must be IDLE."
            )

        if not task:
            raise TaskValidationError("Task instance cannot be None.")

        if not hasattr(task, "description") or not task.description.strip():
            raise TaskValidationError("Task must have a non-empty description.")

    def before_execute(self, task: Task) -> None:
        """Lifecycle hook executed immediately before running a task.

        Transitions state to BUSY.

        Args:
            task: The task that is about to be executed.

        Raises:
            AgentStateError: If the agent is not currently IDLE.
        """
        if self.state != AgentState.IDLE:
            raise AgentStateError(
                f"Cannot start task execution in state {self.state.value}. "
                "Agent must be IDLE."
            )

        self.state = AgentState.BUSY
        self.updated_at = datetime.utcnow()
        self.logger.info("Agent '%s' started executing task: %s", self.name, task.task_id)

    @abstractmethod
    def execute(self, task: Task) -> Any:
        """Abstract method representing core execution logic of the agent.

        Subclasses must implement this method.

        Args:
            task: The task to be executed.

        Returns:
            Any: The execution result.

        Raises:
            AgentExecutionError: If execution fails.
        """
        pass

    def after_execute(self, result: Any) -> Any:
        """Lifecycle hook executed immediately after successful task execution.

        Transitions state back to IDLE.

        Args:
            result: The result payload returned by the execute method.

        Returns:
            Any: The returned result, unmodified or post-processed.
        """
        self.state = AgentState.IDLE
        self.updated_at = datetime.utcnow()
        self.logger.info("Agent '%s' successfully completed task execution.", self.name)
        return result

    def handle_error(self, exception: Exception) -> None:
        """Lifecycle hook called when an exception is encountered.

        Transitions state to ERROR and status to UNHEALTHY.

        Args:
            exception: The exception object that was raised.
        """
        self.state = AgentState.ERROR
        self.status = AgentStatus.UNHEALTHY
        self.updated_at = datetime.utcnow()
        self.logger.error(
            "Agent '%s' encountered an error: %s",
            self.name,
            str(exception),
            exc_info=True
        )

    def shutdown(self) -> None:
        """Lifecycle hook to clean up resources and gracefully shut down the agent.

        Transitions state to SHUTDOWN.
        """
        if self.state == AgentState.SHUTDOWN:
            self.logger.warning("Agent '%s' is already shut down.", self.name)
            return

        self.state = AgentState.SHUTDOWN
        self.updated_at = datetime.utcnow()
        self.logger.info("Agent '%s' has shut down.", self.name)

    def health_check(self) -> Dict[str, Any]:
        """Provides diagnostic information regarding the agent's health and state.

        Returns:
            Dict[str, Any]: Health metrics including status, state, and timestamps.
        """
        return {
            "agent_id": str(self.id),
            "name": self.name,
            "status": self.status.value,
            "state": self.state.value,
            "updated_at": self.updated_at.isoformat(),
            "capabilities": self.capabilities,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the agent state and metadata attributes to a dictionary.

        Returns:
            Dict[str, Any]: Serializable representation of the agent.
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "state": self.state.value,
            "metadata": self.metadata.copy(),
            "capabilities": list(self.capabilities),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """Instantiates a concrete agent from its serialized representation.

        Args:
            data: Dictionary containing serialized agent values.

        Returns:
            BaseAgent: An instance of the concrete subclass.

        Raises:
            KeyError: If mandatory keys are missing from the data.
            ValueError: If datetime or uuid formatting is incorrect.
        """
        instance = cls(
            name=data["name"],
            description=data["description"],
            version=data["version"],
            metadata=data.get("metadata", {}).copy(),
            capabilities=list(data.get("capabilities", [])),
        )

        if "id" in data:
            instance.id = uuid.UUID(data["id"])
        if "created_at" in data:
            instance.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            instance.updated_at = datetime.fromisoformat(data["updated_at"])
        if "status" in data:
            instance.status = AgentStatus(data["status"])
        if "state" in data:
            instance.state = AgentState(data["state"])

        return instance
