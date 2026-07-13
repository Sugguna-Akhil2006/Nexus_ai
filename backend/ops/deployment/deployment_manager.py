"""Controls start and stop lifecycles of services for deployment operations."""

import logging
from typing import Dict, Any

from backend.ops.deployment.environment_validator import EnvironmentValidator
from backend.ops.deployment.startup_checker import StartupChecker
from backend.ops.deployment.shutdown_handler import ShutdownHandler


class DeploymentManager:
    """Orchestrates configuration checking, connection probes, and graceful drains."""

    def __init__(self) -> None:
        """Initializes dependencies."""
        self.validator = EnvironmentValidator()
        self.startup = StartupChecker()
        self.shutdown = ShutdownHandler()
        self.logger = logging.getLogger(__name__)

    def initialize_deployment(self) -> Dict[str, Any]:
        """Runs the validation checks sequence to determine if deployment is viable.

        Returns:
            Dictionary containing checks outcome status.
        """
        self.logger.info("Initializing deployment checks...")
        
        # 1. Validate Env
        env_ok, env_msg = self.validator.validate_env()
        if not env_ok:
            return {"status": "failed", "step": "env_validation", "error": env_msg}

        # 2. Check Startup Sanity (writable directories, etc)
        start_ok, start_msg = self.startup.check_startup_integrity()
        if not start_ok:
            return {"status": "failed", "step": "startup_integrity", "error": start_msg}

        self.logger.info("All startup checks passed. Service ready to launch.")
        return {"status": "success"}
