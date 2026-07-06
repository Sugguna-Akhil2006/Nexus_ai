"""Synchronous Nexus AI public SDK Client."""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend.sdk.api_client import APIClient
from backend.sdk.authentication import Authenticator
from backend.sdk.config import NexusConfig
from backend.sdk.exceptions import ValidationError
from backend.sdk.models import (
    AnalysisResponse,
    JobResponse,
    WorkspaceInfo,
    FileUploadResponse,
    HistoryEntry
)


class WorkspaceClient:
    """Client for workspace management operations."""

    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def create(self, name: str) -> WorkspaceInfo:
        """Creates a new workspace.

        Args:
            name: The workspace name.

        Returns:
            WorkspaceInfo: Newly created workspace metadata.
        """
        res = self._api_client.post("/workspaces", body={"name": name})
        # The API returns {"status": "success", "workspace": {...}}
        workspace_data = res.get("workspace", {})
        return WorkspaceInfo.from_dict(workspace_data)

    def list(self) -> List[WorkspaceInfo]:
        """Lists all workspaces accessible by the authenticated user.

        Returns:
            List[WorkspaceInfo]: List of workspaces.
        """
        res = self._api_client.get("/workspaces")
        workspaces = res.get("workspaces", [])
        return [WorkspaceInfo.from_dict(w) for w in workspaces]


class FileClient:
    """Client for file ingestion and tracking operations."""

    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def upload(self, workspace_id: str, filename: str, content: bytes) -> FileUploadResponse:
        """Uploads and indexes a file in the workspace.

        Args:
            workspace_id: Target workspace ID.
            filename: Name of the file.
            content: Raw file content bytes.

        Returns:
            FileUploadResponse: File ingestion status and metadata.
        """
        # Encode multipart/form-data
        boundary = f"----Boundary{uuid.uuid4().hex}"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
        
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        
        import urllib.request
        from urllib.error import HTTPError
        import json
        from backend.sdk.exceptions import map_status_to_exception
        
        url = f"{self._api_client.config.api_base}/files/upload?workspace_id={workspace_id}"
        req_headers = self._api_client._authenticator.build_headers(headers)
        
        req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self._api_client.config.timeout) as resp:
                raw = resp.read().decode("utf-8")
                parsed = json.loads(raw) if raw else {}
                return FileUploadResponse(
                    document_id=parsed.get("document_id", ""),
                    status=parsed.get("status", ""),
                    filename=filename,
                    chars_extracted=parsed.get("chars_extracted", 0)
                )
        except HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp else "{}"
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"message": raw}
            raise map_status_to_exception(exc.code, parsed) from exc

    def list(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Lists files uploaded to a workspace.

        Args:
            workspace_id: Target workspace ID.

        Returns:
            List[Dict[str, Any]]: List of file records.
        """
        res = self._api_client.get(f"/files?workspace_id={workspace_id}")
        return res.get("files", [])


class ResumeClient:
    """Client for Resume Intelligence operations."""

    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def analyze(
        self,
        workspace_id: str,
        resume_text: str = "",
        document_id: str = "",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """Triggers a resume analysis job.

        Args:
            workspace_id: Active workspace ID.
            resume_text: Raw content of the resume.
            document_id: Pre-uploaded document reference ID.
            user_id: Optional requesting user ID.
            metadata: Custom execution parameters.

        Returns:
            AnalysisResponse: Analysis job identifier and status.
        """
        body = {
            "workspace_id": workspace_id,
            "resume_text": resume_text,
            "document_id": document_id,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        res = self._api_client.post("/resume/analyze", body=body)
        return AnalysisResponse.from_dict(res)


class GitHubClient:
    """Client for GitHub Intelligence operations."""

    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def analyze(
        self,
        workspace_id: str,
        repository_url: str = "",
        username: str = "",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """Triggers a GitHub repository intelligence job.

        Args:
            workspace_id: Active workspace ID.
            repository_url: Target repository URL.
            username: Target user profile.
            user_id: Optional requesting user ID.
            metadata: Optional extra parameters.

        Returns:
            AnalysisResponse: Analysis job status details.
        """
        body = {
            "workspace_id": workspace_id,
            "repository_url": repository_url,
            "username": username,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        res = self._api_client.post("/github/analyze", body=body)
        return AnalysisResponse.from_dict(res)


class DocumentClient:
    """Client for Document Intelligence operations."""

    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def analyze(
        self,
        workspace_id: str,
        query: str = "",
        document_text: str = "",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """Triggers document processing/query analysis.

        Args:
            workspace_id: Target workspace ID.
            query: User search/query parameters.
            document_text: Raw context text inline.
            user_id: Requesting user ID.
            metadata: Optional parameters dict.

        Returns:
            AnalysisResponse: Execution job status.
        """
        body = {
            "workspace_id": workspace_id,
            "query": query,
            "document_text": document_text,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        res = self._api_client.post("/document/analyze", body=body)
        return AnalysisResponse.from_dict(res)


class ProfessionalClient:
    """Client for unified Professional Intelligence operations."""

    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def analyze(
        self,
        workspace_id: str,
        resume_text: str = "",
        github_username: str = "",
        target_role: str = "",
        job_description: str = "",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """Triggers flagship professional profile analysis.

        Args:
            workspace_id: Target workspace.
            resume_text: Inline resume details.
            github_username: Profile handle.
            target_role: Target career position.
            job_description: Job requirements matching description.
            user_id: Requesting user ID.
            metadata: Extra parameters dictionary.

        Returns:
            AnalysisResponse: Analysis status and ID.
        """
        body = {
            "workspace_id": workspace_id,
            "resume_text": resume_text,
            "github_username": github_username,
            "target_role": target_role,
            "job_description": job_description,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        res = self._api_client.post("/professional/analyze", body=body)
        return AnalysisResponse.from_dict(res)


class WorkflowClient:
    """Client for executing workflow automation pipelines."""

    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def run(
        self,
        workflow_id: str,
        workspace_id: str,
        variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> AnalysisResponse:
        """Triggers workflow execution.

        Args:
            workflow_id: Workflow definition ID.
            workspace_id: Target workspace ID.
            variables: Input arguments map.
            user_id: Requesting user.

        Returns:
            AnalysisResponse: Executed workflow summary.
        """
        body = {
            "workflow_id": workflow_id,
            "workspace_id": workspace_id,
            "variables": variables or {},
            "user_id": user_id
        }
        res = self._api_client.post("/workflows/run", body=body)
        return AnalysisResponse.from_dict(res)


class JobClient:
    """Client for tracking background jobs status."""

    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def get_status(self, job_id: str) -> JobResponse:
        """Retrieves background job status and results.

        Args:
            job_id: Unique background job ID.

        Returns:
            JobResponse: Job details.
        """
        res = self._api_client.get(f"/jobs/{job_id}")
        return JobResponse.from_dict(res)

    def list_history(self) -> List[HistoryEntry]:
        """Lists historical job execution logs.

        Returns:
            List[HistoryEntry]: List of history records.
        """
        res = self._api_client.get("/history")
        history = res.get("history", [])
        return [HistoryEntry.from_dict(h) for h in history]


class NexusClient:
    """Synchronous developer SDK entry point client for Nexus AI."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        config = NexusConfig.from_env()
        if api_key:
            config.api_key = api_key
        if base_url:
            config.base_url = base_url

        self.api_client = APIClient(config)
        self.workspaces = WorkspaceClient(self.api_client)
        self.files = FileClient(self.api_client)
        self.resume = ResumeClient(self.api_client)
        self.github = GitHubClient(self.api_client)
        self.document = DocumentClient(self.api_client)
        self.professional = ProfessionalClient(self.api_client)
        self.workflows = WorkflowClient(self.api_client)
        self.jobs = JobClient(self.api_client)
