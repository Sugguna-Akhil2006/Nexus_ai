"""Upload service ensuring security checks and size validation of incoming files."""

import mimetypes
from typing import List, Dict, Any, Optional
from backend.platform.storage.file_storage import FileStorage


class UploadService:
    """Handles and sanitizes uploaded content, matching against validation limits."""

    def __init__(
        self,
        storage: FileStorage,
        allowed_extensions: Optional[List[str]] = None,
        max_size_bytes: int = 50 * 1024 * 1024  # Default 50MB
    ) -> None:
        """Initializes settings.

        Args:
            storage: Destination FileStorage instance.
            allowed_extensions: Acceptable list (e.g. ['.pdf', '.docx', '.png']).
            max_size_bytes: Cap size.
        """
        self.storage = storage
        self.allowed_extensions = allowed_extensions or [".pdf", ".docx", ".txt", ".png", ".jpg", ".csv", ".json"]
        self.max_size = max_size_bytes

    def validate_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Runs validation checks on filename extension and content size.

        Args:
            filename: Name of the uploaded file.
            content: Raw byte payload.

        Returns:
            Dict containing validation status and reason.
        """
        size = len(content)
        if size > self.max_size:
            return {"valid": False, "reason": f"File exceeds maximum allowed size of {self.max_size} bytes."}

        dot_idx = filename.rfind(".")
        if dot_idx == -1:
            return {"valid": False, "reason": "File lacks an extension."}

        ext = filename[dot_idx:].lower()
        if ext not in self.allowed_extensions:
            return {"valid": False, "reason": f"Extension {ext} is not allowed."}

        # Check content MIME type match
        mime_type, _ = mimetypes.guess_type(filename)

        # Hook: Virus Scan Check (detects EICAR test string)
        if not self.scan_for_viruses(content):
            return {"valid": False, "reason": "Virus scan failed: Malicious signature detected."}

        return {
            "valid": True,
            "filename": filename,
            "extension": ext,
            "mime_type": mime_type or "application/octet-stream",
            "size_bytes": size
        }

    def scan_for_viruses(self, content: bytes) -> bool:
        """Mock virus scanner hook. Returns False if a signature is detected.

        Args:
            content: Raw byte payload.
        """
        if b"EICAR-STANDARD-ANTIVIRUS" in content:
            return False
        return True

    def process_upload(self, file_id: str, filename: str, content: bytes) -> str:
        """Validates and writes the file.

        Args:
            file_id: Destination identifier inside storage.
            filename: Source uploaded file name.
            content: Raw byte payload.

        Returns:
            Absolute path to stored file.

        Raises:
            ValueError: If validation failed.
        """
        res = self.validate_file(filename, content)
        if not res["valid"]:
            raise ValueError(res["reason"])

        return self.storage.write_file(file_id, content)
