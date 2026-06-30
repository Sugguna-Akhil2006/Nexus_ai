"""Embedding Agent and Pluggable Document Chunking Layer Module.

Provides abstractions, registries, chunking strategies, validation checks,
and mock providers for vector generation and semantic indexing of text elements.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import logging
import math
import re
import threading
import time
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from backend.runtime.base import AgentState, AgentStatus, BaseAgent
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from backend.runtime.task import Task
from backend.runtime.logger import StructuredLogger
from backend.interfaces.vector import VectorRegistry, VectorRecord, CollectionInfo


# =====================================================================
# Exceptions
# =====================================================================

class EmbeddingError(NexusException):
    """Base exception for all Embedding Agent related errors."""
    pass


class EmbeddingValidationError(EmbeddingError):
    """Raised when embedding validation checks fail."""
    pass


class EmbeddingProviderError(EmbeddingError):
    """Raised when an embedding provider fails to generate vectors."""
    pass


# =====================================================================
# Core Models
# =====================================================================

@dataclass(frozen=True)
class EmbeddingRequest:
    """Authentication parameters defining target document parameters.

    Attributes:
        request_id: Tracking request ID.
        document_id: Target document ID.
        workspace_id: Target workspace context ID.
        model: Expected model key string.
        chunking_strategy: Selected chunking strategy.
        namespace: Isolated search namespace.
        metadata: Extra tracking metadata.
    """
    request_id: str
    document_id: str
    workspace_id: str
    model: str
    chunking_strategy: str
    namespace: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingChunk:
    """Extracted text chunk item details.

    Attributes:
        chunk_id: Bounding box identifier string.
        sequence_number: Placement ordering sequence counter.
        content: Plaintext content.
        token_count: Approximated token count.
        metadata: Extra tag attributes dictionary.
    """
    chunk_id: str
    sequence_number: int
    content: str
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingRecord:
    """Immutable model representing an indexed embedding record.

    Attributes:
        embedding_id: Unique record ID.
        document_id: Parent document identifier.
        chunk_id: Target chunk identifier.
        model: Associated embedding model key.
        vector_dimensions: Length dimensions count.
        version: Version identifier count.
        created_at: Creation timestamp.
        metadata: Extra metadata details.
    """
    embedding_id: str
    document_id: str
    chunk_id: str
    model: str
    vector_dimensions: int
    version: int
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingResult:
    """Consolidated embedding result outcome.

    Attributes:
        request_id: Unique outcome ID.
        total_chunks: Count of chunks.
        indexed_chunks: Count of successfully indexed chunks.
        failed_chunks: Count of failed chunks.
        processing_time: Duration elapsed in float seconds.
        provider: Processing provider name.
        metadata: Extra metadata details.
    """
    request_id: str
    total_chunks: int
    indexed_chunks: int
    failed_chunks: int
    processing_time: float
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Chunking Strategy Abstraction
# =====================================================================

class ChunkingStrategy(ABC):
    """Abstract Strategy outlining text slicing operations."""

    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        """Splits source text string into an array of string chunks."""
        pass


class FixedSizeChunkingStrategy(ChunkingStrategy):
    """Slices text string based on character count boundaries with overlap."""

    def __init__(self, chunk_size: int = 200, overlap: int = 40) -> None:
        if chunk_size <= 0:
            raise EmbeddingValidationError("chunk_size must be positive.")
        if overlap < 0 or overlap >= chunk_size:
            raise EmbeddingValidationError("overlap must be non-negative and smaller than chunk_size.")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += (self.chunk_size - self.overlap)
            if start >= len(text):
                break
        return chunks


class SentenceChunkingStrategy(ChunkingStrategy):
    """Groups text based on standard regex sentence boundary count markers."""

    def __init__(self, sentences_per_chunk: int = 2) -> None:
        if sentences_per_chunk <= 0:
            raise EmbeddingValidationError("sentences_per_chunk must be positive.")
        self.sentences_per_chunk = sentences_per_chunk

    def chunk(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        for i in range(0, len(sentences), self.sentences_per_chunk):
            chunk_text = " ".join(sentences[i:i+self.sentences_per_chunk])
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
        return chunks


class ParagraphChunkingStrategy(ChunkingStrategy):
    """Groups text based on line break paragraph sequences."""

    def __init__(self, paragraphs_per_chunk: int = 1) -> None:
        if paragraphs_per_chunk <= 0:
            raise EmbeddingValidationError("paragraphs_per_chunk must be positive.")
        self.paragraphs_per_chunk = paragraphs_per_chunk

    def chunk(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        paragraphs = text.split("\n\n")
        chunks = []
        for i in range(0, len(paragraphs), self.paragraphs_per_chunk):
            chunk_text = "\n\n".join(paragraphs[i:i+self.paragraphs_per_chunk])
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
        return chunks


class SemanticChunkingStrategy(ChunkingStrategy):
    """Semantic chunking strategy that splits documents by logical domain headings."""

    def chunk(self, text: str) -> List[str]:
        tuples = self.chunk_with_metadata(text)
        return [content for content, _ in tuples]

    def chunk_with_metadata(self, text: str) -> List[tuple[str, str]]:
        if not text or not text.strip():
            return []

        text_lower = text.lower()
        
        is_code = (
            "def " in text or 
            "class " in text or 
            "const " in text or 
            "import " in text or 
            "function " in text or 
            ("{" in text and "}" in text and ";" in text)
        )
        
        is_resume = (
            "education" in text_lower and 
            ("experience" in text_lower or "employment" in text_lower or "work history" in text_lower) and 
            ("skills" in text_lower or "projects" in text_lower)
        )
        
        is_research = (
            "abstract" in text_lower and 
            ("introduction" in text_lower or "methodology" in text_lower or "results" in text_lower) and 
            "conclusion" in text_lower
        )

        chunks = []
        if is_code:
            lines = text.split("\n")
            current_chunk = []
            current_section = "General"
            
            for line in lines:
                line_stripped = line.strip()
                if line_stripped.startswith("class "):
                    if current_chunk:
                        chunks.append(("\n".join(current_chunk), current_section))
                        current_chunk = []
                    current_section = "Classes"
                elif line_stripped.startswith("def ") or line_stripped.startswith("async def "):
                    if current_chunk:
                        chunks.append(("\n".join(current_chunk), current_section))
                        current_chunk = []
                    current_section = "Functions"
                elif line_stripped.startswith("#") or line_stripped.startswith("//") or line_stripped.startswith("/*"):
                    if current_chunk:
                        chunks.append(("\n".join(current_chunk), current_section))
                        current_chunk = []
                    current_section = "Comments"
                elif "readme" in line_stripped.lower():
                    if current_chunk:
                        chunks.append(("\n".join(current_chunk), current_section))
                        current_chunk = []
                    current_section = "README"
                
                current_chunk.append(line)
                
            if current_chunk:
                chunks.append(("\n".join(current_chunk), current_section))
                
        elif is_resume:
            sections_regex = r"(?i)\b(personal information|contact|education|skills|experience|employment|work history|projects|certifications|awards|summary)\b"
            matches = list(re.finditer(sections_regex, text))
            if not matches:
                return self._paragraph_fallback(text, "Resume")
                
            last_idx = 0
            current_section = "Personal Information"
            for match in matches:
                start = match.start()
                if start > last_idx:
                    content = text[last_idx:start].strip()
                    if content:
                        chunks.append((content, current_section))
                current_section = match.group(0).title()
                last_idx = start
            
            content = text[last_idx:].strip()
            if content:
                chunks.append((content, current_section))
                
        elif is_research:
            sections_regex = r"(?i)\b(abstract|introduction|methodology|results|discussion|conclusion|references|related work)\b"
            matches = list(re.finditer(sections_regex, text))
            if not matches:
                return self._paragraph_fallback(text, "Research Paper")
                
            last_idx = 0
            current_section = "Introduction"
            for match in matches:
                start = match.start()
                if start > last_idx:
                    content = text[last_idx:start].strip()
                    if content:
                        chunks.append((content, current_section))
                current_section = match.group(0).title()
                last_idx = start
            
            content = text[last_idx:].strip()
            if content:
                chunks.append((content, current_section))
        else:
            return self._paragraph_fallback(text, "General")

        valid_chunks = []
        for content, section in chunks:
            content_stripped = content.strip()
            if not content_stripped:
                continue
            if len(content_stripped) > 1500:
                paragraphs = content_stripped.split("\n\n")
                for sub_idx, para in enumerate(paragraphs):
                    para_stripped = para.strip()
                    if para_stripped:
                        valid_chunks.append((para_stripped, f"{section} (Part {sub_idx+1})"))
            else:
                valid_chunks.append((content_stripped, section))
                
        return valid_chunks

    def _paragraph_fallback(self, text: str, domain_name: str) -> List[tuple[str, str]]:
        paragraphs = text.split("\n\n")
        chunks = []
        for idx, para in enumerate(paragraphs):
            para_stripped = para.strip()
            if para_stripped:
                chunks.append((para_stripped, f"{domain_name} Section {idx+1}"))
        return chunks


# =====================================================================
# Validation Utilities
# =====================================================================

def validate_embedding_content(text: str) -> None:
    """Validates raw text is non-empty."""
    if not text or not isinstance(text, str) or not text.strip():
        raise EmbeddingValidationError("Content text to embed cannot be empty.")


def validate_chunk_size(chunk_content: str, max_chars: int = 10000) -> None:
    """Validates size limits on individual chunks."""
    if len(chunk_content) > max_chars:
        raise EmbeddingValidationError(f"Chunk size {len(chunk_content)} exceeds maximum limit of {max_chars} characters.")


# =====================================================================
# Embedding Provider Interface
# =====================================================================

class EmbeddingProvider(ABC):
    """Abstract contract for model embedding generators."""

    @abstractmethod
    def generate_embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        """Generates raw coordinate float lists for a list of string blocks."""
        pass

    @abstractmethod
    def supported_models(self) -> List[str]:
        """Lists active model keys."""
        pass

    @abstractmethod
    def supported_dimensions(self, model: str) -> int:
        """Determines expected vector length size for a model."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Queries health status."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock provider simulating embedding vectors generation."""

    def generate_embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        dims = self.supported_dimensions(model)
        results = []
        for text in texts:
            vector = []
            char_sum = sum(ord(c) for c in text) if text else 0
            for i in range(dims):
                val = math.sin(char_sum + i)
                vector.append(round(val, 6))
            results.append(vector)
        return results

    def supported_models(self) -> List[str]:
        return ["mock-embed-small", "mock-embed-large"]

    def supported_dimensions(self, model: str) -> int:
        if model == "mock-embed-large":
            return 768
        return 384

    def health_check(self) -> bool:
        return True


# =====================================================================
# Embedding Registry
# =====================================================================

class EmbeddingRegistry:
    """Thread-safe singleton registry mapping embedding providers."""

    _instance: Optional["EmbeddingRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "EmbeddingRegistry":
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
            self._providers: Dict[str, EmbeddingProvider] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register_provider(self, provider_id: str, provider: EmbeddingProvider) -> None:
        """Registers an EmbeddingProvider."""
        if not provider_id or not str(provider_id).strip():
            raise EmbeddingValidationError("provider_id cannot be empty.")
        if not provider:
            raise EmbeddingValidationError("provider instance cannot be None.")

        with self._lock:
            if provider_id in self._providers:
                raise EmbeddingValidationError(f"Provider '{provider_id}' already registered.")
            self._providers[provider_id] = provider
            self._logger.info(f"Registered embedding provider: {provider_id}")

    def unregister_provider(self, provider_id: str) -> None:
        """Removes a registered provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise EmbeddingValidationError(f"Provider '{provider_id}' not found.")
            del self._providers[provider_id]
            self._logger.info(f"Unregistered embedding provider: {provider_id}")

    def get_provider(self, provider_id: str) -> EmbeddingProvider:
        """Retrieves provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise EmbeddingValidationError(f"Provider '{provider_id}' not registered.")
            return self._providers[provider_id]

    def list_models(self) -> List[str]:
        """Lists active model names across all registered providers."""
        with self._lock:
            models = []
            for provider in self._providers.values():
                models.extend(provider.supported_models())
            return list(set(models))

    def health_check(self) -> Dict[str, bool]:
        """Queries health status across registered providers."""
        with self._lock:
            results = {}
            for pid, provider in self._providers.items():
                try:
                    results[pid] = provider.health_check()
                except Exception:
                    results[pid] = False
            return results


# =====================================================================
# Embedding Agent
# =====================================================================

class EmbeddingAgent(BaseAgent):
    """System agent governing Document Chunking and Semantic Vector Indexing pipelines."""

    def __init__(
        self,
        name: str = "EmbeddingAgent",
        description: str = "Generates and indexes vector representations from structured content",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ) -> None:
        caps = capabilities or ["EMBEDDING_GENERATION", "SEMANTIC_INDEXING"]
        super().__init__(name=name, description=description, version=version, capabilities=caps)
        self.registry = EmbeddingRegistry()
        self.event_bus = EventBus()
        self.vector_registry = VectorRegistry()
        # Thread-safe in-memory incremental indexing catalog cache
        # key: (workspace_id, document_id) -> val: dict containing checksum, version, vector_ids, and records logs
        self._indexing_catalog: Dict[tuple[str, str], Dict[str, Any]] = {}
        self._catalog_lock = threading.Lock()

    def initialize(self) -> None:
        """Initializes Embedding agent."""
        super().initialize()

    def validate_task(self, task: Task) -> None:
        super().validate_task(task)
        if not task.metadata or "action" not in task.metadata:
            raise TaskValidationError("Task metadata must contain an 'action' field.")

    def execute(self, task: Task) -> Any:
        action = task.metadata["action"]
        provider_id = task.metadata.get("provider_id")

        if not provider_id:
            providers = self.registry.list_models()
            if not providers:
                # Fallback check on register
                registered_providers = list(self.registry._providers.keys())
                if not registered_providers:
                    raise EmbeddingValidationError("No embedding providers registered.")
                provider_id = registered_providers[0]
            else:
                # Find which provider supports the model
                provider_id = list(self.registry._providers.keys())[0]

        provider = self.registry.get_provider(provider_id)

        if action == "embed":
            doc_id = task.metadata.get("document_id")
            ws_id = task.metadata.get("workspace_id")
            text = task.metadata.get("text")
            model = task.metadata.get("model", "mock-embed-small")
            strategy_name = task.metadata.get("chunking_strategy", "semantic")
            namespace = task.metadata.get("namespace", "default")
            req_metadata = task.metadata.get("metadata", {})
            force_reindex = task.metadata.get("force_reindex", False)
            vector_provider_id = task.metadata.get("vector_provider_id")

            if not doc_id or not ws_id or text is None:
                raise EmbeddingValidationError("Missing parameters (document_id, workspace_id, text).")

            validate_embedding_content(text)

            # Check supported model
            if model not in provider.supported_models():
                raise EmbeddingValidationError(f"Unsupported embedding model: '{model}'.")

            # Check Vector provider registry
            if not vector_provider_id:
                vec_providers = self.vector_registry.list_providers()
                if not vec_providers:
                    raise EmbeddingValidationError("No vector providers registered.")
                vector_provider_id = vec_providers[0]
            vector_provider = self.vector_registry.get_provider(vector_provider_id)

            checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
            catalog_key = (ws_id, doc_id)

            # Incremental Indexing Check
            with self._catalog_lock:
                cached_entry = self._indexing_catalog.get(catalog_key)

            if cached_entry and cached_entry["checksum"] == checksum and not force_reindex:
                self.logger.info(
                    "Skipping embedding. Document '%s' already indexed with checksum '%s'.",
                    doc_id,
                    checksum
                )
                return EmbeddingResult(
                    request_id=str(uuid.uuid4()),
                    total_chunks=len(cached_entry["chunks"]),
                    indexed_chunks=len(cached_entry["chunks"]),
                    failed_chunks=0,
                    processing_time=0.0,
                    provider=provider_id,
                    metadata={"cached": True, "version": cached_entry["version"]}
                )

            # Determine strategy
            strategy: ChunkingStrategy
            if strategy_name == "fixed":
                strategy = FixedSizeChunkingStrategy()
            elif strategy_name == "sentence":
                strategy = SentenceChunkingStrategy()
            elif strategy_name == "paragraph":
                strategy = ParagraphChunkingStrategy()
            elif strategy_name == "semantic":
                strategy = SemanticChunkingStrategy()
            else:
                raise EmbeddingValidationError(f"Invalid chunking strategy: '{strategy_name}'.")

            self._publish_event("embedding.started", document_id=doc_id, provider=provider_id)
            start_time = time.perf_counter()

            # Handle re-indexing (delete old records from Vector engine collection)
            current_version = 1
            if cached_entry:
                current_version = cached_entry["version"] + 1
                col_id = f"col_{ws_id}"
                try:
                    vector_provider.delete(col_id, cached_entry["vector_ids"], namespace)
                    self._publish_event("embedding.reindexed", document_id=doc_id, version=current_version)
                except Exception as e:
                    self.logger.warning("Could not delete old vectors during reindexing: %s", e)

            # Perform Chunking with metadata support
            chunking_start = time.perf_counter()
            filename = task.metadata.get("filename", "document")
            chunks = []
            if hasattr(strategy, "chunk_with_metadata"):
                chunk_tuples = strategy.chunk_with_metadata(text)
                for idx, (c_text, sec_name) in enumerate(chunk_tuples):
                    validate_chunk_size(c_text)
                    c_id = f"{doc_id}-chunk-{idx}"
                    chunks.append(EmbeddingChunk(
                        chunk_id=c_id,
                        sequence_number=idx,
                        content=c_text,
                        token_count=len(c_text) // 4,
                        metadata={"section": sec_name}
                    ))
                    self._publish_event("embedding.chunk.created", chunk_id=c_id)
            else:
                text_chunks = strategy.chunk(text)
                for idx, c_text in enumerate(text_chunks):
                    validate_chunk_size(c_text)
                    c_id = f"{doc_id}-chunk-{idx}"
                    chunks.append(EmbeddingChunk(
                        chunk_id=c_id,
                        sequence_number=idx,
                        content=c_text,
                        token_count=len(c_text) // 4,
                        metadata={"section": "General"}
                    ))
                    self._publish_event("embedding.chunk.created", chunk_id=c_id)
            chunking_time = time.perf_counter() - chunking_start
            embedding_start = time.perf_counter()

            # Generate Embeddings
            texts_to_embed = [c.content for c in chunks]
            try:
                embeddings = provider.generate_embeddings(texts_to_embed, model)
            except Exception as e:
                self._publish_event("embedding.failed", document_id=doc_id, error=str(e))
                raise EmbeddingProviderError(f"Embedding generation failed: {e}") from e

            # Create Collection if it does not exist
            col_id = f"col_{ws_id}"
            dimensions = provider.supported_dimensions(model)
            col_exists = any(c.collection_id == col_id for c in vector_provider.list_collections())
            if not col_exists:
                vector_provider.create_collection(CollectionInfo(
                    collection_id=col_id,
                    name=f"Collection {ws_id}",
                    dimensions=dimensions,
                    similarity_metric="cosine"
                ))

            # Store into Vector Engine collection
            vector_records = []
            records = []
            vector_ids = []
            now = datetime.utcnow()

            for idx, chunk in enumerate(chunks):
                v_id = f"{doc_id}-v-{idx}"
                vector_ids.append(v_id)
                vector_records.append(VectorRecord(
                    vector_id=v_id,
                    collection=col_id,
                    embedding=embeddings[idx],
                    metadata={
                        "document_id": doc_id,
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.content,
                        "document_name": filename,
                        "section": chunk.metadata.get("section", "General")
                    },
                    namespace=namespace
                ))
                records.append(EmbeddingRecord(
                    embedding_id=v_id,
                    document_id=doc_id,
                    chunk_id=chunk.chunk_id,
                    model=model,
                    vector_dimensions=dimensions,
                    version=current_version,
                    created_at=now,
                    metadata=req_metadata
                ))

            try:
                vector_provider.insert(vector_records)
            except Exception as e:
                self._publish_event("embedding.failed", document_id=doc_id, error=str(e))
                raise EmbeddingProviderError(f"Vector engine insertion failed: {e}") from e

            # Cache the index state in catalog
            with self._catalog_lock:
                self._indexing_catalog[catalog_key] = {
                    "checksum": checksum,
                    "version": current_version,
                    "chunks": chunks,
                    "vector_ids": vector_ids,
                    "records": records
                }

            embedding_time = time.perf_counter() - embedding_start
            duration = time.perf_counter() - start_time
            self._publish_event("embedding.completed", document_id=doc_id)

            return EmbeddingResult(
                request_id=str(uuid.uuid4()),
                total_chunks=len(chunks),
                indexed_chunks=len(chunks),
                failed_chunks=0,
                processing_time=duration,
                provider=provider_id,
                metadata={
                    "version": current_version,
                    "chunking_time": chunking_time,
                    "embedding_time": embedding_time
                }
            )

        elif action == "delete_document_embeddings":
            doc_id = task.metadata.get("document_id")
            ws_id = task.metadata.get("workspace_id")
            namespace = task.metadata.get("namespace", "default")
            vector_provider_id = task.metadata.get("vector_provider_id")

            if not doc_id or not ws_id:
                raise EmbeddingValidationError("Missing document_id or workspace_id parameters.")

            if not vector_provider_id:
                vec_providers = self.vector_registry.list_providers()
                if not vec_providers:
                    raise EmbeddingValidationError("No vector providers registered.")
                vector_provider_id = vec_providers[0]
            vector_provider = self.vector_registry.get_provider(vector_provider_id)

            catalog_key = (ws_id, doc_id)

            with self._catalog_lock:
                cached_entry = self._indexing_catalog.pop(catalog_key, None)

            if cached_entry:
                col_id = f"col_{ws_id}"
                vector_provider.delete(col_id, cached_entry["vector_ids"], namespace)
                return True

            return False

        else:
            raise EmbeddingValidationError(f"Unsupported action: {action}")

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="EmbeddingAgent",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
