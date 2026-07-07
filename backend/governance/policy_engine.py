"""Policy engine responsible for evaluating constraint rules against execution contexts."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.governance.models import PolicyRule
from backend.governance.policy_registry import PolicyRegistry


class PolicyEngine:
    """Evaluates workspace and global policy rules against execution contexts."""

    def __init__(self, registry: Optional[PolicyRegistry] = None) -> None:
        self.registry = registry or PolicyRegistry()

    def evaluate(self, context: Dict[str, Any]) -> List[str]:
        """Evaluates policies against the given execution context parameters.

        Args:
            context: Context containing workspace_id, module, model, provider,
                     cost, tokens, execution_time, plugins.

        Returns:
            List[str]: Descriptions of all policy violations. Empty if compliant.
        """
        workspace_id = context.get("workspace_id", "default")
        policies = self.registry.list_policies(workspace_id)
        violations: List[str] = []

        for p in policies:
            # 1. Module Access Checks
            module = context.get("module")
            if module and "*" not in p.allowed_modules and module not in p.allowed_modules:
                violations.append(f"Module '{module}' is not allowed by policy '{p.policy_id}'.")

            # 2. Model Restrictions
            model = context.get("model")
            if model and "*" not in p.allowed_models and model not in p.allowed_models:
                violations.append(f"Model '{model}' is not allowed by policy '{p.policy_id}'.")

            # 3. Provider Restrictions
            provider = context.get("provider")
            if provider and "*" not in p.allowed_providers and provider not in p.allowed_providers:
                violations.append(f"Provider '{provider}' is not allowed by policy '{p.policy_id}'.")

            # 4. Token Usage Bounds
            tokens = context.get("tokens", 0)
            if tokens > p.max_tokens:
                violations.append(f"Token count {tokens} exceeds policy limit of {p.max_tokens} in '{p.policy_id}'.")

            # 5. Cost Threshold Bounds
            cost = context.get("cost", 0.0)
            if cost > p.max_cost:
                violations.append(f"Estimated cost ${cost:.4f} exceeds limit of ${p.max_cost:.4f} in '{p.policy_id}'.")

            # 6. Plugin Authorization checks
            plugins = context.get("plugins", [])
            for pl in plugins:
                if "*" not in p.allowed_plugins and pl not in p.allowed_plugins:
                    violations.append(f"Plugin '{pl}' is unauthorized by policy '{p.policy_id}'.")

            # 7. Max Execution Time bounds
            exec_time = context.get("execution_time", 0.0)
            if exec_time > p.max_execution_time:
                violations.append(
                    f"Execution time {exec_time}s exceeds policy limit of {p.max_execution_time}s in '{p.policy_id}'."
                )

        return violations
