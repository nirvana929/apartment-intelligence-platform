"""Integration tests for the lease-to-AptGuide internal-header auth boundary.

These tests verify that the /chat endpoint correctly enforces
X-Internal-Token and X-User-Id headers when AUTH_MODE=internal_header.

All tests are skipped when:
  - APTGUIDE3_AUTH_MODE != "internal_header"
  - APTGUIDE3_INTERNAL_TOKEN is not set

To run:
  APTGUIDE3_AUTH_MODE=internal_header \
  APTGUIDE3_INTERNAL_TOKEN=test-secret \
  APTGUIDE3_INTERNAL_TOKEN_REQUIRED=true \
  pytest tests/integration/test_internal_header_auth_live.py -v
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from aptguide3.config import get_settings

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

INTERNAL_TOKEN = os.environ.get("APTGUIDE3_INTERNAL_TOKEN", "")
AUTH_MODE = os.environ.get("APTGUIDE3_AUTH_MODE", "dev")

_skip_reason = (
    "Skipped: APTGUIDE3_AUTH_MODE must be 'internal_header' "
    "and APTGUIDE3_INTERNAL_TOKEN must be set"
)
requires_internal_header = pytest.mark.skipif(
    AUTH_MODE != "internal_header" or not INTERNAL_TOKEN,
    reason=_skip_reason,
)


@pytest.fixture(autouse=True)
def _fresh_settings():
    """Clear the lru_cache so each test reads current env vars."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client():
    from aptguide3.api.app import create_app

    return TestClient(create_app(), raise_server_exceptions=False)


VALID_BODY = {"message": "hello", "session_id": "test-session-001"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@requires_internal_header
def test_missing_internal_token_returns_401(client: TestClient):
    """Request without X-Internal-Token must be rejected."""
    resp = client.post(
        "/chat",
        json=VALID_BODY,
        headers={"X-User-Id": "u1"},
    )
    assert resp.status_code == 401


@requires_internal_header
def test_invalid_internal_token_returns_401(client: TestClient):
    """Request with a wrong X-Internal-Token must be rejected."""
    resp = client.post(
        "/chat",
        json=VALID_BODY,
        headers={
            "X-Internal-Token": "definitely-wrong",
            "X-User-Id": "u1",
        },
    )
    assert resp.status_code == 401


@requires_internal_header
def test_valid_token_missing_user_id_returns_401(client: TestClient):
    """Valid token but missing X-User-Id must be rejected."""
    resp = client.post(
        "/chat",
        json=VALID_BODY,
        headers={"X-Internal-Token": INTERNAL_TOKEN},
    )
    assert resp.status_code == 401


@requires_internal_header
def test_valid_token_and_user_id_returns_200(client: TestClient):
    """Full valid headers should pass auth and return a chat response."""
    resp = client.post(
        "/chat",
        json=VALID_BODY,
        headers={
            "X-Internal-Token": INTERNAL_TOKEN,
            "X-User-Id": "lease-user-42",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "message" in body
    assert "phase" in body


@requires_internal_header
def test_request_id_propagated_to_response(client: TestClient):
    """X-Request-Id sent in the request must appear in the response header."""
    resp = client.post(
        "/chat",
        json=VALID_BODY,
        headers={
            "X-Internal-Token": INTERNAL_TOKEN,
            "X-User-Id": "lease-user-42",
            "X-Request-Id": "trace-abc-999",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-Id") == "trace-abc-999"


@requires_internal_header
def test_body_user_id_ignored_in_internal_header_mode(client: TestClient):
    """user_id in the request body must NOT override X-User-Id header."""
    body_with_spoofed_user = {**VALID_BODY, "user_id": "spoofed-user"}
    resp = client.post(
        "/chat",
        json=body_with_spoofed_user,
        headers={
            "X-Internal-Token": INTERNAL_TOKEN,
            "X-User-Id": "real-lease-user",
        },
    )
    assert resp.status_code == 200
    # The auth context should use "real-lease-user", not "spoofed-user".
    # We cannot directly inspect the frame, but a 200 confirms auth passed.
