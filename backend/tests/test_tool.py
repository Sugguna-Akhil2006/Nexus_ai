import concurrent.futures
import threading
import time
from typing import Any, Dict, List, Optional
import unittest
import uuid

from backend.tools.tool import (
    ToolError,
    ToolValidationError,
    ToolPermissionError,
    ToolNotFoundError,
    ToolTimeoutError,
    ToolCategory,
    ToolMetadata,
    ToolRequest,
    ToolResponse,
    Tool,
    ToolPermissionEvaluator,
    DefaultToolPermissionEvaluator,
    ToolRegistry,
    ToolExecutor,
    ToolDiscovery,
    MockSearchTool,
    MockCalculatorTool,
)
from backend.runtime.event import Event, EventBus, EventType


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestToolSystem(unittest.TestCase):
    """Suite of tests covering the pluggable Tool Framework capability execution layer."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.registry = ToolRegistry()
        with self.registry._lock:
            self.registry._tools.clear()

        self.search_tool = MockSearchTool()
        self.calc_tool = MockCalculatorTool()

        self.registry.register_tool(self.search_tool)
        self.registry.register_tool(self.calc_tool)

        self.executor = ToolExecutor(registry=self.registry)

    def test_schema_validations(self) -> None:
        """Verifies lightweight schema type validators enforce input formats."""
        # 1. Correct Search inputs
        self.search_tool.validate_input({"query": "nexus artificial intelligence", "limit": 3})

        # 2. Missing query field
        with self.assertRaises(ToolValidationError):
            self.search_tool.validate_input({"limit": 5})

        # 3. Mismatched query parameter type
        with self.assertRaises(ToolValidationError):
            self.search_tool.validate_input({"query": 12345})

        # 4. Calculator array type validation
        self.calc_tool.validate_input({"numbers": [1, 2.5, 3]})
        with self.assertRaises(ToolValidationError):
            self.calc_tool.validate_input({"numbers": "not an array"})
        with self.assertRaises(ToolValidationError):
            self.calc_tool.validate_input({"numbers": [1, "two", 3]})

    def test_registry_singleton(self) -> None:
        """Verifies singleton pattern constraints of ToolRegistry."""
        registry2 = ToolRegistry()
        self.assertIs(self.registry, registry2)

    def test_registry_lifecycle(self) -> None:
        """Verifies tool register and unregister constraints on ToolRegistry."""
        with self.assertRaises(ToolValidationError):
            self.registry.register_tool(None)  # type: ignore

        # Register duplicate tool check
        with self.assertRaises(ToolValidationError):
            self.registry.register_tool(self.search_tool)

        # Retrieve
        fetched = self.registry.get_tool("mock_search_tool")
        self.assertIs(fetched, self.search_tool)

        # List category
        search_tools = self.registry.find_by_category(ToolCategory.SEARCH)
        self.assertEqual(len(search_tools), 1)
        self.assertIs(search_tools[0], self.search_tool)

        # Unregister
        self.registry.unregister_tool("mock_search_tool")
        self.assertNotIn("mock_search_tool", [t.schema.tool_id for t in self.registry.list_tools()])

    def test_permission_evaluator(self) -> None:
        """Verifies default permissions evaluator verifies user permission scope tags."""
        # Mock search tool requires "use_search" permission
        req_allowed = ToolRequest(
            request_id="req_1",
            tool_id="mock_search_tool",
            workspace_id="ws_1",
            user_id="user_allowed",
            arguments={"query": "test"},
            metadata={"user_permissions": ["use_search", "read_docs"]}
        )
        res_allowed = self.executor.execute(req_allowed)
        self.assertTrue(res_allowed.success)

        # Missing permission
        req_denied = ToolRequest(
            request_id="req_2",
            tool_id="mock_search_tool",
            workspace_id="ws_1",
            user_id="user_denied",
            arguments={"query": "test"},
            metadata={"user_permissions": ["read_docs"]}
        )
        with self.assertRaises(ToolPermissionError):
            self.executor.execute(req_denied)

        # Verify EventBus event emitted for denial
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("tool.permission.denied", events)

    def test_executor_successful_run(self) -> None:
        """Verifies successful executor runs record timing metrics and outputs."""
        req = ToolRequest(
            request_id="req_calc",
            tool_id="mock_calc_tool",
            workspace_id="ws_1",
            user_id="user_1",
            arguments={"numbers": [10.5, 20.0, 5.5]}
        )
        res = self.executor.execute(req)

        self.assertTrue(res.success)
        self.assertEqual(res.output, 36.0)
        self.assertGreater(res.execution_time, 0.0)

        # EventBus executed verified
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("tool.executed", events)

    def test_executor_error_handling(self) -> None:
        """Verifies executor captures execution crashes, timeouts, and unknown tool errors."""
        # Unknown tool
        req_unknown = ToolRequest("r", "non_existent_tool", "ws", "u", {})
        with self.assertRaises(ToolNotFoundError):
            self.executor.execute(req_unknown)

        # Timeout validation (timeout_seconds <= 0.0)
        req_timeout = ToolRequest(
            request_id="r_time",
            tool_id="mock_calc_tool",
            workspace_id="ws_1",
            user_id="user_1",
            arguments={"numbers": [1]},
            metadata={"timeout_seconds": 0.0}
        )
        with self.assertRaises(ToolTimeoutError):
            self.executor.execute(req_timeout)

        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("tool.timeout", events)

    def test_tool_discovery(self) -> None:
        """Verifies ToolDiscovery fetches local tools catalog details."""
        discovery = ToolDiscovery(registry=self.registry)
        local_tools = discovery.discover_local()
        self.assertEqual(len(local_tools), 2)

        plugin_tools = discovery.discover_plugins()
        self.assertEqual(len(plugin_tools), 2)

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent registrations and lookups operate safely."""
        def run_thread(tid: int) -> None:
            class DummyTool(Tool):
                @property
                def name(self): return f"dummy-{tid}"
                @property
                def description(self): return "desc"
                @property
                def schema(self):
                    return ToolMetadata(
                        tool_id=f"dummy-{tid}",
                        name=self.name,
                        version="1.0",
                        author="System",
                        description="desc",
                        category=ToolCategory.CUSTOM,
                        permissions=[],
                        input_schema={},
                        output_schema={}
                    )
                def execute(self, request): return None
                def validate_input(self, arguments): pass
                def validate_output(self, output): pass
                def health_check(self): return True

            t = DummyTool()
            self.registry.register_tool(t)
            self.assertIs(self.registry.get_tool(f"dummy-{tid}"), t)
            self.registry.unregister_tool(f"dummy-{tid}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
