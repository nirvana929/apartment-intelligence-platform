import pytest

from aptguide3.persistence.redis_store import RedisStateStore


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.ttls = {}

    async def set(self, key, value, ex=None):
        self.values[key] = value
        self.ttls[key] = ex

    async def get(self, key):
        return self.values.get(key)

    async def delete(self, key):
        self.values.pop(key, None)


@pytest.mark.asyncio
async def test_session_state_uses_prefix_and_ttl():
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="aptguide3", session_ttl_seconds=10, pending_ttl_seconds=3)
    await store.save_session("s1", {"hello": "world"})
    assert await store.load_session("s1") == {"hello": "world"}
    assert redis.ttls["aptguide3:session:s1"] == 10


@pytest.mark.asyncio
async def test_pending_action_uses_pending_ttl():
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="aptguide3", session_ttl_seconds=10, pending_ttl_seconds=3)
    await store.save_pending_action("p1", {"type": "confirm"})
    assert await store.load_pending_action("p1") == {"type": "confirm"}
    assert redis.ttls["aptguide3:pending:p1"] == 3


@pytest.mark.asyncio
async def test_load_returns_none_for_missing():
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="aptguide3", session_ttl_seconds=10, pending_ttl_seconds=3)
    assert await store.load_session("missing") is None
    assert await store.load_pending_action("missing") is None


@pytest.mark.asyncio
async def test_delete_removes_key():
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="aptguide3", session_ttl_seconds=10, pending_ttl_seconds=3)
    await store.save_session("s1", {"data": 1})
    await store.delete_session("s1")
    assert await store.load_session("s1") is None
