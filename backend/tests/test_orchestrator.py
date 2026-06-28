from datetime import datetime
import threading
from typing import Any, Dict, List
import unittest
import uuid

from backend.runtime.base import AgentState, AgentStatus, BaseAgent
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import NexusException
from backend.agents.orchestrator import (
    AgentCapability,
    AgentRegistry,
    AgentRequest,
    AgentResponse,
    AgentValidationError,
    DefaultAgentSelectionStrategy,
    MergeAggregationStrategy,
    OrchestrationExecutionPlan,
    OrchestrationPlanError,
    OrchestratorAgent,
    ResultAggregationStrategy,
)
from backend.runtime.task import Task


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class DummyWorkerAgent(BaseAgent):
    """Specialized mock agent for orchestrator testing."""

    def execute(self, task: Task) -> Any:
        return {str(self.id): f"Result from {self.name}"}


class CrashingWorkerAgent(BaseAgent):
    """Mock agent designed to fail execution once and then succeed on retry."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.failures = 0

    def execute(self, task: Task) -> Any:
        if self.failures == 0:
            self.failures += 1
            raise RuntimeError("Primary failure")
        return {str(self.id): "Success on retry"}


class TestOrchestratorSystem(unittest.TestCase):
    """Suite of tests covering the Orchestrator Agent and Framework."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        with self.registry._lock:
            self.registry._agents.clear()
        self.event_bus = EventBus()
        self.event_bus.clear()

        # Initialize Orchestrator
        self.orchestrator = OrchestratorAgent()
        self.orchestrator.initialize()

    def test_singleton_registry(self) -> None:
        """Verifies that AgentRegistry behaves as a singleton."""
        registry2 = AgentRegistry()
        self.assertIs(self.registry, registry2)

    def test_agent_registration_validation(self) -> None:
        """Verifies validations enforce agent ID uniqueness and capability searches."""
        agent = DummyWorkerAgent(
            name="ChatWorker",
            description="",
            version="1.0.0",
            capabilities=[AgentCapability.CHAT]
        )

        # Register
        self.registry.register_agent(str(agent.id), agent)
        self.assertIn(agent, self.registry.list_agents())

        # Duplicate ID check
        with self.assertRaises(AgentValidationError):
            self.registry.register_agent(str(agent.id), agent)

        # Lookup capability matches
        matches = self.registry.find_by_capability(AgentCapability.CHAT)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].id, agent.id)

    def test_agent_selection_prioritizes_idle_healthy(self) -> None:
        """Verifies default agent selection prioritizes healthy and Idle agents."""
        a1 = DummyWorkerAgent(
            name="Chat1", description="", version="1.0.0",
            capabilities=[AgentCapability.CHAT]
        )
        a1.initialize()
        a1.state = AgentState.BUSY  # busy

        a2 = DummyWorkerAgent(
            name="Chat2", description="", version="1.0.0",
            capabilities=[AgentCapability.CHAT]
        )
        a2.initialize()
        a2.state = AgentState.IDLE  # idle

        self.registry.register_agent(str(a1.id), a1)
        self.registry.register_agent(str(a2.id), a2)

        strategy = DefaultAgentSelectionStrategy()
        selected = strategy.select_agent(self.registry, AgentCapability.CHAT)

        # Should select the Idle one (a2)
        self.assertEqual(selected.id, a2.id)

    def test_orchestration_execution_and_events(self) -> None:
        """Verifies execution planning, parallel dispatch, and results aggregation."""
        # Register specialized agents
        doc_agent = DummyWorkerAgent(
            name="DocProc",
            description="",
            version="1.0.0",
            capabilities=[AgentCapability.DOCUMENT_PROCESSING]
        )
        search_agent = DummyWorkerAgent(
            name="Search",
            description="",
            version="1.0.0",
            capabilities=[AgentCapability.SEARCH]
        )

        self.registry.register_agent(str(doc_agent.id), doc_agent)
        self.registry.register_agent(str(search_agent.id), search_agent)

        # Trigger event bus tracking
        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        # Create user request triggering both agents
        request = AgentRequest(
            request_id="req1",
            user_id="user123",
            input="Please process document and search details"
        )

        response = self.orchestrator.handle(request)

        # Verify output aggregation
        self.assertEqual(response.status, "SUCCESS")
        self.assertIn(str(doc_agent.id), response.outputs)
        self.assertIn(str(search_agent.id), response.outputs)
        self.assertEqual(response.outputs[str(doc_agent.id)], "Result from DocProc")

        # Check published events
        self.event_bus.dispatch_all()
        event_names = [e.payload["event_name"] for e in receiver.events]
        self.assertIn("orchestrator.request.received", event_names)
        self.assertIn("orchestrator.plan.created", event_names)
        self.assertIn("orchestrator.execution.started", event_names)
        self.assertIn("orchestrator.execution.completed", event_names)

    def test_fallback_strategies(self) -> None:
        """Verifies fallback strategy modes: abort, retry, ignore."""
        crashing = CrashingWorkerAgent(
            name="Crasher",
            description="",
            version="1.0.0",
            capabilities=[AgentCapability.CHAT]
        )
        self.registry.register_agent(str(crashing.id), crashing)

        # Case 1: abort (raises error)
        req_abort = AgentRequest(
            request_id="r_abort",
            user_id="u",
            input="chat with crasher",
            metadata={"fallback_strategy": "abort"}
        )
        res_abort = self.orchestrator.handle(req_abort)
        self.assertEqual(res_abort.status, "FAILURE")

        # Case 2: retry (succeeds on second attempt)
        crashing.failures = 0  # reset
        crashing.state = AgentState.IDLE
        crashing.status = AgentStatus.HEALTHY
        req_retry = AgentRequest(
            request_id="r_retry",
            user_id="u",
            input="chat with crasher",
            metadata={"fallback_strategy": "retry"}
        )
        res_retry = self.orchestrator.handle(req_retry)
        self.assertEqual(res_retry.status, "SUCCESS")
        self.assertEqual(res_retry.outputs[str(crashing.id)], "Success on retry")

        # Case 3: ignore (records status failed, does not crash orchestrator)
        crashing.failures = 0  # reset
        crashing.state = AgentState.IDLE
        crashing.status = AgentStatus.HEALTHY
        req_ignore = AgentRequest(
            request_id="r_ignore",
            user_id="u",
            input="chat with crasher",
            metadata={"fallback_strategy": "ignore"}
        )
        res_ignore = self.orchestrator.handle(req_ignore)
        self.assertEqual(res_ignore.status, "SUCCESS")
        self.assertIn("error", res_ignore.outputs[str(crashing.id)])

    def test_thread_safety_concurrency(self) -> None:
        """Verifies concurrent execution handling on the Orchestrator."""
        worker = DummyWorkerAgent(
            name="Chat",
            description="",
            version="1.0.0",
            capabilities=[AgentCapability.CHAT]
        )
        self.registry.register_agent(str(worker.id), worker)

        num_threads = 8
        requests_per_thread = 10

        results = []
        results_lock = threading.Lock()

        def run_worker() -> None:
            for _ in range(requests_per_thread):
                req = AgentRequest(
                    request_id=str(uuid.uuid4()),
                    user_id="concur",
                    input="chat with agent"
                )
                res = self.orchestrator.handle(req)
                with results_lock:
                    results.append(res)

        threads = [threading.Thread(target=run_worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), num_threads * requests_per_thread)
        for res in results:
            self.assertEqual(res.status, "SUCCESS")


if __name__ == "__main__":
    unittest.main()
