"""Tests for backend.product.cache_service."""

import time
import pytest
from backend.product.cache_service import (
    CacheService,
    NAMESPACE_REPORTS,
    NAMESPACE_JOBS,
    NAMESPACE_METRICS,
    NAMESPACE_HISTORY,
    NAMESPACE_DASHBOARD,
)


@pytest.fixture(autouse=True)
def clean_cache():
    """Reset the singleton cache state before each test."""
    svc = CacheService()
    for ns in [NAMESPACE_REPORTS, NAMESPACE_JOBS, NAMESPACE_METRICS, NAMESPACE_HISTORY, NAMESPACE_DASHBOARD]:
        svc.invalidate_namespace(ns)
    svc.reset_stats()
    yield
    for ns in [NAMESPACE_REPORTS, NAMESPACE_JOBS, NAMESPACE_METRICS, NAMESPACE_HISTORY, NAMESPACE_DASHBOARD]:
        svc.invalidate_namespace(ns)


class TestCacheServiceSingleton:
    def test_singleton_returns_same_instance(self):
        a = CacheService()
        b = CacheService()
        assert a is b


class TestCacheServiceSetGet:
    def test_set_and_get_returns_value(self):
        svc = CacheService()
        svc.set(NAMESPACE_REPORTS, "rpt-1", {"score": 85.0})
        result = svc.get(NAMESPACE_REPORTS, "rpt-1")
        assert result == {"score": 85.0}

    def test_get_missing_key_returns_none(self):
        svc = CacheService()
        assert svc.get(NAMESPACE_REPORTS, "nonexistent") is None

    def test_expired_entry_returns_none(self):
        svc = CacheService()
        svc.set(NAMESPACE_REPORTS, "rpt-expired", "value", ttl_seconds=0)
        # Entry should already be expired
        time.sleep(0.01)
        result = svc.get(NAMESPACE_REPORTS, "rpt-expired")
        assert result is None

    def test_set_overrides_existing_value(self):
        svc = CacheService()
        svc.set(NAMESPACE_REPORTS, "rpt-1", "first")
        svc.set(NAMESPACE_REPORTS, "rpt-1", "second")
        assert svc.get(NAMESPACE_REPORTS, "rpt-1") == "second"

    def test_invalid_namespace_raises_value_error(self):
        svc = CacheService()
        with pytest.raises(ValueError, match="Unknown cache namespace"):
            svc.set("invalid_ns", "key", "value")

    def test_get_invalid_namespace_raises_value_error(self):
        svc = CacheService()
        with pytest.raises(ValueError):
            svc.get("not_a_namespace", "key")


class TestCacheServiceInvalidate:
    def test_invalidate_existing_key_returns_true(self):
        svc = CacheService()
        svc.set(NAMESPACE_REPORTS, "rpt-del", "data")
        assert svc.invalidate(NAMESPACE_REPORTS, "rpt-del") is True

    def test_invalidate_missing_key_returns_false(self):
        svc = CacheService()
        assert svc.invalidate(NAMESPACE_REPORTS, "nonexistent") is False

    def test_invalidate_namespace_clears_all_entries(self):
        svc = CacheService()
        svc.set(NAMESPACE_REPORTS, "a", 1)
        svc.set(NAMESPACE_REPORTS, "b", 2)
        count = svc.invalidate_namespace(NAMESPACE_REPORTS)
        assert count == 2
        assert svc.get(NAMESPACE_REPORTS, "a") is None
        assert svc.get(NAMESPACE_REPORTS, "b") is None


class TestCacheServiceListKeys:
    def test_list_keys_returns_active_keys(self):
        svc = CacheService()
        svc.set(NAMESPACE_JOBS, "j1", "v1")
        svc.set(NAMESPACE_JOBS, "j2", "v2")
        keys = svc.list_keys(NAMESPACE_JOBS)
        assert "j1" in keys
        assert "j2" in keys

    def test_list_keys_excludes_expired(self):
        svc = CacheService()
        svc.set(NAMESPACE_JOBS, "live", "v", ttl_seconds=300)
        svc.set(NAMESPACE_JOBS, "dead", "v", ttl_seconds=0)
        time.sleep(0.01)
        keys = svc.list_keys(NAMESPACE_JOBS)
        assert "live" in keys
        assert "dead" not in keys


class TestCacheServiceExists:
    def test_exists_returns_true_for_live_entry(self):
        svc = CacheService()
        svc.set(NAMESPACE_METRICS, "m1", 42)
        assert svc.exists(NAMESPACE_METRICS, "m1") is True

    def test_exists_returns_false_for_missing_entry(self):
        svc = CacheService()
        assert svc.exists(NAMESPACE_METRICS, "missing") is False


class TestCacheServiceStats:
    def test_stats_includes_hit_rate(self):
        svc = CacheService()
        svc.set(NAMESPACE_REPORTS, "r1", "val")
        svc.get(NAMESPACE_REPORTS, "r1")   # hit
        svc.get(NAMESPACE_REPORTS, "r2")   # miss
        stats = svc.stats()
        assert stats["global_hits"] >= 1
        assert stats["global_misses"] >= 1
        assert 0 <= stats["hit_rate_pct"] <= 100

    def test_stats_includes_namespace_counts(self):
        svc = CacheService()
        svc.set(NAMESPACE_REPORTS, "r1", "a")
        svc.set(NAMESPACE_REPORTS, "r2", "b")
        stats = svc.stats()
        assert stats["namespaces"][NAMESPACE_REPORTS] >= 2
