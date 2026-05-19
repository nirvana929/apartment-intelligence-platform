"""Integration test: live readiness probes against running services.

Skipped unless all required environment variables are set to non-default
values.  When enabled, verifies that each connectivity probe in the
readiness report returns "ok".
"""
from __future__ import annotations

import os

import pytest

_mysql_dsn = os.environ.get("APTGUIDE3_MYSQL_DSN", "")
_redis_url = os.environ.get("APTGUIDE3_REDIS_URL", "")
_lease_base_url = os.environ.get("APTGUIDE3_LEASE_BASE_URL", "")
_vector_uri = os.environ.get("APTGUIDE3_VECTOR_URI", "")

_all_services_configured = all([_mysql_dsn, _redis_url, _lease_base_url, _vector_uri])

pytestmark = pytest.mark.skipif(
    not _all_services_configured,
    reason="Live services not configured; skipping readiness probe integration tests",
)


@pytest.mark.asyncio
async def test_live_probes_all_ok():
    from aptguide3.api.readiness import build_readiness_report
    from aptguide3.config import Settings

    settings = Settings()
    report = await build_readiness_report(settings, live=True)

    assert report["ready"] is True
    for check in report["checks"]:
        if check["required"]:
            assert check.get("probe") == "ok", f"{check['name']} probe failed: {check.get('probe')}"


@pytest.mark.asyncio
async def test_live_probes_record_probe_status():
    from aptguide3.api.readiness import build_readiness_report
    from aptguide3.config import Settings

    settings = Settings()
    report = await build_readiness_report(settings, live=True)

    for check in report["checks"]:
        assert "probe" in check, f"{check['name']} missing 'probe' key"
