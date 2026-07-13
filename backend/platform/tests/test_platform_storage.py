"""Unit tests for Platform Storage module."""

import os
import shutil
import time
import unittest

from backend.platform.storage.file_storage import FileStorage
from backend.platform.storage.object_storage import S3ObjectStorage
from backend.platform.storage.upload_service import UploadService
from backend.platform.storage.download_service import DownloadService
from backend.platform.auth.authorization import AuthorizationService


class TestPlatformStorage(unittest.TestCase):
    """Test suite covering files storage, object fallbacks, uploads/downloads, and retention managers."""

    def setUp(self) -> None:
        self.root_dir = "test_storage_dir"
        self.storage = FileStorage(root_dir=self.root_dir)
        self.auth = AuthorizationService()

    def tearDown(self) -> None:
        if os.path.exists(self.root_dir):
            shutil.rmtree(self.root_dir)
        if os.path.exists("storage_data"):
            shutil.rmtree("storage_data")

    def test_file_storage_operations(self) -> None:
        """Verifies direct file write/read/delete cycles."""
        fid = "doc.txt"
        data = b"Nexus AI storage content payload."
        
        path = self.storage.write_file(fid, data)
        self.assertTrue(os.path.exists(path))
        self.assertEqual(self.storage.read_file(fid), data)
        
        # Exists check
        self.assertTrue(self.storage.exists(fid))
        
        # Delete check
        self.assertTrue(self.storage.delete_file(fid))
        self.assertFalse(self.storage.exists(fid))

    def test_s3_fallback_storage(self) -> None:
        """Verifies S3 object storage fallback handles upload and download paths."""
        s3 = S3ObjectStorage(bucket_name="test-bucket", region="us-east-1", use_mock_fallback=True)
        key = "dataset.csv"
        payload = b"col1,col2\nval1,val2"
        
        path = s3.upload_object(key, payload, content_type="text/csv")
        self.assertTrue(os.path.exists(path))
        self.assertEqual(s3.download_object(key), payload)
        
        self.assertTrue(s3.delete_object(key))

    def test_upload_service_validation(self) -> None:
        """Verifies uploaded file size caps and extension whitelist rules."""
        us = UploadService(self.storage, allowed_extensions=[".png"], max_size_bytes=100)
        
        # Valid upload
        res = us.validate_file("image.png", b"12345")
        self.assertTrue(res["valid"])
        
        # Too large
        res_large = us.validate_file("image.png", b"a" * 150)
        self.assertFalse(res_large["valid"])
        
        # Blocked extension
        res_ext = us.validate_file("document.pdf", b"123")
        self.assertFalse(res_ext["valid"])

    def test_download_service_authorization(self) -> None:
        """Verifies role permissions checks are evaluated on file download requests."""
        ds = DownloadService(self.storage, self.auth)
        fid = "secret.txt"
        data = b"Secret data"
        self.storage.write_file(fid, data)

        # Admin can access
        content = ds.authorize_and_download(fid, "admin")
        self.assertEqual(content, data)

        # Viewer cannot access data:write if required, or test custom block
        with self.assertRaises(PermissionError):
            ds.authorize_and_download(fid, "viewer", required_permission="workspace:delete")
