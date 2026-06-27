class NexusException(Exception):
    """Base exception for Nexus AI framework."""
    pass


class AgentException(NexusException):
    """Exception raised for agent-related errors."""
    pass


class AgentInitializationError(AgentException):
    """Raised when agent initialization fails."""
    pass


class AgentStateError(AgentException):
    """Raised when an action is performed in an invalid agent state."""
    pass


class AgentExecutionError(AgentException):
    """Raised when agent execution fails."""
    pass


class TaskException(NexusException):
    """Exception raised for task-related errors."""
    pass


class TaskValidationError(TaskException):
    """Raised when task validation fails."""
    pass


class WorkflowException(NexusException):
    """Exception raised for workflow-related errors."""
    pass


class RegistryException(NexusException):
    """Base exception for registry-related errors."""
    pass


class AgentRegistrationError(RegistryException):
    """Raised when agent registration fails (e.g. duplicate UUID or name)."""
    pass


class AgentNotFoundError(RegistryException):
    """Raised when an agent is not found in the registry."""
    pass


class EventException(NexusException):
    """Base exception for all event-related errors."""
    pass


class DuplicateSubscriptionError(EventException):
    """Raised when subscribing a handler that is already subscribed."""
    pass


class SubscriptionNotFoundError(EventException):
    """Raised when trying to unsubscribe a handler that is not registered."""
    pass


class EventValidationError(EventException):
    """Raised when event validation fails."""
    pass


