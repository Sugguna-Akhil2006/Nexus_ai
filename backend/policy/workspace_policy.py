"""Workspace policies creator generating default workspace governance rules."""

from __future__ import annotations

from backend.policy.models import (
    Policy,
    PolicyDecision,
    PolicyRule,
    PolicyType,
    RuleCondition,
)


class WorkspacePolicy:
    """Pre-configures standard workspace limits and access control policies."""

    @staticmethod
    def create_default(workspace_id: str) -> Policy:
        """Generates default workspace cost and module access control policies."""
        return Policy(
            policy_id=f"ws_policy_{workspace_id}",
            name=f"Default Workspace Policy for {workspace_id}",
            policy_type=PolicyType.WORKSPACE,
            target_id=workspace_id,
            rules=[
                PolicyRule(
                    rule_id="max_cost_limit",
                    name="Cost Ceiling Enforcement",
                    decision=PolicyDecision.DENY,
                    conditions=[
                        RuleCondition(field="cost", operator="gt", value=10.0),
                    ],
                    message="Action cost exceeds the workspace limit of $10.00.",
                ),
                PolicyRule(
                    rule_id="warn_high_cost",
                    name="High Cost Warn Alert",
                    decision=PolicyDecision.WARN,
                    conditions=[
                        RuleCondition(field="cost", operator="gt", value=5.0),
                    ],
                    message="Warning: This action costs more than $5.00.",
                ),
            ],
        )
