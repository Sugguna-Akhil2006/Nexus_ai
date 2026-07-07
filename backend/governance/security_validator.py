"""Security validator responsible for prompt injection detection, PII checking, and safety validation."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.governance.models import SecurityCheckResult


class SecurityValidator:
    """Performs defensive validation scans on incoming and outgoing payloads."""

    # Simple heuristic regex for PII (SSN, credit card)
    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    CC_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
    
    # Heuristics for prompt injection detection
    INJECTION_KEYWORDS = [
        "ignore previous instructions",
        "ignore all previous",
        "system override",
        "bypass system",
        "you must now act as",
        "dan mode",
        "jailbreak",
        "reset all instructions",
    ]

    def validate_payload(self, payload: Dict[str, Any]) -> SecurityCheckResult:
        """Runs checks for injection, unsafe tool calls, sensitive leakage, and file safety.

        Args:
            payload: Request execution inputs dictionary.

        Returns:
            SecurityCheckResult: Found violations and warnings.
        """
        result = SecurityCheckResult()
        
        # Combine all text inputs to scan
        text_content = ""
        if "resume_text" in payload:
            text_content += " " + str(payload["resume_text"])
        if "query" in payload:
            text_content += " " + str(payload["query"])
        if "document_text" in payload:
            text_content += " " + str(payload["document_text"])
        if "metadata" in payload and isinstance(payload["metadata"], dict):
            # Check all values in metadata
            for v in payload["metadata"].values():
                text_content += " " + str(v)

        text_content_lower = text_content.lower()

        # 1. Prompt Injection Scanning
        for kw in self.INJECTION_KEYWORDS:
            if kw in text_content_lower:
                result.has_prompt_injection = True
                result.warnings.append(f"Prompt injection attempt detected: keyword '{kw}' matches.")
                break

        # 2. PII / Sensitive data exposure scan
        if self.SSN_PATTERN.search(text_content):
            result.detected_pii.append("SSN")
            result.warnings.append("PII Leak Warning: Social Security Number detected in content.")
        if self.CC_PATTERN.search(text_content):
            result.detected_pii.append("CreditCard")
            result.warnings.append("PII Leak Warning: Credit Card pattern detected in content.")

        # 3. Unsafe tool calls validation
        tool_calls = payload.get("tool_calls", [])
        unsafe_keywords = ["subprocess", "os.system", "eval", "exec", "shutil", "sh"]
        for t in tool_calls:
            tool_name = str(t).lower()
            if any(ukw in tool_name for ukw in unsafe_keywords):
                result.has_unsafe_tools = True
                result.warnings.append(f"Unsafe tool execution attempt blocked: tool '{t}'.")

        # 4. Malicious files extension checks
        filename = payload.get("filename", "").lower()
        malicious_exts = [".exe", ".bat", ".sh", ".py", ".cmd", ".vbs"]
        if filename and any(filename.endswith(ext) for ext in malicious_exts):
            result.is_malicious_file = True
            result.warnings.append(f"Malicious file upload attempt blocked: '{filename}' extension.")

        return result
