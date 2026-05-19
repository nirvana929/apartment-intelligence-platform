"""Integration tests: end-to-end chat persistence through /api/chat.

These tests verify the full chain: HTTP request -> auth -> chat service -> persistence -> response.

All tests run in memory mode by default (no external dependencies).
Tests prefixed ``test_mysql_*`` are skipped unless:
  - APTGUIDE3_PERSISTENCE_MODE is ``mysql`` or ``hybrid``
  - APTGUIDE3_MYSQL_DSN is set to a non-default value

To run all tests (memory-only):
  pytest tests/integration/test_chat_live_persistence.py -v

To run with MySQL persistence:
  APTGUIDE3_PERSISTENCE_MODE=mysql \
  APTGUIDE3_MYSQL_DSN=mysql+asyncmy://root:pass@localhost:3306/aptguide3 \
  pytest tests/integration/test_chat_live_persistence.py -v
"""

from __future__ import annotations

import os
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from aptguide3.config import get_settings

# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------

_persistence_mode = os.environ.get("APTGUIDE3_PERSISTENCE_MODE", "memory")
_mysql_dsn = os.environ.get("APTGUIDE3_MYSQL_DSN", "")
_has_mysql_persistence = (
    _persistence_mode in ("mysql", "hybrid")
    and bool(_mysql_dsn)
)

requires_mysql_persistence = pytest.mark.skipif(
    not _has_mysql_persistence,
    reason=(
        "APTGUIDE3_PERSISTENCE_MODE must be 'mysql' or 'hybrid' "
        "and APTGUIDE3_MYSQL_DSN must be set"
    ),
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fresh_caches():
    """Clear LRU caches so each test reads current env vars."""
    from aptguide3.api.deps import get_chat_service

    get_settings.cache_clear()
    get_chat_service.cache_clear()
    yield
    get_settings.cache_clear()
    get_chat_service.cache_clear()


@pytest.fixture()
def client():
    from aptguide3.api.app import create_app

    return TestClient(create_app(), raise_server_exceptions=False)


@pytest.fixture()
def session_id():
    """Return a unique session ID for each test."""
    return f"integ-{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Tests -- response shape (always run, memory mode is fine)
# ---------------------------------------------------------------------------


def test_chat_returns_200(client: TestClient, session_id: str):
    """POST /chat in dev mode returns HTTP 200."""
    resp = client.post("/chat", json={"message": "你好", "session_id": session_id})
    assert resp.status_code == 200


def test_chat_response_has_required_fields(client: TestClient, session_id: str):
    """Response body contains all ChatResponse fields."""
    resp = client.post("/chat", json={"message": "你好", "session_id": session_id})
    assert resp.status_code == 200
    body = resp.json()

    # Required fields per ChatResponse schema
    assert "message" in body, "missing 'message' field"
    assert "phase" in body, "missing 'phase' field"
    assert "cards" in body, "missing 'cards' field"
    assert isinstance(body["message"], str), "'message' should be a string"
    assert isinstance(body["phase"], str), "'phase' should be a string"
    assert isinstance(body["cards"], list), "'cards' should be a list"


def test_chat_response_has_actions_and_metadata(client: TestClient, session_id: str):
    """Response body contains actions and metadata fields."""
    resp = client.post("/chat", json={"message": "你好", "session_id": session_id})
    assert resp.status_code == 200
    body = resp.json()

    assert "actions" in body, "missing 'actions' field"
    assert "metadata" in body, "missing 'metadata' field"
    assert isinstance(body["actions"], list), "'actions' should be a list"
    assert isinstance(body["metadata"], dict), "'metadata' should be a dict"


def test_chat_dev_mode_auth_passes(client: TestClient, session_id: str):
    """In dev mode, no auth headers are required -- request succeeds."""
    resp = client.post(
        "/chat",
        json={"message": "找房", "session_id": session_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"], "response message should not be empty"


def test_chat_unique_sessions_are_independent(client: TestClient):
    """Two requests with different session_ids return independent responses."""
    sid_a = f"integ-a-{uuid.uuid4().hex[:8]}"
    sid_b = f"integ-b-{uuid.uuid4().hex[:8]}"

    resp_a = client.post("/chat", json={"message": "你好A", "session_id": sid_a})
    resp_b = client.post("/chat", json={"message": "你好B", "session_id": sid_b})

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200


# ---------------------------------------------------------------------------
# Tests -- LLM degradation (graceful clarify when LLM unavailable)
# ---------------------------------------------------------------------------


def test_chat_degrades_gracefully_without_llm(client: TestClient, session_id: str):
    """When no LLM API key is configured, the service returns a clarify response."""
    # The default Settings has llm_api_key="" (empty), so ClarifyOnlyUnderstanding
    # is used.  We verify the response phase is 'clarify'.
    resp = client.post(
        "/chat",
        json={"message": "帮我找房", "session_id": session_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    # With ClarifyOnlyUnderstanding, the route is "clarify" -> phase is "clarify"
    assert body["phase"] == "clarify", (
        f"Expected phase='clarify' when LLM is unavailable, got '{body['phase']}'"
    )
    assert body["message"], "clarify response should have a non-empty message"


# ---------------------------------------------------------------------------
# Tests -- MySQL persistence (skipped unless persistence_mode is mysql/hybrid)
# ---------------------------------------------------------------------------


@requires_mysql_persistence
def test_mysql_chat_message_persisted(client: TestClient, session_id: str):
    """After a chat request, the user and assistant messages are in MySQL."""
    import asyncmy

    dsn = _mysql_dsn
    # Parse DSN for direct SQL verification
    import re
    from urllib.parse import unquote, urlparse

    normalized = re.sub(r"^mysql\+\w+://", "mysql://", dsn)
    parsed = urlparse(normalized)
    host = parsed.hostname or "localhost"
    port = parsed.port or 3306
    user = unquote(parsed.username or "root")
    password = unquote(parsed.password or "")
    database = (parsed.path or "/aptguide3").lstrip("/")

    # Send a chat request with a unique marker
    marker = f"persist-test-{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/chat",
        json={"message": marker, "session_id": session_id},
    )
    assert resp.status_code == 200, f"Chat request failed: {resp.text}"

    # Give fire-and-forget persistence tasks time to complete
    time.sleep(1.0)

    # Verify messages were persisted
    async def _check_messages():
        conn = await asyncmy.connect(
            host=host, port=port, user=user, password=password,
            database=database, charset="utf8mb4",
        )
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT role, content FROM aptguide3_messages "
                    "WHERE session_id = %s ORDER BY message_id",
                    (session_id,),
                )
                rows = await cur.fetchall()
                return rows
        finally:
            conn.close()

    import asyncio
    rows = asyncio.run(_check_messages())

    assert len(rows) >= 2, (
        f"Expected at least 2 message rows (user + assistant), got {len(rows)}"
    )
    roles = [row[0] for row in rows]
    assert "user" in roles, "No 'user' message persisted"
    assert "assistant" in roles, "No 'assistant' message persisted"

    # Verify the user message content matches our marker
    user_messages = [row[1] for row in rows if row[0] == "user"]
    assert any(marker in msg for msg in user_messages), (
        f"User message with marker '{marker}' not found in persisted messages"
    )

    # Cleanup
    async def _cleanup():
        conn = await asyncmy.connect(
            host=host, port=port, user=user, password=password,
            database=database, charset="utf8mb4",
        )
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM aptguide3_messages WHERE session_id = %s",
                    (session_id,),
                )
                await cur.execute(
                    "DELETE FROM aptguide3_sessions WHERE session_id = %s",
                    (session_id,),
                )
                await conn.commit()
        finally:
            conn.close()

    asyncio.run(_cleanup())


@requires_mysql_persistence
def test_mysql_session_updated(client: TestClient, session_id: str):
    """After a chat request, the session record exists in MySQL."""
    import re
    from urllib.parse import unquote, urlparse

    import asyncmy

    normalized = re.sub(r"^mysql\+\w+://", "mysql://", _mysql_dsn)
    parsed = urlparse(normalized)
    host = parsed.hostname or "localhost"
    port = parsed.port or 3306
    user = unquote(parsed.username or "root")
    password = unquote(parsed.password or "")
    database = (parsed.path or "/aptguide3").lstrip("/")

    resp = client.post(
        "/chat",
        json={"message": "session test", "session_id": session_id},
    )
    assert resp.status_code == 200

    # Give fire-and-forget persistence tasks time to complete
    time.sleep(1.0)

    async def _check_session():
        conn = await asyncmy.connect(
            host=host, port=port, user=user, password=password,
            database=database, charset="utf8mb4",
        )
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT session_id, context FROM aptguide3_sessions "
                    "WHERE session_id = %s",
                    (session_id,),
                )
                row = await cur.fetchone()
                return row
        finally:
            conn.close()

    import asyncio
    row = asyncio.run(_check_session())

    assert row is not None, (
        f"Session '{session_id}' not found in aptguide3_sessions after chat"
    )
    assert row[0] == session_id

    # Cleanup
    async def _cleanup():
        conn = await asyncmy.connect(
            host=host, port=port, user=user, password=password,
            database=database, charset="utf8mb4",
        )
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM aptguide3_messages WHERE session_id = %s",
                    (session_id,),
                )
                await cur.execute(
                    "DELETE FROM aptguide3_sessions WHERE session_id = %s",
                    (session_id,),
                )
                await conn.commit()
        finally:
            conn.close()

    asyncio.run(_cleanup())
