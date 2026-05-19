"""Integration test: live Redis state-store verification.

Skipped unless APTGUIDE3_REDIS_URL is set.
Tests session and pending-action CRUD against a real Redis instance.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest

_HAS_REDIS = bool(os.environ.get("APTGUIDE3_REDIS_URL"))

pytestmark = pytest.mark.skipif(
    not _HAS_REDIS,
    reason="APTGUIDE3_REDIS_URL not set; skipping Redis integration tests",
)


def _unique_prefix() -> str:
    """Return a unique key prefix to avoid cross-test collisions."""
    return f"test_redis_{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def redis_url() -> str:
    return os.environ["APTGUIDE3_REDIS_URL"]


@pytest.mark.asyncio
async def test_session_write_read(redis_url: str):
    """save_session then load_session returns matching data."""
    import redis.asyncio as aioredis

    from aptguide3.persistence.redis_store import RedisStateStore

    client = aioredis.from_url(redis_url, decode_responses=True)
    store = RedisStateStore(
        client,
        prefix=_unique_prefix(),
        session_ttl_seconds=300,
        pending_ttl_seconds=300,
    )
    session_id = uuid.uuid4().hex
    data = {"user_id": "u1", "context": {"apartment": "A-101"}}

    try:
        await store.save_session(session_id, data)
        loaded = await store.load_session(session_id)
        assert loaded == data, f"Expected {data}, got {loaded}"
    finally:
        await client.delete(store._key("session", session_id))
        await client.aclose()


@pytest.mark.asyncio
async def test_session_delete(redis_url: str):
    """After delete_session, load_session returns None."""
    import redis.asyncio as aioredis

    from aptguide3.persistence.redis_store import RedisStateStore

    client = aioredis.from_url(redis_url, decode_responses=True)
    store = RedisStateStore(
        client,
        prefix=_unique_prefix(),
        session_ttl_seconds=300,
        pending_ttl_seconds=300,
    )
    session_id = uuid.uuid4().hex
    data = {"user_id": "u2"}

    try:
        await store.save_session(session_id, data)
        await store.delete_session(session_id)
        loaded = await store.load_session(session_id)
        assert loaded is None, "load_session should return None after delete"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_pending_action_write_read(redis_url: str):
    """save_pending_action then load_pending_action returns matching data."""
    import redis.asyncio as aioredis

    from aptguide3.persistence.redis_store import RedisStateStore

    client = aioredis.from_url(redis_url, decode_responses=True)
    store = RedisStateStore(
        client,
        prefix=_unique_prefix(),
        session_ttl_seconds=300,
        pending_ttl_seconds=300,
    )
    action_id = uuid.uuid4().hex
    data = {"action_type": "confirm_viewing", "payload": {"slot": "2026-05-20"}}

    try:
        await store.save_pending_action(action_id, data)
        loaded = await store.load_pending_action(action_id)
        assert loaded == data, f"Expected {data}, got {loaded}"
    finally:
        await client.delete(store._key("pending", action_id))
        await client.aclose()


@pytest.mark.asyncio
async def test_pending_action_ttl(redis_url: str):
    """Pending action saved with 1s TTL expires after 2s."""
    import redis.asyncio as aioredis

    from aptguide3.persistence.redis_store import RedisStateStore

    client = aioredis.from_url(redis_url, decode_responses=True)
    # Use a dedicated store with 1-second pending TTL for this test
    store = RedisStateStore(
        client,
        prefix=_unique_prefix(),
        session_ttl_seconds=300,
        pending_ttl_seconds=1,
    )
    action_id = uuid.uuid4().hex
    data = {"action_type": "ephemeral"}

    try:
        await store.save_pending_action(action_id, data)
        # Confirm it exists immediately
        immediate = await store.load_pending_action(action_id)
        assert immediate is not None, "Pending action should exist immediately after save"

        await asyncio.sleep(2)

        expired = await store.load_pending_action(action_id)
        assert expired is None, "Pending action should be None after TTL expires"
    finally:
        await client.aclose()
