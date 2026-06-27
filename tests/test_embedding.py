import concurrent.futures
from datetime import datetime
import threading
import time
from typing import Any, Dict, List, Optional
import unittest
import uuid

from core.embedding import (
    EmbeddingError,
    EmbeddingValidationError,
    EmbeddingProviderError,
    EmbeddingRequest,
    EmbeddingChunk,
    EmbeddingRecord,
    EmbeddingResult,
    ChunkingStrategy,
    FixedSizeChunkingStrategy,
    SentenceChunkingStrategy,
    ParagraphChunkingStrategy,
    EmbeddingProvider,
    MockEmbeddingProvider,
    EmbeddingRegistry,
    EmbeddingAgent,
    validate_embedding_content,
    validate_chunk_size,
)
from core.base import AgentState, AgentStatus
from core.event import Event, EventBus, EventType
from core.task import Task
from core.vector import VectorRegistry, MemoryVectorProvider, CollectionInfo


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestEmbeddingSystem(unittest.TestCase):
    """Suite of tests covering pluggable chunking and document embedding indexing."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        # Setup Embedding Registry
        self.registry = EmbeddingRegistry()
        with self.registry._lock:
            self.registry._providers.clear()
        self.provider = MockEmbeddingProvider()
        self.registry.register_provider("mock", self.provider)

        # Setup Vector Registry and Provider
        self.vector_registry = VectorRegistry()
        with self.vector_registry._lock:
            self.vector_registry._providers.clear()
        self.vector_provider = MemoryVectorProvider()
        self.vector_registry.register_provider("memory_vector", self.vector_provider)

        self.agent = EmbeddingAgent()
        self.agent.initialize()

    def test_chunking_strategies(self) -> None:
        """Verifies text splitting bounds for fixed size, sentences, and paragraphs strategies."""
        text = "Hello world. This is sentence two! And sentence three?"

        # 1. FixedSize (char-based)
        fixed = FixedSizeChunkingStrategy(chunk_size=15, overlap=5)
        chunks_fixed = fixed.chunk(text)
        self.assertTrue(len(chunks_fixed) > 2)
        self.assertEqual(chunks_fixed[0], "Hello world. Th")

        # 2. Sentence based
        sentence = SentenceChunkingStrategy(sentences_per_chunk=2)
        chunks_sent = sentence.chunk(text)
        self.assertEqual(len(chunks_sent), 2)
        self.assertEqual(chunks_sent[0], "Hello world. This is sentence two!")
        self.assertEqual(chunks_sent[1], "And sentence three?")

        # 3. Paragraph based
        para_text = "Para one content details.\n\nPara two content description."
        para = ParagraphChunkingStrategy(paragraphs_per_chunk=1)
        chunks_para = para.chunk(para_text)
        self.assertEqual(len(chunks_para), 2)
        self.assertEqual(chunks_para[0], "Para one content details.")
        self.assertEqual(chunks_para[1], "Para two content description.")

    def test_validation_utilities(self) -> None:
        """Verifies validations reject empty inputs and oversized chunks."""
        validate_embedding_content("valid text context")
        with self.assertRaises(EmbeddingValidationError):
            validate_embedding_content("")
        with self.assertRaises(EmbeddingValidationError):
            validate_embedding_content(None)  # type: ignore

        validate_chunk_size("small chunk text", max_chars=100)
        with self.assertRaises(EmbeddingValidationError):
            validate_chunk_size("extremely large chunk text exceeds limit parameter", max_chars=20)

    def test_registry_singleton(self) -> None:
        """Verifies singleton pattern constraints of EmbeddingRegistry."""
        registry2 = EmbeddingRegistry()
        self.assertIs(self.registry, registry2)

    def test_provider_registration(self) -> None:
        """Verifies provider register and unregister constraints on EmbeddingRegistry."""
        with self.assertRaises(EmbeddingValidationError):
            self.registry.register_provider("", self.provider)
        with self.assertRaises(EmbeddingValidationError):
            self.registry.register_provider("mock2", None)  # type: ignore
        with self.assertRaises(EmbeddingValidationError):
            self.registry.register_provider("mock", self.provider)  # duplicate check

        self.registry.unregister_provider("mock")
        self.assertNotIn("mock", self.registry.list_models())

    def test_agent_embed_task_new_document(self) -> None:
        """Verifies embedding generation, vector insertion, and EventBus signals for a new file."""
        text_content = "This is a single sentence document text for embedding generation."
        task = Task(
            description="Generate embeddings",
            metadata={
                "action": "embed",
                "document_id": "doc_abc",
                "workspace_id": "ws_123",
                "text": text_content,
                "model": "mock-embed-small",
                "chunking_strategy": "sentence",
                "namespace": "test_space"
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        res: EmbeddingResult = self.agent.execute(task)
        self.agent.after_execute(res)

        self.assertEqual(res.total_chunks, 1)
        self.assertEqual(res.indexed_chunks, 1)
        self.assertEqual(res.failed_chunks, 0)
        self.assertEqual(res.metadata.get("version"), 1)

        # Check collection exists in Vector engine
        cols = self.vector_provider.list_collections()
        self.assertEqual(len(cols), 1)
        self.assertEqual(cols[0].collection_id, "col_ws_123")
        self.assertEqual(cols[0].dimensions, 384)

        # Check records in Vector store
        namespace_records = self.vector_provider._store["col_ws_123"]["test_space"].values()
        self.assertEqual(len(namespace_records), 1)
        record = list(namespace_records)[0]
        self.assertEqual(record.metadata["document_id"], "doc_abc")
        self.assertEqual(len(record.embedding), 384)

        # Check EventBus triggers
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("embedding.started", events)
        self.assertIn("embedding.chunk.created", events)
        self.assertIn("embedding.completed", events)

    def test_agent_embed_incremental_indexing(self) -> None:
        """Verifies re-embedding is skipped if context is unchanged, and version bumps on modifications."""
        text_content = "This is a sentence. And sentence two."
        task = Task(
            description="Embed first run",
            metadata={
                "action": "embed",
                "document_id": "doc_xyz",
                "workspace_id": "ws_123",
                "text": text_content,
                "model": "mock-embed-small",
                "chunking_strategy": "sentence",
                "namespace": "test_space"
            }
        )
        # 1. First run (New document)
        res1: EmbeddingResult = self.agent.execute(task)
        self.assertEqual(res1.metadata.get("version"), 1)
        self.assertFalse(res1.metadata.get("cached", False))

        # 2. Second run (Identical content, should skip model generation and return cache)
        res2: EmbeddingResult = self.agent.execute(task)
        self.assertEqual(res2.metadata.get("version"), 1)
        self.assertTrue(res2.metadata.get("cached", False))

        # 3. Third run (Modified content, should increment version and re-index)
        task_mod = Task(
            description="Embed modified run",
            metadata={
                "action": "embed",
                "document_id": "doc_xyz",
                "workspace_id": "ws_123",
                "text": text_content + " And modified sentence three.",
                "model": "mock-embed-small",
                "chunking_strategy": "sentence",
                "namespace": "test_space"
            }
        )
        res3: EmbeddingResult = self.agent.execute(task_mod)
        self.assertEqual(res3.metadata.get("version"), 2)
        self.assertFalse(res3.metadata.get("cached", False))

        # Verify old vectors are cleared and new vectors are stored in vector engine
        namespace_records = self.vector_provider._store["col_ws_123"]["test_space"].values()
        # "This is a sentence. And sentence two. And modified sentence three." has 3 sentences -> grouped by 2 -> 2 chunks
        self.assertEqual(len(namespace_records), 2)
        for r in namespace_records:
            self.assertEqual(r.metadata["document_id"], "doc_xyz")

        # Verify reindexed event trigger
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("embedding.reindexed", events)

    def test_agent_delete_document_embeddings(self) -> None:
        """Verifies deletion task removes vector records from collection and catalog cache."""
        task_embed = Task(
            description="Embed first",
            metadata={
                "action": "embed",
                "document_id": "doc_del",
                "workspace_id": "ws_del",
                "text": "Document context data.",
                "namespace": "space_del"
            }
        )
        self.agent.execute(task_embed)

        # Check records exist in vector engine
        self.assertIn("doc_del-v-0", self.vector_provider._store["col_ws_del"]["space_del"])

        task_delete = Task(
            description="Delete embeddings",
            metadata={
                "action": "delete_document_embeddings",
                "document_id": "doc_del",
                "workspace_id": "ws_del",
                "namespace": "space_del"
            }
        )
        self.agent.validate_task(task_delete)
        self.agent.before_execute(task_delete)
        success = self.agent.execute(task_delete)
        self.agent.after_execute(success)

        self.assertTrue(success)
        # Check records deleted from vector engine provider
        self.assertNotIn("doc_del-v-0", self.vector_provider._store["col_ws_del"]["space_del"])

        # Check catalog entry is removed
        self.assertNotIn(("ws_del", "doc_del"), self.agent._indexing_catalog)

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent registrations and lookups operate safely."""
        def run_thread(tid: int) -> None:
            class DummyEmbedProvider(EmbeddingProvider):
                def generate_embeddings(self, texts, model): return [[0.0]]
                def supported_models(self): return ["dummy"]
                def supported_dimensions(self, model): return 1
                def health_check(self): return True

            pid = f"dummy-{tid}"
            self.registry.register_provider(pid, DummyEmbedProvider())
            self.assertIn(pid, self.registry._providers)
            self.registry.unregister_provider(pid)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
