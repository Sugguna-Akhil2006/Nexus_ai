"""Embedding Selector selecting optimal text embedding models."""

from __future__ import annotations

from typing import List, Optional

from backend.platform.models import ModelProfile


class EmbeddingSelector:
    """Selects optimal embedding model from available profiles."""

    def select_embedding_model(self, models: List[ModelProfile]) -> Optional[ModelProfile]:
        # Filter models with capability embedding
        embedding_models = [m for m in models if "embedding" in m.capabilities or "embeddings" in m.capabilities]
        if embedding_models:
            return embedding_models[0]

        # Defaults
        for m in models:
            if "local" in m.capabilities:
                return m
        return models[0] if models else None
