"""Tests for backend.product.serialization."""

import pytest
from pydantic import BaseModel
from backend.product.serialization import (
    ProductResponse,
    PaginatedResponse,
    ErrorResponse,
    serialize_report,
    serialize_report_json,
    serialize_history,
    paginate,
)


class MockReport(BaseModel):
    report_id: str
    score: float
    tags: list = []


class TestProductResponse:
    def test_ok_creates_success_response(self):
        resp = ProductResponse.ok(data={"key": "value"})
        assert resp.success is True
        assert resp.data == {"key": "value"}

    def test_ok_includes_message(self):
        resp = ProductResponse.ok(data=42, message="done")
        assert resp.message == "done"

    def test_fail_creates_failure_response(self):
        resp = ProductResponse.fail("something broke")
        assert resp.success is False
        assert resp.data is None
        assert "something broke" in resp.message

    def test_response_has_request_id(self):
        resp = ProductResponse.ok(data=None)
        assert resp.request_id is not None
        assert len(resp.request_id) > 0

    def test_response_has_timestamp(self):
        resp = ProductResponse.ok(data=None)
        assert resp.timestamp is not None


class TestPaginatedResponse:
    def test_from_list_full_page(self):
        items = list(range(20))
        resp = PaginatedResponse.from_list(items, total=50, page=1, page_size=20)
        assert resp.items == list(range(20))
        assert resp.total == 50
        assert resp.has_next is True
        assert resp.has_prev is False

    def test_from_list_middle_page(self):
        resp = PaginatedResponse.from_list([], total=100, page=3, page_size=20)
        assert resp.has_prev is True
        assert resp.has_next is True

    def test_from_list_last_page(self):
        resp = PaginatedResponse.from_list([], total=40, page=2, page_size=20)
        assert resp.has_next is False

    def test_from_list_single_page(self):
        resp = PaginatedResponse.from_list([1, 2], total=2, page=1, page_size=20)
        assert resp.has_next is False
        assert resp.has_prev is False


class TestErrorResponse:
    def test_error_response_success_false(self):
        err = ErrorResponse(error_code="NOT_FOUND", message="Record not found")
        assert err.success is False
        assert err.error_code == "NOT_FOUND"

    def test_error_response_has_timestamp(self):
        err = ErrorResponse(error_code="ERR", message="test")
        assert err.timestamp is not None


class TestSerializeReport:
    def test_serialize_pydantic_model(self):
        report = MockReport(report_id="r-1", score=75.0, tags=["a", "b"])
        data = serialize_report(report)
        assert data["report_id"] == "r-1"
        assert data["score"] == 75.0
        assert data["tags"] == ["a", "b"]

    def test_serialize_raises_for_plain_object(self):
        class Unserializable:
            pass
        with pytest.raises(ValueError, match="Cannot serialize"):
            serialize_report(Unserializable())

    def test_serialize_report_json_returns_string(self):
        report = MockReport(report_id="r-2", score=90.0)
        result = serialize_report_json(report)
        assert isinstance(result, str)
        assert "r-2" in result


class TestSerializeHistory:
    def test_serialize_history_list(self):
        reports = [MockReport(report_id=f"r-{i}", score=float(i)) for i in range(3)]
        result = serialize_history(reports)
        assert len(result) == 3
        assert result[0]["report_id"] == "r-0"

    def test_serialize_history_skips_failures(self):
        class Bad:
            pass
        reports = [MockReport(report_id="r-ok", score=1.0), Bad()]
        result = serialize_history(reports)
        assert len(result) == 1


class TestPaginate:
    def test_paginate_first_page(self):
        items = list(range(50))
        result = paginate(items, page=1, page_size=10)
        assert result["items"] == list(range(10))
        assert result["total"] == 50
        assert result["has_next"] is True
        assert result["has_prev"] is False

    def test_paginate_last_page(self):
        items = list(range(25))
        result = paginate(items, page=3, page_size=10)
        assert result["items"] == [20, 21, 22, 23, 24]
        assert result["has_next"] is False
        assert result["has_prev"] is True

    def test_paginate_empty_list(self):
        result = paginate([], page=1, page_size=10)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["has_next"] is False

    def test_paginate_clamps_page_size(self):
        items = list(range(300))
        result = paginate(items, page=1, page_size=999)
        assert len(result["items"]) == 200  # capped at 200
