"""Integration test: live MySQL repository verification.

Skipped unless APTGUIDE3_MYSQL_DSN is set to a non-default value.
Tests CRUD operations against a real MySQL instance via SQLAlchemy async.
"""
from __future__ import annotations

import os
import uuid

import pytest

_mysql_dsn = os.environ.get("APTGUIDE3_MYSQL_DSN", "")
_has_mysql = bool(_mysql_dsn)

pytestmark = pytest.mark.skipif(
    not _has_mysql,
    reason="APTGUIDE3_MYSQL_DSN not set; skipping MySQL repository integration tests",
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
        "run_id": uuid.uuid4().hex,
        "trace_id": uuid.uuid4().hex,
    }


@pytest.mark.asyncio
async def test_session_upsert_and_load(sessionmaker, unique_ids):
    """upsert_session then load_session returns matching data."""
    from aptguide3.persistence.mysql_repos import MySqlSessionRepository

    repo = MySqlSessionRepository(sessionmaker)
    sid = unique_ids["session_id"]
    uid = unique_ids["user_id"]
    context = {"apartment": "B-202", "source": "test"}

    await repo.upsert_session(sid, uid, context)
    loaded = await repo.load_session(sid)

    assert loaded is not None, "load_session should return a dict after upsert"
    assert loaded["session_id"] == sid
    assert loaded["user_id"] == uid
    assert loaded["context"] == context

    # Cleanup
    from sqlalchemy import text

    async with sessionmaker() as sess:
        await sess.execute(
            text("DELETE FROM aptguide3_sessions WHERE session_id = :sid"),
            {"sid": sid},
        )
        await sess.commit()


@pytest.mark.asyncio
async def test_message_append(sessionmaker, unique_ids):
    """append_message does not raise and the row is persisted."""
    from sqlalchemy import text

    from aptguide3.persistence.mysql_repos import (
        MySqlMessageRepository,
        MySqlSessionRepository,
    )

    # First create the parent session so FK constraints are satisfied
    session_repo = MySqlSessionRepository(sessionmaker)
    sid = unique_ids["session_id"]
    uid = unique_ids["user_id"]
    await repo_upsert_safe(session_repo, sid, uid)

    msg_repo = MySqlMessageRepository(sessionmaker)
    rid = unique_ids["request_id"]

    await msg_repo.append_message(
        session_id=sid,
        user_id=uid,
        request_id=rid,
        role="user",
        content="Hello from integration test",
        metadata={"test": True},
    )

    # Verify the row exists
    async with sessionmaker() as sess:
        result = await sess.execute(
            text("SELECT COUNT(*) FROM aptguide3_messages WHERE request_id = :rid"),
            {"rid": rid},
        )
        count = result.scalar()
        assert count == 1, f"Expected 1 message row, got {count}"

    # Cleanup
    async with sessionmaker() as sess:
        await sess.execute(
            text("DELETE FROM aptguide3_messages WHERE request_id = :rid"),
            {"rid": rid},
        )
        await sess.execute(
            text("DELETE FROM aptguide3_sessions WHERE session_id = :sid"),
            {"sid": sid},
        )
        await sess.commit()


@pytest.mark.asyncio
async def test_procedure_run_start_and_complete(sessionmaker, unique_ids):
    """start_run then complete_run updates the status."""
    from sqlalchemy import text

    from aptguide3.persistence.mysql_repos import (
        MySqlProcedureRunRepository,
        MySqlSessionRepository,
    )

    # Create parent session
    session_repo = MySqlSessionRepository(sessionmaker)
    sid = unique_ids["session_id"]
    uid = unique_ids["user_id"]
    await repo_upsert_safe(session_repo, sid, uid)

    run_repo = MySqlProcedureRunRepository(sessionmaker)
    run_id = unique_ids["run_id"]
    rid = unique_ids["request_id"]

    await run_repo.start_run(
        run_id=run_id,
        request_id=rid,
        session_id=sid,
        user_id=uid,
        procedure_name="test_procedure",
        route="/test",
        task="integration test task",
        metadata={"step": 1},
    )

    # Verify running status
    async with sessionmaker() as sess:
        result = await sess.execute(
            text("SELECT status FROM aptguide3_procedure_runs WHERE run_id = :rid"),
            {"rid": run_id},
        )
        row = result.fetchone()
        assert row is not None, "Procedure run row should exist"
        assert row[0] == "running", f"Expected 'running', got '{row[0]}'"

    await run_repo.complete_run(run_id=run_id, status="completed", metadata={"step": 2, "result": "ok"})

    # Verify completed status
    async with sessionmaker() as sess:
        result = await sess.execute(
            text("SELECT status FROM aptguide3_procedure_runs WHERE run_id = :rid"),
            {"rid": run_id},
        )
        row = result.fetchone()
        assert row[0] == "completed", f"Expected 'completed', got '{row[0]}'"

    # Cleanup
    async with sessionmaker() as sess:
        await sess.execute(
            text("DELETE FROM aptguide3_procedure_runs WHERE run_id = :rid"),
            {"rid": run_id},
        )
        await sess.execute(
            text("DELETE FROM aptguide3_sessions WHERE session_id = :sid"),
            {"sid": sid},
        )
        await sess.commit()


@pytest.mark.asyncio
async def test_trace_event_append(sessionmaker, unique_ids):
    """append_trace_event does not raise and the row is persisted."""
    from sqlalchemy import text

    from aptguide3.persistence.mysql_repos import (
        MySqlSessionRepository,
        MySqlTraceRepository,
    )

    # Create parent session
    session_repo = MySqlSessionRepository(sessionmaker)
    sid = unique_ids["session_id"]
    uid = unique_ids["user_id"]
    await repo_upsert_safe(session_repo, sid, uid)

    trace_repo = MySqlTraceRepository(sessionmaker)
    trace_id = unique_ids["trace_id"]
    rid = unique_ids["request_id"]

    await trace_repo.append_trace_event(
        trace_id=trace_id,
        request_id=rid,
        session_id=sid,
        event_name="test_event",
        payload={"detail": "integration test trace"},
    )

    # Verify the row exists
    async with sessionmaker() as sess:
        result = await sess.execute(
            text("SELECT COUNT(*) FROM aptguide3_trace_events WHERE trace_id = :tid"),
            {"tid": trace_id},
        )
        count = result.scalar()
        assert count == 1, f"Expected 1 trace event row, got {count}"

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def repo_upsert_safe(session_repo, session_id: str, user_id: str) -> None:
    """Upsert a session, swallowing duplicate-key errors from prior test runs."""
    try:
        await session_repo.upsert_session(session_id, user_id, {"_test": True})
    except Exception:
        pass  # session may already exist from a previous failed cleanup
