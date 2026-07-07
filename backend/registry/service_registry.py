"""Service Registry responsible for registration and auto-discovery of core agent services."""

from __future__ import annotations

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityMetadata, CapabilityType


class ServiceRegistry:
    """Discovers and registers core agent capabilities."""

    def __init__(self, cap_registry: Optional[CapabilityRegistry] = None) -> None:
        self.cap_registry = cap_registry or CapabilityRegistry()

    def discover_services(self) -> None:
        """Discovers standard platform agents and registers them into the control plane."""
        # 1. Workspace Agent
        self.cap_registry.register_capability(CapabilityMetadata(
            capability_id="agent-workspace",
            name="WorkspaceAgent",
            type=CapabilityType.AGENT,
            version="1.0.0",
            description="Manages workspace scopes, member profiles, and isolation domains.",
            tags=["workspace", "management"]
        ))

        # 2. Document Agent
        self.cap_registry.register_capability(CapabilityMetadata(
            capability_id="agent-document",
            name="DocumentAgent",
            type=CapabilityType.AGENT,
            version="1.0.0",
            description="Handles document uploads, ocr parsing, and plaintext extraction.",
            tags=["document", "parsing"]
        ))

        # 3. Chat Agent
        self.cap_registry.register_capability(CapabilityMetadata(
            capability_id="agent-chat",
            name="ChatAgent",
            type=CapabilityType.AGENT,
            version="1.0.0",
            description="Provides context-aware conversational chat capabilities.",
            tags=["chat", "interaction"]
        ))

        # 4. Search Agent
        self.cap_registry.register_capability(CapabilityMetadata(
            capability_id="agent-search",
            name="SearchAgent",
            type=CapabilityType.AGENT,
            version="1.0.0",
            description="Provides semantic retrieval and keyword matching across collections.",
            tags=["search", "retrieval"]
        ))
