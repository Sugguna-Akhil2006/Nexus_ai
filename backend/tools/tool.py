"""Tool Framework and Pluggable Capability Execution Layer Module.

Provides abstractions, registries, schema validators, executors,
and mock tools for executable capabilities run independently of agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import datetime
from enum import Enum
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from backend.runtime.logger import StructuredLogger


# =====================================================================
# Exceptions
# =====================================================================

class ToolError(NexusException):
    """Base exception for all Tool Framework related errors."""
    pass


class ToolValidationError(ToolError):
    """Raised when request arguments validation or schemas verification fails."""
    pass


class ToolPermissionError(ToolError):
    """Raised when user/agent does not have sufficient permission to execute tool."""
    pass


class ToolNotFoundError(ToolError):
    """Raised when requested tool is not found in registries."""
    pass


class ToolTimeoutError(ToolError):
    """Raised when tool execution exceeds timeout bounds."""
    pass


# =====================================================================
# Enums and Data Models
# =====================================================================

class ToolCategory(Enum):
    """Supported tool logical categories classification."""
    FILE = "FILE"
    SEARCH = "SEARCH"
    DOCUMENT = "DOCUMENT"
    GITHUB = "GITHUB"
    WEB = "WEB"
    DATABASE = "DATABASE"
    EMAIL = "EMAIL"
    CALENDAR = "CALENDAR"
    ANALYTICS = "ANALYTICS"
    AI = "AI"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True)
class ToolMetadata:
    """Immutable metadata schemas governing a pluggable tool.

    Attributes:
        tool_id: Unique identifier key string.
        name: Common name of the tool.
        version: Version details.
        author: Creation author name.
        description: Description text of the capability.
        category: Logical ToolCategory origin.
        permissions: List of permission key strings required to execute the tool.
        input_schema: Argument properties schema mappings.
        output_schema: Outward returns type schemas.
        metadata: Extra metrics or tags details.
    """
    tool_id: str
    name: str
    version: str
    author: str
    description: str
    category: ToolCategory
    permissions: List[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolRequest:
    """Authentication parameters defining target document parameters.

    Attributes:
        request_id: Tracking request ID.
        tool_id: Target tool ID.
        workspace_id: Target workspace context ID.
        user_id: Caller user identifier.
        arguments: Arguments dictionary to run tool.
        metadata: Extra tracking metadata.
    """
    request_id: str
    tool_id: str
    workspace_id: str
    user_id: str
    arguments: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResponse:
    """Execution outcomes packet.

    Attributes:
        response_id: Tracking response ID.
        success: True if execution finished successfully.
        output: Returns payload from tool.
        execution_time: Duration elapsed in float seconds.
        diagnostics: Debugging diagnostics details.
        metadata: Extra metadata details.
    """
    response_id: str
    success: bool
    output: Any
    execution_time: float
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Validation Utilities
# =====================================================================

def validate_schema_value(name: str, val: Any, schema_type: str) -> None:
    """Validates value data types matching standard schema models.

    Raises:
        ToolValidationError: On type mismatch.
    """
    if schema_type == "string" and not isinstance(val, str):
        raise ToolValidationError(f"Argument '{name}' must be a string, got {type(val).__name__}.")
    elif schema_type == "integer" and not isinstance(val, int):
        raise ToolValidationError(f"Argument '{name}' must be an integer, got {type(val).__name__}.")
    elif schema_type == "number" and not isinstance(val, (int, float)):
        raise ToolValidationError(f"Argument '{name}' must be a number, got {type(val).__name__}.")
    elif schema_type == "boolean" and not isinstance(val, bool):
        raise ToolValidationError(f"Argument '{name}' must be a boolean, got {type(val).__name__}.")
    elif schema_type == "array" and not isinstance(val, list):
        raise ToolValidationError(f"Argument '{name}' must be a list, got {type(val).__name__}.")
    elif schema_type == "object" and not isinstance(val, dict):
        raise ToolValidationError(f"Argument '{name}' must be a dict, got {type(val).__name__}.")


# =====================================================================
# Tool Interface ABC
# =====================================================================

class Tool(ABC):
    """Abstract Base Class specifying contracts governing pluggable executable capabilities."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Retrieves name descriptor of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Retrieves descriptive task summary of the tool."""
        pass

    @property
    @abstractmethod
    def schema(self) -> ToolMetadata:
        """Retrieves schemas metadata structure definition of the tool."""
        pass

    @abstractmethod
    def execute(self, request: ToolRequest) -> Any:
        """Executes capability task."""
        pass

    @abstractmethod
    def validate_input(self, arguments: Dict[str, Any]) -> None:
        """Verifies arguments conform to inputs schema."""
        pass

    @abstractmethod
    def validate_output(self, output: Any) -> None:
        """Verifies output conforms to outputs schema."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks connection health status."""
        pass


# =====================================================================
# Tool Permissions Evaluator
# =====================================================================

class ToolPermissionEvaluator(ABC):
    """Abstract evaluator checking execution credentials context."""

    @abstractmethod
    def evaluate(self, request: ToolRequest, metadata: ToolMetadata) -> bool:
        """Evaluates permission eligibility checks."""
        pass


class DefaultToolPermissionEvaluator(ToolPermissionEvaluator):
    """Permissions evaluator verifying required system scope tags."""

    def evaluate(self, request: ToolRequest, metadata: ToolMetadata) -> bool:
        if not metadata.permissions:
            return True
        user_perms = request.metadata.get("user_permissions", [])
        for perm in metadata.permissions:
            if perm not in user_perms:
                return False
        return True


# =====================================================================
# Tool Registry
# =====================================================================

class ToolRegistry:
    """Thread-safe singleton registry managing pluggable tools."""

    _instance: Optional["ToolRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ToolRegistry":
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
            self._tools: Dict[str, Tool] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register_tool(self, tool: Tool) -> None:
        """Registers a Tool capability."""
        if not tool:
            raise ToolValidationError("tool instance cannot be None.")
        meta = tool.schema
        if not meta or not meta.tool_id or not str(meta.tool_id).strip():
            raise ToolValidationError("Tool schema must specify a valid tool_id.")

        with self._lock:
            if meta.tool_id in self._tools:
                raise ToolValidationError(f"Tool '{meta.tool_id}' already registered.")
            self._tools[meta.tool_id] = tool
            self._logger.info(f"Registered tool capability: {meta.tool_id}")

    def unregister_tool(self, tool_id: str) -> None:
        """Removes a tool registration."""
        with self._lock:
            if tool_id not in self._tools:
                raise ToolValidationError(f"Tool '{tool_id}' not found.")
            del self._tools[tool_id]
            self._logger.info(f"Unregistered tool capability: {tool_id}")

    def get_tool(self, tool_id: str) -> Tool:
        """Retrieves tool capability."""
        with self._lock:
            if tool_id not in self._tools:
                raise ToolNotFoundError(f"Tool '{tool_id}' not registered.")
            return self._tools[tool_id]

    def list_tools(self) -> List[Tool]:
        """Lists active tools."""
        with self._lock:
            return list(self._tools.values())

    def find_by_category(self, category: ToolCategory) -> List[Tool]:
        """Filters active tools by category."""
        with self._lock:
            return [t for t in self._tools.values() if t.schema.category == category]

    def health_check(self) -> Dict[str, bool]:
        """Queries health status across registered tools."""
        with self._lock:
            results = {}
            for tid, tool in self._tools.items():
                try:
                    results[tid] = tool.health_check()
                except Exception:
                    results[tid] = False
            return results


# =====================================================================
# Tool Executor
# =====================================================================

class ToolExecutor:
    """Thread-safe coordinator managing schemas validation and executions metrics logging."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        permission_evaluator: Optional[ToolPermissionEvaluator] = None
    ) -> None:
        self.registry = registry or ToolRegistry()
        self.permission_evaluator = permission_evaluator or DefaultToolPermissionEvaluator()
        self.event_bus = EventBus()
        self.logger = StructuredLogger()

    def execute(self, request: ToolRequest) -> ToolResponse:
        """Runs validation schemas and executes tool capability tasks.

        Args:
            request: Ingestion request specifications.

        Returns:
            ToolResponse: Outcome package details.
        """
        if not request:
            raise ToolValidationError("ToolRequest cannot be None.")

        # Timeout settings check
        timeout = request.metadata.get("timeout_seconds", 30.0)

        try:
            tool = self.registry.get_tool(request.tool_id)
        except ToolNotFoundError as e:
            self._publish_event("tool.failed", tool_id=request.tool_id, error=str(e))
            raise

        meta = tool.schema

        # Evaluate permissions
        eligible = self.permission_evaluator.evaluate(request, meta)
        if not eligible:
            self._publish_event("tool.permission.denied", tool_id=request.tool_id, user_id=request.user_id)
            raise ToolPermissionError(f"Permission denied: User '{request.user_id}' cannot run tool '{request.tool_id}'.")

        # Validate request arguments schema
        try:
            tool.validate_input(request.arguments)
        except ToolValidationError as e:
            self._publish_event("tool.failed", tool_id=request.tool_id, error=str(e))
            raise

        self._publish_event("tool.executed", tool_id=request.tool_id)
        start_time = time.perf_counter()

        try:
            # Perform capability execute (simulated timeout validation)
            if timeout <= 0.0:
                raise ToolTimeoutError(f"Tool '{request.tool_id}' execution timed out.")

            output = tool.execute(request)
            duration = time.perf_counter() - start_time

            # Validate output schema
            tool.validate_output(output)

            # Log metrics without secret leaks
            self.logger.info(
                f"Successful tool execution: {request.tool_id}. Workspace: {request.workspace_id}. Duration: {duration:.3f}s."
            )

            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=output,
                execution_time=duration,
                diagnostics={"timeout_seconds": timeout}
            )

        except Exception as e:
            duration = time.perf_counter() - start_time
            self._publish_event("tool.failed", tool_id=request.tool_id, error=str(e))
            if isinstance(e, ToolTimeoutError):
                self._publish_event("tool.timeout", tool_id=request.tool_id)
                raise
            raise ToolError(f"Execution failed on tool '{request.tool_id}': {e}") from e

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ToolExecutor",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)


# =====================================================================
# Tool Discovery
# =====================================================================

class ToolDiscovery:
    """Registry searcher utility locating active plugins and builtin tools."""

    def __init__(self, registry: Optional[ToolRegistry] = None) -> None:
        self.registry = registry or ToolRegistry()

    def discover_local(self) -> List[Tool]:
        """Lists active tools currently saved in the registry."""
        return self.registry.list_tools()

    def discover_plugins(self) -> List[Tool]:
        """Lists metadata of plugin-discovered capabilities (placeholder)."""
        # Placeholder returns active registry tools list
        return self.registry.list_tools()


# =====================================================================
# Mock Tool Implementations
# =====================================================================

class MockSearchTool(Tool):
    """Mock search capability tool."""

    @property
    def name(self) -> str:
        return "MockSearchTool"

    @property
    def description(self) -> str:
        return "Simulates searching database queries for matching keywords"

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="mock_search_tool",
            name=self.name,
            version="1.0.0",
            author="System",
            description=self.description,
            category=ToolCategory.SEARCH,
            permissions=["use_search"],
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "array",
                "items": {"type": "string"}
            }
        )

    def execute(self, request: ToolRequest) -> Any:
        query = request.arguments["query"]
        limit = request.arguments.get("limit", 2)
        return [f"Query result {i} matching '{query}'" for i in range(1, limit + 1)]

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "query" not in arguments:
            raise ToolValidationError("Missing required argument 'query'.")
        validate_schema_value("query", arguments["query"], "string")
        if "limit" in arguments:
            validate_schema_value("limit", arguments["limit"], "integer")

    def validate_output(self, output: Any) -> None:
        validate_schema_value("output", output, "array")

    def health_check(self) -> bool:
        return True


class MockCalculatorTool(Tool):
    """Mock analytics math calculator tool."""

    @property
    def name(self) -> str:
        return "MockCalculatorTool"

    @property
    def description(self) -> str:
        return "Simulates math calculations adding an array of numbers"

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="mock_calc_tool",
            name=self.name,
            version="1.0.0",
            author="System",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "numbers": {
                        "type": "array",
                        "items": {"type": "number"}
                    }
                },
                "required": ["numbers"]
            },
            output_schema={
                "type": "number"
            }
        )

    def execute(self, request: ToolRequest) -> Any:
        return float(sum(request.arguments["numbers"]))

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "numbers" not in arguments:
            raise ToolValidationError("Missing required argument 'numbers'.")
        validate_schema_value("numbers", arguments["numbers"], "list" if not isinstance(arguments["numbers"], list) else "array")
        for val in arguments["numbers"]:
            if not isinstance(val, (int, float)):
                raise ToolValidationError("Calculator values must be numbers.")

    def validate_output(self, output: Any) -> None:
        validate_schema_value("output", output, "number")

    def health_check(self) -> bool:
        return True
