"""Structured audit logging service for security compliance audits."""

import datetime
import json
import logging
from typing import Dict, Any, Optional


class AuditLogger:
    """Manages writing structured security events to standard log streams."""

    def __init__(self, name: str = "nexus_audit", log_file: Optional[str] = None) -> None:
        """Initializes logging configs.

        Args:
            name: Logger identifier.
            log_file: Path to write audit logs to.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            formatter = logging.Formatter("%(message)s")
            
            # Console handler
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            
            # File handler
            if log_file:
                fh = logging.FileHandler(log_file)
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)

    def log_event(
        self,
        event_type: str,
        user_id: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Writes a structured log line to output audit stream.

        Args:
            event_type: 'auth', 'access', 'data_mutation', etc.
            user_id: ID of the performing user.
            action: Specific action performed (e.g. 'delete_workspace').
            status: Result (e.g. 'success', 'failure').
            details: Extra metadata.
        """
        payload = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "status": status,
            "details": details or {}
        }
        self.logger.info(json.dumps(payload))
