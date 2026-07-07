"""Automated test validating all Release Candidate checks."""

from __future__ import annotations

import unittest
from backend.release_validator import run_release_candidate_validation


class TestReleaseCandidateValidation(unittest.TestCase):
    """Release Candidate assertions suite."""

    def test_run_release_candidate_validation(self) -> None:
        """Runs validation checks and asserts all subsystems are healthy."""
        success = run_release_candidate_validation()
        self.assertTrue(success, "Release Candidate Validation checks failed!")
