"""Object storage module containing S3 client abstraction and local fallbacks."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from backend.platform.storage.file_storage import FileStorage


class ObjectStorage(ABC):
    """Abstract interface class for Blob/Object storage."""

    @abstractmethod
    def upload_object(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        """Uploads raw binary bytes to block storage."""
        pass

    @abstractmethod
    def download_object(self, key: str) -> bytes:
        """Downloads raw binary bytes from block storage."""
        pass

    @abstractmethod
    def delete_object(self, key: str) -> bool:
        """Removes an object from block storage."""
        pass


class S3ObjectStorage(ObjectStorage):
    """S3-compatible implementation of ObjectStorage."""

    def __init__(self, bucket_name: str, region: str = "us-east-1", use_mock_fallback: bool = True) -> None:
        """Initializes client configurations. Fallback to LocalStorage is supported."""
        self.bucket_name = bucket_name
        self.region = region
        self.use_fallback = use_mock_fallback
        self.fallback_storage = FileStorage(root_dir=f"storage_data/s3_fallback_{bucket_name}")
        
        # Verify boto3 library is available; otherwise enforce local fallback
        try:
            import boto3
            self.s3_client = boto3.client("s3", region_name=region)
            self.has_boto = True
        except ImportError:
            self.has_boto = False

    def upload_object(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        """Uploads a file to S3 (or fallback directory)."""
        if not self.has_boto or self.use_fallback:
            return self.fallback_storage.write_file(key, data)

        import botocore.exceptions
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                **extra_args
            )
            return f"s3://{self.bucket_name}/{key}"
        except Exception:
            if self.use_fallback:
                return self.fallback_storage.write_file(key, data)
            raise

    def download_object(self, key: str) -> bytes:
        """Downloads raw binary contents."""
        if not self.has_boto or self.use_fallback:
            return self.fallback_storage.read_file(key)

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except Exception:
            if self.use_fallback:
                return self.fallback_storage.read_file(key)
            raise

    def delete_object(self, key: str) -> bool:
        """Deletes an object from the store."""
        if not self.has_boto or self.use_fallback:
            return self.fallback_storage.delete_file(key)

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False
