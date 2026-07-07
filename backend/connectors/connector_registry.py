"""Connector Registry managing active driver mappings for 18 enterprise connectors."""

from __future__ import annotations

from typing import Any, Dict, List, Type

from backend.connectors.base_connector import BaseConnector
from backend.connectors.models import ConnectorConfig


# Concrete Mock Connector Implementations
class MockBaseConnector(BaseConnector):
    """Base class for all mock enterprise connectors."""

    def validate_connection(self) -> bool:
        return True

    def perform_health_check(self) -> bool:
        return True

    def discover_metadata(self) -> Dict[str, Any]:
        return {"fields": ["id", "content", "updated_at"], "category": self.config.connector_type}

    def sync_data(self, checkpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Simulate returning sync items
        return [{"id": "item-1", "content": f"Sync data from {self.config.connector_type}"}]


class GitHubConnector(MockBaseConnector): pass
class GitLabConnector(MockBaseConnector): pass
class BitbucketConnector(MockBaseConnector): pass
class GoogleDriveConnector(MockBaseConnector): pass
class OneDriveConnector(MockBaseConnector): pass
class DropboxConnector(MockBaseConnector): pass
class NotionConnector(MockBaseConnector): pass
class SlackConnector(MockBaseConnector): pass
class JiraConnector(MockBaseConnector): pass
class ConfluenceConnector(MockBaseConnector): pass
class LinearConnector(MockBaseConnector): pass
class GmailConnector(MockBaseConnector): pass
class OutlookConnector(MockBaseConnector): pass
class PostgresConnector(MockBaseConnector): pass
class MySQLConnector(MockBaseConnector): pass
class MongoDBConnector(MockBaseConnector): pass
class SQLiteConnector(MockBaseConnector): pass
class FilesystemConnector(MockBaseConnector): pass


class ConnectorRegistry:
    """Dynamic registry managing driver maps of external connector integrations."""

    def __init__(self) -> None:
        self._drivers: Dict[str, Type[BaseConnector]] = {
            "github": GitHubConnector,
            "gitlab": GitLabConnector,
            "bitbucket": BitbucketConnector,
            "google_drive": GoogleDriveConnector,
            "onedrive": OneDriveConnector,
            "dropbox": DropboxConnector,
            "notion": NotionConnector,
            "slack": SlackConnector,
            "jira": JiraConnector,
            "confluence": ConfluenceConnector,
            "linear": LinearConnector,
            "gmail": GmailConnector,
            "outlook": OutlookConnector,
            "postgres": PostgresConnector,
            "mysql": MySQLConnector,
            "mongodb": MongoDBConnector,
            "sqlite": SQLiteConnector,
            "filesystem": FilesystemConnector
        }

    def register_driver(self, type_name: str, driver_cls: Type[BaseConnector]) -> None:
        self._drivers[type_name.lower()] = driver_cls

    def get_driver_class(self, type_name: str) -> Optional[Type[BaseConnector]]:
        return self._drivers.get(type_name.lower())

    def list_available_types(self) -> List[str]:
        return list(self._drivers.keys())
