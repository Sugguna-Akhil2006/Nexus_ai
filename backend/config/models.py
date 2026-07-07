"""Pydantic data models for configuration settings and environment profiles."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class EnvironmentType(str, Enum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProviderSetting(BaseModel):
    """Configurations governing an LLM provider integration."""

    enabled: bool = True
    api_key: str = ""
    endpoint: str = ""
    model_name: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7


class DatabaseSetting(BaseModel):
    """Database and caching connection descriptors."""

    db_path: str = "nexus_ai.db"
    vector_store_path: str = "vector_store"
    cache_path: str = "cache_store"
    ttl_seconds: int = 3600


class ServerSetting(BaseModel):
    """Host and port configurations for the ASGI server."""

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"


class LimitsSetting(BaseModel):
    """Upload and request throughput bounds."""

    max_upload_size_mb: int = 50
    requests_per_minute: int = 60
    concurrent_executions: int = 10


class AppConfig(BaseModel):
    """Consolidated application config containing all operational parameters."""

    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    server: ServerSetting = Field(default_factory=ServerSetting)
    database: DatabaseSetting = Field(default_factory=DatabaseSetting)
    providers: Dict[str, LLMProviderSetting] = Field(default_factory=dict)
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    limits: LimitsSetting = Field(default_factory=LimitsSetting)
