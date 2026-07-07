"""Prompt Registry managing LLM prompt templates registry."""

from __future__ import annotations

from typing import Optional

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityMetadata, CapabilityType


class PromptRegistry:
    """Manages prompt template capability entries."""

    def __init__(self, cap_registry: Optional[CapabilityRegistry] = None) -> None:
        self.cap_registry = cap_registry or CapabilityRegistry()

    def discover_prompts(self) -> None:
        """Auto-discovers and registers standard platform prompt templates."""
        # General chat template
        self.cap_registry.register_capability(CapabilityMetadata(
            capability_id="prompt-general-chat",
            name="General Chat Template",
            type=CapabilityType.PROMPT,
            version="1.0.0",
            description="Default conversational chat system instruction prompt.",
            tags=["chat", "system-prompt"]
        ))

        # Resume analysis template
        self.cap_registry.register_capability(CapabilityMetadata(
            capability_id="prompt-resume-extraction",
            name="Resume Skill Extraction Prompt",
            type=CapabilityType.PROMPT,
            version="1.0.0",
            description="Analyzes resumes to extract skills and compile structured ATS scores.",
            tags=["resume", "ats", "extraction"]
        ))
