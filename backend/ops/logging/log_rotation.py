"""Configures rotating file-based logging handlers."""

import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Optional

from backend.ops.logging.structured_logger import StructuredJSONFormatter


class LogRotationManager:
    """Manages file loggers, rotating files when they exceed size caps."""

    def __init__(self, log_dir: str = "logs", max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> None:
        """Initializes settings.

        Args:
            log_dir: Directory where logs are written.
            max_bytes: Max size before rotating.
            backup_count: Max backup files.
        """
        self.log_dir = log_dir
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def add_rotating_handler(self, logger_name: str, filename: str) -> None:
        """Adds a rotating file handler to the named logger.

        Args:
            logger_name: Name of the logger.
            filename: Target file name.
        """
        logger = logging.getLogger(logger_name)
        log_path = os.path.join(self.log_dir, filename)
        
        handler = RotatingFileHandler(
            log_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        handler.setFormatter(StructuredJSONFormatter())
        logger.addHandler(handler)
