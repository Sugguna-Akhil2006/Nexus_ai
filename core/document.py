"""Document Agent and Enterprise Document Lifecycle Management Module.

Provides abstractions, registries, in-memory reference providers, validation checks,
and routing engines for documents, versions, metadata, and capability routing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import logging
import os
import threading
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from core.base import AgentState, AgentStatus, BaseAgent
from core.event import Event, EventBus, EventType
from core.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from core.task import Task
from core.logger import StructuredLogger


# =====================================================================
# Exceptions
# =====================================================================

class DocumentError(NexusException):
    """Base exception for all Document Agent related errors."""
    pass


class DocumentValidationError(DocumentError):
    """Raised when document validation or checks fail."""
    pass


class DocumentNotFoundError(DocumentError):
    """Raised when a document or version is not found."""
    pass


# =====================================================================
# Enums and Data Models
# =====================================================================

class DocumentStatus(Enum):
    """Lifecycle statuses of a document."""
    UPLOADED = "UPLOADED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DocumentMetadata:
    """Enterprise metadata attributes associated with a document.

    Attributes:
        title: Document title.
        author: Creation author.
        language: Language categorization.
        tags: List of catalog tags.
        page_count: Page count parameter, default 0.
        creation_date: Creation timestamp, optional.
        modification_date: Last modification timestamp, optional.
        custom_metadata: Extra arbitrary metadata dictionary.
    """
    title: str = ""
    author: str = ""
    language: str = ""
    tags: List[str] = field(default_factory=list)
    page_count: int = 0
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Document:
    """Immutable model representing a document profile.

    Attributes:
        document_id: Unique document ID.
        workspace_id: Workspace tenant group owner.
        project_id: Project scope tag.
        owner_id: User ID of creator.
        filename: Original file name.
        mime_type: Detected MIME type.
        file_size: Size in bytes.
        checksum: Cryptographic SHA-256 hash checksum.
        version: Integer version counter.
        status: Status category.
        created_at: Creation timestamp.
        updated_at: Last modification timestamp.
        metadata: Linked DocumentMetadata.
    """
    document_id: str
    workspace_id: str
    project_id: str
    owner_id: str
    filename: str
    mime_type: str
    file_size: int
    checksum: str
    version: int
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: DocumentMetadata


@dataclass(frozen=True)
class DocumentVersion:
    """Immutable log of a specific document version.

    Attributes:
        version_id: Unique version ID.
        document_id: Target document ID.
        version_number: Target version number.
        checksum: Hash checksum matching this version's payload.
        created_at: Version creation timestamp.
        created_by: Target user ID of publisher.
        metadata: Associated version metadata.
    """
    version_id: str
    document_id: str
    version_number: int
    checksum: str
    created_at: datetime
    created_by: str
    metadata: DocumentMetadata


@dataclass(frozen=True)
class DocumentImportRequest:
    """Parameters envelope for document ingestion tasks."""
    workspace_id: str
    project_id: str
    uploaded_by: str
    source: Union[bytes, str]
    filename: str
    content_type: str
    metadata: Optional[DocumentMetadata] = None


@dataclass(frozen=True)
class DocumentImportResponse:
    """ ingesting outcomes response profile."""
    document: Document
    validation_result: Dict[str, Any]
    routing_plan: List[str]
    diagnostics: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Validation Utilities
# =====================================================================

SUPPORTED_MIMES: Set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/markdown",
    "text/html",
    "text/csv",
    "application/json",
    "application/xml",
    "image/png",
    "image/jpeg",
    "application/zip",
}

MIME_MAP: Dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".html": "text/html",
    ".csv": "text/csv",
    ".json": "application/json",
    ".xml": "application/xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".zip": "application/zip",
}


def detect_mime_type(filename: str) -> str:
    """Detects MIME type by extension."""
    _, ext = os.path.splitext(filename.lower())
    return MIME_MAP.get(ext, "application/octet-stream")


def compute_checksum(content: bytes) -> str:
    """Computes SHA-256 checksum."""
    return hashlib.sha256(content).hexdigest()


def validate_mime_type(mime_type: str) -> None:
    """Validates supported MIME types."""
    if mime_type not in SUPPORTED_MIMES:
        raise DocumentValidationError(f"Unsupported MIME type: {mime_type}")


def validate_file_size(size: int, max_size: int = 100 * 1024 * 1024) -> None:
    """Validates file size limits."""
    if size < 0:
        raise DocumentValidationError("File size cannot be negative.")
    if size > max_size:
        raise DocumentValidationError(f"File size {size} exceeds maximum limit of {max_size} bytes.")


def validate_content(content: bytes) -> None:
    """Validates document binary integrity."""
    if content is None or not isinstance(content, (bytes, bytearray)):
        raise DocumentValidationError("Invalid document content type. Must be bytes.")
    if len(content) == 0:
        raise DocumentValidationError("Document content cannot be empty or corrupted.")


# =====================================================================
# Document Storage Provider Abstraction
# =====================================================================

class DocumentProvider(ABC):
    """Abstract contract governing document storage operations."""

    @abstractmethod
    def import_document(self, document: Document, content: bytes) -> Document:
        """Saves document binary content and metadata profile."""
        pass

    @abstractmethod
    def retrieve_document(self, document_id: str) -> Optional[bytes]:
        """Retrieves raw content bytes."""
        pass

    @abstractmethod
    def update_document(self, document: Document) -> Document:
        """Updates document profile values."""
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Removes a document and linked versions from persistence."""
        pass

    @abstractmethod
    def archive_document(self, document_id: str) -> bool:
        """Sets document state to ARCHIVED."""
        pass

    @abstractmethod
    def list_documents(self, workspace_id: str) -> List[Document]:
        """Lists documents inside a workspace tenant."""
        pass

    @abstractmethod
    def add_version(self, version: DocumentVersion) -> DocumentVersion:
        """Stores a new DocumentVersion."""
        pass

    @abstractmethod
    def get_versions(self, document_id: str) -> List[DocumentVersion]:
        """Lists versions associated with a document."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks connection integrity."""
        pass


class InMemoryDocumentProvider(DocumentProvider):
    """In-memory persistence reference implementation of DocumentProvider."""

    def __init__(self) -> None:
        self.documents: Dict[str, Document] = {}
        self.contents: Dict[str, bytes] = {}
        self.versions: Dict[str, List[DocumentVersion]] = {}
        self.health_healthy = True

    def import_document(self, document: Document, content: bytes) -> Document:
        self.documents[document.document_id] = document
        self.contents[document.document_id] = content
        if document.document_id not in self.versions:
            self.versions[document.document_id] = []
        return document

    def retrieve_document(self, document_id: str) -> Optional[bytes]:
        return self.contents.get(document_id)

    def update_document(self, document: Document) -> Document:
        self.documents[document.document_id] = document
        return document

    def delete_document(self, document_id: str) -> bool:
        if document_id in self.documents:
            del self.documents[document_id]
            self.contents.pop(document_id, None)
            self.versions.pop(document_id, None)
            return True
        return False

    def archive_document(self, document_id: str) -> bool:
        doc = self.documents.get(document_id)
        if doc:
            import dataclasses
            archived = dataclasses.replace(doc, status=DocumentStatus.ARCHIVED.value, updated_at=datetime.utcnow())
            self.documents[document_id] = archived
            return True
        return False

    def list_documents(self, workspace_id: str) -> List[Document]:
        return [doc for doc in self.documents.values() if doc.workspace_id == workspace_id]

    def add_version(self, version: DocumentVersion) -> DocumentVersion:
        doc_id = version.document_id
        if doc_id not in self.versions:
            self.versions[doc_id] = []
        self.versions[doc_id].append(version)
        return version

    def get_versions(self, document_id: str) -> List[DocumentVersion]:
        return self.versions.get(document_id, [])

    def health_check(self) -> bool:
        return self.health_healthy


# =====================================================================
# Document Registry
# =====================================================================

class DocumentRegistry:
    """Thread-safe registry routing ingestion through active providers."""

    _instance: Optional["DocumentRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "DocumentRegistry":
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
            self._providers: Dict[str, DocumentProvider] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register_provider(self, provider_id: str, provider: DocumentProvider) -> None:
        """Registers a DocumentProvider."""
        if not provider_id or not str(provider_id).strip():
            raise DocumentValidationError("provider_id cannot be empty.")
        if not provider:
            raise DocumentValidationError("provider instance cannot be None.")

        with self._lock:
            if provider_id in self._providers:
                raise DocumentValidationError(f"Provider '{provider_id}' already registered.")
            self._providers[provider_id] = provider
            self._logger.info(f"Registered document provider: {provider_id}")

    def unregister_provider(self, provider_id: str) -> None:
        """Removes a registered provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise DocumentValidationError(f"Provider '{provider_id}' not found.")
            del self._providers[provider_id]
            self._logger.info(f"Unregistered document provider: {provider_id}")

    def get_provider(self, provider_id: str) -> DocumentProvider:
        """Retrieves provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise DocumentValidationError(f"Provider '{provider_id}' not registered.")
            return self._providers[provider_id]

    def list_providers(self) -> List[str]:
        """Lists active provider IDs."""
        with self._lock:
            return list(self._providers.keys())

    def check_duplicate(self, provider_id: str, workspace_id: str, project_id: str, checksum: str) -> None:
        """Checks for duplicate uploads inside same workspace and project."""
        provider = self.get_provider(provider_id)
        docs = provider.list_documents(workspace_id)
        for doc in docs:
            if doc.project_id == project_id and doc.checksum == checksum and doc.status != DocumentStatus.DELETED.value:
                raise DocumentValidationError(f"Duplicate upload detected. Checksum '{checksum}' already exists.")

    def health_check(self) -> Dict[str, bool]:
        """Queries health of registered providers."""
        with self._lock:
            results = {}
            for pid, provider in self._providers.items():
                try:
                    results[pid] = provider.health_check()
                except Exception:
                    results[pid] = False
            return results


# =====================================================================
# Ingestion Routing Abstractions
# =====================================================================

class DocumentRoutingStrategy(ABC):
    """Abstract routing determiner outlining downstream agent pipelines."""

    @abstractmethod
    def determine_route(self, document: Document, content: bytes) -> List[str]:
        """Determines target agent capabilities list based on format and context."""
        pass


class DefaultDocumentRoutingStrategy(DocumentRoutingStrategy):
    """Configuration-driven capability mapping selector."""

    def __init__(self, routes_config: Optional[Dict[str, List[str]]] = None) -> None:
        self.routes_config = routes_config or {
            "application/pdf": ["OCR", "EMBEDDING", "SEARCH_INDEX", "KNOWLEDGE_BASE"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ["EMBEDDING", "SEARCH_INDEX", "KNOWLEDGE_BASE"],
            "text/plain": ["EMBEDDING", "SEARCH_INDEX", "KNOWLEDGE_BASE"],
            "text/markdown": ["EMBEDDING", "SEARCH_INDEX", "KNOWLEDGE_BASE"],
            "text/html": ["EMBEDDING", "SEARCH_INDEX", "KNOWLEDGE_BASE"],
            "text/csv": ["EMBEDDING", "SEARCH_INDEX", "KNOWLEDGE_BASE"],
            "application/json": ["EMBEDDING", "SEARCH_INDEX", "KNOWLEDGE_BASE"],
            "application/xml": ["EMBEDDING", "SEARCH_INDEX", "KNOWLEDGE_BASE"],
            "image/png": ["OCR", "EMBEDDING", "SEARCH_INDEX"],
            "image/jpeg": ["OCR", "EMBEDDING", "SEARCH_INDEX"],
        }

    def determine_route(self, document: Document, content: bytes) -> List[str]:
        return list(self.routes_config.get(document.mime_type, ["EMBEDDING", "SEARCH_INDEX"]))


# =====================================================================
# Document Agent
# =====================================================================

class DocumentAgent(BaseAgent):
    """System agent governing the lifecycle and processing pipeline of documents."""

    def __init__(
        self,
        name: str = "DocumentAgent",
        description: str = "Ingests, versions, validates, and routes documents through capabilities pipelines",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ) -> None:
        caps = capabilities or ["DOCUMENT_INGESTION", "LIFECYCLE_MANAGEMENT"]
        super().__init__(name=name, description=description, version=version, capabilities=caps)
        self.registry = DocumentRegistry()
        self.event_bus = EventBus()
        self.routing_strategy: DocumentRoutingStrategy = DefaultDocumentRoutingStrategy()

    def initialize(self) -> None:
        """Initializes the agent."""
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
                raise DocumentValidationError("No document providers registered.")
            provider_id = providers[0]

        provider = self.registry.get_provider(provider_id)

        if action == "import_document":
            ws_id = task.metadata.get("workspace_id")
            proj_id = task.metadata.get("project_id", "default")
            uploaded_by = task.metadata.get("uploaded_by")
            source = task.metadata.get("source")
            filename = task.metadata.get("filename")
            content_type = task.metadata.get("content_type")
            meta_input = task.metadata.get("metadata")

            if not ws_id or not uploaded_by or source is None or not filename:
                raise DocumentValidationError("Missing required import parameters (workspace_id, uploaded_by, source, filename).")

            # Extract source bytes
            if isinstance(source, str):
                # source path or string text. Convert to bytes
                content = source.encode("utf-8")
            else:
                content = bytes(source)

            # Ingestion Start Event
            self._publish_event("document.import.started", filename=filename, workspace_id=ws_id)

            # Validation
            validate_content(content)
            file_size = len(content)
            validate_file_size(file_size)

            mime = content_type or detect_mime_type(filename)
            validate_mime_type(mime)

            checksum = compute_checksum(content)
            self.registry.check_duplicate(provider_id, ws_id, proj_id, checksum)

            # Validated Event
            self._publish_event("document.validated", filename=filename, checksum=checksum)

            # Reconstruct Metadata
            if meta_input and isinstance(meta_input, dict):
                meta = DocumentMetadata(
                    title=meta_input.get("title", filename),
                    author=meta_input.get("author", uploaded_by),
                    language=meta_input.get("language", "en"),
                    tags=meta_input.get("tags", []),
                    page_count=meta_input.get("page_count", 0),
                    creation_date=meta_input.get("creation_date"),
                    modification_date=meta_input.get("modification_date"),
                    custom_metadata=meta_input.get("custom_metadata", {})
                )
            elif meta_input and isinstance(meta_input, DocumentMetadata):
                meta = meta_input
            else:
                meta = DocumentMetadata(title=filename, author=uploaded_by)

            doc_id = str(uuid.uuid4())
            now = datetime.utcnow()
            doc = Document(
                document_id=doc_id,
                workspace_id=ws_id,
                project_id=proj_id,
                owner_id=uploaded_by,
                filename=filename,
                mime_type=mime,
                file_size=file_size,
                checksum=checksum,
                version=1,
                status=DocumentStatus.UPLOADED.value,
                created_at=now,
                updated_at=now,
                metadata=meta
            )

            created_doc = provider.import_document(doc, content)

            # Register Version
            v_id = str(uuid.uuid4())
            version = DocumentVersion(
                version_id=v_id,
                document_id=doc_id,
                version_number=1,
                checksum=checksum,
                created_at=now,
                created_by=uploaded_by,
                metadata=meta
            )
            provider.add_version(version)

            # Routing Plan
            route_plan = self.routing_strategy.determine_route(doc, content)
            self._publish_event("document.routing.completed", document_id=doc_id, plan=route_plan)

            # Import Complete Event
            self._publish_event("document.import.completed", document_id=doc_id, workspace_id=ws_id)

            return DocumentImportResponse(
                document=created_doc,
                validation_result={"valid": True, "mime": mime, "size": file_size},
                routing_plan=route_plan
            )

        elif action == "retrieve_document":
            doc_id = task.metadata.get("document_id")
            if not doc_id:
                raise DocumentValidationError("Missing document_id parameter.")

            content = provider.retrieve_document(doc_id)
            if content is None:
                raise DocumentNotFoundError(f"Document '{doc_id}' not found.")
            return content

        elif action == "archive_document":
            doc_id = task.metadata.get("document_id")
            if not doc_id:
                raise DocumentValidationError("Missing document_id parameter.")

            success = provider.archive_document(doc_id)
            if success:
                self._publish_event("document.archived", document_id=doc_id)
            return success

        elif action == "delete_document":
            doc_id = task.metadata.get("document_id")
            if not doc_id:
                raise DocumentValidationError("Missing document_id parameter.")

            success = provider.delete_document(doc_id)
            if success:
                self._publish_event("document.deleted", document_id=doc_id)
            return success

        elif action == "list_documents":
            ws_id = task.metadata.get("workspace_id")
            if not ws_id:
                raise DocumentValidationError("Missing workspace_id parameter.")
            return provider.list_documents(ws_id)

        elif action == "create_version":
            doc_id = task.metadata.get("document_id")
            source = task.metadata.get("source")
            created_by = task.metadata.get("created_by")
            meta_input = task.metadata.get("metadata")

            if not doc_id or source is None or not created_by:
                raise DocumentValidationError("Missing parameters (document_id, source, created_by).")

            docs = provider.list_documents(task.metadata.get("workspace_id", ""))
            doc = None
            if doc_id in provider.documents:
                doc = provider.documents[doc_id]
            else:
                for d in docs:
                    if d.document_id == doc_id:
                        doc = d
                        break

            if not doc:
                raise DocumentNotFoundError(f"Document '{doc_id}' not found.")

            if isinstance(source, str):
                content = source.encode("utf-8")
            else:
                content = bytes(source)

            validate_content(content)
            file_size = len(content)
            validate_file_size(file_size)
            checksum = compute_checksum(content)

            # Check if this checksum already matches active version
            if doc.checksum == checksum:
                raise DocumentValidationError("Version payload matches the existing document checksum.")

            # Load versions to determine next number
            versions = provider.get_versions(doc_id)
            next_version_num = len(versions) + 1

            if meta_input and isinstance(meta_input, dict):
                meta = DocumentMetadata(
                    title=meta_input.get("title", doc.filename),
                    author=meta_input.get("author", created_by),
                    tags=meta_input.get("tags", []),
                    page_count=meta_input.get("page_count", 0),
                    custom_metadata=meta_input.get("custom_metadata", {})
                )
            elif meta_input and isinstance(meta_input, DocumentMetadata):
                meta = meta_input
            else:
                meta = doc.metadata

            now = datetime.utcnow()
            v_id = str(uuid.uuid4())
            new_version = DocumentVersion(
                version_id=v_id,
                document_id=doc_id,
                version_number=next_version_num,
                checksum=checksum,
                created_at=now,
                created_by=created_by,
                metadata=meta
            )
            provider.add_version(new_version)

            # Update Document main entry
            import dataclasses
            updated_doc = dataclasses.replace(
                doc,
                checksum=checksum,
                file_size=file_size,
                version=next_version_num,
                updated_at=now,
                metadata=meta
            )
            provider.update_document(updated_doc)
            self._publish_event("document.version.created", document_id=doc_id, version=next_version_num)

            return new_version

        else:
            raise DocumentValidationError(f"Unsupported action: {action}")

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="DocumentAgent",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
