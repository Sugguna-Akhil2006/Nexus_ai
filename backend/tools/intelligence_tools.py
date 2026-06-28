"""Reusable Intelligence Tools Module.

Implements standard Prompt 38 tools bridging to stateless services.
"""

import time
from typing import Any, Dict, List, Optional
import uuid

from backend.tools.tool import Tool, ToolMetadata, ToolCategory, ToolRequest, ToolResponse, ToolRegistry
from backend.services.intelligence.summary import SummaryService
from backend.services.intelligence.entity import EntityExtractionService
from backend.services.intelligence.classification import ClassificationService
from backend.services.intelligence.comparison import ComparisonService
from backend.services.intelligence.recommendation import RecommendationService
from backend.services.intelligence.report import ReportService

# =====================================================================
# 1. Summary Tool
# =====================================================================

class SummaryTool(Tool):
    """Converts raw text to summaries."""

    @property
    def name(self) -> str:
        return "Summary Tool"

    @property
    def description(self) -> str:
        return "Summarizes input text concisely using LLMs."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="summary_tool",
            name=self.name,
            version="1.0.0",
            author="System",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            output_schema={"type": "string"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments:
            raise Exception("Missing argument: text")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        service = SummaryService()
        try:
            summary = service.summarize(text, request.workspace_id, request.user_id)
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=summary,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output=str(e),
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 2. Entity Extraction Tool
# =====================================================================

class EntityExtractionTool(Tool):
    """Isolates structured key-value values according to schemas."""

    @property
    def name(self) -> str:
        return "Entity Extraction Tool"

    @property
    def description(self) -> str:
        return "Extracts structured schema entity details from raw documents."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="entity_extraction_tool",
            name=self.name,
            version="1.0.0",
            author="System",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "schema_def": {"type": "object"}
                },
                "required": ["text", "schema_def"]
            },
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments or "schema_def" not in arguments:
            raise Exception("Missing required arguments: text and schema_def")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        schema_def = request.arguments.get("schema_def", {})
        service = EntityExtractionService()
        try:
            extracted = service.extract_entities(text, schema_def, request.workspace_id, request.user_id)
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=extracted,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output=str(e),
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 3. Classification Tool
# =====================================================================

class ClassificationTool(Tool):
    """Categorizes payloads against user defined tags list."""

    @property
    def name(self) -> str:
        return "Classification Tool"

    @property
    def description(self) -> str:
        return "Classifies text into categories labels."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="classification_tool",
            name=self.name,
            version="1.0.0",
            author="System",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "categories": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["text", "categories"]
            },
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "text" not in arguments or "categories" not in arguments:
            raise Exception("Missing required arguments: text and categories")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        text = request.arguments.get("text", "")
        categories = request.arguments.get("categories", [])
        service = ClassificationService()
        try:
            classification = service.classify(text, categories, request.workspace_id, request.user_id)
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=classification,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output=str(e),
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 4. Comparison Tool
# =====================================================================

class ComparisonTool(Tool):
    """Performs side-by-side comparative mapping delta changes."""

    @property
    def name(self) -> str:
        return "Comparison Tool"

    @property
    def description(self) -> str:
        return "Compares data payloads to yield diff summaries."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="comparison_tool",
            name=self.name,
            version="1.0.0",
            author="System",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={
                "type": "object",
                "properties": {
                    "items": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["items"]
            },
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "items" not in arguments:
            raise Exception("Missing argument: items")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        items = request.arguments.get("items", [])
        service = ComparisonService()
        try:
            comparison = service.compare(items, request.workspace_id, request.user_id)
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=comparison,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output=str(e),
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 5. Recommendation Tool
# =====================================================================

class RecommendationTool(Tool):
    """Generates prioritized checklists items."""

    @property
    def name(self) -> str:
        return "Recommendation Tool"

    @property
    def description(self) -> str:
        return "Generates logical recommendations based on context data."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="recommendation_tool",
            name=self.name,
            version="1.0.0",
            author="System",
            description=self.description,
            category=ToolCategory.ANALYTICS,
            permissions=["read"],
            input_schema={
                "type": "object",
                "properties": {
                    "context_text": {"type": "string"},
                    "goals": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["context_text", "goals"]
            },
            output_schema={"type": "array"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "context_text" not in arguments or "goals" not in arguments:
            raise Exception("Missing required arguments: context_text and goals")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        context_text = request.arguments.get("context_text", "")
        goals = request.arguments.get("goals", [])
        service = RecommendationService()
        try:
            recs = service.generate_recommendations(context_text, goals, request.workspace_id, request.user_id)
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=recs,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output=str(e),
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# 6. Report Tool
# =====================================================================

class ReportTool(Tool):
    """Formats raw analytical logs to printable markdown layouts."""

    @property
    def name(self) -> str:
        return "Report Tool"

    @property
    def description(self) -> str:
        return "Formats analysis data into report representations."

    @property
    def schema(self) -> ToolMetadata:
        return ToolMetadata(
            tool_id="report_tool",
            name=self.name,
            version="1.0.0",
            author="System",
            description=self.description,
            category=ToolCategory.CUSTOM,
            permissions=["read"],
            input_schema={
                "type": "object",
                "properties": {
                    "report_data": {"type": "object"},
                    "title": {"type": "string"}
                },
                "required": ["report_data"]
            },
            output_schema={"type": "object"}
        )

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        if "report_data" not in arguments:
            raise Exception("Missing argument: report_data")

    def validate_output(self, output: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, request: ToolRequest) -> ToolResponse:
        start_time = time.perf_counter()
        report_data = request.arguments.get("report_data", {})
        title = request.arguments.get("title", "Analysis Report")
        service = ReportService()
        try:
            formats = service.generate_report_formats(report_data, title)
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=True,
                output=formats,
                execution_time=time.perf_counter() - start_time
            )
        except Exception as e:
            return ToolResponse(
                response_id=str(uuid.uuid4()),
                success=False,
                output=str(e),
                execution_time=time.perf_counter() - start_time
            )


# =====================================================================
# Registration Hook
# =====================================================================

def register_intelligence_tools() -> None:
    """Convenience callback to register tools in ToolRegistry."""
    registry = ToolRegistry()
    tools = [
        SummaryTool(),
        EntityExtractionTool(),
        ClassificationTool(),
        ComparisonTool(),
        RecommendationTool(),
        ReportTool()
    ]
    for tool in tools:
        try:
            registry.register_tool(tool)
        except Exception:
            # Overwrite if duplicate registration exception raises
            pass

# Execute auto-registration hook
register_intelligence_tools()
