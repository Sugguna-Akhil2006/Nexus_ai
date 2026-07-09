"""Provider policies creator defining allowed provider credentials and timeouts."""

from __future__ import annotations

from backend.policy.models import (
    Policy,
    PolicyDecision,
    PolicyRule,
    PolicyType,
    RuleCondition,
)


class ProviderPolicy:
    """Configures LLM model and connection constraints."""

    @staticmethod
    def create_default(provider_id: str) -> Policy:
        """Denies expensive models or unauthorized providers."""
        return Policy(
            policy_id=f"provider_policy_{provider_id}",
            name=f"Provider model policies for {provider_id}",
            policy_type=PolicyType.PROVIDER,
            target_id=provider_id,
            rules=[
                PolicyRule(
                    rule_id="restrict_expensive_models",
                    name="Deny Expensive Model Names",
                    decision=PolicyDecision.DENY,
                    conditions=[
                        RuleCondition(field="model", operator="in", value=["gpt-4-expensive", "claude-3-opus"]),
                    ],
                    message="Model is blacklisted by organizational provider policies.",
                ),
            ],
        )
