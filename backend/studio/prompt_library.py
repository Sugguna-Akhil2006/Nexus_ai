"""Prompt Library managing template variations and historical outputs."""

from __future__ import annotations

from typing import List, Optional

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityMetadata, CapabilityType
from backend.studio.models import PromptTemplate


class PromptLibrary:
    """Manages prompt template variations, revisions, and outputs."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def list_prompts(self) -> List[PromptTemplate]:
        """Lists registered prompt templates."""
        caps = self.registry.list_capabilities(CapabilityType.PROMPT)
        prompts = []
        for c in caps:
            prompts.append(PromptTemplate(
                prompt_id=c.capability_id,
                category=c.extra.get("category", "General"),
                version=c.version,
                template=c.extra.get("template_content", "System prompt template content"),
                example_outputs=c.extra.get("example_outputs", []),
                usage_count=c.health.usage_count
            ))
        return prompts

    def save_prompt(self, prompt_id: str, template: str, category: str = "General") -> None:
        """Saves or updates a prompt template revision."""
        meta = CapabilityMetadata(
            capability_id=prompt_id,
            name=prompt_id.replace("prompt-", "").replace("-", " ").title(),
            type=CapabilityType.PROMPT,
            version="1.0.0",
            description=f"Studio custom prompt template: {prompt_id}",
            extra={
                "template_content": template,
                "category": category,
                "example_outputs": ["Mock generated output."]
            }
        )
        self.registry.register_capability(meta)
