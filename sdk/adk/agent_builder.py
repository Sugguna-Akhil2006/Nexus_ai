"""AgentBuilder - fluent API for constructing production-grade Nexus AI agents."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from sdk.adk.models import AgentConfig, ToolDefinition, WorkflowStep


class AgentBuilder:
    """Fluent builder API for composing agent configurations.

    Example::

        agent = (
            AgentBuilder()
            .name("Resume Agent")
            .description("Analyzes and optimizes resumes.")
            .model("gpt-4")
            .provider("openai")
            .tool("search_docs", search_docs_fn, "Searches documentation")
            .memory("in_memory")
            .version("1.0.0")
            .build()
        )
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._description: str = ""
        self._version: str = "1.0.0"
        self._model_id: str = "gpt-4"
        self._provider_id: str = "openai"
        self._tools: List[ToolDefinition] = []
        self._workflow_steps: List[WorkflowStep] = []
        self._memory_backend: str = "in_memory"
        self._system_prompt: Optional[str] = None
        self._metadata: Dict[str, Any] = {}

    def name(self, agent_name: str) -> "AgentBuilder":
        """Sets the agent's display name.

        Args:
            agent_name: Human-readable name string.

        Returns:
            Self for method chaining.
        """
        self._name = agent_name
        return self

    def description(self, agent_description: str) -> "AgentBuilder":
        """Sets the agent's purpose description.

        Args:
            agent_description: Descriptive text string.

        Returns:
            Self for method chaining.
        """
        self._description = agent_description
        return self

    def version(self, semver: str) -> "AgentBuilder":
        """Sets the agent semantic version.

        Args:
            semver: Semantic version string (e.g. ``"1.0.0"``).

        Returns:
            Self for method chaining.
        """
        self._version = semver
        return self

    def model(self, model_id: str) -> "AgentBuilder":
        """Sets the LLM model identifier.

        Args:
            model_id: Model identifier string (e.g. ``"gpt-4"``).

        Returns:
            Self for method chaining.
        """
        self._model_id = model_id
        return self

    def provider(self, provider_id: str) -> "AgentBuilder":
        """Sets the LLM provider identifier.

        Args:
            provider_id: Provider string (e.g. ``"openai"``, ``"gemini"``).

        Returns:
            Self for method chaining.
        """
        self._provider_id = provider_id
        return self

    def tool(
        self,
        name: str,
        fn: Callable[..., Any],
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> "AgentBuilder":
        """Registers a callable tool with the agent.

        Args:
            name: Unique tool name.
            fn: Tool callable.
            description: Short description of the tool.
            parameters: Parameter schema hints.

        Returns:
            Self for method chaining.
        """
        self._tools.append(
            ToolDefinition(
                name=name,
                description=description,
                fn=fn,
                parameters=parameters or {},
            )
        )
        return self

    def memory(self, backend: str = "in_memory") -> "AgentBuilder":
        """Sets the memory backend type.

        Args:
            backend: Backend identifier (``"in_memory"``, ``"redis"``, ``"sqlite"``).

        Returns:
            Self for method chaining.
        """
        self._memory_backend = backend
        return self

    def workflow(self, step: WorkflowStep) -> "AgentBuilder":
        """Appends a workflow step to the agent execution plan.

        Args:
            step: Configured WorkflowStep instance.

        Returns:
            Self for method chaining.
        """
        self._workflow_steps.append(step)
        return self

    def system_prompt(self, prompt_template_name: str) -> "AgentBuilder":
        """Attaches a named system prompt template.

        Args:
            prompt_template_name: Registered prompt template name.

        Returns:
            Self for method chaining.
        """
        self._system_prompt = prompt_template_name
        return self

    def metadata(self, **kwargs: Any) -> "AgentBuilder":
        """Merges arbitrary key/value metadata.

        Args:
            **kwargs: Metadata key/value pairs.

        Returns:
            Self for method chaining.
        """
        self._metadata.update(kwargs)
        return self

    def build(self) -> AgentConfig:
        """Validates and constructs the final AgentConfig.

        Returns:
            Fully validated AgentConfig instance.

        Raises:
            ValueError: If required fields are missing.
        """
        if not self._name.strip():
            raise ValueError("Agent name is required.")
        if not self._description.strip():
            raise ValueError("Agent description is required.")

        return AgentConfig(
            name=self._name,
            description=self._description,
            version=self._version,
            model_id=self._model_id,
            provider_id=self._provider_id,
            tools=list(self._tools),
            workflow_steps=list(self._workflow_steps),
            memory_backend=self._memory_backend,
            system_prompt=self._system_prompt,
            metadata=dict(self._metadata),
        )
