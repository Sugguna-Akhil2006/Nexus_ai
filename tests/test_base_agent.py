import unittest
import uuid
from typing import Any

from core.base import BaseAgent, AgentState, AgentStatus
from core.task import Task
from core.exceptions import (
    AgentStateError,
    TaskValidationError,
)


class ConcreteTestAgent(BaseAgent):
    """A concrete implementation of BaseAgent for testing purposes."""

    def execute(self, task: Task) -> Any:
        return f"Executed: {task.description}"


class TestBaseAgent(unittest.TestCase):

    def setUp(self) -> None:
        self.agent = ConcreteTestAgent(
            name="TestAgent",
            description="Agent for testing",
            version="1.0.0",
            capabilities=["testing"]
        )

    def test_initial_state(self) -> None:
        self.assertEqual(self.agent.state, AgentState.UNINITIALIZED)
        self.assertEqual(self.agent.status, AgentStatus.UNINITIALIZED)
        self.assertIsInstance(self.agent.id, uuid.UUID)

    def test_initialize(self) -> None:
        self.agent.initialize()
        self.assertEqual(self.agent.state, AgentState.IDLE)
        self.assertEqual(self.agent.status, AgentStatus.HEALTHY)

    def test_initialize_already_initialized_raises(self) -> None:
        self.agent.initialize()
        with self.assertRaises(AgentStateError):
            self.agent.initialize()

    def test_validate_task_not_idle_raises(self) -> None:
        task = Task(description="Test task")
        with self.assertRaises(AgentStateError):
            self.agent.validate_task(task)

    def test_validate_task_invalid_raises(self) -> None:
        self.agent.initialize()
        with self.assertRaises(TaskValidationError):
            self.agent.validate_task(None)  # type: ignore

        task = Task(description="")
        with self.assertRaises(TaskValidationError):
            self.agent.validate_task(task)

    def test_lifecycle_success(self) -> None:
        self.agent.initialize()
        task = Task(description="Run test")

        self.agent.validate_task(task)
        self.agent.before_execute(task)
        self.assertEqual(self.agent.state, AgentState.BUSY)

        result = self.agent.execute(task)
        self.assertEqual(result, "Executed: Run test")

        final_result = self.agent.after_execute(result)
        self.assertEqual(final_result, "Executed: Run test")
        self.assertEqual(self.agent.state, AgentState.IDLE)

    def test_handle_error(self) -> None:
        err = ValueError("Something went wrong")
        self.agent.handle_error(err)
        self.assertEqual(self.agent.state, AgentState.ERROR)
        self.assertEqual(self.agent.status, AgentStatus.UNHEALTHY)

    def test_shutdown(self) -> None:
        self.agent.shutdown()
        self.assertEqual(self.agent.state, AgentState.SHUTDOWN)

    def test_serialization(self) -> None:
        data = self.agent.to_dict()
        self.assertEqual(data["name"], "TestAgent")
        self.assertEqual(data["version"], "1.0.0")

        new_agent = ConcreteTestAgent.from_dict(data)
        self.assertEqual(new_agent.name, "TestAgent")
        self.assertEqual(new_agent.version, "1.0.0")
        self.assertEqual(new_agent.id, self.agent.id)


if __name__ == "__main__":
    unittest.main()
