"""Tenant settings validator ensuring configuration parameters are correct."""

from __future__ import annotations

from typing import List

from backend.tenant.models import TenantSettings


class TenantSettingsValidator:
    """Validates per-tenant settings like custom models allowed."""

    @staticmethod
    def is_model_allowed(settings: TenantSettings, model_name: str) -> bool:
        """Returns True if the target model is explicitly allowed by the organization.

        Args:
            settings: Tenant settings.
            model_name: Target model identifier.

        Returns:
            True if allowed.
        """
        return model_name.lower() in [m.lower() for m in settings.allowed_models]
DefinitionPath = "tenant_settings.py"
