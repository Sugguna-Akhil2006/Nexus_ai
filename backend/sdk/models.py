"""Public SDK data models for Nexus AI API requests and responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class JobStatus(str, Enum):
    """Execution job lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AnalyzeRequest:
    """Base analysis request shared across intelligence modules.

    Attributes:
        workspace_id: Target workspace identifier.
        user_id: Optional requesting user identifier.
        document_ids: Associated document identifiers.
        metadata: Module-specific input payload.
    """

    workspace_id: str
    user_id: Optional[str] = None
    document_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the request to a JSON-compatible dictionary.

        Returns:
            Dictionary representation suitable for API payloads.
        """
        payload: Dict[str, Any] = {
            "workspace_id": self.workspace_id,
            "document_ids": self.document_ids,
            "metadata": self.metadata,
        }
        if self.user_id is not None:
            payload["user_id"] = self.user_id
        return payload


@dataclass
class ResumeAnalyzeRequest(AnalyzeRequest):
    """Resume analysis request with optional inline resume text."""

    resume_text: str = ""
    document_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes resume-specific fields into the request payload.

        Returns:
            Dictionary representation including resume inputs.
        """
        payload = super().to_dict()
        if self.resume_text:
            payload["metadata"]["resume_text"] = self.resume_text
        if self.document_id:
            payload["document_ids"] = list(set(payload["document_ids"] + [self.document_id]))
        return payload


@dataclass
class GitHubAnalyzeRequest(AnalyzeRequest):
    """GitHub analysis request."""

    repository_url: str = ""
    username: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes GitHub-specific fields into the request payload.

        Returns:
            Dictionary representation including GitHub inputs.
        """
        payload = super().to_dict()
        if self.repository_url:
            payload["metadata"]["repository_url"] = self.repository_url
        if self.username:
            payload["metadata"]["username"] = self.username
        return payload


@dataclass
class DocumentAnalyzeRequest(AnalyzeRequest):
    """Document analysis request."""

    query: str = ""
    document_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes document-specific fields into the request payload.

        Returns:
            Dictionary representation including document inputs.
        """
        payload = super().to_dict()
        if self.query:
            payload["metadata"]["query"] = self.query
        if self.document_text:
            payload["metadata"]["document_text"] = self.document_text
        return payload


@dataclass
class ProfessionalAnalyzeRequest(AnalyzeRequest):
    """Professional intelligence analysis request."""

    resume_text: str = ""
    github_username: str = ""
    target_role: str = ""
    job_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes professional analysis fields into the request payload.

        Returns:
            Dictionary representation including professional inputs.
        """
        payload = super().to_dict()
        payload.update({
            "resume_text": self.resume_text,
            "github_username": self.github_username,
            "target_role": self.target_role,
            "job_description": self.job_description,
        })
        return payload


@dataclass
class WorkflowRunRequest:
    """Workflow execution request."""

    workflow_id: str
    workspace_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the workflow run request.

        Returns:
            Dictionary representation suitable for API payloads.
        """
        payload: Dict[str, Any] = {
            "workflow_id": self.workflow_id,
            "workspace_id": self.workspace_id,
            "variables": self.variables,
        }
        if self.user_id is not None:
            payload["user_id"] = self.user_id
        return payload


@dataclass
class AnalysisResponse:
    """Standard analysis response from the public API.

    Attributes:
        job_id: Unique job/execution identifier.
        status: Execution status string.
        module: Intelligence module name.
        execution_time: Duration in seconds.
        data: Result payload.
        warnings: Non-fatal warning messages.
        errors: Stage-level error messages.
    """

    job_id: str
    status: str
    module: str = ""
    execution_time: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> AnalysisResponse:
        """Creates an AnalysisResponse from an API JSON payload.

        Args:
            payload: Parsed JSON response body.

        Returns:
            Populated AnalysisResponse instance.
        """
        return cls(
            job_id=payload.get("job_id") or payload.get("execution_id", ""),
            status=payload.get("status", ""),
            module=payload.get("module", ""),
            execution_time=float(payload.get("execution_time", 0.0)),
            data=payload.get("data", {}),
            warnings=list(payload.get("warnings", [])),
            errors=dict(payload.get("errors", {})),
        )


@dataclass
class JobResponse:
    """Job status response."""

    job_id: str
    status: JobStatus
    progress: float = 0.0
    module: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> JobResponse:
        """Creates a JobResponse from an API JSON payload.

        Args:
            payload: Parsed JSON response body.

        Returns:
            Populated JobResponse instance.
        """
        status_raw = payload.get("status", JobStatus.PENDING.value)
        try:
            status = JobStatus(status_raw)
        except ValueError:
            status = JobStatus.PENDING
        return cls(
            job_id=payload.get("job_id", ""),
            status=status,
            progress=float(payload.get("progress", 0.0)),
            module=payload.get("module", ""),
            result=payload.get("result"),
            error=payload.get("error"),
            created_at=payload.get("created_at", ""),
            updated_at=payload.get("updated_at", ""),
        )


@dataclass
class WorkspaceInfo:
    """Workspace summary returned by the API."""

    workspace_id: str
    name: str
    owner_id: str = ""
    status: str = "active"

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> WorkspaceInfo:
        """Creates a WorkspaceInfo from an API JSON payload.

        Args:
            payload: Parsed JSON workspace record.

        Returns:
            Populated WorkspaceInfo instance.
        """
        return cls(
            workspace_id=payload.get("workspace_id", ""),
            name=payload.get("name", ""),
            owner_id=payload.get("owner_id", ""),
            status=payload.get("status", "active"),
        )


@dataclass
class FileUploadResponse:
    """File upload response."""

    document_id: str
    status: str
    filename: str = ""
    chars_extracted: int = 0

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> FileUploadResponse:
        """Creates a FileUploadResponse from an API JSON payload.

        Args:
            payload: Parsed JSON response body.

        Returns:
            Populated FileUploadResponse instance.
        """
        return cls(
            document_id=payload.get("document_id", ""),
            status=payload.get("status", ""),
            filename=payload.get("filename", ""),
            chars_extracted=int(payload.get("chars_extracted", 0)),
        )


@dataclass
class HistoryEntry:
    """Single history record for a past execution."""

    entry_id: str
    job_id: str
    module: str
    status: str
    workspace_id: str
    created_at: str
    execution_time: float = 0.0

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> HistoryEntry:
        """Creates a HistoryEntry from an API JSON payload.

        Args:
            payload: Parsed JSON history record.

        Returns:
            Populated HistoryEntry instance.
        """
        return cls(
            entry_id=payload.get("entry_id", ""),
            job_id=payload.get("job_id", ""),
            module=payload.get("module", ""),
            status=payload.get("status", ""),
            workspace_id=payload.get("workspace_id", ""),
            created_at=payload.get("created_at", ""),
            execution_time=float(payload.get("execution_time", 0.0)),
        )
