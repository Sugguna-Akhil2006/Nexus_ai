from datetime import datetime
import threading
from typing import Any, Dict, List
import unittest
import uuid

from core.context import Context, ContextSection, ContextSource
from core.event import Event, EventBus, EventType
from core.prompt import (
    CircularInheritanceError,
    DefaultPromptOptimizer,
    DefaultPromptRenderer,
    Prompt,
    PromptOptimizer,
    PromptRegistry,
    PromptRenderer,
    PromptRequest,
    PromptResponse,
    PromptSection,
    PromptTemplate,
    PromptValidationError,
    PromptVariable,
    TemplateNotFoundError,
)


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class CustomPromptRenderer(PromptRenderer):
    """Custom renderer for verifying overrides hooks."""

    def render(self, request: PromptRequest, resolved_template: PromptTemplate) -> Prompt:
        return Prompt(
            prompt_id=uuid.uuid4(),
            template_id=resolved_template.template_id,
            rendered_text="Custom Rendered Output",
            system_prompt=None,
            user_prompt="Custom Rendered Output",
            messages=[],
            estimated_tokens=5,
            created_at=datetime.utcnow()
        )


class TestPromptSystem(unittest.TestCase):
    """Suite of tests covering the Prompt Engine and Registry system."""

    def setUp(self) -> None:
        self.registry = PromptRegistry()
        with self.registry._lock:
            self.registry._templates.clear()
            self.registry.set_renderer(DefaultPromptRenderer())
            self.registry.set_optimizer(DefaultPromptOptimizer())
        self.event_bus = EventBus()
        self.event_bus.clear()

    def test_singleton(self) -> None:
        """Verifies that PromptRegistry behaves as a singleton."""
        registry2 = PromptRegistry()
        self.assertIs(self.registry, registry2)

    def test_registration_validation(self) -> None:
        """Verifies validations enforce ID uniqueness, duplicate variables check."""
        var1 = PromptVariable(name="name", type="string")
        var2 = PromptVariable(name="name", type="string")  # Duplicate name
        sec = PromptSection(section_id="s1", title="Title", content="Content")

        t_bad = PromptTemplate(
            template_id="t_bad",
            name="Bad",
            version="1.0.0",
            description="",
            author="",
            variables=[var1, var2],
            sections=[sec]
        )

        with self.assertRaises(PromptValidationError):
            self.registry.register_template(t_bad)

        # Successful registration
        t_ok = PromptTemplate(
            template_id="t_ok",
            name="OK",
            version="1.0.0",
            description="",
            author="",
            variables=[var1],
            sections=[sec]
        )
        self.registry.register_template(t_ok)
        self.assertIn(t_ok, self.registry.list_templates())

        # Duplicate ID
        with self.assertRaises(PromptValidationError):
            self.registry.register_template(t_ok)

    def test_template_inheritance_resolution(self) -> None:
        """Verifies child inherits sections/variables and resolves overrides."""
        p_var = PromptVariable(name="role", type="string", default_value="assistant")
        p_sec = PromptSection(section_id="system", title="System Instructions", content="You are a {role}.", priority=1.0, metadata={"role": "system"})

        parent = PromptTemplate(
            template_id="parent",
            name="Parent Template",
            version="1.0.0",
            description="",
            author="",
            variables=[p_var],
            sections=[p_sec]
        )

        c_var = PromptVariable(name="role", type="string", default_value="support agent")  # overrides role
        c_sec = PromptSection(section_id="user", title="User query", content="Task: {query}", priority=2.0)

        child = PromptTemplate(
            template_id="child",
            name="Child Template",
            version="1.0.0",
            description="",
            author="",
            variables=[c_var, PromptVariable(name="query", type="string")],
            sections=[c_sec],
            inheritance="parent"
        )

        self.registry.register_template(parent)
        self.registry.register_template(child)

        # Render child request
        request = PromptRequest(
            template="child",
            variables={"query": "fix billing problem"}
        )

        response = self.registry.render(request)

        # Verifies formatting: "You are a support agent.\n\nTask: fix billing problem"
        self.assertIn("You are a support agent.", response.prompt.rendered_text)
        self.assertIn("Task: fix billing problem", response.prompt.rendered_text)
        self.assertEqual(response.prompt.system_prompt, "You are a support agent.")
        self.assertEqual(response.prompt.user_prompt, "Task: fix billing problem")

    def test_circular_inheritance_detection(self) -> None:
        """Verifies circular references raise CircularInheritanceError."""
        # A inherits B, B inherits A
        t_a = PromptTemplate(
            template_id="A",
            name="A",
            version="1.0.0",
            description="",
            author="",
            inheritance="B"
        )
        t_b = PromptTemplate(
            template_id="B",
            name="B",
            version="1.0.0",
            author="",
            description="",
            inheritance="A"
        )

        self.registry.register_template(t_a)
        # Registering B (which points to A, creating circular link) should trigger error
        with self.assertRaises(CircularInheritanceError):
            self.registry.register_template(t_b)

    def test_rendering_missing_required_variable_raises(self) -> None:
        """Verifies rendering fails when a required variable is missing."""
        var = PromptVariable(name="req_var", type="string", required=True)
        sec = PromptSection(section_id="s1", title="Title", content="Value: {req_var}")
        temp = PromptTemplate(
            template_id="temp",
            name="Temp",
            version="1.0.0",
            description="",
            author="",
            variables=[var],
            sections=[sec]
        )
        self.registry.register_template(temp)

        with self.assertRaises(PromptValidationError):
            self.registry.render(PromptRequest(template="temp", variables={}))

    def test_context_integration(self) -> None:
        """Verifies Context engine response integrations formatting placeholder logic."""
        sec1 = ContextSection("ctx1", ContextSource.VECTOR, "Docs", "vector search context content", 0.9, 10)
        context = Context(
            context_id=uuid.uuid4(),
            sections=[sec1],
            metadata={},
            created_at=datetime.utcnow(),
            total_tokens=10
        )

        # Template uses context variable placeholder
        p_sec = PromptSection(section_id="s", title="T", content="Context:\n{context}")
        temp = PromptTemplate(
            template_id="temp",
            name="Temp",
            version="1.0.0",
            description="",
            author="",
            variables=[PromptVariable(name="context", type="string", required=False)],
            sections=[p_sec]
        )
        self.registry.register_template(temp)

        request = PromptRequest(template="temp", context=context)
        response = self.registry.render(request)

        self.assertIn("vector search context content", response.prompt.rendered_text)

    def test_custom_renderer_override(self) -> None:
        """Verifies custom renderer overrides rendering execution."""
        temp = PromptTemplate(
            template_id="temp",
            name="Temp",
            version="1.0.0",
            description="",
            author="",
            sections=[PromptSection("s", "T", "content")]
        )
        self.registry.register_template(temp)

        self.registry.set_renderer(CustomPromptRenderer())
        response = self.registry.render(PromptRequest(template="temp"))
        self.assertEqual(response.prompt.rendered_text, "Custom Rendered Output")

    def test_thread_safety_concurrency(self) -> None:
        """Verifies concurrent rendering execution safety."""
        temp = PromptTemplate(
            template_id="temp",
            name="Temp",
            version="1.0.0",
            description="",
            author="",
            variables=[PromptVariable(name="val", type="string")],
            sections=[PromptSection("s", "T", "Val: {val}")]
        )
        self.registry.register_template(temp)

        num_threads = 10
        renders_per_thread = 15

        results = []
        results_lock = threading.Lock()

        def worker(thread_idx: int) -> None:
            for i in range(renders_per_thread):
                req = PromptRequest(template="temp", variables={"val": f"thread_{thread_idx}_{i}"})
                res = self.registry.render(req)
                with results_lock:
                    results.append(res)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), num_threads * renders_per_thread)
        for res in results:
            self.assertTrue(res.prompt.rendered_text.startswith("Val: thread_"))


if __name__ == "__main__":
    unittest.main()
