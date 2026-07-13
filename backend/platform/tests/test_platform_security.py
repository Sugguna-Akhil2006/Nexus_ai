"""Unit tests for Platform Security module."""

import json
import os
import unittest

from backend.platform.security.rate_limiter import RateLimiter
from backend.platform.security.request_validator import RequestValidator
from backend.platform.security.csrf import CSRFProtector
from backend.platform.security.cors import CORSManager
from backend.platform.security.audit_logger import AuditLogger
from backend.platform.security.security_headers import SecurityHeadersManager


class TestPlatformSecurity(unittest.TestCase):
    """Test suite covering rate limiting, sanitization, CSRF, and CORS headers."""

    def test_rate_limiter(self) -> None:
        """Verifies rate limits blocks exceeding requests."""
        rl = RateLimiter(rate_limit=2, window_seconds=1.0)
        client = "127.0.0.1"

        self.assertTrue(rl.is_allowed(client))
        self.assertTrue(rl.is_allowed(client))
        # Third request should be blocked
        self.assertFalse(rl.is_allowed(client))

    def test_request_validator(self) -> None:
        """Verifies HTML sanitizations and email syntax parsing."""
        rv = RequestValidator()
        self.assertEqual(rv.sanitize_string("<script>alert(1)</script> hello"), "hello")
        self.assertTrue(rv.validate_email("user@domain.com"))
        self.assertFalse(rv.validate_email("bad-email"))

    def test_csrf_protector(self) -> None:
        """Verifies CSRF token matching comparisons."""
        csrf = CSRFProtector()
        t1 = csrf.generate_token()
        t2 = csrf.generate_token()

        self.assertTrue(csrf.verify_token(t1, t1))
        self.assertFalse(csrf.verify_token(t1, t2))

    def test_cors_headers(self) -> None:
        """Verifies CORS header dictionary generations for allowed origins."""
        cors = CORSManager(allowed_origins=["http://localhost:3000"])
        self.assertTrue(cors.is_origin_allowed("http://localhost:3000"))
        self.assertFalse(cors.is_origin_allowed("http://attacker.com"))

        headers = cors.get_cors_headers("http://localhost:3000")
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "http://localhost:3000")

    def test_audit_logger(self) -> None:
        """Verifies structured audit logs file outputs."""
        log_file = "test_audit.log"
        if os.path.exists(log_file):
            os.remove(log_file)

        logger = AuditLogger(name="test_audit_log", log_file=log_file)
        logger.log_event("auth", "user-1", "login", "success", {"ip": "127.0.0.1"})

        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r") as f:
            line = f.readline()
            payload = json.loads(line)
            self.assertEqual(payload["event_type"], "auth")
            self.assertEqual(payload["user_id"], "user-1")

        for handler in list(logger.logger.handlers):
            handler.close()
            logger.logger.removeHandler(handler)

        os.remove(log_file)

    def test_security_headers(self) -> None:
        """Verifies injection of security headers."""
        shm = SecurityHeadersManager()
        headers = {}
        shm.inject_headers(headers)
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
