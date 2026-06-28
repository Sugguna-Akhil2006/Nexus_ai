from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import dataclasses
from datetime import datetime
from enum import Enum
import math
import threading
import time
from typing import Any, Dict, List, Optional, Union
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import NexusException
from backend.runtime.logger import StructuredLogger


class VectorError(NexusException):
    """Base exception for all Vector Engine related errors."""
    pass


class VectorValidationError(VectorError):
    """Raised when record properties, dimension checks, or similarity strategy matches fail."""
    pass


class CollectionNotFoundError(VectorError):
    """Raised when the specified vector collection is not found."""
    pass


class ProviderNotFoundError(VectorError):
    """Raised when the specified VectorProvider is not registered."""
    pass


@dataclass(frozen=True)
class VectorRecord:
    """Immutable model representing an indexed vector record.

    Attributes:
        vector_id: Unique identifier for the vector.
        collection: Parent collection ID name.
        embedding: Dimension values float list.
        metadata: Associated query filterable metadata.
        namespace: Namespace isolation bucket.
        created_at: Indexed timestamp.
        updated_at: Modifying timestamp.
    """
    vector_id: str
    collection: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    namespace: str = "default"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class CollectionInfo:
    """Immutable catalog description specifying collection schemas.

    Attributes:
        collection_id: Unique string key name.
        name: Common name label.
        dimensions: Expected embedding dimensions limit.
        similarity_metric: Default similarity metric identifier.
        metadata: Collection metadata details.
        created_at: Created timestamp.
    """
    collection_id: str
    name: str
    dimensions: int
    similarity_metric: str  # cosine, dot_product, euclidean, manhattan
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class SearchRequest:
    """Encapsulates similarity query request criteria.

    Attributes:
        embedding: Query vector coordinates list.
        collection: Target collection ID name.
        namespace: Isolated search namespace.
        top_k: Max match count to return.
        filters: Metadata structured filters mapping.
        similarity_metric: Overriding metric strategy choice.
        hybrid_options: Placeholder configurations map.
        metadata: Request options metadata map.
    """
    embedding: List[float]
    collection: str
    namespace: str = "default"
    top_k: int = 10
    filters: Dict[str, Any] = field(default_factory=dict)
    similarity_metric: Optional[str] = None
    hybrid_options: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    """Immutable single match output entry.

    Attributes:
        vector_id: Matching record ID.
        score: Evaluated similarity score (higher is more similar).
        metadata: Record metadata details copy.
        payload: Document payload copy.
    """
    vector_id: str
    score: float
    metadata: Dict[str, Any]
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResponse:
    """Consolidated similarity query outcome metrics.

    Attributes:
        request_id: Unique query search request tracking ID.
        results: Sorted match results.
        search_time: Query execution latency in seconds.
        provider: Provider identifier.
        diagnostics: Processing diagnostic metadata mapping.
    """
    request_id: str
    results: List[SearchResult]
    search_time: float
    provider: str
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class SimilarityStrategy(ABC):
    """Interface defining pluggable vector distance metric algorithms."""

    @abstractmethod
    def calculate(self, v1: List[float], v2: List[float]) -> float:
        """Calculates similarity score between two float vectors.

        Args:
            v1: Vector one float coordinates.
            v2: Vector two float coordinates.

        Returns:
            float: Evaluated similarity score (higher is more similar).
        """
        pass


class CosineSimilarityStrategy(SimilarityStrategy):
    """Computes cosine similarity between two dimensional vectors."""

    def calculate(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)


class DotProductSimilarityStrategy(SimilarityStrategy):
    """Computes basic dot product between two dimensional vectors."""

    def calculate(self, v1: List[float], v2: List[float]) -> float:
        return sum(a * b for a, b in zip(v1, v2))


class EuclideanSimilarityStrategy(SimilarityStrategy):
    """Computes Euclidean distance converting values to a similarity score."""

    def calculate(self, v1: List[float], v2: List[float]) -> float:
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
        return 1.0 / (1.0 + dist)


class ManhattanSimilarityStrategy(SimilarityStrategy):
    """Computes Manhattan distance converting values to a similarity score."""

    def calculate(self, v1: List[float], v2: List[float]) -> float:
        dist = sum(abs(a - b) for a, b in zip(v1, v2))
        return 1.0 / (1.0 + dist)


class FilterEngine:
    """Evaluates recursive filters matching metadata mapping structures."""

    @staticmethod
    def matches(metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        if not filters:
            return True

        for k, v in filters.items():
            if k == "$or":
                if not isinstance(v, list):
                    return False
                matched_any = False
                for sub in v:
                    if FilterEngine.matches(metadata, sub):
                        matched_any = True
                        break
                if not matched_any:
                    return False
            elif k == "$and":
                if not isinstance(v, list):
                    return False
                for sub in v:
                    if not FilterEngine.matches(metadata, sub):
                        return False
            else:
                if k not in metadata:
                    return False

                meta_val = metadata[k]
                if isinstance(v, dict):
                    # Operator evaluating
                    for op, op_val in v.items():
                        if op == "$eq":
                            if meta_val != op_val:
                                return False
                        elif op == "$ne":
                            if meta_val == op_val:
                                return False
                        elif op == "$gt":
                            if not (meta_val > op_val):
                                return False
                        elif op == "$gte":
                            if not (meta_val >= op_val):
                                return False
                        elif op == "$lt":
                            if not (meta_val < op_val):
                                return False
                        elif op == "$lte":
                            if not (meta_val <= op_val):
                                return False
                        elif op == "$contains":
                            if isinstance(meta_val, list):
                                if op_val not in meta_val:
                                    return False
                            elif isinstance(meta_val, str):
                                if op_val not in meta_val:
                                    return False
                            else:
                                return False
                        else:
                            return False
                else:
                    if meta_val != v:
                        return False
        return True


class VectorProvider(ABC):
    """Abstract Base Class specifying provider execution requirements interfaces."""

    @abstractmethod
    def create_collection(self, info: CollectionInfo) -> None:
        """Saves a new vector collection catalog.

        Args:
            info: CollectionInfo definition.
        """
        pass

    @abstractmethod
    def delete_collection(self, collection_id: str) -> None:
        """Removes a collection.

        Args:
            collection_id: The ID of the collection.
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[CollectionInfo]:
        """Lists metadata of active collections.

        Returns:
            List[CollectionInfo]: Gathers list.
        """
        pass

    @abstractmethod
    def insert(self, records: List[VectorRecord]) -> None:
        """Indexes vector records.

        Args:
            records: Records list.
        """
        pass

    @abstractmethod
    def update(self, records: List[VectorRecord]) -> None:
        """Updates vector records.

        Args:
            records: Records list.
        """
        pass

    @abstractmethod
    def delete(self, collection: str, vector_ids: List[str], namespace: str = "default") -> None:
        """Deletes vector records.

        Args:
            collection: Target collection.
            vector_ids: Records IDs.
            namespace: Namespace bucket.
        """
        pass

    @abstractmethod
    def search(self, request: SearchRequest) -> List[SearchResult]:
        """Executes similarity match queries.

        Args:
            request: The SearchRequest.

        Returns:
            List[SearchResult]: Gathers matches.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Queries provider endpoint health connection metrics.

        Returns:
            bool: True if accessible.
        """
        pass


class MemoryVectorProvider(VectorProvider):
    """Thread-safe reference implementation storing vector indices in memory."""

    def __init__(self, provider_id: str = "memory_vector") -> None:
        self.provider_id = provider_id
        self._collections: Dict[str, CollectionInfo] = {}
        # store: collection -> namespace -> vector_id -> VectorRecord
        self._store: Dict[str, Dict[str, Dict[str, VectorRecord]]] = {}
        self._lock = threading.RLock()
        self._strategies: Dict[str, SimilarityStrategy] = {
            "cosine": CosineSimilarityStrategy(),
            "dot_product": DotProductSimilarityStrategy(),
            "euclidean": EuclideanSimilarityStrategy(),
            "manhattan": ManhattanSimilarityStrategy(),
        }

    def create_collection(self, info: CollectionInfo) -> None:
        if not info or not info.collection_id:
            raise VectorValidationError("Collection catalog must specify a valid ID.")

        with self._lock:
            if info.collection_id in self._collections:
                raise VectorValidationError(f"Collection '{info.collection_id}' already exists.")
            self._collections[info.collection_id] = info
            self._store[info.collection_id] = {}

    def delete_collection(self, collection_id: str) -> None:
        with self._lock:
            if collection_id not in self._collections:
                raise CollectionNotFoundError(f"Collection '{collection_id}' not found.")
            del self._collections[collection_id]
            if collection_id in self._store:
                del self._store[collection_id]

    def list_collections(self) -> List[CollectionInfo]:
        with self._lock:
            return list(self._collections.values())

    def insert(self, records: List[VectorRecord]) -> None:
        if not records:
            return

        with self._lock:
            for r in records:
                col_info = self._collections.get(r.collection)
                if not col_info:
                    raise CollectionNotFoundError(f"Collection '{r.collection}' does not exist.")

                if len(r.embedding) != col_info.dimensions:
                    raise VectorValidationError(
                        f"Dimension mismatch: Record has {len(r.embedding)}, but collection requires {col_info.dimensions}."
                    )

                if r.namespace not in self._store[r.collection]:
                    self._store[r.collection][r.namespace] = {}

                if r.vector_id in self._store[r.collection][r.namespace]:
                    raise VectorValidationError(
                        f"Vector ID '{r.vector_id}' already exists in namespace '{r.namespace}'."
                    )

                self._store[r.collection][r.namespace][r.vector_id] = r

    def update(self, records: List[VectorRecord]) -> None:
        if not records:
            return

        with self._lock:
            for r in records:
                col_info = self._collections.get(r.collection)
                if not col_info:
                    raise CollectionNotFoundError(f"Collection '{r.collection}' does not exist.")

                if len(r.embedding) != col_info.dimensions:
                    raise VectorValidationError(
                        f"Dimension mismatch on update: Record has {len(r.embedding)}, but collection requires {col_info.dimensions}."
                    )

                namespaces = self._store.get(r.collection, {})
                vector_map = namespaces.get(r.namespace, {})
                if r.vector_id not in vector_map:
                    raise VectorValidationError(
                        f"Vector ID '{r.vector_id}' not found in namespace '{r.namespace}' on update."
                    )

                updated_rec = dataclasses.replace(
                    r,
                    updated_at=datetime.utcnow()
                )
                self._store[r.collection][r.namespace][r.vector_id] = updated_rec

    def delete(self, collection: str, vector_ids: List[str], namespace: str = "default") -> None:
        with self._lock:
            if collection not in self._collections:
                raise CollectionNotFoundError(f"Collection '{collection}' does not exist.")

            vector_map = self._store.get(collection, {}).get(namespace, {})
            for vid in vector_ids:
                if vid in vector_map:
                    del vector_map[vid]

    def search(self, request: SearchRequest) -> List[SearchResult]:
        if not request or not request.collection:
            raise VectorValidationError("SearchRequest must specify a collection ID.")

        with self._lock:
            col_info = self._collections.get(request.collection)
            if not col_info:
                raise CollectionNotFoundError(f"Collection '{request.collection}' does not exist.")

            if len(request.embedding) != col_info.dimensions:
                raise VectorValidationError(
                    f"Search dimension mismatch: Request has {len(request.embedding)}, but collection requires {col_info.dimensions}."
                )

            # Resolve similarity strategy
            metric = request.similarity_metric or col_info.similarity_metric
            strategy = self._strategies.get(metric.lower())
            if not strategy:
                raise VectorValidationError(f"Unsupported similarity metric: '{metric}'.")

            # Collect records in the specified namespace
            namespace_records = self._store.get(request.collection, {}).get(request.namespace, {}).values()

            scored_results = []
            for rec in namespace_records:
                # Apply filter engine matches
                if FilterEngine.matches(rec.metadata, request.filters):
                    score = strategy.calculate(request.embedding, rec.embedding)
                    scored_results.append(
                        SearchResult(
                            vector_id=rec.vector_id,
                            score=score,
                            metadata=rec.metadata.copy(),
                            payload=rec.metadata.get("payload", {})
                        )
                    )

            # Sort descending by score
            scored_results.sort(key=lambda x: x.score, reverse=True)

            return scored_results[:request.top_k]

    def health_check(self) -> bool:
        return True


class VectorRegistry:
    """Thread-safe Singleton managing active VectorProviders registration and routing."""
    _instance: Optional["VectorRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "VectorRegistry":
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
            self._providers: Dict[str, VectorProvider] = {}
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def register_provider(self, provider_id: str, provider: VectorProvider) -> None:
        """Registers a VectorProvider.

        Args:
            provider_id: Unique string key identifier.
            provider: Active class interface instance.

        Raises:
            VectorValidationError: On duplicate registrations or validation errors.
        """
        if not provider_id or not str(provider_id).strip():
            raise VectorValidationError("provider_id cannot be empty.")
        if not provider:
            raise VectorValidationError("provider instance cannot be None.")

        with self._lock:
            if provider_id in self._providers:
                raise VectorValidationError(f"Provider '{provider_id}' is already registered.")
            self._providers[provider_id] = provider

        self.logger.info(f"Vector provider registered. ID: {provider_id}")

    def unregister_provider(self, provider_id: str) -> None:
        """Removes provider registration.

        Args:
            provider_id: Unique provider ID.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(f"Provider '{provider_id}' not found.")
            del self._providers[provider_id]

        self.logger.info(f"Vector provider unregistered. ID: {provider_id}")

    def get_provider(self, provider_id: str) -> VectorProvider:
        """Retrieves provider.

        Args:
            provider_id: Unique provider ID.

        Returns:
            VectorProvider: Provider adapter.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(f"Provider '{provider_id}' not found.")
            return self._providers[provider_id]

    def list_providers(self) -> List[str]:
        """Lists registered providers.

        Returns:
            List[str]: Provider IDs list.
        """
        with self._lock:
            return list(self._providers.keys())

    def search(self, provider_id: str, request: SearchRequest) -> SearchResponse:
        """Routes similarity query search request to target provider.

        Args:
            provider_id: The ID of the provider.
            request: The SearchRequest query.

        Returns:
            SearchResponse: Execution results metrics.
        """
        provider = self.get_provider(provider_id)

        self._publish_event("vector.search.started", collection=request.collection, provider_id=provider_id)
        start_time = time.perf_counter()

        try:
            results = provider.search(request)
            duration = time.perf_counter() - start_time
            self._publish_event("vector.search.completed", collection=request.collection, provider_id=provider_id)

            return SearchResponse(
                request_id=str(uuid.uuid4()),
                results=results,
                search_time=duration,
                provider=provider_id
            )
        except Exception as e:
            self._publish_event("vector.provider.failed", provider_id=provider_id, error=str(e))
            self.logger.error(f"Vector search failed on provider '{provider_id}': {e}")
            raise VectorError(f"Vector search execution crashed: {e}") from e

    def health_check(self) -> Dict[str, bool]:
        """Queries health check across registered providers.

        Returns:
            Dict[str, bool]: Health statuses map.
        """
        status_map = {}
        with self._lock:
            for pid, provider in self._providers.items():
                try:
                    status_map[pid] = provider.health_check()
                except Exception:
                    status_map[pid] = False
        return status_map

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="VectorEngine",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
