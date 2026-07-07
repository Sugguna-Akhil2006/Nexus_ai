"""Plugin policies enforcing security sandbox levels and permissions."""

from __future__ import annotations

from backend.policy.models import (
    Policy,
    PolicyDecision,
    PolicyRule,
    PolicyType,
    RuleCondition,
)


class PluginPolicy:
    """Configures third-party plugin security constraints."""

    @staticmethod
    def create_default(plugin_id: str) -> Policy:
        """Denies plugins requesting forbidden scopes without prior approval."""
        return Policy(
            policy_id=f"plugin_policy_{plugin_id}",
            name=f"Plugin policy settings for {plugin_id}",
            policy_type=PolicyType.PLUGIN,
            target_id=plugin_id,
            rules=[
                PolicyRule(
                    rule_id="sandbox_permission_guard",
                    name="Deny Unsanctioned Filesystem Access",
                    decision=PolicyDecision.DENY,
                    conditions=[
                        RuleCondition(field="permissions", operator="contains", value="filesystem"),
                    ],
                    message="Plugin sandbox permission denied for 'filesystem' access.",
                ),
            ],
        )
