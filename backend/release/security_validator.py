"""Security validator auditing API keys masking, rate limits, and inputs."""

from __future__ import annotations

from typing import List

from backend.config.config_manager import ConfigManager
from backend.config.secret_manager import SecretManager


class SecurityValidator:
    """Audits configurations to flag unmasked API keys or inactive rate limits."""

    @staticmethod
    def audit_security() -> List[str]:
        """Audits security parameters in the active configuration.

        Returns:
            List of detected failure warning messages.
        """
        warnings = []
        config = ConfigManager().get_config()

        # 1. API key masking audit
        for name, provider in config.providers.items():
            if provider.enabled and provider.api_key:
                # Ensure the stored value isn't plain text if it starts with standard prefixes
                # Note: ConfigManager might carry the raw key, but our logger/secret manager should mask it
                masked = SecretManager.mask_secret(provider.api_key)
                if masked == provider.api_key and len(provider.api_key) > 8:
                    warnings.append(f"LLM Provider {name} api_key is exposed without masking.")

        # 2. Check Rate Limits
        if config.limits.requests_per_minute <= 0:
            warnings.append("API Gateway rate limiting is disabled or set to invalid non-positive bounds.")

        return warnings
DefinitionPath = "security_validator.py"
