"""AgentTester - local test runner with mock provider support for ADK agents."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from unittest.mock import MagicMock

from sdk.adk.models import AgentConfig, ToolDefinition


class MockProvider:
    """Simulates an LLM provider response for local testing.

    Attributes:
        response: Fixed response returned for all inference calls.
        call_count: Number of times the provider was called.
    """

    def __init__(self, response: str = "mock_response") -> None:
        self.response = response
        self.call_count: int = 0
        self.calls: List[Dict[str, Any]] = []

    def infer(self, prompt: str, **kwargs: Any) -> str:
        """Simulates model inference.

        Args:
            prompt: Input prompt string.
            **kwargs: Additional inference parameters.

        Returns:
            Configured mock response string.
        """
        self.call_count += 1
        self.calls.append({"prompt": prompt, **kwargs})
        return self.response

    def reset(self) -> None:
        """Resets call tracking state."""
        self.call_count = 0
        self.calls.clear()


class AgentTester:
    """Local agent test runner enabling dry-run and mock provider execution.

    Example::

        tester = AgentTester(agent_config)
        tester.mock_provider(response="Test response")
        result = tester.run({"task": "analyze resume"})
        assert result["status"] == "success"
    """

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._mock_provider: Optional[MockProvider] = None
        self._tool_overrides: Dict[str, Callable[..., Any]] = {}
        self._execution_trace: List[Dict[str, Any]] = []

    def mock_provider(self, response: str = "mock_response") -> "AgentTester":
        """Installs a mock LLM provider.

        Args:
            response: Fixed string returned by mock inference.

        Returns:
            Self for method chaining.
        """
        self._mock_provider = MockProvider(response=response)
        return self

    def override_tool(self, tool_name: str, fn: Callable[..., Any]) -> "AgentTester":
        """Replaces a tool implementation with a custom callable for testing.

        Args:
            tool_name: Name of the tool to override.
            fn: Replacement callable.

        Returns:
            Self for method chaining.
        """
        self._tool_overrides[tool_name] = fn
        return self

    def run(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes the agent in local test mode.

        Runs each registered tool in sequence using mock or overridden callables.

        Args:
            context: Optional execution context dictionary.

        Returns:
            Dict containing ``status``, ``results``, and ``trace``.
        """
        ctx = context or {}
        results: Dict[str, Any] = {}
        self._execution_trace = []

        for tool_def in self.config.tools:
            fn = self._tool_overrides.get(tool_def.name, tool_def.fn)
            try:
                result = fn(ctx)
                results[tool_def.name] = result
                self._execution_trace.append({
                    "tool": tool_def.name,
                    "status": "success",
                    "result": result,
                })
            except Exception as exc:
                results[tool_def.name] = {"error": str(exc)}
                self._execution_trace.append({
                    "tool": tool_def.name,
                    "status": "error",
                    "error": str(exc),
                })

        # Simulate provider call if mock is installed
        if self._mock_provider:
            system_prompt = self.config.system_prompt or "You are a helpful assistant."
            provider_result = self._mock_provider.infer(system_prompt, context=ctx)
            results["__provider__"] = provider_result

        return {
            "status": "success",
            "agent": self.config.name,
            "results": results,
            "trace": self._execution_trace,
        }

    def replay(self, trace: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Replays a previous execution trace for debugging.

        Args:
            trace: List of trace step dictionaries from a previous run.

        Returns:
            Replay report dictionary.
        """
        return {
            "status": "replayed",
            "steps": len(trace),
            "trace": trace,
        }

    @property
    def execution_trace(self) -> List[Dict[str, Any]]:
        """Returns the execution trace from the last run."""
        return list(self._execution_trace)

    @property
    def mock_provider_calls(self) -> int:
        """Returns the number of mock provider calls in the last run."""
        return self._mock_provider.call_count if self._mock_provider else 0
