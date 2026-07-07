"""Provider Registry managing discovery of LLM, embedding, and vector database providers."""

from __future__ import annotations

from typing import Optional

from backend.interfaces.model import ModelRegistry
from backend.interfaces.vector import VectorRegistry
from backend.agents.embedding import EmbeddingRegistry
from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityMetadata, CapabilityType


class ProviderRegistry:
    """Discovers and registers LLM and vector database providers dynamically."""

    def __init__(self, cap_registry: Optional[CapabilityRegistry] = None) -> None:
        self.cap_registry = cap_registry or CapabilityRegistry()

    def discover_providers(self) -> None:
        """Queries Model, Vector, and Embedding Registries to auto-register capabilities."""
        # 1. Discover LLM Providers
        try:
            model_reg = ModelRegistry()
            for provider_name in model_reg.list_providers():
                self.cap_registry.register_capability(CapabilityMetadata(
                    capability_id=f"provider-llm-{provider_name.lower()}",
                    name=provider_name,
                    type=CapabilityType.LLM_PROVIDER,
                    version="1.0.0",
                    description=f"Registered LLM Inference model provider: {provider_name}",
                    tags=["llm", "inference"]
                ))
        except Exception:
            pass

        # 2. Discover Vector Providers
        try:
            vector_reg = VectorRegistry()
            for provider_name in vector_reg.list_providers():
                self.cap_registry.register_capability(CapabilityMetadata(
                    capability_id=f"provider-vector-{provider_name.lower()}",
                    name=provider_name,
                    type=CapabilityType.EMBEDDING_PROVIDER,
                    version="1.0.0",
                    description=f"Registered Vector database indexing provider: {provider_name}",
                    tags=["vector", "embedding", "db"]
                ))
        except Exception:
            pass

        # 3. Discover Embedding Providers
        try:
            embed_reg = EmbeddingRegistry()
            for provider_name in embed_reg.list_providers():
                self.cap_registry.register_capability(CapabilityMetadata(
                    capability_id=f"provider-embed-{provider_name.lower()}",
                    name=provider_name,
                    type=CapabilityType.EMBEDDING_PROVIDER,
                    version="1.0.0",
                    description=f"Registered Text Embedding generation provider: {provider_name}",
                    tags=["embedding", "nlp"]
                ))
        except Exception:
            pass
