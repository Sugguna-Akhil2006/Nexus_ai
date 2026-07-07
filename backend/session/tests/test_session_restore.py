"""Tests for full session creation, updates, rebuilding, and restoration."""

import unittest
from backend.session.session_manager import SessionManager
from backend.session.models import CheckpointType, Decision, DecisionType
from backend.runtime.event import Event, EventBus, EventType


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestSessionRestore(unittest.TestCase):
    """Verifies that SessionManager correctly restores, rebuilds, and publishes events."""

    def setUp(self) -> None:
        self.manager = SessionManager()
        self.event_receiver = MockEventReceiver()
        self.event_bus = EventBus()
        # Reset the event bus singleton state between tests
        with self.event_bus._lock:
            self.event_bus._subscribers.clear()
            self.event_bus._queue.clear()
            self.event_bus._history.clear()
            self.event_bus._statistics = {
                "published_count": 0,
                "dispatched_count": 0,
                "failed_count": 0,
                "by_type": {}
            }
        # Subscribe to all events
        self.event_bus.subscribe("*", self.event_receiver)

    def test_session_lifecycle(self) -> None:
        """Tests session creation, status updates, timelines, and restoration."""
        # 1. Create session
        inst = self.manager.create_session("Coding Session")
        session_id = inst.model.session_id

        # Dispatch events
        self.event_bus.dispatch_all()

        # Check session.created event was published
        created_events = [e for e in self.event_receiver.events if e.event_type == EventType.SESSION_CREATED]
        self.assertEqual(len(created_events), 1)
        self.assertEqual(created_events[0].payload["session_id"], session_id)

        # 2. Update workspace status
        self.manager.update_workspace_status(
            session_id=session_id,
            current_project="Nexus UI",
            objective="Develop console layout",
            add_file="console.py",
            add_task="Design styling"
        )

        self.event_bus.dispatch_all()
        ws_events = [e for e in self.event_receiver.events if e.event_type == EventType.WORKSPACE_UPDATED]
        self.assertEqual(len(ws_events), 1)

        # 3. Create checkpoints
        self.manager.checkpoint_session(
            session_id=session_id,
            checkpoint_type=CheckpointType.WORKFLOW_START,
            description="Start of frontend coding"
        )

        self.event_bus.dispatch_all()
        chk_events = [e for e in self.event_receiver.events if e.event_type == EventType.CHECKPOINT_CREATED]
        self.assertEqual(len(chk_events), 1)

        # 4. Restore session
        restored = self.manager.restore_session(session_id)
        self.assertEqual(restored.workspace_memory.get_snapshot().current_project, "Nexus UI")
        self.assertIsNotNone(restored.model.restored_at)

        self.event_bus.dispatch_all()
        restored_events = [e for e in self.event_receiver.events if e.event_type == EventType.SESSION_RESTORED]
        self.assertEqual(len(restored_events), 1)

    def test_context_rebuilt(self) -> None:
        """Tests reconstructing context for a brand new session using the rebuilder."""
        inst = self.manager.create_session("New Empty Session")
        session_id = inst.model.session_id

        decisions = [
            Decision(title="Use React", description="Architecture choice", decision_type=DecisionType.ARCHITECTURE)
        ]
        goals = ["Rebuild workspace", "Test components"]
        pending = ["Task A"]

        inst.rebuilder.rebuild_context(
            active_project="Nexus rebuild",
            goals=goals,
            decisions=decisions,
            pending_tasks=pending,
            recent_files=["index.js"],
            knowledge_query=None
        )

        # Dispatch events
        self.event_bus.dispatch_all()

        # Assert rebuilt state
        ws = inst.workspace_memory.get_snapshot()
        self.assertEqual(ws.current_project, "Nexus rebuild")
        self.assertEqual(ws.recent_files, ["index.js"])
        self.assertEqual(ws.pending_tasks, ["Task A"])

        # Check event
        rebuilt_events = [e for e in self.event_receiver.events if e.event_type == EventType.CONTEXT_REBUILT]
        self.assertEqual(len(rebuilt_events), 1)
        self.assertEqual(rebuilt_events[0].payload["project"], "Nexus rebuild")
