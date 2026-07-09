"""Plugin testing framework for running isolated plugin test suites."""

from __future__ import annotations

import traceback
import unittest
from typing import List, Type

from sdk.plugins.models import PluginManifestModel, PluginTestResult
from sdk.plugins.plugin_sdk import NexusPlugin


class PluginTesting:
    """Runs standardised lifecycle and health-check tests against a plugin instance.

    The testing framework instantiates the plugin, calls each lifecycle hook in
    order, and verifies health_check() returns True.  Additional test classes
    supplied by the caller are discovered and run via :mod:`unittest`.

    Example::

        result = PluginTesting.run_lifecycle_tests(manifest, MyPlugin)
        assert result.success
    """

    @staticmethod
    def run_lifecycle_tests(
        manifest: PluginManifestModel,
        plugin_cls: Type[NexusPlugin],
    ) -> PluginTestResult:
        """Exercises every lifecycle hook and returns a structured test result.

        Args:
            manifest: Plugin manifest (used for the result label).
            plugin_cls: The concrete :class:`NexusPlugin` subclass to test.

        Returns:
            :class:`PluginTestResult` summarising passed/failed counts.
        """
        passed = 0
        errors: List[str] = []

        def run_step(label: str, fn: object, *args: object) -> None:
            nonlocal passed
            try:
                fn(*args)  # type: ignore[call-arg]
                passed += 1
            except Exception as exc:
                errors.append(f"{label}: {exc}\n{traceback.format_exc()}")

        instance = plugin_cls()

        run_step("on_load", instance.on_load)
        run_step("on_enable", instance.on_enable)
        run_step("on_disable", instance.on_disable)
        run_step("on_update", instance.on_update, "99.0.0")
        run_step("on_remove", instance.on_remove)

        # health_check must return True
        try:
            healthy = instance.health_check()
            if healthy:
                passed += 1
            else:
                errors.append("health_check: returned False.")
        except Exception as exc:
            errors.append(f"health_check: {exc}")

        return PluginTestResult(
            plugin_id=manifest.plugin_id,
            passed=passed,
            failed=len(errors),
            errors=errors,
            success=len(errors) == 0,
        )

    @staticmethod
    def run_unittest_suite(test_class: Type[unittest.TestCase]) -> PluginTestResult:
        """Runs a unittest.TestCase subclass and maps results to :class:`PluginTestResult`.

        Args:
            test_class: TestCase subclass to execute.

        Returns:
            :class:`PluginTestResult`.
        """
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, "w"))  # type: ignore[call-overload]

        import io
        buf = io.StringIO()
        runner = unittest.TextTestRunner(verbosity=0, stream=buf)
        result = runner.run(suite)

        error_msgs = [f"{str(tc)}: {err}" for tc, err in result.errors + result.failures]
        passed = result.testsRun - len(result.errors) - len(result.failures)

        return PluginTestResult(
            plugin_id=test_class.__name__,
            passed=passed,
            failed=len(result.errors) + len(result.failures),
            errors=error_msgs,
            success=result.wasSuccessful(),
        )


import os  # noqa: E402 – imported at bottom to avoid shadowing stdlib
