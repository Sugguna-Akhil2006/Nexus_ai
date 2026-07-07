"""API catalog extracting and seeding REST and WebSocket gateway endpoints."""

from __future__ import annotations

from typing import List

from backend.architecture.models import APIEndpointInfo


class APICatalog:
    """Extracts and formats system REST and WebSocket endpoints."""

    @staticmethod
    def get_catalog() -> List[APIEndpointInfo]:
        """Compiles the list of system endpoints.

        Returns:
            List of APIEndpointInfo descriptors.
        """
        # Seed core documented contracts
        catalog = [
            APIEndpointInfo(
                path="/api/auth/login",
                method="POST",
                summary="Authenticate user and issue session token.",
                parameters=["username", "password"],
            ),
            APIEndpointInfo(
                path="/api/auth/register",
                method="POST",
                summary="Register new user credentials.",
                parameters=["username", "password", "email"],
            ),
            APIEndpointInfo(
                path="/api/resume/analyze",
                method="POST",
                summary="Upload resume document and trigger ATS parsing.",
                parameters=["workspace_id", "file"],
            ),
            APIEndpointInfo(
                path="/api/github/analyze",
                method="POST",
                summary="Analyze target github repository health.",
                parameters=["workspace_id", "repo_url"],
            ),
            APIEndpointInfo(
                path="/api/document/analyze",
                method="POST",
                summary="Analyze and ingest technical documents into knowledge base.",
                parameters=["workspace_id", "file"],
            ),
            APIEndpointInfo(
                path="/api/chat/ws",
                method="WS",
                summary="WebSocket gateway for streaming conversational intelligence.",
                parameters=["token"],
            ),
        ]
        return catalog
DefinitionPath = "api_catalog.py"
