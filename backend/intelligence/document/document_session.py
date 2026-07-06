"""Thread-safe coordinator orchestrating multi-turn document sessions, caching, and event buses."""

import uuid
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.intelligence.document.conversation import DocumentConversationResponse
from backend.intelligence.document.query_engine import DocumentQueryEngine
from backend.intelligence.document.reasoning import CrossDocumentReasoning
from backend.intelligence.document.citation_manager import CitationManager
from backend.intelligence.document.response_generator import DocumentResponseGenerator
from backend.intelligence.document.workspace_memory import WorkspaceMemory
from backend.intelligence.document.knowledge_cache import KnowledgeCache


class DocumentSessionManager:
    """Manages active conversational workflows, locks, caches, and publishers."""

    _instance: Optional["DocumentSessionManager"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "DocumentSessionManager":
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
            self.query_engine = DocumentQueryEngine()
            self.reasoning_engine = CrossDocumentReasoning()
            self.citation_manager = CitationManager()
            self.generator = DocumentResponseGenerator()
            self.memory = WorkspaceMemory()
            self.cache = KnowledgeCache()
            self.event_bus = EventBus()
            self._session_locks: Dict[str, threading.Lock] = {}
            self._locks_lock = threading.Lock()
            self._initialized = True

    def _get_session_lock(self, conversation_id: str) -> threading.Lock:
        """Retrieves or registers a thread lock for conversational session isolation."""
        with self._locks_lock:
            if conversation_id not in self._session_locks:
                self._session_locks[conversation_id] = threading.Lock()
            return self._session_locks[conversation_id]

    def chat_turn(
        self,
        workspace_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> DocumentConversationResponse:
        """Processes a single conversational turn in a thread-safe manner."""
        opts = options or {}
        
        # 1. Resolve or create conversation ID
        conv_id = conversation_id or f"conv-{str(uuid.uuid4())[:8]}"

        # Acquire lock for target session to prevent race conditions on concurrent requests
        lock = self._get_session_lock(conv_id)
        with lock:
            # 2. Check Low-Latency cache
            cached = self.cache.lookup(workspace_id, query)
            if cached and not opts.get("force_refresh", False):
                # Ensure conversation_id matches current request context
                cached["conversation_id"] = conv_id
                return DocumentConversationResponse(**cached)

            # Publish event: document.query.started
            self.event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="DocumentSession",
                payload={
                    "event": "document.query.started",
                    "workspace_id": workspace_id,
                    "conversation_id": conv_id,
                    "query": query,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))

            # 3. Retrieve short-term history
            history = self.memory.get_messages(conv_id)
            if not history and conversation_id:
                # Save conversation metadata in DB storage if newly created with custom ID
                self.memory.save_conversation(conv_id, workspace_id, f"Chat Session {conv_id}")
            elif not history:
                self.memory.save_conversation(conv_id, workspace_id, f"Chat Session {conv_id}")

            # 4. Search document chunks
            search_limit = opts.get("limit", 4)
            search_mode = opts.get("search_mode", "HYBRID")
            retrieved_chunks = self.query_engine.search_chunks(
                workspace_id=workspace_id,
                query=query,
                document_ids=document_ids,
                search_mode=search_mode,
                limit=search_limit,
                options=opts
            )

            # 7. Map citations & names
            document_names = {}
            active_docs = self.query_engine.get_workspace_documents(workspace_id, document_ids)
            for d_id, (fname, _) in active_docs.items():
                document_names[d_id] = fname

            # 5. Extract related documents filenames
            related_docs = list(set([
                document_names.get(
                    c.chunk_id.split("-")[0] + "-" + c.chunk_id.split("-")[1]
                    if (c.chunk_id.startswith("doc-") and len(c.chunk_id.split("-")) >= 2)
                    else c.chunk_id.split("-")[0],
                    c.chunk_id.split("-")[0]
                )
                for c in retrieved_chunks if c.chunk_id
            ]))

            # 6. Execute cross-document reasoning
            reasoning_ctx, overall_conf = self.reasoning_engine.reason_over_documents(query, retrieved_chunks)

            citations = self.citation_manager.create_citations(
                retrieved_chunks=retrieved_chunks,
                document_names=document_names,
                confidence_factor=overall_conf
            )

            # 8. Generate answer
            answer, summary, suggestions = self.generator.generate_response(
                query=query,
                chunks=retrieved_chunks,
                reasoning_context=reasoning_ctx,
                history=history
            )

            # 9. Save message turns to relational history database
            self.memory.add_message(conv_id, "user", query)
            self.memory.add_message(conv_id, "assistant", answer)

            # Publish event: document.memory.updated
            self.event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="DocumentSession",
                payload={
                    "event": "document.memory.updated",
                    "workspace_id": workspace_id,
                    "conversation_id": conv_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))

            # 10. Log search to searches log
            self.memory.log_search(
                workspace_id=workspace_id,
                query=query,
                search_mode=search_mode,
                limit=search_limit,
                results_count=len(retrieved_chunks)
            )

            # Compute flat evidence text
            evidence_text = "\n\n".join([c.text for c in retrieved_chunks])

            response = DocumentConversationResponse(
                answer=answer,
                summary=summary,
                evidence=evidence_text,
                citations=citations,
                confidence=overall_conf,
                related_documents=related_docs,
                suggested_follow_up_questions=suggestions,
                conversation_id=conv_id
            )

            # 11. Cache response
            self.cache.store(workspace_id, query, response.model_dump())

            # Publish events: document.response.generated & document.query.completed
            self.event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="DocumentSession",
                payload={
                    "event": "document.response.generated",
                    "conversation_id": conv_id,
                    "confidence": overall_conf,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            self.event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="DocumentSession",
                payload={
                    "event": "document.query.completed",
                    "workspace_id": workspace_id,
                    "conversation_id": conv_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))

            return response
