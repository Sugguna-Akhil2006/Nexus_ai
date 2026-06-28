import unittest
import threading
from typing import Any

from backend.runtime.base import BaseAgent, AgentStatus
from backend.runtime.registry import AgentRegistry
from backend.runtime.task import Task
from backend.runtime.exceptions import (
    AgentRegistrationError,
    AgentNotFoundError,
)


class DummyAgent(BaseAgent):

    def execute(self, task: Task) -> Any:
        return "dummy execution"


class TestAgentRegistry(unittest.TestCase):

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

        self.agent1 = DummyAgent(
            name="AgentOne",
            description="First Dummy Agent",
            version="1.0.0",
            capabilities=["nlp", "search"]
        )
        self.agent2 = DummyAgent(
            name="AgentTwo",
            description="Second Dummy Agent",
            version="1.0.0",
            capabilities=["math", "search"]
        )

    def test_singleton(self) -> None:
        registry_two = AgentRegistry()
        self.assertIs(self.registry, registry_two)

    def test_register_and_get(self) -> None:
        self.registry.register(self.agent1)
        self.assertEqual(self.registry.count(), 1)

        retrieved = self.registry.get(self.agent1.id)
        self.assertIs(retrieved, self.agent1)

        retrieved_by_name = self.registry.get_by_name(self.agent1.name)
        self.assertIs(retrieved_by_name, self.agent1)

    def test_register_duplicate_raises(self) -> None:
        self.registry.register(self.agent1)
        with self.assertRaises(AgentRegistrationError):
            self.registry.register(self.agent1)

        duplicate_id_agent = DummyAgent(
            id=self.agent1.id,
            name="DifferentName",
            description="Description",
            version="1.0.0"
        )
        with self.assertRaises(AgentRegistrationError):
            self.registry.register(duplicate_id_agent)

        duplicate_name_agent = DummyAgent(
            name="AgentOne",
            description="Description",
            version="1.0.0"
        )
        with self.assertRaises(AgentRegistrationError):
            self.registry.register(duplicate_name_agent)

    def test_unregister(self) -> None:
        self.registry.register(self.agent1)
        self.assertTrue(self.registry.exists(self.agent1.id))

        self.registry.unregister(self.agent1.id)
        self.assertFalse(self.registry.exists(self.agent1.id))
        self.assertEqual(self.registry.count(), 0)

        with self.assertRaises(AgentNotFoundError):
            self.registry.get(self.agent1.id)

    def test_list_and_count(self) -> None:
        self.registry.register(self.agent1)
        self.registry.register(self.agent2)

        agents = self.registry.list_agents()
        self.assertEqual(len(agents), 2)
        self.assertIn(self.agent1, agents)
        self.assertIn(self.agent2, agents)
        self.assertEqual(self.registry.count(), 2)

    def test_capability_indexing(self) -> None:
        self.registry.register(self.agent1)
        self.registry.register(self.agent2)

        search_agents = self.registry.get_by_capability("search")
        self.assertEqual(len(search_agents), 2)
        self.assertIn(self.agent1, search_agents)
        self.assertIn(self.agent2, search_agents)

        nlp_agents = self.registry.get_by_capability("nlp")
        self.assertEqual(len(nlp_agents), 1)
        self.assertIn(self.agent1, nlp_agents)

        none_agents = self.registry.get_by_capability("non-existent")
        self.assertEqual(len(none_agents), 0)

    def test_health_monitoring(self) -> None:
        self.agent1.status = AgentStatus.HEALTHY
        self.agent2.status = AgentStatus.UNHEALTHY

        self.registry.register(self.agent1)
        self.registry.register(self.agent2)

        healthy = self.registry.healthy_agents()
        self.assertEqual(len(healthy), 1)
        self.assertIn(self.agent1, healthy)

        unhealthy = self.registry.unhealthy_agents()
        self.assertEqual(len(unhealthy), 1)
        self.assertIn(self.agent2, unhealthy)

    def test_thread_safety(self) -> None:
        def register_worker(index: int) -> None:
            agent = DummyAgent(
                name=f"ThreadAgent_{index}",
                description="Thread test agent",
                version="1.0.0",
                capabilities=["thread-safe"]
            )
            self.registry.register(agent)

        threads = []
        for i in range(50):
            t = threading.Thread(target=register_worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(self.registry.count(), 50)
        self.assertEqual(len(self.registry.get_by_capability("thread-safe")), 50)


if __name__ == "__main__":
    unittest.main()
