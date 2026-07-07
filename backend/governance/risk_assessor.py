"""Risk assessor classifying execution risks dynamically."""

from __future__ import annotations

from typing import Any, Dict

from backend.governance.models import RiskAssessment, RiskLevel, SecurityCheckResult


class RiskAssessor:
    """Classifies execution risk dynamically with detailed natural language explanations."""

    def assess_risk(self, context: Dict[str, Any], security_result: SecurityCheckResult) -> RiskAssessment:
        """Evaluates payload and safety metrics to classify risk dynamically.

        Args:
            context: Context details of the current execution.
            security_result: Security scans result.

        Returns:
            RiskAssessment: The calculated level, score, and explanation.
        """
        score = 0.1
        reasons: List[str] = []

        # 1. Critical risk conditions
        if security_result.has_prompt_injection:
            score = max(score, 0.95)
            reasons.append("Prompt injection keywords or vector patterns detected.")
        if security_result.is_malicious_file:
            score = max(score, 0.90)
            reasons.append("Uploaded file extension or signature flagged as malicious.")
        if security_result.has_unsafe_tools:
            score = max(score, 0.85)
            reasons.append("Execution uses unsafe system commands or executable functions.")

        # 2. High risk conditions
        if security_result.detected_pii:
            score = max(score, 0.75)
            reasons.append(f"PII data types exposed: {', '.join(security_result.detected_pii)}.")

        # 3. Medium risk conditions
        tokens = context.get("tokens", 0)
        if tokens > 4096:
            score = max(score, 0.50)
            reasons.append(f"High token consumption: {tokens} tokens requested.")

        cost = context.get("cost", 0.0)
        if cost > 0.50:
            score = max(score, 0.45)
            reasons.append(f"High estimated cost: ${cost:.2f}.")

        # Classify Level
        if score >= 0.85:
            level = RiskLevel.CRITICAL
        elif score >= 0.70:
            level = RiskLevel.HIGH
        elif score >= 0.40:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        if not reasons:
            explanation = "Execution complies with default governance safety guidelines. No warnings flagged."
        else:
            explanation = f"Risk flagged due to: {'; '.join(reasons)}"

        return RiskAssessment(
            risk_level=level,
            score=score,
            explanation=explanation,
            checks_evaluated={
                "has_prompt_injection": security_result.has_prompt_injection,
                "detected_pii": security_result.detected_pii,
                "has_unsafe_tools": security_result.has_unsafe_tools,
                "is_malicious_file": security_result.is_malicious_file,
                "tokens": tokens,
                "cost": cost
            }
        )
