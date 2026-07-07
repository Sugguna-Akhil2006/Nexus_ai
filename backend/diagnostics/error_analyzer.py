"""Error analyzer classifying execution failures into standard categories."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from backend.diagnostics.models import ErrorCategory, ErrorRecord


class ErrorAnalyzer:
    """Classifies exceptions and tracebacks to target operational error categories."""

    @staticmethod
    def classify(
        request_id: str,
        error: Exception,
        module_name: Optional[str] = None,
    ) -> ErrorRecord:
        """Analyzes exception types or messages to create a categorized ErrorRecord.

        Args:
            request_id: Active request identifier.
            error: Caught exception.
            module_name: Optional module context.

        Returns:
            ErrorRecord detailing the category and message.
        """
        err_msg = str(error)
        err_type = type(error).__name__

        category = ErrorCategory.UNKNOWN

        # Simple semantic type classification
        if "validation" in err_msg.lower() or "valueerror" in err_type.lower():
            category = ErrorCategory.VALIDATION
        elif "provider" in err_msg.lower() or "openai" in err_type.lower() or "ollama" in err_type.lower():
            category = ErrorCategory.PROVIDER
        elif "timeout" in err_msg.lower() or "timeout" in err_type.lower():
            category = ErrorCategory.TIMEOUT
        elif "workflow" in err_msg.lower() or "automation" in err_msg.lower():
            category = ErrorCategory.WORKFLOW
        elif "dependency" in err_msg.lower() or "resolver" in err_msg.lower():
            category = ErrorCategory.DEPENDENCY

        return ErrorRecord(
            error_id=f"err-{uuid.uuid4().hex[:8]}",
            request_id=request_id,
            category=category,
            message=f"{err_type}: {err_msg}",
            module_name=module_name,
            timestamp=datetime.utcnow().isoformat(),
        )
