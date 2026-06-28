import concurrent.futures
from datetime import datetime
import threading
import time
from typing import Any, Dict, List, Optional
import unittest
import uuid

from backend.agents.chat import (
    ChatError,
    ChatValidationError,
    ChatProviderError,
    Citation,
    ConversationMessage,
    Conversation,
    ChatRequest,
    ChatResponse,
    ChatSession,
    MemoryStrategy,
    SlidingWindowMemoryStrategy,
    LastNMemoryStrategy,
    ToolExecutionStrategy,
    DefaultToolExecutionStrategy,
    StreamingResponse,
    SimpleStreamingResponse,
    MockChatModelProvider,
    ChatRegistry,
    ChatAgent,
    validate_chat_request,
)
from backend.runtime.base import AgentState, AgentStatus
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.task import Task
from backend.interfaces.model import ModelRegistry
from backend.agents.search import SearchRegistry, MockSearchProvider


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestChatSystem(unittest.TestCase):
    """Suite of tests covering pluggable memory strategies and orchestrating chat agent interactions."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        # Setup Chat Registry
        self.registry = ChatRegistry()
        with self.registry._lock:
            self.registry._conversations.clear()

        # Setup Model Interface Provider
        self.model_registry = ModelRegistry()
        with self.model_registry._lock:
            self.model_registry._providers.clear()
        self.model_provider = MockChatModelProvider()
        self.model_registry.register_provider("mock_chat", self.model_provider)

        # Setup Search Registry for retrieval
        self.search_registry = SearchRegistry()
        with self.search_registry._lock:
            self.search_registry._providers.clear()
        self.search_provider = MockSearchProvider()
        self.search_registry.register_provider("mock_search", self.search_provider)

        self.agent = ChatAgent()
        self.agent.initialize()

    def test_memory_strategies(self) -> None:
        """Verifies messages windowing limits on sliding window and Last N strategies."""
        messages = [
            ConversationMessage(str(i), "user", f"msg {i}", datetime.utcnow())
            for i in range(8)
        ]

        # 1. Sliding Window
        sliding = SlidingWindowMemoryStrategy(window_size=3)
        filtered_sliding = sliding.filter_messages(messages)
        self.assertEqual(len(filtered_sliding), 3)
        self.assertEqual(filtered_sliding[0].message_id, "5")
        self.assertEqual(filtered_sliding[2].message_id, "7")

        # 2. Last N
        last_n = LastNMemoryStrategy(n=5)
        filtered_last_n = last_n.filter_messages(messages)
        self.assertEqual(len(filtered_last_n), 5)
        self.assertEqual(filtered_last_n[0].message_id, "3")
        self.assertEqual(filtered_last_n[4].message_id, "7")

    def test_validation_utilities(self) -> None:
        """Verifies validation constraints reject bad parameter request options."""
        # Valid Request
        req = ChatRequest(
            request_id="req_1",
            conversation_id="conv_1",
            workspace_id="ws_1",
            user_id="user_1",
            message="hello bot",
            attachments=[{"name": "doc.pdf", "type": "pdf"}]
        )
        validate_chat_request(req)

        # Empty Message
        with self.assertRaises(ChatValidationError):
            validate_chat_request(ChatRequest("r", "conv", "ws", "u", ""))

        # Missing Conversation ID
        with self.assertRaises(ChatValidationError):
            validate_chat_request(ChatRequest("r", "", "ws", "u", "msg"))

        # Invalid Attachment format (missing type)
        with self.assertRaises(ChatValidationError):
            validate_chat_request(ChatRequest("r", "conv", "ws", "u", "msg", [{"name": "doc.pdf"}]))

    def test_registry_singleton(self) -> None:
        """Verifies singleton pattern constraints of ChatRegistry."""
        registry2 = ChatRegistry()
        self.assertIs(self.registry, registry2)

    def test_registry_lifecycle(self) -> None:
        """Verifies conversation registration and unregistration lifecycle."""
        conv = self.registry.create_conversation("ws_123", "Main Conversation", ["user_1"])
        self.assertEqual(conv.title, "Main Conversation")
        self.assertEqual(len(conv.messages), 0)

        # Fetch
        fetched = self.registry.get_conversation(conv.conversation_id)
        self.assertEqual(fetched.conversation_id, conv.conversation_id)

        # Delete
        success = self.registry.delete_conversation(conv.conversation_id)
        self.assertTrue(success)
        with self.assertRaises(ChatValidationError):
            self.registry.get_conversation(conv.conversation_id)

    def test_agent_create_conversation_task(self) -> None:
        """Verifies task action to save new conversation database entries."""
        task = Task(
            description="Create conversation",
            metadata={
                "action": "create_conversation",
                "workspace_id": "ws_test",
                "title": "Agent Chat session",
                "participants": ["user_1"]
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        conv: Conversation = self.agent.execute(task)
        self.agent.after_execute(conv)

        self.assertEqual(conv.title, "Agent Chat session")
        self.assertEqual(conv.workspace_id, "ws_test")

    def test_agent_send_message_task(self) -> None:
        """Verifies sending message triggers prompts, models generation, and event notifications."""
        conv = self.registry.create_conversation("ws_test", "Chat title", ["user_1"])
        cid = conv.conversation_id

        task = Task(
            description="Send message task",
            metadata={
                "action": "send_message",
                "conversation_id": cid,
                "workspace_id": "ws_test",
                "user_id": "user_1",
                "message": "hello agent framework",
                "retrieval_options": {
                    "enable_search": True,
                    "collections": ["wiki"]
                }
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        res: ChatResponse = self.agent.execute(task)
        self.agent.after_execute(res)

        self.assertEqual(res.conversation_id, cid)
        self.assertIn("Mock LLM answer", res.message)
        self.assertEqual(res.finish_reason, "stop")

        # Verify message appended inside history logs
        history = self.registry.get_conversation(cid).messages
        self.assertEqual(len(history), 2)  # User + Assistant
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[1].role, "assistant")

        # Confirm EventBus triggers
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("chat.started", events)
        self.assertIn("chat.context.loaded", events)
        self.assertIn("chat.prompt.generated", events)
        self.assertIn("chat.model.invoked", events)
        self.assertIn("chat.completed", events)

    def test_agent_stream_task(self) -> None:
        """Verifies streaming response generation yields tokens correctly."""
        conv = self.registry.create_conversation("ws_test", "Chat title", ["user_1"])
        cid = conv.conversation_id

        task = Task(
            description="Stream message task",
            metadata={
                "action": "stream",
                "conversation_id": cid,
                "workspace_id": "ws_test",
                "user_id": "user_1",
                "message": "hello steam agent"
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        stream_res: SimpleStreamingResponse = self.agent.execute(task)
        self.agent.after_execute(stream_res)

        # Iterate tokens
        tokens = list(stream_res.stream_tokens())
        self.assertGreater(len(tokens), 2)
        self.assertIn("Mock ", tokens[0])

        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("chat.stream.started", events)

    def test_tenant_isolation_breach(self) -> None:
        """Verifies workspace isolation constraints raise ValidationError."""
        conv = self.registry.create_conversation("ws_correct", "Chat title", ["user_1"])
        cid = conv.conversation_id

        task = Task(
            description="Tenant isolation breach query",
            metadata={
                "action": "send_message",
                "conversation_id": cid,
                "workspace_id": "ws_attacker",
                "user_id": "user_1",
                "message": "try breach"
            }
        )
        with self.assertRaises(ChatValidationError):
            self.agent.execute(task)

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent registrations and lookups operate safely."""
        def run_thread(tid: int) -> None:
            cid = f"conv-{tid}"
            conv = Conversation(
                conversation_id=cid,
                workspace_id="ws_1",
                title=f"title {tid}",
                participants=[],
                messages=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.registry.update_conversation(conv)
            self.assertEqual(self.registry.get_conversation(cid).title, f"title {tid}")
            self.registry.delete_conversation(cid)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
