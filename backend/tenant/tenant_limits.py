"""Tenant limits validator checking quota constraints per organization."""

from __future__ import annotations

from typing import Dict

from backend.tenant.models import TenantLimits


class TenantLimitsValidator:
    """Enforces API rate limits, token quotas, and concurrency thresholds."""

    @staticmethod
    def is_api_allowed(limits: TenantLimits, current_rpm: int) -> bool:
        """Returns True if requests per minute falls below the rate limits.

        Args:
            limits: Tenant resource limits.
            current_rpm: Current requests per minute count.

        Returns:
            True if allowed.
        """
        return current_rpm <= limits.api_rate_limit

    @staticmethod
    def is_concurrency_allowed(limits: TenantLimits, active_jobs: int) -> bool:
        """Returns True if concurrent job runs falls below concurrent limits."""
        return active_jobs < limits.max_concurrent_jobs

    @staticmethod
    def is_token_quota_allowed(limits: TenantLimits, consumed_monthly: int) -> bool:
        """Returns True if consumed tokens fall below monthly token quotas."""
        return consumed_monthly < limits.token_limit_monthly
DefinitionPath = "tenant_limits.py"
