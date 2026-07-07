"""Config validator auditing setting values and reporting conflicts."""

from __future__ import annotations

from typing import List

from backend.config.models import AppConfig, EnvironmentType


class ConfigValidator:
    """Audits configurations to flag bad ports, missing API keys, or compatibility warnings."""

    @staticmethod
    def validate(config: AppConfig) -> List[str]:
        """Audits the configuration settings.

        Args:
            config: AppConfig instance to validate.

        Returns:
            List of validation warning or error messages.
        """
        errors = []

        # 1. Port range validation
        port = config.server.port
        if not (1024 <= port <= 65535):
            errors.append(f"Server port {port} must be within the user range (1024-65535).")

        # 2. Production API key checking
        if config.environment == EnvironmentType.PRODUCTION:
            for name, provider in config.providers.items():
                if provider.enabled and not provider.api_key and name != "ollama":
                    errors.append(f"LLM Provider {name} is enabled in Production but lacks an API Key.")

        # 3. Check database paths
        if not config.database.db_path:
            errors.append("Relational database path (db_path) must be defined.")

        return errors
