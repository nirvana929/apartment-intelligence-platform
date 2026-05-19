from __future__ import annotations

import pytest

from aptguide3.api.readiness import build_readiness_report
from aptguide3.config import Settings


@pytest.mark.asyncio
async def test_readiness_reports_missing_live_credentials_without_crashing():
    report = await build_readiness_report(Settings(llm_api_key="", embedding_api_key=""))
    names = {check["name"] for check in report["checks"]}
    assert {"mysql_config", "redis_config", "lease_config", "llm_config", "embedding_config"}.issubset(names)
    assert isinstance(report["ready"], bool)


@pytest.mark.asyncio
async def test_readiness_not_ready_when_required_config_missing():
    settings = Settings(mysql_dsn="", redis_url="")
    report = await build_readiness_report(settings)
    assert report["ready"] is False


@pytest.mark.asyncio
async def test_readiness_ready_when_required_config_present():
    settings = Settings(
        mysql_dsn="mysql+asyncmy://root:pass@localhost:3306/test",
        redis_url="redis://localhost:6379/0",
        lease_base_url="http://localhost:8081",
        vector_uri="http://localhost:19530",
    )
    report = await build_readiness_report(settings)
    assert report["ready"] is True


@pytest.mark.asyncio
async def test_live_true_does_not_crash_with_bad_config():
    """live=True with unreachable services must not raise — errors are recorded in probe."""
    settings = Settings(
        mysql_dsn="mysql+asyncmy://root:pass@127.0.0.1:1/test",
        redis_url="redis://127.0.0.1:1/0",
        lease_base_url="http://127.0.0.1:1",
        vector_uri="http://127.0.0.1:1",
    )
    report = await build_readiness_report(settings, live=True)
    assert isinstance(report["ready"], bool)
    # Each required check should have a probe key indicating failure
    for check in report["checks"]:
        if check["required"]:
            assert "probe" in check
            assert check["probe"].startswith("error:")


@pytest.mark.asyncio
async def test_live_false_no_probe_key():
    """When live=False, checks should NOT have a 'probe' key."""
    settings = Settings(
        mysql_dsn="mysql+asyncmy://root:pass@localhost:3306/test",
        redis_url="redis://localhost:6379/0",
        lease_base_url="http://localhost:8081",
        vector_uri="http://localhost:19530",
    )
    report = await build_readiness_report(settings, live=False)
    for check in report["checks"]:
        assert "probe" not in check
