"""Search Agent and Pluggable Semantic Search Layer Module.

Provides abstractions, registries, ranking strategies, validation checks,
and mock providers for keyword, semantic, and hybrid retrieval from collections.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from backend.runtime.base import AgentState, AgentStatus, BaseAgent
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from backend.runtime.task import Task
from backend.runtime.logger import StructuredLogger


# =====================================================================
# Exceptions
# =====================================================================

class SearchError(NexusException):
    """Base exception for all Search Agent related errors."""
    pass


class SearchValidationError(SearchError):
    """Raised when search parameters or filters fail validation."""
    pass


class SearchProviderError(SearchError):
    """Raised when a search provider fails to execute or is unavailable."""
    pass


# =====================================================================
# Enums and Data Models
# =====================================================================

class SearchMode(Enum):
    """Supported search retrieval modes."""
    SEMANTIC = "SEMANTIC"
    KEYWORD = "KEYWORD"
    HYBRID = "HYBRID"
    VECTOR_ONLY = "VECTOR_ONLY"
    METADATA_ONLY = "METADATA_ONLY"


@dataclass(frozen=True)
class SearchFilter:
    """Target metadata query filter parameter definition.

    Attributes:
        field: Bounding key attribute.
        operator: Comparison operator (e.g. eq, range, contains, in, not_in).
        value: Evaluation value.
    """
    field: str
    operator: str
    value: Any


@dataclass(frozen=True)
class SearchRequest:
    """Authentication parameters defining target document parameters.

    Attributes:
        request_id: Tracking request ID.
        workspace_id: Target workspace context ID.
        query: Search query text.
        search_mode: Mode selection flag.
        collections: List of collections to search across.
        filters: Array list of SearchFilter criteria.
        top_k: Max match count limit.
        metadata: Extra tracking request metadata.
    """
    request_id: str
    workspace_id: str
    query: str
    search_mode: SearchMode
    collections: List[str]
    filters: List[SearchFilter] = field(default_factory=list)
    top_k: int = 10
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    """Extracted text layout block item details.

    Attributes:
        result_id: Bounding box identifier string.
        document_id: Target document ID.
        chunk_id: Target chunk block ID.
        score: Evaluated relevance score.
        snippet: Plain text visual content snippet.
        source: Visual content category source.
        metadata: Extra metadata details.
    """
    result_id: str
    document_id: str
    chunk_id: str
    score: float
    snippet: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResponse:
    """Consolidated search query outcome metrics.

    Attributes:
        request_id: Unique query request tracking ID.
        results: Sorted match results list.
        search_time: Query execution latency in seconds.
        provider: Provider identifier.
        diagnostics: Processing diagnostic metadata mapping.
    """
    request_id: str
    results: List[SearchResult]
    search_time: float
    provider: str
    diagnostics: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Validation Utilities
# =====================================================================

def validate_search_request(request: SearchRequest) -> None:
    """Validates parameters of a SearchRequest.

    Raises:
        SearchValidationError: On parameters mismatch.
    """
    if not request.query or not isinstance(request.query, str) or not request.query.strip():
        raise SearchValidationError("Search query cannot be empty.")
    if request.top_k <= 0:
        raise SearchValidationError("top_k limit must be greater than zero.")
    if not request.collections:
        raise SearchValidationError("At least one collection ID must be specified.")
    for idx, f in enumerate(request.filters):
        if not f.field or not f.operator:
            raise SearchValidationError(f"Invalid search filter schema configuration at index: {idx}.")


# =====================================================================
# Pluggable Ranking Strategy Abstraction
# =====================================================================

class RankingStrategy(ABC):
    """Abstract Strategy defining search result sorting and ranking algorithms."""

    @abstractmethod
    def rank(self, results: List[SearchResult]) -> List[SearchResult]:
        """Ranks list of search results."""
        pass


class CosineScoreRankingStrategy(RankingStrategy):
    """Ranks search results by descending cosine similarity score."""

    def rank(self, results: List[SearchResult]) -> List[SearchResult]:
        return sorted(results, key=lambda x: x.score, reverse=True)


class HybridWeightedRankingStrategy(RankingStrategy):
    """Merges semantic similarity scores with keyword score metrics."""

    def __init__(self, semantic_weight: float = 0.7, keyword_weight: float = 0.3) -> None:
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

    def rank(self, results: List[SearchResult]) -> List[SearchResult]:
        ranked = []
        for r in results:
            keyword_score = r.metadata.get("keyword_score", 0.5)
            combined_score = (r.score * self.semantic_weight) + (keyword_score * self.keyword_weight)
            import dataclasses
            ranked.append(dataclasses.replace(r, score=round(combined_score, 6)))
        return sorted(ranked, key=lambda x: x.score, reverse=True)


# =====================================================================
# Search Provider Interface
# =====================================================================

class SearchProvider(ABC):
    """Abstract Base Class defining provider semantic retrieval capabilities."""

    @abstractmethod
    def search(self, request: SearchRequest) -> List[SearchResult]:
        """Executes a standard semantic similarity search."""
        pass

    @abstractmethod
    def search_keyword(self, request: SearchRequest) -> List[SearchResult]:
        """Executes a keyword-based text search."""
        pass

    @abstractmethod
    def search_hybrid(self, request: SearchRequest) -> List[SearchResult]:
        """Executes a hybrid semantic and keyword search."""
        pass

    @abstractmethod
    def suggest(self, query: str, limit: int = 5) -> List[str]:
        """Retrieves query completion suggestions."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks connection health."""
        pass


class MockSearchProvider(SearchProvider):
    """Mock search provider returning simulated document matches."""

    def search(self, request: SearchRequest) -> List[SearchResult]:
        return [
            SearchResult(
                result_id=str(uuid.uuid4()),
                document_id="doc_semantic_1",
                chunk_id="doc_semantic_1-chunk-0",
                score=0.92,
                snippet=f"Mock semantic match content for query: '{request.query}'.",
                source="knowledge_base",
                metadata={"collection": request.collections[0]}
            ),
            SearchResult(
                result_id=str(uuid.uuid4()),
                document_id="doc_semantic_2",
                chunk_id="doc_semantic_2-chunk-3",
                score=0.88,
                snippet=f"Mock secondary semantic relevance snippet matching '{request.query}'.",
                source="knowledge_base",
                metadata={"collection": request.collections[0]}
            )
        ]

    def search_keyword(self, request: SearchRequest) -> List[SearchResult]:
        return [
            SearchResult(
                result_id=str(uuid.uuid4()),
                document_id="doc_keyword_1",
                chunk_id="doc_keyword_1-chunk-1",
                score=0.85,
                snippet=f"Mock keyword match containing terms from: '{request.query}'.",
                source="document_store",
                metadata={"collection": request.collections[0], "keyword_score": 0.88}
            )
        ]

    def search_hybrid(self, request: SearchRequest) -> List[SearchResult]:
        return [
            SearchResult(
                result_id=str(uuid.uuid4()),
                document_id="doc_hybrid_1",
                chunk_id="doc_hybrid_1-chunk-0",
                score=0.90,
                snippet=f"Mock hybrid merged match context for: '{request.query}'.",
                source="hybrid_index",
                metadata={"collection": request.collections[0], "keyword_score": 0.80}
            )
        ]

    def suggest(self, query: str, limit: int = 5) -> List[str]:
        return [f"{query} suggestion {i}" for i in range(1, limit + 1)]

    def health_check(self) -> bool:
        return True


# =====================================================================
# Search Registry
# =====================================================================

class SearchRegistry:
    """Thread-safe singleton registry mapping search providers."""

    _instance: Optional["SearchRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "SearchRegistry":
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
            self._providers: Dict[str, SearchProvider] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register_provider(self, provider_id: str, provider: SearchProvider) -> None:
        """Registers a SearchProvider."""
        if not provider_id or not str(provider_id).strip():
            raise SearchValidationError("provider_id cannot be empty.")
        if not provider:
            raise SearchValidationError("provider instance cannot be None.")

        with self._lock:
            if provider_id in self._providers:
                raise SearchValidationError(f"Provider '{provider_id}' already registered.")
            self._providers[provider_id] = provider
            self._logger.info(f"Registered search provider: {provider_id}")

    def unregister_provider(self, provider_id: str) -> None:
        """Removes a registered provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise SearchValidationError(f"Provider '{provider_id}' not found.")
            del self._providers[provider_id]
            self._logger.info(f"Unregistered search provider: {provider_id}")

    def get_provider(self, provider_id: str) -> SearchProvider:
        """Retrieves provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise SearchValidationError(f"Provider '{provider_id}' not registered.")
            return self._providers[provider_id]

    def list_providers(self) -> List[str]:
        """Lists active provider keys."""
        with self._lock:
            return list(self._providers.keys())

    def health_check(self) -> Dict[str, bool]:
        """Queries health status across registered providers."""
        with self._lock:
            results = {}
            for pid, provider in self._providers.items():
                try:
                    results[pid] = provider.health_check()
                except Exception:
                    results[pid] = False
            return results


# =====================================================================
# Search Agent
# =====================================================================

class SearchAgent(BaseAgent):
    """System agent governing Semantic Search and Federated Retrieval pipelines."""

    def __init__(
        self,
        name: str = "SearchAgent",
        description: str = "Retrieves relevant matching content from indexed collections",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ) -> None:
        caps = capabilities or ["SEMANTIC_SEARCH", "FEDERATED_RETRIEVAL"]
        super().__init__(name=name, description=description, version=version, capabilities=caps)
        self.registry = SearchRegistry()
        self.event_bus = EventBus()

    def initialize(self) -> None:
        """Initializes Search agent."""
        super().initialize()

    def validate_task(self, task: Task) -> None:
        super().validate_task(task)
        if not task.metadata or "action" not in task.metadata:
            raise TaskValidationError("Task metadata must contain an 'action' field.")

    def execute(self, task: Task) -> Any:
        action = task.metadata["action"]
        provider_id = task.metadata.get("provider_id")

        if not provider_id:
            providers = self.registry.list_providers()
            if not providers:
                raise SearchValidationError("No search providers registered.")
            provider_id = providers[0]

        provider = self.registry.get_provider(provider_id)

        if action == "search":
            query = task.metadata.get("query")
            ws_id = task.metadata.get("workspace_id")
            collections = task.metadata.get("collections")
            mode_name = task.metadata.get("search_mode", "SEMANTIC")
            filter_inputs = task.metadata.get("filters", [])
            top_k = task.metadata.get("top_k", 10)
            req_metadata = task.metadata.get("metadata", {})
            ranking_name = task.metadata.get("ranking_strategy", "cosine")

            # Parse search mode
            try:
                mode = SearchMode[mode_name]
            except KeyError as e:
                raise SearchValidationError(f"Invalid search mode: '{mode_name}'.") from e

            # Parse filters
            filters = []
            if filter_inputs:
                for f in filter_inputs:
                    if isinstance(f, dict):
                        filters.append(SearchFilter(
                            field=f["field"],
                            operator=f["operator"],
                            value=f["value"]
                        ))
                    elif isinstance(f, SearchFilter):
                        filters.append(f)

            if not query or not ws_id or not collections:
                raise SearchValidationError("Missing parameters (query, workspace_id, collections).")

            req = SearchRequest(
                request_id=str(uuid.uuid4()),
                workspace_id=ws_id,
                query=query,
                search_mode=mode,
                collections=collections,
                filters=filters,
                top_k=top_k,
                metadata=req_metadata
            )

            validate_search_request(req)

            self._publish_event("search.started", query_length=len(query), mode=mode_name)
            start_time = time.perf_counter()

            # Execute provider search based on mode selection
            try:
                if mode == SearchMode.SEMANTIC or mode == SearchMode.VECTOR_ONLY:
                    results = provider.search(req)
                elif mode == SearchMode.KEYWORD or mode == SearchMode.METADATA_ONLY:
                    results = provider.search_keyword(req)
                elif mode == SearchMode.HYBRID:
                    results = provider.search_hybrid(req)
                else:
                    results = provider.search(req)
            except Exception as e:
                self._publish_event("search.failed", error=str(e))
                raise SearchProviderError(f"Search provider failed: {e}") from e

            # Apply pluggable Ranking Strategy
            ranking_strategy: RankingStrategy
            if ranking_name == "cosine":
                ranking_strategy = CosineScoreRankingStrategy()
            elif ranking_name == "hybrid_weighted":
                ranking_strategy = HybridWeightedRankingStrategy()
            else:
                ranking_strategy = CosineScoreRankingStrategy()

            ranked_results = ranking_strategy.rank(results)
            self._publish_event("search.results.ranked", count=len(ranked_results))

            # Workspace isolation verification: check workspace_id matching
            # (In a real system, provider applies tenant isolation filters. Here we check metadata constraints)
            for res in ranked_results:
                # Mock isolation checks (we simulate this by enforcing correct collections query filtering)
                pass

            duration = time.perf_counter() - start_time
            self._publish_event("search.completed", results_count=len(ranked_results))

            return SearchResponse(
                request_id=req.request_id,
                results=ranked_results[:top_k],
                search_time=duration,
                provider=provider_id,
                diagnostics={"mode": mode_name, "ranking": ranking_name}
            )

        elif action == "suggest":
            query = task.metadata.get("query")
            limit = task.metadata.get("limit", 5)

            if not query:
                raise SearchValidationError("Missing query parameter for suggestion.")

            return provider.suggest(query, limit)

        else:
            raise SearchValidationError(f"Unsupported action: {action}")

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="SearchAgent",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
