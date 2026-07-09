"""Environment loader parsing environment variables and populating config profiles."""

from __future__ import annotations

import os
from typing import Dict

from backend.config.models import AppConfig, DatabaseSetting, EnvironmentType, LLMProviderSetting, ServerSetting


class EnvironmentLoader:
    """Loads system environment variables and populates AppConfig instances."""

    @staticmethod
    def load_from_env() -> AppConfig:
        """Parses active environment variables to create a populated AppConfig.

        Returns:
            AppConfig with loaded settings.
        """
        # Determine environment type
        env_str = os.getenv("NEXUS_ENV", "development").lower()
        if env_str == "testing":
            env = EnvironmentType.TESTING
        elif env_str == "staging":
            env = EnvironmentType.STAGING
        elif env_str == "production":
            env = EnvironmentType.PRODUCTION
        else:
            env = EnvironmentType.DEVELOPMENT

        # Build ServerSetting
        server = ServerSetting(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            reload=(env == EnvironmentType.DEVELOPMENT),
            log_level=os.getenv("LOG_LEVEL", "info"),
        )

        # Build DatabaseSetting
        database = DatabaseSetting(
            db_path=os.getenv("DATABASE_URL", "nexus_ai.db"),
            vector_store_path=os.getenv("VECTOR_STORE_PATH", "vector_store"),
            cache_path=os.getenv("CACHE_PATH", "cache_store"),
        )

        # Preseed default providers
        providers: Dict[str, LLMProviderSetting] = {}
        for p in ["openai", "gemini", "anthropic", "ollama"]:
            providers[p] = LLMProviderSetting(
                enabled=(p == "ollama" or os.getenv(f"{p.upper()}_API_KEY") is not None),
                api_key=os.getenv(f"{p.upper()}_API_KEY", ""),
                endpoint=os.getenv(f"{p.upper()}_API_ENDPOINT", ""),
                model_name=os.getenv(f"{p.upper()}_MODEL_NAME", ""),
            )

        # Default feature flags
        feature_flags = {
            "resume_module": True,
            "github_module": True,
            "document_module": True,
            "experimental_composition": False,
        }

        return AppConfig(
            environment=env,
            server=server,
            database=database,
            providers=providers,
            feature_flags=feature_flags,
        )
