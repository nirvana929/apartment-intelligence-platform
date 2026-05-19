"""Skip-safe smoke test for the lease-to-AptGuide gateway chain.

Verifies that AptGuide 3.0 /api/chat accepts requests with internal-header
auth when running as a live service on port 8100.

All tests are skipped unless APTGUIDE3_GATEWAY_TEST=1 is set.

To run:
  APTGUIDE3_GATEWAY_TEST=1 \
  APTGUIDE3_INTERNAL_TOKEN=<shared-token> \
  uv run pytest tests/integration/test_lease_gateway_chain.py -v
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("APTGUIDE3_GATEWAY_TEST"),
    reason="gateway chain test requires APTGUIDE3_GATEWAY_TEST=1",
)


def test_gateway_chat_endpoint():
    """POST /api/chat with internal headers returns 200 and expected fields."""
    import httpx

    resp = httpx.post(
        "http://127.0.0.1:8100/api/chat",
        json={"message": "你好", "session_id": "chain-test-001"},
        headers={
            "X-Internal-Token": os.environ.get("APTGUIDE3_INTERNAL_TOKEN", ""),
            "X-User-Id": "1",
            "X-Request-Id": "chain-test-req-001",
        },
        timeout=15.0,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
