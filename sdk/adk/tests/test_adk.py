"""Comprehensive unit tests for the Nexus ADK."""

from __future__ import annotations

import concurrent.futures
import os
import tempfile
import unittest

from sdk.adk.agent_builder import AgentBuilder
from sdk.adk.agent_packager import AgentPackager
from sdk.adk.agent_tester import AgentTester
from sdk.adk.memory_builder import MemoryBuilder
from sdk.adk.models import RetryPolicy, WorkflowStepType
from sdk.adk.plugin_builder import PluginBuilder
from sdk.adk.project_template import ProjectTemplate
from sdk.adk.prompt_builder import PromptBuilder
from sdk.adk.provider_builder import ProviderBuilder
from sdk.adk.tool_builder import ToolRegistry, tool
from sdk.adk.workflow_builder import WorkflowBuilder


class TestAgentBuilder(unittest.TestCase):
    """Tests for the fluent AgentBuilder API."""

    def test_build_minimal_agent(self) -> None:
        config = (
            AgentBuilder()
            .name("Test Agent")
            .description("A test agent.")
            .build()
        )
        self.assertEqual(config.name, "Test Agent")
        self.assertEqual(config.description, "A test agent.")
        self.assertEqual(config.version, "1.0.0")

    def test_build_full_agent(self) -> None:
        def my_tool(ctx: dict) -> str:
            return "hello"

        config = (
            AgentBuilder()
            .name("Full Agent")
            .description("Full configuration agent.")
            .version("2.0.0")
            .model("claude-3-opus")
            .provider("anthropic")
            .tool("greet", my_tool, "Says hello")
            .memory("sqlite")
            .system_prompt("greeting_prompt")
            .metadata(env="test", region="us-east-1")
            .build()
        )
        self.assertEqual(config.model_id, "claude-3-opus")
        self.assertEqual(config.provider_id, "anthropic")
        self.assertEqual(len(config.tools), 1)
        self.assertEqual(config.tools[0].name, "greet")
        self.assertEqual(config.memory_backend, "sqlite")
        self.assertEqual(config.system_prompt, "greeting_prompt")
        self.assertEqual(config.metadata["env"], "test")

    def test_build_raises_without_name(self) -> None:
        with self.assertRaises(ValueError):
            AgentBuilder().description("desc").build()

    def test_build_raises_without_description(self) -> None:
        with self.assertRaises(ValueError):
            AgentBuilder().name("agent").build()


class TestWorkflowBuilder(unittest.TestCase):
    """Tests for WorkflowBuilder step types."""

    def test_sequential_step_executes(self) -> None:
        results = []

        def step_fn(ctx: dict) -> str:
            results.append("ran")
            return "done"

        builder = WorkflowBuilder().sequential("step1", step_fn)
        output = builder.execute()
        self.assertEqual(output["step1"], "done")
        self.assertEqual(results, ["ran"])

    def test_parallel_step_executes_concurrently(self) -> None:
        call_log = []

        def fn_a(ctx: dict) -> str:
            call_log.append("a")
            return "a"

        def fn_b(ctx: dict) -> str:
            call_log.append("b")
            return "b"

        builder = WorkflowBuilder().parallel("par", [fn_a, fn_b])
        output = builder.execute()
        self.assertIn("par", output)
        self.assertEqual(sorted(output["par"]), ["a", "b"])

    def test_conditional_step_skipped(self) -> None:
        called = []

        def cond_fn(ctx: dict) -> str:
            called.append("ran")
            return "result"

        builder = WorkflowBuilder().conditional(
            "cond", cond_fn, condition=lambda ctx: False
        )
        output = builder.execute()
        self.assertEqual(output["cond"], "skipped")
        self.assertEqual(called, [])

    def test_conditional_step_runs_when_true(self) -> None:
        def cond_fn(ctx: dict) -> str:
            return "passed"

        builder = WorkflowBuilder().conditional(
            "cond", cond_fn, condition=lambda ctx: True
        )
        output = builder.execute()
        self.assertEqual(output["cond"], "passed")

    def test_loop_step_iterates(self) -> None:
        counter = []

        def loop_fn(ctx: dict) -> int:
            counter.append(1)
            return len(counter)

        builder = WorkflowBuilder().loop("looper", loop_fn, loop_count=4)
        output = builder.execute()
        self.assertEqual(len(output["looper"]), 4)

    def test_retry_on_failure(self) -> None:
        attempts = []

        def flaky_fn(ctx: dict) -> str:
            attempts.append(1)
            if len(attempts) < 3:
                raise RuntimeError("temporary error")
            return "recovered"

        builder = WorkflowBuilder().sequential(
            "flaky",
            flaky_fn,
            retry_policy=RetryPolicy.FIXED,
            max_retries=3,
        )
        output = builder.execute()
        self.assertEqual(output["flaky"], "recovered")


class TestToolBuilder(unittest.TestCase):
    """Tests for the @tool decorator and ToolRegistry."""

    def setUp(self) -> None:
        ToolRegistry().clear()

    def test_tool_decorator_registers(self) -> None:
        @tool(description="A test tool")
        def my_search(ctx: dict) -> str:
            return "search result"

        registered = ToolRegistry().get("my_search")
        self.assertIsNotNone(registered)
        self.assertEqual(registered.description, "A test tool")

    def test_tool_decorator_bare(self) -> None:
        @tool
        def bare_tool(ctx: dict) -> str:
            """Bare tool docstring."""
            return "bare"

        registered = ToolRegistry().get("bare_tool")
        self.assertIsNotNone(registered)

    def test_tool_invocation_works(self) -> None:
        @tool(name="adder", description="Adds numbers")
        def add(ctx: dict) -> int:
            return ctx.get("a", 0) + ctx.get("b", 0)

        result = add({"a": 3, "b": 4})
        self.assertEqual(result, 7)


class TestPromptBuilder(unittest.TestCase):
    """Tests for PromptBuilder template construction and rendering."""

    def test_build_and_render(self) -> None:
        prompt = (
            PromptBuilder()
            .name("greeting")
            .template("Hello {name}, welcome to {platform}!")
            .build()
        )
        rendered = prompt.render(name="Alice", platform="Nexus")
        self.assertEqual(rendered, "Hello Alice, welcome to Nexus!")

    def test_auto_variable_extraction(self) -> None:
        prompt = (
            PromptBuilder()
            .name("test")
            .template("The {color} {animal} jumped.")
            .build()
        )
        self.assertIn("color", prompt.variables)
        self.assertIn("animal", prompt.variables)

    def test_missing_variable_raises(self) -> None:
        prompt = (
            PromptBuilder()
            .name("test")
            .template("Hello {name}!")
            .build()
        )
        with self.assertRaises(KeyError):
            prompt.render(greeting="hi")

    def test_empty_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            PromptBuilder().template("Hello {name}!").build()


class TestMemoryBuilder(unittest.TestCase):
    """Tests for MemoryBuilder configuration."""

    def test_defaults(self) -> None:
        config = MemoryBuilder().build()
        self.assertEqual(config.backend, "in_memory")
        self.assertEqual(config.max_entries, 1000)
        self.assertEqual(config.ttl_seconds, 0)

    def test_custom_config(self) -> None:
        config = (
            MemoryBuilder()
            .backend("redis")
            .max_entries(500)
            .ttl(3600)
            .connection_url("redis://localhost:6379")
            .option("db", 0)
            .build()
        )
        self.assertEqual(config.backend, "redis")
        self.assertEqual(config.max_entries, 500)
        self.assertEqual(config.ttl_seconds, 3600)
        self.assertEqual(config.options["db"], 0)


class TestProviderBuilder(unittest.TestCase):
    """Tests for ProviderBuilder configuration."""

    def test_defaults(self) -> None:
        config = ProviderBuilder().build()
        self.assertEqual(config.provider_id, "openai")
        self.assertEqual(config.model_id, "gpt-4")
        self.assertFalse(config.streaming)

    def test_custom_provider(self) -> None:
        config = (
            ProviderBuilder()
            .provider("ollama")
            .model("phi3:mini")
            .base_url("http://localhost:11434")
            .temperature(0.3)
            .streaming(True)
            .build()
        )
        self.assertEqual(config.provider_id, "ollama")
        self.assertEqual(config.temperature, 0.3)
        self.assertTrue(config.streaming)


class TestPluginBuilder(unittest.TestCase):
    """Tests for PluginBuilder manifest scaffolding."""

    def test_build_manifest(self) -> None:
        manifest = (
            PluginBuilder()
            .name("github_plugin")
            .version("2.0.0")
            .author("Dev Team")
            .description("GitHub integration")
            .capability("github_fetch")
            .dependency("requests", ">=2.28.0")
            .entry_point("plugins.github_plugin.GitHubPlugin")
            .build()
        )
        self.assertEqual(manifest.plugin_name, "github_plugin")
        self.assertIn("github_fetch", manifest.capabilities)
        self.assertEqual(manifest.dependencies["requests"], ">=2.28.0")

    def test_empty_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            PluginBuilder().build()

    def test_scaffold_files(self) -> None:
        files = PluginBuilder().name("my_plugin").description("test").scaffold_files()
        self.assertIn("my_plugin.py", files)
        self.assertIn("MyPlugin", files["my_plugin.py"])


class TestProjectTemplate(unittest.TestCase):
    """Tests for ProjectTemplate scaffold generation."""

    def test_generate_agent_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpl = ProjectTemplate()
            files = tmpl.generate("agent", "test_agent", tmpdir)
            self.assertIn("test_agent/agent.py", files)
            self.assertIn("test_agent/README.md", files)
            # Verify files exist on disk
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "test_agent", "agent.py")))

    def test_generate_workflow_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpl = ProjectTemplate()
            files = tmpl.generate("workflow", "my_workflow", tmpdir)
            self.assertIn("my_workflow/workflow.py", files)

    def test_invalid_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            ProjectTemplate().generate("invalid_type", "test", ".")


class TestAgentTester(unittest.TestCase):
    """Tests for AgentTester local execution and mock provider."""

    def _make_agent(self) -> AgentBuilder:
        def greet_fn(ctx: dict) -> str:
            return "Hello!"

        return (
            AgentBuilder()
            .name("Test Bot")
            .description("A test bot.")
            .tool("greet", greet_fn, "Greets the user")
        )

    def test_run_with_mock_provider(self) -> None:
        config = self._make_agent().build()
        tester = AgentTester(config)
        tester.mock_provider(response="mock LLM output")
        result = tester.run()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results"]["greet"], "Hello!")
        self.assertEqual(result["results"]["__provider__"], "mock LLM output")
        self.assertEqual(tester.mock_provider_calls, 1)

    def test_tool_override(self) -> None:
        config = self._make_agent().build()
        tester = AgentTester(config)
        tester.override_tool("greet", lambda ctx: "overridden!")
        result = tester.run()
        self.assertEqual(result["results"]["greet"], "overridden!")

    def test_execution_trace_captured(self) -> None:
        config = self._make_agent().build()
        tester = AgentTester(config)
        tester.run()
        trace = tester.execution_trace
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]["tool"], "greet")
        self.assertEqual(trace[0]["status"], "success")

    def test_replay_returns_trace(self) -> None:
        config = self._make_agent().build()
        tester = AgentTester(config)
        tester.run()
        trace = tester.execution_trace
        replay = tester.replay(trace)
        self.assertEqual(replay["status"], "replayed")
        self.assertEqual(replay["steps"], 1)


class TestAgentPackager(unittest.TestCase):
    """Tests for AgentPackager archive creation and inspection."""

    def _make_agent_config(self) -> "AgentConfig":  # type: ignore[name-defined]
        return (
            AgentBuilder()
            .name("PackageBot")
            .description("An agent to package.")
            .version("1.2.3")
            .build()
        )

    def test_package_creates_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_agent_config()
            packager = AgentPackager()
            archive_path = packager.package(config, output_dir=tmpdir)
            self.assertTrue(os.path.exists(archive_path))
            self.assertTrue(archive_path.endswith(".nxpkg"))

    def test_inspect_reads_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_agent_config()
            packager = AgentPackager()
            archive_path = packager.package(config, output_dir=tmpdir)
            manifest = packager.inspect(archive_path)
            self.assertEqual(manifest.agent_name, "PackageBot")
            self.assertEqual(manifest.version, "1.2.3")

    def test_list_packages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_agent_config()
            packager = AgentPackager()
            packager.package(config, output_dir=tmpdir)
            packages = packager.list_packages(search_dir=tmpdir)
            self.assertEqual(len(packages), 1)

    def test_inspect_nonexistent_raises(self) -> None:
        packager = AgentPackager()
        with self.assertRaises(FileNotFoundError):
            packager.inspect("/nonexistent/path.nxpkg")


class TestConcurrentToolRegistry(unittest.TestCase):
    """Concurrent safety tests for the ToolRegistry."""

    def setUp(self) -> None:
        ToolRegistry().clear()

    def test_concurrent_registrations(self) -> None:
        registry = ToolRegistry()
        errors = []

        def register_tool(index: int) -> None:
            from sdk.adk.models import ToolDefinition
            try:
                registry.register(ToolDefinition(
                    name=f"tool_{index}",
                    description=f"Tool {index}",
                    fn=lambda ctx: index,
                ))
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(register_tool, i) for i in range(20)]
            concurrent.futures.wait(futures)

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(registry.list_tools()), 20)


if __name__ == "__main__":
    unittest.main()
