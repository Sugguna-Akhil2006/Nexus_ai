from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from typing import Any, Dict, List, Optional, Union
import uuid

from core.event import Event, EventBus, EventType
from core.exceptions import NexusException
from core.logger import StructuredLogger


class ContextError(NexusException):
    """Base exception for all Context Engine related errors."""
    pass


class ContextValidationError(ContextError):
    """Raised when context requests or properties configuration are invalid."""
    pass


class ProviderError(ContextError):
    """Raised when context gathering provider adapters crash."""
    pass


class ProviderNotFoundError(ContextError):
    """Raised when the requested ContextProvider is not registered."""
    pass


class ContextSource(Enum):
    """Logical classification categories specifying context source origins."""
    MEMORY = "MEMORY"
    VECTOR = "VECTOR"
    STORAGE = "STORAGE"
    WORKFLOW = "WORKFLOW"
    USER = "USER"
    SYSTEM = "SYSTEM"
    TOOL = "TOOL"
    AGENT = "AGENT"
    PLUGIN = "PLUGIN"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True)
class ContextSection:
    """Immutable section of context text gathered from a source provider.

    Attributes:
        section_id: Unique identifier string.
        source: The logical ContextSource origin category.
        title: Descriptive label.
        content: Text content payload.
        relevance_score: Float relevance score weight (0.0 to 1.0).
        token_count: Length token budget cost estimator.
        metadata: Section metadata mapping.
    """
    section_id: str
    source: ContextSource
    title: str
    content: str
    relevance_score: float
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Context:
    """Consolidated immutable context returned to prompt engines.

    Attributes:
        context_id: Unique UUID transaction tracking code.
        sections: Trimmed, prioritized, and ranked context sections.
        metadata: Context metadata details.
        created_at: Collection timestamp.
        total_tokens: Total token count.
        priority: Priority weighting.
    """
    context_id: uuid.UUID
    sections: List[ContextSection]
    metadata: Dict[str, Any]
    created_at: datetime
    total_tokens: int
    priority: float = 1.0


@dataclass(frozen=True)
class ContextRequest:
    """Defines search parameters and sources required to assemble context.

    Attributes:
        task: Target Task reference details placeholder.
        user: Optional user identifier.
        workflow: Optional workflow trace context.
        max_tokens: Max boundary budget limit.
        required_sources: Source origins prioritized as required.
        optional_sources: Source origins categorized as optional.
        metadata: Query search options configuration details.
    """
    task: Optional[Any] = None
    user: Optional[str] = None
    workflow: Optional[Any] = None
    max_tokens: int = 4096
    required_sources: List[ContextSource] = field(default_factory=list)
    optional_sources: List[ContextSource] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextResponse:
    """Contains consolidated context payload and metadata metrics.

    Attributes:
        context: The final Context object.
        provider_diagnostics: Provider diagnostics diagnostics mapping.
        token_usage: Dict summarizing total/trimmed token counts.
        collection_metrics: Diagnostics execution duration metrics metadata.
    """
    context: Context
    provider_diagnostics: Dict[str, Any]
    token_usage: Dict[str, int]
    collection_metrics: Dict[str, Any]


class ContextProvider(ABC):
    """Abstract Base Class specifying interfaces extending Context gathering."""

    @abstractmethod
    def collect(self, request: ContextRequest) -> List[ContextSection]:
        """Queries the source context registry and returns matching sections.

        Args:
            request: Structured context search parameter inputs.

        Returns:
            List[ContextSection]: Context segments fetched.
        """
        pass

    @abstractmethod
    def supports(self, source: ContextSource) -> bool:
        """Verifies if the provider supports the requested source category.

        Args:
            source: Target ContextSource origin.

        Returns:
            bool: True if supported.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Queries downstream connectivity state.

        Returns:
            bool: True if healthy.
        """
        pass


class ContextRankingStrategy(ABC):
    """Interface defining pluggable mechanisms for ranking context sections."""

    @abstractmethod
    def rank(self, sections: List[ContextSection]) -> List[ContextSection]:
        """Ranks context sections logically.

        Args:
            sections: Input context sections.

        Returns:
            List[ContextSection]: Sorted list of context sections.
        """
        pass


class DefaultContextRankingStrategy(ContextRankingStrategy):
    """Default ranking algorithm considering relevance, recency, source, and tokens."""

    def __init__(self, source_priorities: Optional[Dict[ContextSource, float]] = None) -> None:
        self.source_priorities = source_priorities or {
            ContextSource.SYSTEM: 10.0,
            ContextSource.USER: 9.0,
            ContextSource.AGENT: 8.0,
            ContextSource.MEMORY: 7.0,
            ContextSource.VECTOR: 6.0,
            ContextSource.STORAGE: 5.0,
            ContextSource.TOOL: 4.0,
            ContextSource.WORKFLOW: 3.0,
            ContextSource.PLUGIN: 2.0,
            ContextSource.CUSTOM: 1.0,
        }

    def rank(self, sections: List[ContextSection]) -> List[ContextSection]:
        def sort_key(s: ContextSection) -> Any:
            relevance = s.relevance_score
            priority = self.source_priorities.get(s.source, 1.0)

            # Recency
            timestamp = 0.0
            ts_val = s.metadata.get("timestamp")
            if ts_val:
                try:
                    if isinstance(ts_val, (int, float)):
                        timestamp = float(ts_val)
                    else:
                        dt = datetime.fromisoformat(str(ts_val))
                        timestamp = dt.timestamp()
                except Exception:
                    pass

            # Token efficiency (lower token count for equal relevance is preferred)
            efficiency = s.relevance_score / max(1, s.token_count)

            # Negated values for descending sorting
            return (-relevance, -priority, -timestamp, -efficiency)

        sorted_sections = list(sections)
        sorted_sections.sort(key=sort_key)
        return sorted_sections


class TokenBudgetManager:
    """Enforces token budget limits while preserving required resources."""

    def __init__(self, max_tokens: int) -> None:
        self.max_tokens = max_tokens
        self.discarded_sections: List[ContextSection] = []

    def enforce(
        self,
        sorted_sections: List[ContextSection],
        required_sources: List[ContextSource]
    ) -> List[ContextSection]:
        """Trims low priority items to conform to the token limits constraint.

        Args:
            sorted_sections: Sorted context sections list.
            required_sources: Context sources prioritized to avoid trimming.

        Returns:
            List[ContextSection]: Trimmed context list.
        """
        self.discarded_sections.clear()

        # Segregate required from optional
        required = []
        optional = []
        for s in sorted_sections:
            if s.source in required_sources:
                required.append(s)
            else:
                optional.append(s)

        current_tokens = 0
        final_sections = []

        # Add required first
        for s in required:
            if current_tokens + s.token_count <= self.max_tokens:
                final_sections.append(s)
                current_tokens += s.token_count
            else:
                self.discarded_sections.append(s)

        # Add optional
        for s in optional:
            if current_tokens + s.token_count <= self.max_tokens:
                final_sections.append(s)
                current_tokens += s.token_count
            else:
                self.discarded_sections.append(s)

        return final_sections


class ContextDeduplicator:
    """Helper to detect and eliminate duplicate context segments."""

    @staticmethod
    def deduplicate(sections: List[ContextSection]) -> List[ContextSection]:
        """Eliminates duplicates by matching clean contents and section IDs.

        Args:
            sections: Input context sections.

        Returns:
            List[ContextSection]: Deduplicated context sections.
        """
        seen_ids = set()
        seen_contents = set()
        unique = []

        for s in sections:
            clean_content = str(s.content).strip()
            if s.section_id in seen_ids or clean_content in seen_contents:
                continue
            seen_ids.add(s.section_id)
            seen_contents.add(clean_content)
            unique.append(s)
        return unique


class ContextRegistry:
    """Thread-safe Singleton registry coordinating ContextProviders."""
    _instance: Optional["ContextRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ContextRegistry":
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
            self._providers: Dict[str, ContextProvider] = {}
            self._ranking_strategy: ContextRankingStrategy = DefaultContextRankingStrategy()
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def register_provider(self, provider_id: str, provider: ContextProvider) -> None:
        """Registers a ContextProvider.

        Args:
            provider_id: Unique string identifier.
            provider: Active class interface instance.

        Raises:
            ContextValidationError: If duplicate ID registration fails.
        """
        if not provider_id or not str(provider_id).strip():
            raise ContextValidationError("provider_id cannot be empty.")
        if not provider:
            raise ContextValidationError("provider instance cannot be None.")

        with self._lock:
            if provider_id in self._providers:
                raise ContextValidationError(f"Provider '{provider_id}' is already registered.")
            self._providers[provider_id] = provider

        self.logger.info(f"Context provider registered. ID: {provider_id}")

    def unregister_provider(self, provider_id: str) -> None:
        """Removes a provider from the active registry.

        Args:
            provider_id: Unique provider ID.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(f"Provider '{provider_id}' not found.")
            del self._providers[provider_id]

        self.logger.info(f"Context provider unregistered. ID: {provider_id}")

    def list_providers(self) -> List[str]:
        """Lists IDs of registered context providers.

        Returns:
            List[str]: Gathers list of provider IDs.
        """
        with self._lock:
            return list(self._providers.keys())

    def get_ranking_strategy(self) -> ContextRankingStrategy:
        """Retrieves active ranking strategy."""
        with self._lock:
            return self._ranking_strategy

    def set_ranking_strategy(self, strategy: ContextRankingStrategy) -> None:
        """Changes active context ranking strategy.

        Args:
            strategy: Custom ranking strategy.
        """
        with self._lock:
            self._ranking_strategy = strategy

    def health_check(self) -> Dict[str, bool]:
        """Queries health status across registered providers.

        Returns:
            Dict[str, bool]: Health status dictionary.
        """
        status_map = {}
        with self._lock:
            for pid, provider in self._providers.items():
                try:
                    status_map[pid] = provider.health_check()
                except Exception:
                    status_map[pid] = False
        return status_map

    def collect(self, request: ContextRequest) -> ContextResponse:
        """Queries active providers to gather context, ranking, and budget.

        Args:
            request: Structured context gathering instructions details.

        Returns:
            ContextResponse: Combined details.
        """
        if not request:
            raise ContextValidationError("ContextRequest cannot be None.")

        self.logger.info(f"Context collection started (max_tokens: {request.max_tokens})")
        self._publish_event("context.collection.started", max_tokens=request.max_tokens)

        start_time = datetime.utcnow()
        collected_sections: List[ContextSection] = []
        diagnostics = {}

        # Gathers active providers snapshots
        with self._lock:
            providers_snapshot = dict(self._providers)

        # Query loop
        for pid, provider in providers_snapshot.items():
            try:
                sections = provider.collect(request)
                collected_sections.extend(sections)
                diagnostics[pid] = {"status": "success", "count": len(sections)}
            except Exception as e:
                diagnostics[pid] = {"status": "failed", "error": str(e)}
                self._publish_event("context.provider.failed", provider_id=pid, error=str(e))
                self.logger.warning(f"Context provider '{pid}' failed to collect context: {e}")

        # Deduplication
        deduplicated = ContextDeduplicator.deduplicate(collected_sections)

        # Ranking
        strategy = self.get_ranking_strategy()
        ranked = strategy.rank(deduplicated)

        # Budgeting
        budget_manager = TokenBudgetManager(request.max_tokens)
        final_sections = budget_manager.enforce(ranked, request.required_sources)

        if budget_manager.discarded_sections:
            self._publish_event(
                "context.trimmed",
                discarded_count=len(budget_manager.discarded_sections),
                remaining_count=len(final_sections)
            )
            self.logger.info(
                f"Context trimmed. Discarded {len(budget_manager.discarded_sections)} items."
            )

        completed_at = datetime.utcnow()
        duration = (completed_at - start_time).total_seconds()
        total_tokens = sum(s.token_count for s in final_sections)

        context = Context(
            context_id=uuid.uuid4(),
            sections=final_sections,
            metadata=request.metadata.copy(),
            created_at=completed_at,
            total_tokens=total_tokens
        )

        token_usage = {
            "total_tokens": total_tokens,
            "max_tokens": request.max_tokens,
            "discarded_tokens": sum(s.token_count for s in budget_manager.discarded_sections)
        }

        collection_metrics = {
            "duration": duration,
            "raw_count": len(collected_sections),
            "deduped_count": len(deduplicated),
            "final_count": len(final_sections)
        }

        self._publish_event("context.collection.completed", total_tokens=total_tokens)
        return ContextResponse(
            context=context,
            provider_diagnostics=diagnostics,
            token_usage=token_usage,
            collection_metrics=collection_metrics
        )

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ContextEngine",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
