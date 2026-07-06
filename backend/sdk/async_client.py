"""Asynchronous Nexus AI public SDK Client."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from backend.sdk.client import NexusClient
from backend.sdk.models import (
    AnalysisResponse,
    JobResponse,
    WorkspaceInfo,
    FileUploadResponse,
    HistoryEntry
)


class AsyncWorkspaceClient:
    """Asynchronous client for workspace management operations."""

    def __init__(self, sync_client: Any) -> None:
        self._sync = sync_client

    async def create(self, name: str) -> WorkspaceInfo:
        """Creates a new workspace asynchronously."""
        return await asyncio.to_thread(self._sync.create, name)

    async def list(self) -> List[WorkspaceInfo]:
        """Lists all workspaces asynchronously."""
        return await asyncio.to_thread(self._sync.list)


class AsyncFileClient:
    """Asynchronous client for file ingestion and tracking operations."""

    def __init__(self, sync_client: Any) -> None:
        self._sync = sync_client

    async def upload(self, workspace_id: str, filename: str, content: bytes) -> FileUploadResponse:
        """Uploads and indexes a file asynchronously."""
        return await asyncio.to_thread(self._sync.upload, workspace_id, filename, content)

    async def list(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Lists files in workspace asynchronously."""
        return await asyncio.to_thread(self._sync.list, workspace_id)


class AsyncResumeClient:
    """Asynchronous client for Resume Intelligence operations."""

    def __init__(self, sync_client: Any) -> None:
        self._sync = sync_client

    async def analyze(
        self,
        workspace_id: str,
        resume_text: str = "",
        document_id: str = "",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """Triggers a resume analysis job asynchronously."""
        return await asyncio.to_thread(
            self._sync.analyze,
            workspace_id,
            resume_text,
            document_id,
            user_id,
            metadata
        )


class AsyncGitHubClient:
    """Asynchronous client for GitHub Intelligence operations."""

    def __init__(self, sync_client: Any) -> None:
        self._sync = sync_client

    async def analyze(
        self,
        workspace_id: str,
        repository_url: str = "",
        username: str = "",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """Triggers a GitHub repository intelligence job asynchronously."""
        return await asyncio.to_thread(
            self._sync.analyze,
            workspace_id,
            repository_url,
            username,
            user_id,
            metadata
        )


class AsyncDocumentClient:
    """Asynchronous client for Document Intelligence operations."""

    def __init__(self, sync_client: Any) -> None:
        self._sync = sync_client

    async def analyze(
        self,
        workspace_id: str,
        query: str = "",
        document_text: str = "",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """Triggers document processing/query analysis asynchronously."""
        return await asyncio.to_thread(
            self._sync.analyze,
            workspace_id,
            query,
            document_text,
            user_id,
            metadata
        )


class AsyncProfessionalClient:
    """Asynchronous client for unified Professional Intelligence operations."""

    def __init__(self, sync_client: Any) -> None:
        self._sync = sync_client

    async def analyze(
        self,
        workspace_id: str,
        resume_text: str = "",
        github_username: str = "",
        target_role: str = "",
        job_description: str = "",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """Triggers flagship professional profile analysis asynchronously."""
        return await asyncio.to_thread(
            self._sync.analyze,
            workspace_id,
            resume_text,
            github_username,
            target_role,
            job_description,
            user_id,
            metadata
        )


class AsyncWorkflowClient:
    """Asynchronous client for executing workflow automation pipelines."""

    def __init__(self, sync_client: Any) -> None:
        self._sync = sync_client

    async def run(
        self,
        workflow_id: str,
        workspace_id: str,
        variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> AnalysisResponse:
        """Triggers workflow execution asynchronously."""
        return await asyncio.to_thread(
            self._sync.run,
            workflow_id,
            workspace_id,
            variables,
            user_id
        )


class AsyncJobClient:
    """Asynchronous client for tracking background jobs status."""

    def __init__(self, sync_client: Any) -> None:
        self._sync = sync_client

    async def get_status(self, job_id: str) -> JobResponse:
        """Retrieves background job status asynchronously."""
        return await asyncio.to_thread(self._sync.get_status, job_id)

    async def list_history(self) -> List[HistoryEntry]:
        """Lists historical job execution logs asynchronously."""
        return await asyncio.to_thread(self._sync.list_history)


class AsyncNexusClient:
    """Asynchronous developer SDK entry point client for Nexus AI."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self._sync_client = NexusClient(api_key=api_key, base_url=base_url)
        self.workspaces = AsyncWorkspaceClient(self._sync_client.workspaces)
        self.files = AsyncFileClient(self._sync_client.files)
        self.resume = AsyncResumeClient(self._sync_client.resume)
        self.github = AsyncGitHubClient(self._sync_client.github)
        self.document = AsyncDocumentClient(self._sync_client.document)
        self.professional = AsyncProfessionalClient(self._sync_client.professional)
        self.workflows = AsyncWorkflowClient(self._sync_client.workflows)
        self.jobs = AsyncJobClient(self._sync_client.jobs)
