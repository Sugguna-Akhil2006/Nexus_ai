from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Union
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import NexusException
from backend.runtime.logger import StructuredLogger


class PromptError(NexusException):
    """Base exception for all Prompt Engine related errors."""
    pass


class PromptValidationError(PromptError):
    """Raised when prompt validation fails due to missing variables or schemas."""
    pass


class TemplateNotFoundError(PromptError):
    """Raised when a requested template identifier is not found."""
    pass


class CircularInheritanceError(PromptError):
    """Raised when a circular inheritance loop is detected in templates."""
    pass


@dataclass(frozen=True)
class PromptVariable:
    """Immutable variable validation constraint schema descriptor.

    Attributes:
        name: Unique variable key name.
        type: String type identifier (e.g. string, number).
        default_value: Optional fallback default.
        required: True if variable must be provided.
        validator: Optional custom validation hook.
        description: Informational description.
    """
    name: str
    type: str
    default_value: Optional[Any] = None
    required: bool = True
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""


@dataclass(frozen=True)
class PromptSection:
    """Immutable block template section within parent template.

    Attributes:
        section_id: Unique string key identifier.
        title: Descriptive label.
        content: Text string content with format placeholders.
        priority: Priority order weight (lower means higher priority/order).
        required: True if section must be present.
        metadata: Section metadata mapping.
    """
    section_id: str
    title: str
    content: str
    priority: float = 1.0
    required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptTemplate:
    """Immutable collection of variables, sections and inheritance scopes.

    Attributes:
        template_id: Unique template ID identifier.
        name: Common template name.
        version: Version identifier.
        description: Description text.
        author: Author name descriptor.
        variables: Expected validation variables list.
        sections: Context composition section templates list.
        inheritance: Parent template ID code.
        metadata: Extra metadata details.
    """
    template_id: str
    name: str
    version: str
    description: str
    author: str
    variables: List[PromptVariable] = field(default_factory=list)
    sections: List[PromptSection] = field(default_factory=list)
    inheritance: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Prompt:
    """Consolidated provider-ready generated prompts descriptors.

    Attributes:
        prompt_id: Unique UUID transaction tracking code.
        template_id: Source template ID identifier.
        rendered_text: Final concatenated rendered string.
        system_prompt: System role prompt text.
        user_prompt: User role prompt text.
        messages: Provider chat messages formatted payload.
        estimated_tokens: Estimated input token count.
        created_at: Generation datetime stamp.
        metadata: Extra metadata.
    """
    prompt_id: uuid.UUID
    template_id: Optional[str]
    rendered_text: str
    system_prompt: Optional[str]
    user_prompt: Optional[str]
    messages: List[Dict[str, Any]]
    estimated_tokens: int
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptRequest:
    """Encapsulates parameters needed to render a prompt.

    Attributes:
        context: Context engine responses summary if RAG is requested.
        template: Base template definition or template ID string.
        variables: Placeholder key-value variables configuration map.
        provider: Provider identifier context.
        model: Model identifier context.
        constraints: Extra sizing parameters context.
        metadata: Optional request options mapping.
    """
    context: Optional[Any] = None
    template: Optional[Union[PromptTemplate, str]] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    provider: Optional[str] = None
    model: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptResponse:
    """Conveys rendered prompt payload metadata metrics.

    Attributes:
        prompt: Consolidated rendered Prompt object.
        diagnostics: Collection execution metrics dictionary.
        estimated_tokens: Token count approximation value.
        rendering_time: Processing latency in seconds.
        warnings: Warnings generated during execution.
    """
    prompt: Prompt
    diagnostics: Dict[str, Any]
    estimated_tokens: int
    rendering_time: float
    warnings: List[str] = field(default_factory=list)


class PromptRenderer(ABC):
    """Abstract interface defining standard prompt composition renderer."""

    @abstractmethod
    def render(self, request: PromptRequest, resolved_template: PromptTemplate) -> Prompt:
        """Assembles prompt content and populates placeholders.

        Args:
            request: Render request parameters.
            resolved_template: Resolved prompt template specifications.

        Returns:
            Prompt: Rendered prompt outcomes.
        """
        pass


class PromptOptimizer(ABC):
    """Abstract interface defining prompt post-processing compression optimizations."""

    @abstractmethod
    def optimize(self, prompt: Prompt) -> Prompt:
        """Optimizes prompt for token efficiency.

        Args:
            prompt: Input Prompt object.

        Returns:
            Prompt: Optimized Prompt.
        """
        pass


class DefaultPromptRenderer(PromptRenderer):
    """Default renderer concatenating prompt sections and variables formatting."""

    def render(self, request: PromptRequest, resolved_template: PromptTemplate) -> Prompt:
        # Prepare variable mapping (merge defaults)
        vars_map = {}
        for var in resolved_template.variables:
            if var.default_value is not None:
                vars_map[var.name] = var.default_value

        vars_map.update(request.variables)

        # Context formatting representation
        context_str = ""
        if request.context:
            context_str = "\n\n".join(
                f"[{sec.source.value}] {sec.title}:\n{sec.content}"
                for sec in request.context.sections
            )
        vars_map["context"] = context_str

        # Sort sections by priority
        sorted_sections = list(resolved_template.sections)
        sorted_sections.sort(key=lambda s: s.priority)

        rendered_sections = []
        system_content_parts = []
        user_content_parts = []

        for sec in sorted_sections:
            content = sec.content
            # Interpolate variables
            try:
                # Find all {var_name} formatted tags
                placeholders = re.findall(r"\{([a-zA-Z0-9_]+)\}", content)
                for ph in placeholders:
                    if ph in vars_map:
                        content = content.replace(f"{{{ph}}}", str(vars_map[ph]))
                    elif sec.required:
                        raise PromptValidationError(
                            f"Missing value for required placeholder '{ph}' in section '{sec.section_id}'."
                        )
            except Exception as e:
                if isinstance(e, PromptValidationError):
                    raise
                raise PromptValidationError(f"Interpolation failed for section '{sec.section_id}': {e}") from e

            rendered_sections.append(content)
            # Partition sections to Chat roles heuristically
            if sec.metadata.get("role") == "system":
                system_content_parts.append(content)
            else:
                user_content_parts.append(content)

        rendered_text = "\n\n".join(rendered_sections)
        system_prompt = "\n\n".join(system_content_parts) if system_content_parts else None
        user_prompt = "\n\n".join(user_content_parts) if user_content_parts else None

        # Build messages payload
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
        if not messages and rendered_text:
            messages.append({"role": "user", "content": rendered_text})

        # Token estimation (word boundary base approximation placeholder)
        word_count = len(re.findall(r"\w+", rendered_text))
        estimated_tokens = int(word_count * 1.3)

        return Prompt(
            prompt_id=uuid.uuid4(),
            template_id=resolved_template.template_id,
            rendered_text=rendered_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            messages=messages,
            estimated_tokens=estimated_tokens,
            created_at=datetime.utcnow(),
            metadata=resolved_template.metadata.copy()
        )


class DefaultPromptOptimizer(PromptOptimizer):
    """Trims whitespace gaps and sequences to compress token usage."""

    def optimize(self, prompt: Prompt) -> Prompt:
        text = prompt.rendered_text
        # Remove consecutive duplicate newline gaps
        text_opt = re.sub(r"\n{3,}", "\n\n", text)
        # Remove duplicate space gaps
        text_opt = re.sub(r" {2,}", " ", text_opt)
        text_opt = text_opt.strip()

        if text_opt == text:
            return prompt

        system_opt = re.sub(r"\n{3,}", "\n\n", prompt.system_prompt).strip() if prompt.system_prompt else None
        user_opt = re.sub(r"\n{3,}", "\n\n", prompt.user_prompt).strip() if prompt.user_prompt else None

        messages_opt = []
        if system_opt:
            messages_opt.append({"role": "system", "content": system_opt})
        if user_opt:
            messages_opt.append({"role": "user", "content": user_opt})

        word_count = len(re.findall(r"\w+", text_opt))
        estimated_tokens = int(word_count * 1.3)

        return Prompt(
            prompt_id=prompt.prompt_id,
            template_id=prompt.template_id,
            rendered_text=text_opt,
            system_prompt=system_opt,
            user_prompt=user_opt,
            messages=messages_opt,
            estimated_tokens=estimated_tokens,
            created_at=prompt.created_at,
            metadata=prompt.metadata.copy()
        )


class PromptRegistry:
    """Thread-safe Singleton managing PromptTemplates registration and composition rendering."""
    _instance: Optional["PromptRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "PromptRegistry":
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
            self.logger = StructuredLogger()
            self.event_bus = EventBus()
            self._templates: Dict[str, PromptTemplate] = {}
            self._renderer: PromptRenderer = DefaultPromptRenderer()
            self._optimizer: PromptOptimizer = DefaultPromptOptimizer()
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def register_template(self, template: PromptTemplate) -> None:
        """Registers a PromptTemplate.

        Args:
            template: Immutable template model definitions.

        Raises:
            PromptValidationError: On duplicate registrations or circular cycles.
        """
        if not template or not template.template_id or not str(template.template_id).strip():
            raise PromptValidationError("Template ID cannot be empty.")

        with self._lock:
            if template.template_id in self._templates:
                raise PromptValidationError(f"Template ID '{template.template_id}' is already registered.")

            # Duplicate variable check
            seen_vars = set()
            for v in template.variables:
                if v.name in seen_vars:
                    raise PromptValidationError(f"Duplicate variable '{v.name}' in template '{template.template_id}'.")
                seen_vars.add(v.name)

            # Circular inheritance check
            if template.inheritance:
                self._check_circular_inheritance(template.template_id, template.inheritance)

            self._templates[template.template_id] = template

        self._publish_event("prompt.template.registered", template_id=template.template_id)
        self.logger.info(f"Successful prompt template registration. ID: {template.template_id}")

    def unregister_template(self, template_id: str) -> None:
        """Removes template registration.

        Args:
            template_id: Unique template ID.
        """
        with self._lock:
            if template_id not in self._templates:
                raise TemplateNotFoundError(f"Template '{template_id}' not found.")
            del self._templates[template_id]

        self.logger.info(f"Prompt template unregistered. ID: {template_id}")

    def get_template(self, template_id: str) -> PromptTemplate:
        """Gets target template definition.

        Args:
            template_id: Unique template ID.

        Returns:
            PromptTemplate: Saved template.
        """
        with self._lock:
            if template_id not in self._templates:
                raise TemplateNotFoundError(f"Template '{template_id}' not found.")
            return self._templates[template_id]

    def list_templates(self) -> List[PromptTemplate]:
        """Lists registered templates.

        Returns:
            List[PromptTemplate]: Templates catalog.
        """
        with self._lock:
            return list(self._templates.values())

    def get_renderer(self) -> PromptRenderer:
        """Retrieves active renderer."""
        with self._lock:
            return self._renderer

    def set_renderer(self, renderer: PromptRenderer) -> None:
        """Changes active renderer.

        Args:
            renderer: Custom prompt renderer.
        """
        with self._lock:
            self._renderer = renderer

    def get_optimizer(self) -> PromptOptimizer:
        """Retrieves active optimizer."""
        with self._lock:
            return self._optimizer

    def set_optimizer(self, optimizer: PromptOptimizer) -> None:
        """Changes active optimizer.

        Args:
            optimizer: Custom prompt optimizer.
        """
        with self._lock:
            self._optimizer = optimizer

    def render(self, request: PromptRequest) -> PromptResponse:
        """Translates requests into variables formatted provider prompts.

        Args:
            request: Sizing limits and variable placeholder config inputs.

        Returns:
            PromptResponse: Processing outcomes payload metrics.
        """
        if not request:
            raise PromptValidationError("PromptRequest cannot be None.")

        self.logger.info("Prompt rendering started.")
        self._publish_event("prompt.render.started")

        start_time = time.perf_counter()
        warnings: List[str] = []

        try:
            # Resolve target template
            if not request.template:
                raise PromptValidationError("PromptRequest must specify a template or template ID.")

            if isinstance(request.template, str):
                base_temp = self.get_template(request.template)
            else:
                base_temp = request.template

            # Resolve inheritance tree variables and sections
            resolved_template = self._resolve_template(base_temp)

            # Enforce validation variables requirements
            self.validate_variables(resolved_template, request.variables, warnings)

            # Delegate rendering
            renderer = self.get_renderer()
            prompt = renderer.render(request, resolved_template)

            # Enforce post-rendering optimization compression
            optimizer = self.get_optimizer()
            optimized_prompt = optimizer.optimize(prompt)

            self._publish_event("prompt.optimized")

            duration = time.perf_counter() - start_time
            self._publish_event("prompt.render.completed", estimated_tokens=optimized_prompt.estimated_tokens)

            diagnostics = {
                "template_id": base_temp.template_id,
                "sections_count": len(resolved_template.sections),
                "variables_count": len(resolved_template.variables)
            }

            return PromptResponse(
                prompt=optimized_prompt,
                diagnostics=diagnostics,
                estimated_tokens=optimized_prompt.estimated_tokens,
                rendering_time=duration,
                warnings=warnings
            )

        except Exception as e:
            self._publish_event("prompt.validation.failed", error=str(e))
            self.logger.error(f"Prompt rendering validation failed: {e}")
            if isinstance(e, (PromptValidationError, CircularInheritanceError, TemplateNotFoundError)):
                raise
            raise PromptError(f"Rendering failed: {e}") from e

    def validate_variables(self, template: PromptTemplate, variables: Dict[str, Any], warnings: List[str]) -> None:
        """Validates input variables map details.

        Args:
            template: Target resolved template model definition.
            variables: Input variables.
            warnings: Warnings list to populate.
        """
        for var in template.variables:
            val = variables.get(var.name, var.default_value)
            if val is None:
                if var.required:
                    raise PromptValidationError(f"Missing required prompt variable: '{var.name}'")
                continue

            # Validate custom type conversions
            if var.validator and not var.validator(val):
                raise PromptValidationError(f"Custom validation failed for prompt variable '{var.name}'.")

    def _resolve_template(self, template: PromptTemplate, visited: Optional[set] = None) -> PromptTemplate:
        if visited is None:
            visited = set()

        if template.template_id in visited:
            raise CircularInheritanceError(f"Circular template inheritance detected for '{template.template_id}'.")
        visited.add(template.template_id)

        if not template.inheritance:
            return template

        parent = self.get_template(template.inheritance)
        resolved_parent = self._resolve_template(parent, visited)

        # Merge variables map
        vars_map = {v.name: v for v in resolved_parent.variables}
        for v in template.variables:
            vars_map[v.name] = v  # child override

        # Merge sections map
        sections_map = {s.section_id: s for s in resolved_parent.sections}
        for s in template.sections:
            sections_map[s.section_id] = s  # child override

        return PromptTemplate(
            template_id=template.template_id,
            name=template.name,
            version=template.version,
            description=template.description,
            author=template.author,
            variables=list(vars_map.values()),
            sections=list(sections_map.values()),
            inheritance=None,
            metadata={**resolved_parent.metadata, **template.metadata}
        )

    def _check_circular_inheritance(self, child_id: str, parent_id: str, visited: Optional[set] = None) -> None:
        if visited is None:
            visited = {child_id}

        if parent_id in visited:
            raise CircularInheritanceError(f"Circular inheritance path detected: {parent_id} in {visited}")

        visited.add(parent_id)
        parent_temp = self._templates.get(parent_id)
        if parent_temp and parent_temp.inheritance:
            self._check_circular_inheritance(child_id, parent_temp.inheritance, visited)

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="PromptEngine",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
