"""ADK data models defining agent configs, workflow steps, and tool definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class WorkflowStepType(Enum):
    """Supported workflow step execution modes."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"


class RetryPolicy(Enum):
    """Retry strategy modes."""

    NONE = "none"
    FIXED = "fixed"
    EXPONENTIAL = "exponential"


@dataclass
class ToolDefinition:
    """Describes a callable tool exposed to an agent.

    Attributes:
        name: Unique tool identifier.
        description: Human-readable tool purpose.
        fn: The callable function implementing the tool.
        parameters: Parameter schema hints.
    """

    name: str
    description: str
    fn: Callable[..., Any]
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """A single step inside an ADK workflow.

    Attributes:
        name: Step label.
        step_type: Execution mode (sequential, parallel, conditional, loop).
        tool_name: Name of the tool to invoke (optional).
        condition: Callable returning bool for conditional steps.
        loop_count: Number of iterations for loop steps.
        timeout_seconds: Max allowed execution seconds.
        retry_policy: Retry strategy to apply on failure.
        max_retries: Max retry attempts.
    """

    name: str
    step_type: WorkflowStepType = WorkflowStepType.SEQUENTIAL
    tool_name: Optional[str] = None
    condition: Optional[Callable[..., bool]] = None
    loop_count: int = 1
    timeout_seconds: float = 30.0
    retry_policy: RetryPolicy = RetryPolicy.NONE
    max_retries: int = 0


@dataclass
class PromptTemplate:
    """A versioned prompt template supporting variable substitution.

    Attributes:
        name: Template identifier.
        version: Template semantic version.
        template: Raw template string with ``{variable}`` placeholders.
        variables: Expected variable names.
    """

    name: str
    version: str
    template: str
    variables: List[str] = field(default_factory=list)

    def render(self, **kwargs: Any) -> str:
        """Renders the template substituting provided variables.

        Args:
            **kwargs: Variable name/value pairs.

        Returns:
            Rendered string.

        Raises:
            KeyError: If a required variable is missing.
        """
        missing = [v for v in self.variables if v not in kwargs]
        if missing:
            raise KeyError(f"Missing prompt variables: {missing}")
        return self.template.format(**kwargs)


@dataclass
class AgentConfig:
    """Complete agent configuration produced by AgentBuilder.

    Attributes:
        name: Agent name.
        description: Agent purpose description.
        version: Semantic version.
        model_id: LLM model identifier.
        tools: List of registered tool definitions.
        workflow_steps: Ordered workflow steps.
        memory_backend: Memory backend type identifier.
        provider_id: LLM provider identifier.
        system_prompt: Optional system prompt template name.
        metadata: Arbitrary key/value metadata.
    """

    name: str
    description: str
    version: str = "1.0.0"
    model_id: str = "gpt-4"
    tools: List[ToolDefinition] = field(default_factory=list)
    workflow_steps: List[WorkflowStep] = field(default_factory=list)
    memory_backend: str = "in_memory"
    provider_id: str = "openai"
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
