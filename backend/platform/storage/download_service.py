"""Download service verifying permissions and retrieving stored files securely."""

from typing import Dict, Any, Optional
from backend.platform.storage.file_storage import FileStorage
from backend.platform.auth.authorization import AuthorizationService


class DownloadService:
    """Coordinates secure file retrieval, validating access policies first."""

    def __init__(self, storage: FileStorage, auth_service: AuthorizationService) -> None:
        """Initializes settings.

        Args:
            storage: Storage backend engine.
            auth_service: System authorization policy checker.
        """
        self.storage = storage
        self.auth_service = auth_service

    def authorize_and_download(
        self,
        file_id: str,
        user_role: str,
        required_permission: str = "data:read"
    ) -> bytes:
        """Validates if user role has read permission, then returns file content.

        Args:
            file_id: Storage file key.
            user_role: The role of the requesting user.
            required_permission: The capability token needed.

        Returns:
            The raw file byte content.

        Raises:
            PermissionError: If user is unauthorized.
            FileNotFoundError: If file not found in storage.
        """
        # Validate RBAC permissions
        if not self.auth_service.has_permission(user_role, required_permission):
            raise PermissionError("Access denied. Insufficient permissions to download this resource.")

        if not self.storage.exists(file_id):
            raise FileNotFoundError(f"Requested file {file_id} not found in storage.")

        return self.storage.read_file(file_id)
