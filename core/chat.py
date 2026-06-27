"""Chat Agent and Multi-turn Conversational AI Orchestration Module.

Provides abstractions, registries, memory strategies, tool execution plans,
and mock model providers for coordinate retrieval, prompt rendering, and streaming chat completions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import logging
import threading
import time
from typing import Any, Dict, Iterator, List, Optional, Set, Union
import uuid

from core.base import AgentState, AgentStatus, BaseAgent
from core.event import Event, EventBus, EventType
from core.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from core.task import Task
from core.logger import StructuredLogger

# Import Model Interface components
from core.model import (
    ModelProvider,
    InferenceRequest,
    InferenceResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ModelCapability,
    ModelRegistry,
    ModelError,
)

# Import Prompt Engine and Context Engine components
from core.prompt import PromptRegistry, PromptRequest, PromptTemplate, PromptSection
from core.context import ContextRegistry, ContextRequest, ContextSource, ContextSection


# =====================================================================
# Exceptions
# =====================================================================

class ChatError(NexusException):
    """Base exception for all Chat Agent related errors."""
    pass


class ChatValidationError(ChatError):
    """Raised when chat parameters or validations fail."""
    pass


class ChatProviderError(ChatError):
    """Raised when conversation model execution fails."""
    pass


# =====================================================================
# Core Models
# =====================================================================

@dataclass(frozen=True)
class Citation:
    """Immutable model representing a retrieved reference source.

    Attributes:
        citation_id: Unique citation ID.
        source: Source collection or service name.
        document_id: Reference document ID.
        chunk_id: Reference chunk block ID.
        relevance_score: Calculated score metrics.
        metadata: Extra citation metadata.
    """
    citation_id: str
    source: str
    document_id: str
    chunk_id: str
    relevance_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConversationMessage:
    """Immutable entry representing a message inside history.

    Attributes:
        message_id: Unique message identifier.
        role: Message role (system, user, assistant, tool).
        content: Plaintext content.
        timestamp: Time of message.
        citations: Connected citation objects.
        tool_calls: Serialized tool execution calls.
        metadata: Custom metadata payloads.
    """
    message_id: str
    role: str
    content: str
    timestamp: datetime
    citations: List[Citation] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Conversation:
    """Immutable model mapping a chat history.

    Attributes:
        conversation_id: Unique conversation identifier.
        workspace_id: Parent tenant workspace workspace_id.
        title: Conversation title.
        participants: User or agent identifier tags.
        messages: Messages sequence.
        created_at: Creation timestamp.
        updated_at: Modifying timestamp.
        metadata: Extra metadata options.
    """
    conversation_id: str
    workspace_id: str
    title: str
    participants: List[str]
    messages: List[ConversationMessage]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatRequest:
    """Parameters query package mapping chat request options.

    Attributes:
        request_id: UUID transaction tracking.
        conversation_id: Associated conversation.
        workspace_id: Workspace tenant group.
        user_id: Creator identifier user_id.
        message: Plaintext message text.
        attachments: Structured file metadata lists.
        model_preferences: Preference directives model/provider.
        retrieval_options: Context retrieval options mapping.
        tool_options: Tool configurations details.
        response_format: Output formatting schemas.
        metadata: Extra details metadata.
    """
    request_id: str
    conversation_id: str
    workspace_id: str
    user_id: str
    message: str
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    model_preferences: Dict[str, Any] = field(default_factory=dict)
    retrieval_options: Dict[str, Any] = field(default_factory=dict)
    tool_options: Dict[str, Any] = field(default_factory=dict)
    response_format: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatResponse:
    """Outcome payload generated by the ChatAgent.

    Attributes:
        response_id: Tracking ID.
        conversation_id: Conversation session identifier.
        message: assistant plaintext response.
        citations: List of source citation references.
        tool_results: Summary execution results of tools.
        token_usage: Dict mapping prompt and completion token sizes.
        latency: Processing duration latency in float seconds.
        finish_reason: Execution stop flag status.
        metadata: Extra metadata outcomes.
    """
    response_id: str
    conversation_id: str
    message: str
    citations: List[Citation] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)
    latency: float = 0.0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatSession:
    """State descriptor mapping ongoing conversation caches.

    Attributes:
        session_id: Tracking session ID.
        active_model: Expected active model name.
        memory_snapshot: Filtered history sequence.
        context_snapshot: Gathered context engines description mapping.
        status: Active state details.
        metadata: Metadata configs.
    """
    session_id: str
    active_model: str
    memory_snapshot: List[Dict[str, Any]]
    context_snapshot: Dict[str, Any]
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Pluggable Memory Strategies
# =====================================================================

class MemoryStrategy(ABC):
    """Abstract Strategy defining conversational history windowing filtering rules."""

    @abstractmethod
    def filter_messages(self, messages: List[ConversationMessage]) -> List[ConversationMessage]:
        """Slices messages arrays to retain relevant historical context limits."""
        pass


class SlidingWindowMemoryStrategy(MemoryStrategy):
    """Filters history to the last N messages sequence bounds."""

    def __init__(self, window_size: int = 5) -> None:
        if window_size <= 0:
            raise ChatValidationError("window_size must be positive.")
        self.window_size = window_size

    def filter_messages(self, messages: List[ConversationMessage]) -> List[ConversationMessage]:
        return messages[-self.window_size:]


class LastNMemoryStrategy(MemoryStrategy):
    """Filters history strictly keeping the last N elements."""

    def __init__(self, n: int = 10) -> None:
        if n <= 0:
            raise ChatValidationError("N limit size must be positive.")
        self.n = n

    def filter_messages(self, messages: List[ConversationMessage]) -> List[ConversationMessage]:
        return messages[-self.n:]


# =====================================================================
# Pluggable Tool Execution Strategies
# =====================================================================

class ToolExecutionStrategy(ABC):
    """Abstract Strategy governing executable custom tool sequences."""

    @abstractmethod
    def execute_tools(self, tool_calls: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Invokes tools lists sequentially or in parallel."""
        pass


class DefaultToolExecutionStrategy(ToolExecutionStrategy):
    """Simple sequential execution adapter for registered capability tools."""

    def execute_tools(self, tool_calls: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for call in tool_calls:
            name = call.get("name", "unknown")
            arguments = call.get("arguments", {})
            call_id = call.get("id", str(uuid.uuid4()))
            # Simulated outcome result
            results.append({
                "tool_call_id": call_id,
                "name": name,
                "status": "success",
                "result": f"Executed tool '{name}' successfully."
            })
        return results


# =====================================================================
# Pluggable Streaming Responses
# =====================================================================

class StreamingResponse(ABC):
    """Abstract iterator yielding token chunks from ongoing LLM operations."""

    @abstractmethod
    def stream_tokens(self) -> Iterator[str]:
        """Yields textual token segments iteratively."""
        pass

    @abstractmethod
    def get_citations(self) -> List[Citation]:
        """Collects citation references associated with stream content."""
        pass


class SimpleStreamingResponse(StreamingResponse):
    """Reference implementation streaming split words string sequences."""

    def __init__(self, text: str, citations: List[Citation]) -> None:
        self.text = text
        self.citations = citations

    def stream_tokens(self) -> Iterator[str]:
        for word in self.text.split(" "):
            yield word + " "
            time.sleep(0.005)

    def get_citations(self) -> List[Citation]:
        return self.citations


# =====================================================================
# Validation Utilities
# =====================================================================

def validate_chat_request(request: ChatRequest) -> None:
    """Validates parameters of a ChatRequest.

    Raises:
        ChatValidationError: If empty messages or formats are invalid.
    """
    if not request.message or not isinstance(request.message, str) or not request.message.strip():
        raise ChatValidationError("Message content text cannot be empty.")
    if not request.conversation_id:
        raise ChatValidationError("conversation_id cannot be empty.")
    if not request.workspace_id:
        raise ChatValidationError("workspace_id context cannot be empty.")
    # Check attachments validation constraints
    for idx, att in enumerate(request.attachments):
        if not att.get("name") or not att.get("type"):
            raise ChatValidationError(f"Invalid attachment schema at index: {idx}.")


# =====================================================================
# Mock Model Provider Adapter
# =====================================================================

class MockChatModelProvider(ModelProvider):
    """Mock model provider supporting chat capabilities."""

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        prompt_text = request.prompt or ""
        messages = request.messages
        last_msg = messages[-1]["content"] if messages else "Hello"

        # Simulates checking for specific queries (e.g. tools, search matches)
        content = f"Mock LLM answer matching prompt: '{last_msg}'."
        return InferenceResponse(
            request_id=str(uuid.uuid4()),
            content=content,
            finish_reason="stop",
            token_usage={"prompt_tokens": 12, "completion_tokens": 18, "total_tokens": 30},
            latency=0.04,
            provider="mock_chat",
            model=request.model
        )

    def generate_stream(self, request: InferenceRequest) -> Iterator[InferenceResponse]:
        yield self.generate(request)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        return EmbeddingResponse(
            request_id=str(uuid.uuid4()),
            embeddings=[[0.0] * 384],
            token_usage={"total_tokens": 5},
            latency=0.01,
            provider="mock_chat",
            model=request.model
        )

    def list_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                model_id="mock-chat-model",
                provider="mock_chat",
                name="Mock Chat Model",
                version="1.0.0",
                context_window=4096,
                max_output_tokens=2048,
                supported_modalities=["text"],
                capabilities=[ModelCapability.CHAT, ModelCapability.COMPLETION]
            )
        ]

    def get_model(self, model_id: str) -> ModelInfo:
        for m in self.list_models():
            if m.model_id == model_id:
                return m
        raise ChatValidationError(f"Model '{model_id}' not found.")

    def health_check(self) -> bool:
        return True

    def supports(self, capability: ModelCapability) -> bool:
        return capability in [ModelCapability.CHAT, ModelCapability.COMPLETION]


# =====================================================================
# Chat Registry
# =====================================================================

class ChatRegistry:
    """Thread-safe singleton registry managing conversations."""

    _instance: Optional["ChatRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ChatRegistry":
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
            self._conversations: Dict[str, Conversation] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def create_conversation(self, workspace_id: str, title: str, participants: List[str]) -> Conversation:
        """Saves a new conversation catalog."""
        cid = str(uuid.uuid4())
        now = datetime.utcnow()
        conv = Conversation(
            conversation_id=cid,
            workspace_id=workspace_id,
            title=title,
            participants=participants,
            messages=[],
            created_at=now,
            updated_at=now
        )
        with self._lock:
            self._conversations[cid] = conv
        return conv

    def get_conversation(self, conversation_id: str) -> Conversation:
        """Retrieves target conversation history details."""
        with self._lock:
            if conversation_id not in self._conversations:
                raise ChatValidationError(f"Conversation '{conversation_id}' not found.")
            return self._conversations[conversation_id]

    def update_conversation(self, conversation: Conversation) -> None:
        """Updates stored conversation state."""
        with self._lock:
            self._conversations[conversation.conversation_id] = conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """Removes a conversation."""
        with self._lock:
            if conversation_id in self._conversations:
                del self._conversations[conversation_id]
                return True
            return False

    def list_conversations(self, workspace_id: str) -> List[Conversation]:
        """Lists active conversations in workspace."""
        with self._lock:
            return [c for c in self._conversations.values() if c.workspace_id == workspace_id]

    def health_check(self) -> bool:
        """Checks connection integrity."""
        return True


# =====================================================================
# Chat Agent
# =====================================================================

class ChatAgent(BaseAgent):
    """System agent governing Conversational AI interactions and tool/context orchestrations."""

    def __init__(
        self,
        name: str = "ChatAgent",
        description: str = "Orchestrates chat memory histories, knowledge retrieval, and tool executions",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ) -> None:
        caps = capabilities or ["CONVERSATIONAL_AI", "TOOL_ORCHESTRATION"]
        super().__init__(name=name, description=description, version=version, capabilities=caps)
        self.registry = ChatRegistry()
        self.event_bus = EventBus()
        self.model_registry = ModelRegistry()
        self.prompt_registry = PromptRegistry()
        self.context_registry = ContextRegistry()
        self.memory_strategy: MemoryStrategy = SlidingWindowMemoryStrategy(window_size=10)
        self.tool_execution_strategy: ToolExecutionStrategy = DefaultToolExecutionStrategy()

    def initialize(self) -> None:
        """Initializes Chat agent."""
        super().initialize()
        # Ensure default templates are registered
        try:
            self.prompt_registry.register_template(PromptTemplate(
                template_id="default_chat_template",
                name="Default Chat Template",
                version="1.0.0",
                description="Concatenates context and user query",
                author="System",
                variables=[],
                sections=[
                    PromptSection("s1", "System Context", "You are a helpful assistant.\nContext: {context}", 1.0, False, {"role": "system"}),
                    PromptSection("s2", "User Message", "{query}", 2.0, True, {"role": "user"})
                ]
            ))
        except Exception:
            pass

    def validate_task(self, task: Task) -> None:
        super().validate_task(task)
        if not task.metadata or "action" not in task.metadata:
            raise TaskValidationError("Task metadata must contain an 'action' field.")

    def execute(self, task: Task) -> Any:
        action = task.metadata["action"]

        if action == "create_conversation":
            ws_id = task.metadata.get("workspace_id")
            title = task.metadata.get("title", "New Conversation")
            participants = task.metadata.get("participants", [])

            if not ws_id:
                raise ChatValidationError("Missing workspace_id parameter.")

            return self.registry.create_conversation(ws_id, title, participants)

        elif action == "send_message":
            conv_id = task.metadata.get("conversation_id")
            ws_id = task.metadata.get("workspace_id")
            user_id = task.metadata.get("user_id")
            message = task.metadata.get("message")
            attachments = task.metadata.get("attachments", [])
            model_prefs = task.metadata.get("model_preferences", {})
            ret_options = task.metadata.get("retrieval_options", {})
            tool_options = task.metadata.get("tool_options", {})
            response_format = task.metadata.get("response_format")

            req = ChatRequest(
                request_id=str(uuid.uuid4()),
                conversation_id=conv_id,
                workspace_id=ws_id,
                user_id=user_id,
                message=message,
                attachments=attachments,
                model_preferences=model_prefs,
                retrieval_options=ret_options,
                tool_options=tool_options,
                response_format=response_format
            )

            validate_chat_request(req)

            self._publish_event("chat.started", request_id=req.request_id, conversation_id=conv_id)
            start_time = time.perf_counter()

            # Retrieve conversation
            conv = self.registry.get_conversation(conv_id)

            # Check for Workspace isolation breach
            if conv.workspace_id != ws_id:
                raise ChatValidationError("Workspace tenant isolation violation.")

            # Load history & Apply Memory strategy
            filtered_history = self.memory_strategy.filter_messages(conv.messages)

            # 1. Coordinate retrieval & gather context using Context Engine
            # (Context engine gathers system, memory, vector segments)
            self._publish_event("chat.context.loaded", request_id=req.request_id)
            ctx_request = ContextRequest(
                user=user_id,
                max_tokens=2048,
                required_sources=[ContextSource.MEMORY],
                optional_sources=[ContextSource.VECTOR]
            )
            # Create a mock section from memory
            mock_sections = []
            for msg in filtered_history:
                mock_sections.append(ContextSection(
                    section_id=msg.message_id,
                    source=ContextSource.MEMORY,
                    title=msg.role,
                    content=msg.content,
                    relevance_score=1.0,
                    token_count=len(msg.content) // 4
                ))

            # Trigger Search Agent if vector search is requested
            citations = []
            if ret_options.get("enable_search", False):
                # Search matching documents snippet
                query_term = message
                from core.search import SearchAgent
                search_agent = SearchAgent()
                try:
                    search_res = search_agent.execute(Task(
                        description="Internal search",
                        metadata={
                            "action": "search",
                            "workspace_id": ws_id,
                            "query": query_term,
                            "collections": ret_options.get("collections", ["default"]),
                            "top_k": 3
                        }
                    ))
                    # Convert SearchResults to ContextSection and Citation models
                    for idx, res in enumerate(search_res.results):
                        cite_id = f"cite-{idx}"
                        citations.append(Citation(
                            citation_id=cite_id,
                            source=res.source,
                            document_id=res.document_id,
                            chunk_id=res.chunk_id,
                            relevance_score=res.score
                        ))
                        mock_sections.append(ContextSection(
                            section_id=res.result_id,
                            source=ContextSource.VECTOR,
                            title=f"Source Document {res.document_id}",
                            content=res.snippet,
                            relevance_score=res.score,
                            token_count=len(res.snippet) // 4
                        ))
                except Exception as e:
                    self.logger.warning("Search agent retrieval failed: %s", e)

            # Insert mock context sections into ContextEngine registry
            # We construct ContextResponse details directly
            context_response = self.context_registry.collect(ctx_request)
            # Override gathered sections with our formatted history & search blocks
            import dataclasses
            ctx_obj = dataclasses.replace(context_response.context, sections=mock_sections)

            # 2. Render Prompt using Prompt Engine
            self._publish_event("chat.prompt.generated", request_id=req.request_id)
            prompt_req = PromptRequest(
                context=ctx_obj,
                template="default_chat_template",
                variables={"query": message}
            )
            prompt_res = self.prompt_registry.render(prompt_req)

            # 3. Model Inference via Model Interface
            model_id = model_prefs.get("model", "mock-chat-model")
            self._publish_event("chat.model.invoked", model=model_id)

            # Lookup Model Provider in ModelRegistry
            provider_id = self.model_registry.list_providers()
            if not provider_id:
                raise ChatValidationError("No model providers registered in Model Interface.")
            provider = self.model_registry.get_provider(provider_id[0])

            # Prepare chat message messages list
            chat_messages = []
            for msg in filtered_history:
                chat_messages.append({"role": msg.role, "content": msg.content})
            chat_messages.append({"role": "user", "content": prompt_res.prompt.rendered_text})

            inf_req = InferenceRequest(
                model=model_id,
                messages=chat_messages,
                prompt=prompt_res.prompt.rendered_text
            )

            try:
                inf_res = provider.generate(inf_req)
            except Exception as e:
                self._publish_event("chat.failed", error=str(e))
                raise ChatProviderError(f"Model interface generate failed: {e}") from e

            # Handle Tool Calls
            tool_results = []
            # Check if provider returned tool execution triggers (simulated inside metadata or response)
            sim_tool_calls = inf_res.metadata.get("tool_calls", [])
            if sim_tool_calls:
                tool_results = self.tool_execution_strategy.execute_tools(sim_tool_calls, {})

            # Append Messages to history (User + Assistant)
            user_msg = ConversationMessage(
                message_id=str(uuid.uuid4()),
                role="user",
                content=message,
                timestamp=datetime.utcnow()
            )
            assistant_msg = ConversationMessage(
                message_id=str(uuid.uuid4()),
                role="assistant",
                content=inf_res.content,
                timestamp=datetime.utcnow(),
                citations=citations,
                tool_calls=sim_tool_calls
            )

            # Update conversation messages sequence
            updated_messages = list(conv.messages) + [user_msg, assistant_msg]
            updated_conv = dataclasses.replace(conv, messages=updated_messages, updated_at=datetime.utcnow())
            self.registry.update_conversation(updated_conv)

            duration = time.perf_counter() - start_time
            self._publish_event("chat.completed", conversation_id=conv_id)

            return ChatResponse(
                response_id=inf_res.request_id,
                conversation_id=conv_id,
                message=inf_res.content,
                citations=citations,
                tool_results=tool_results,
                token_usage=inf_res.token_usage,
                latency=duration,
                finish_reason=inf_res.finish_reason
            )

        elif action == "stream":
            conv_id = task.metadata.get("conversation_id")
            ws_id = task.metadata.get("workspace_id")
            user_id = task.metadata.get("user_id")
            message = task.metadata.get("message")
            model_prefs = task.metadata.get("model_preferences", {})

            if not conv_id or not ws_id or not message:
                raise ChatValidationError("Missing parameters (conversation_id, workspace_id, message).")

            conv = self.registry.get_conversation(conv_id)
            if conv.workspace_id != ws_id:
                raise ChatValidationError("Workspace tenant isolation violation.")

            self._publish_event("chat.stream.started", conversation_id=conv_id)

            # Create mock Streaming Response
            citations = [
                Citation("cite-stream-1", "knowledge_base", "doc_stream_1", "chunk_stream_0", 0.95)
            ]
            response_text = f"Mock streaming response answer to your message: '{message}'."

            # Append messages sequence
            user_msg = ConversationMessage(
                message_id=str(uuid.uuid4()),
                role="user",
                content=message,
                timestamp=datetime.utcnow()
            )
            assistant_msg = ConversationMessage(
                message_id=str(uuid.uuid4()),
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow(),
                citations=citations
            )
            import dataclasses
            updated_conv = dataclasses.replace(
                conv,
                messages=list(conv.messages) + [user_msg, assistant_msg],
                updated_at=datetime.utcnow()
            )
            self.registry.update_conversation(updated_conv)

            self._publish_event("chat.completed", conversation_id=conv_id)
            return SimpleStreamingResponse(response_text, citations)

        elif action == "history":
            conv_id = task.metadata.get("conversation_id")
            if not conv_id:
                raise ChatValidationError("Missing conversation_id parameter.")
            return self.registry.get_conversation(conv_id).messages

        elif action == "delete_conversation":
            conv_id = task.metadata.get("conversation_id")
            if not conv_id:
                raise ChatValidationError("Missing conversation_id parameter.")
            return self.registry.delete_conversation(conv_id)

        else:
            raise ChatValidationError(f"Unsupported action: {action}")

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ChatAgent",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
