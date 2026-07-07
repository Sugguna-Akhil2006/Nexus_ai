"""Tool Registry managing discovery of plugins and agent execution tools."""

from __future__ import annotations

from typing import Optional

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityMetadata, CapabilityType


class ToolRegistry:
    """Discovers and registers custom capability tools and plugins."""

    def __init__(self, cap_registry: Optional[CapabilityRegistry] = None) -> None:
        self.cap_registry = cap_registry or CapabilityRegistry()

    def discover_tools(self) -> None:
        """Auto-discovers and registers standard platform tools and plugins."""
        # Vector search tool
        self.cap_registry.register_capability(CapabilityMetadata(
            capability_id="tool-vector-search",
            name="Vector Search Tool",
            type=CapabilityType.TOOL,
            version="1.0.0",
            description="Performs semantic document retrieval and keyword search.",
            tags=["vector", "search", "retrieval"]
        ))

        # PDF parser plugin
        self.cap_registry.register_capability(CapabilityMetadata(
            capability_id="plugin-pdf-parser",
            name="PDF Parser Plugin",
            type=CapabilityType.PLUGIN,
            version="1.0.0",
            description="Extracts plaintext and metadata structure from PDF files.",
            tags=["pdf", "parser", "plugin"]
        ))
