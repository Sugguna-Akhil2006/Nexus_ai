from datetime import datetime, timedelta
import unittest
import uuid

from backend.runtime.result import (
    Result,
    ResultStatus,
    ResultValidationError,
)


class TestResultSystem(unittest.TestCase):
    """Suite of tests covering the standardized Result class lifecycle."""

    def test_success_creation(self) -> None:
        """Verifies success result instantiation and defaults."""
        result = Result.success(output="data", warnings=["some warning"])

        self.assertTrue(result.is_success())
        self.assertFalse(result.is_failure())
        self.assertTrue(result.has_warnings())
        self.assertEqual(result.output, "data")
        self.assertEqual(result.warnings, ["some warning"])
        self.assertEqual(result.errors, [])
        self.assertEqual(result.status, ResultStatus.SUCCESS)

    def test_failure_creation(self) -> None:
        """Verifies failure result instantiation and error enforcement."""
        result = Result.failure(errors=["operation failed"])

        self.assertFalse(result.is_success())
        self.assertTrue(result.is_failure())
        self.assertFalse(result.has_warnings())
        self.assertEqual(result.errors, ["operation failed"])
        self.assertEqual(result.status, ResultStatus.FAILURE)

    def test_warning_creation(self) -> None:
        """Verifies warning outcome creation."""
        result = Result.warning(output="payload", warnings=["warn"])
        self.assertTrue(result.is_success())
        self.assertFalse(result.is_failure())
        self.assertTrue(result.has_warnings())
        self.assertEqual(result.status, ResultStatus.WARNING)

    def test_timeout_creation(self) -> None:
        """Verifies timeout outcome creation."""
        result = Result.timeout(errors=["deadline exceeded"])
        self.assertFalse(result.is_success())
        self.assertTrue(result.is_failure())
        self.assertEqual(result.status, ResultStatus.TIMEOUT)

    def test_retry_creation(self) -> None:
        """Verifies retry outcome creation."""
        result = Result.retry(errors=["connection timeout"])
        self.assertFalse(result.is_success())
        self.assertTrue(result.is_failure())
        self.assertEqual(result.status, ResultStatus.RETRY)

    def test_cancel_creation(self) -> None:
        """Verifies cancelled outcome creation."""
        result = Result.cancel()
        self.assertFalse(result.is_success())
        self.assertTrue(result.is_failure())
        self.assertEqual(result.status, ResultStatus.CANCELLED)

    def test_validation_errors_in_success(self) -> None:
        """Verifies validation prevents errors list in success statuses."""
        with self.assertRaises(ResultValidationError):
            Result(
                status=ResultStatus.SUCCESS,
                errors=["some error"]
            )

    def test_validation_missing_errors_in_failure(self) -> None:
        """Verifies validation prevents empty errors list in failure statuses."""
        with self.assertRaises(ResultValidationError):
            Result(
                status=ResultStatus.FAILURE,
                errors=[]
            )

    def test_validation_negative_execution_time(self) -> None:
        """Verifies execution time validation rules."""
        with self.assertRaises(ResultValidationError):
            Result(
                status=ResultStatus.SUCCESS,
                execution_time_ms=-50.0
            )

    def test_validation_invalid_timestamps(self) -> None:
        """Verifies completion timestamps validation rules."""
        start = datetime.utcnow()
        end = start - timedelta(seconds=10)
        with self.assertRaises(ResultValidationError):
            Result(
                status=ResultStatus.SUCCESS,
                started_at=start,
                finished_at=end
            )

    def test_validation_result_id_uuid(self) -> None:
        """Verifies uuid format validation checks."""
        with self.assertRaises(ResultValidationError):
            Result(
                status=ResultStatus.SUCCESS,
                result_id="not-a-uuid"  # type: ignore
            )

    def test_duration_calculation(self) -> None:
        """Verifies calculation of duration in seconds."""
        start = datetime.utcnow()
        end = start + timedelta(milliseconds=750)
        result1 = Result(
            status=ResultStatus.SUCCESS,
            started_at=start,
            finished_at=end
        )
        self.assertEqual(result1.duration(), 0.75)

        result2 = Result(
            status=ResultStatus.SUCCESS,
            execution_time_ms=1200.0
        )
        self.assertEqual(result2.duration(), 1.2)

    def test_serialization(self) -> None:
        """Verifies serialization and deserialization functions to_dict and from_dict."""
        t_id = uuid.uuid4()
        a_id = uuid.uuid4()
        tr_id = uuid.uuid4()
        result = Result(
            status=ResultStatus.SUCCESS,
            task_id=t_id,
            agent_id=a_id,
            trace_id=tr_id,
            execution_time_ms=150.0,
            output="test output",
            warnings=["test warning"],
            metadata={"source": "test_suite"}
        )

        serialized = result.to_dict()
        self.assertEqual(serialized["status"], "SUCCESS")
        self.assertEqual(serialized["task_id"], str(t_id))
        self.assertEqual(serialized["agent_id"], str(a_id))
        self.assertEqual(serialized["trace_id"], str(tr_id))
        self.assertEqual(serialized["execution_time_ms"], 150.0)

        deserialized = Result.from_dict(serialized)
        self.assertEqual(deserialized.result_id, result.result_id)
        self.assertEqual(deserialized.task_id, result.task_id)
        self.assertEqual(deserialized.agent_id, result.agent_id)
        self.assertEqual(deserialized.trace_id, result.trace_id)
        self.assertEqual(deserialized.status, result.status)
        self.assertEqual(deserialized.output, result.output)
        self.assertEqual(deserialized.warnings, result.warnings)
        self.assertEqual(deserialized.metadata, result.metadata)

    def test_from_dict_validation_error(self) -> None:
        """Verifies that from_dict raises ResultValidationError on bad dictionary formats."""
        with self.assertRaises(ResultValidationError):
            Result.from_dict({"status": "INVALID_STATUS"})

    def test_copy(self) -> None:
        """Verifies clone method copy."""
        result = Result.success(output="sample data", metadata={"env": "testing"})
        cloned = result.copy()

        self.assertEqual(cloned, result)
        self.assertIsNot(cloned, result)
        self.assertIsNot(cloned.metadata, result.metadata)

    def test_immutability(self) -> None:
        """Verifies Result instance is frozen."""
        result = Result.success(output="data")
        with self.assertRaises(AttributeError):
            result.output = "new data"  # type: ignore


if __name__ == "__main__":
    unittest.main()
