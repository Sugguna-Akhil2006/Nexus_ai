import threading
from typing import Dict, List, Set, Any, Optional
import uuid

from core.base import BaseAgent, AgentStatus
from core.exceptions import (
    AgentRegistrationError,
    AgentNotFoundError,
)


class AgentRegistry:
    """Thread-safe Singleton registry for managing AI Agent lifecycles.

    This registry coordinates registration, unregistration, health monitoring,
    and capability-based indexing of AI agents. It uses internal dictionaries
    for O(1) lookups and enforces thread safety.
    """
    _instance: Optional["AgentRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "AgentRegistry":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self._agents: Dict[uuid.UUID, BaseAgent] = {}
            self._name_to_id: Dict[str, uuid.UUID] = {}
            self._capability_to_ids: Dict[str, Set[uuid.UUID]] = {}
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def validate(self, agent: BaseAgent) -> None:
        """Validates that the object is a valid BaseAgent instance with required fields.

        Args:
            agent: The agent instance to validate.

        Raises:
            AgentRegistrationError: If the agent validation fails.
        """
        if not isinstance(agent, BaseAgent):
            raise AgentRegistrationError(
                "Invalid agent type. Object must be an instance of BaseAgent."
            )
        if not agent.id:
            raise AgentRegistrationError("Agent must have a valid UUID ID.")
        if not agent.name or not agent.name.strip():
            raise AgentRegistrationError("Agent must have a non-empty name.")

    def register(self, agent: BaseAgent) -> None:
        """Registers a BaseAgent instance into the registry.

        Args:
            agent: The BaseAgent instance to register.

        Raises:
            AgentRegistrationError: If validation fails or duplicate ID/name exists.
        """
        self.validate(agent)

        with self._lock:
            if agent.id in self._agents:
                raise AgentRegistrationError(
                    f"Agent registration failed. ID '{agent.id}' is already registered."
                )
            if agent.name in self._name_to_id:
                raise AgentRegistrationError(
                    f"Agent registration failed. Name '{agent.name}' is already registered."
                )

            self._agents[agent.id] = agent
            self._name_to_id[agent.name] = agent.id

            for capability in agent.capabilities:
                if capability not in self._capability_to_ids:
                    self._capability_to_ids[capability] = set()
                self._capability_to_ids[capability].add(agent.id)

    def unregister(self, agent_id: uuid.UUID) -> None:
        """Unregisters an agent by its unique identifier.

        Args:
            agent_id: The UUID of the agent to unregister.

        Raises:
            AgentNotFoundError: If the agent is not found in the registry.
        """
        with self._lock:
            if agent_id not in self._agents:
                raise AgentNotFoundError(
                    f"Unregistration failed. Agent with ID '{agent_id}' not found."
                )

            agent = self._agents[agent_id]

            # Remove from capabilities index
            for capability in agent.capabilities:
                if capability in self._capability_to_ids:
                    self._capability_to_ids[capability].discard(agent_id)
                    if not self._capability_to_ids[capability]:
                        del self._capability_to_ids[capability]

            # Remove from name index
            if agent.name in self._name_to_id:
                del self._name_to_id[agent.name]

            # Remove from main agents registry
            del self._agents[agent_id]

    def get(self, agent_id: uuid.UUID) -> BaseAgent:
        """Retrieves an agent from the registry by its UUID.

        Args:
            agent_id: The UUID of the agent.

        Returns:
            BaseAgent: The registered agent instance.

        Raises:
            AgentNotFoundError: If the agent is not found in the registry.
        """
        with self._lock:
            if agent_id not in self._agents:
                raise AgentNotFoundError(f"Agent with ID '{agent_id}' not found.")
            return self._agents[agent_id]

    def get_by_name(self, name: str) -> BaseAgent:
        """Retrieves an agent from the registry by its name.

        Args:
            name: The name of the agent.

        Returns:
            BaseAgent: The registered agent instance.

        Raises:
            AgentNotFoundError: If the agent is not found in the registry.
        """
        with self._lock:
            if name not in self._name_to_id:
                raise AgentNotFoundError(f"Agent with name '{name}' not found.")
            return self._agents[self._name_to_id[name]]

    def exists(self, agent_id: uuid.UUID) -> bool:
        """Checks if an agent exists in the registry.

        Args:
            agent_id: The UUID of the agent.

        Returns:
            bool: True if the agent is registered, False otherwise.
        """
        with self._lock:
            return agent_id in self._agents

    def list_agents(self) -> List[BaseAgent]:
        """Lists all registered agents.

        Returns:
            List[BaseAgent]: A list of all registered agent instances.
        """
        with self._lock:
            return list(self._agents.values())

    def healthy_agents(self) -> List[BaseAgent]:
        """Retrieves all registered agents with a healthy status.

        Returns:
            List[BaseAgent]: A list of healthy agent instances.
        """
        with self._lock:
            return [
                agent for agent in self._agents.values()
                if agent.status == AgentStatus.HEALTHY
            ]

    def unhealthy_agents(self) -> List[BaseAgent]:
        """Retrieves all registered agents that do not have a healthy status.

        Returns:
            List[BaseAgent]: A list of unhealthy/degraded agent instances.
        """
        with self._lock:
            return [
                agent for agent in self._agents.values()
                if agent.status != AgentStatus.HEALTHY
            ]

    def count(self) -> int:
        """Returns the total number of registered agents.

        Returns:
            int: Number of registered agents.
        """
        with self._lock:
            return len(self._agents)

    def clear(self) -> None:
        """Clears all agents and indexes from the registry."""
        with self._lock:
            self._agents.clear()
            self._name_to_id.clear()
            self._capability_to_ids.clear()

    def get_by_capability(self, capability: str) -> List[BaseAgent]:
        """Retrieves all registered agents that possess the specified capability.

        Args:
            capability: The capability string to filter by.

        Returns:
            List[BaseAgent]: A list of agents matching the capability.
        """
        with self._lock:
            agent_ids = self._capability_to_ids.get(capability, set())
            return [self._agents[aid] for aid in agent_ids if aid in self._agents]
