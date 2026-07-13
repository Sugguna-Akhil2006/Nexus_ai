"""Local filesystem storage module."""

import os
import shutil
from typing import BinaryIO, Dict, Any


class FileStorage:
    """Manages file storage and retrieval on local disk."""

    def __init__(self, root_dir: str = "storage_data") -> None:
        """Initializes the local file storage.

        Args:
            root_dir: Target directory path for file persistence.
        """
        self.root_dir = root_dir
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)

    def _get_path(self, file_id: str) -> str:
        """Constructs target file path safely."""
        return os.path.abspath(os.path.join(self.root_dir, file_id))

    def write_file(self, file_id: str, content: bytes) -> str:
        """Writes binary data payload to local path."""
        path = self._get_path(file_id)
        # Ensure parent dirs exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def read_file(self, file_id: str) -> bytes:
        """Retrieves raw file content payload."""
        path = self._get_path(file_id)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File {file_id} not found in storage.")
        with open(path, "rb") as f:
            return f.read()

    def delete_file(self, file_id: str) -> bool:
        """Removes the file from local storage."""
        path = self._get_path(file_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def exists(self, file_id: str) -> bool:
        """Checks if file exists in storage."""
        return os.path.exists(self._get_path(file_id))
