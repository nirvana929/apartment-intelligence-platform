"""Integration test: live MySQL trace and audit repository verification.

Skipped unless APTGUIDE3_MYSQL_DSN is set to a non-default value.
Tests that trace events and audit events are written to MySQL correctly.
"""
from __future__ import annotations

import os
import uuid

import pytest

_mysql_dsn = os.environ.get("APTGUIDE3_MYSQL_DSN", "")
_has_mysql = bool(_mysql_dsn)

pytestmark = pytest.mark.skipif(
    not _has_mysql,
    reason="APTGUIDE3_MYSQL_DSN not set; skipping trace/audit integration tests",
)


@pytest.fixture()
def sessionmaker():
    """Create an async sessionmaker from the configured DSN."""
    from aptguide3.database.database import build_sessionmaker

    return build_sessionmaker(_mysql_dsn)


@pytest.fixture()
def unique_ids() -> dict[str, str]:
    """Return a dict of unique IDs for a single test run."""
    return {
        "session_id": uuid.uuid4().hex,
        "user_id": f"user_{uuid.uuid4().hex[:8]}",
        "request_id": uuid.uuid4().hex,
        "trace_id": uuid.uuid4().hex,
    }


async def _upsert_session_safe(session_repo, session_id: str, user_id: str) -> None:
    """Upsert a session, swallowing duplicate-key errors from prior test runs."""
    try:
        await session_repo.upsert_session(session_id, user_id, {"_test": True})
    except Exception:
        pass


@pytest.mark.asyncio
async def test_trace_event_written_to_mysql(sessionmaker, unique_ids):
    """A trace event is persisted to aptguide3_trace_events via MySqlTraceRepository."""
    from sqlalchemy import text

    from aptguide3.persistence.mysql_repos import (
        MySqlSessionRepository,
        MySqlTraceRepository,
    )

    # Create parent session for FK constraints
    session_repo = MySqlSessionRepository(sessionmaker)
    sid = unique_ids["session_id"]
    uid = unique_ids["user_id"]
    await _upsert_session_safe(session_repo, sid, uid)

    trace_repo = MySqlTraceRepository(sessionmaker)
    trace_id = unique_ids["trace_id"]

    await trace_repo.append_trace_event(
        trace_id=trace_id,
        request_id=unique_ids["request_id"],
        session_id=sid,
        event_name="integration_trace_test",
        payload={"source": "test_trace_audit_live"},
    )

    # Verify the row exists
    async with sessionmaker() as sess:
        result = await sess.execute(
            text("SELECT event_name, payload FROM aptguide3_trace_events WHERE trace_id = :tid"),
            {"tid": trace_id},
        )
        row = result.fetchone()
        assert row is not None, "Trace event row should exist"
        assert row[0] == "integration_trace_test"

    # Cleanup
    async with sessionmaker() as sess:
        await sess.execute(
            text("DELETE FROM aptguide3_trace_events WHERE trace_id = :tid"),
            {"tid": trace_id},
        )
        await sess.execute(
            text("DELETE FROM aptguide3_sessions WHERE session_id = :sid"),
            {"sid": sid},
        )
        await sess.commit()


@pytest.mark.asyncio
async def test_audit_event_written_to_mysql(sessionmaker, unique_ids):
    """An audit event is persisted to aptguide3_audit_log via MySqlAuditRepository."""
    from sqlalchemy import text

    from aptguide3.persistence.mysql_repos import (
        MySqlAuditRepository,
        MySqlSessionRepository,
    )

    # Create parent session for FK constraints
    session_repo = MySqlSessionRepository(sessionmaker)
    sid = unique_ids["session_id"]
    uid = unique_ids["user_id"]
    await _upsert_session_safe(session_repo, sid, uid)

    audit_repo = MySqlAuditRepository(sessionmaker)

    await audit_repo.append_audit_event(
        user_id=uid,
        session_id=sid,
        event_type="integration_audit_test",
        payload={"source": "test_trace_audit_live"},
    )

    # Verify the row exists
    async with sessionmaker() as sess:
        result = await sess.execute(
            text(
                "SELECT event_type, payload FROM aptguide3_audit_log "
                "WHERE session_id = :sid AND event_type = :et"
            ),
            {"sid": sid, "et": "integration_audit_test"},
        )
        row = result.fetchone()
        assert row is not None, "Audit event row should exist"
        assert row[0] == "integration_audit_test"

    # Cleanup
    async with sessionmaker() as sess:
        await sess.execute(
            text(
                "DELETE FROM aptguide3_audit_log "
                "WHERE session_id = :sid AND event_type = :et"
            ),
            {"sid": sid, "et": "integration_audit_test"},
        )
        await sess.execute(
            text("DELETE FROM aptguide3_sessions WHERE session_id = :sid"),
            {"sid": sid},
        )
        await sess.commit()
