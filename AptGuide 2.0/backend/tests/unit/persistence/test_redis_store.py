import json

from aptguide2.persistence.redis_store import RedisStateStore


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}
        self.ttls = {}

    async def set(self, key, value, ex=None):
        self.values[key] = value
        self.ttls[key] = ex

    async def get(self, key):
        return self.values.get(key)

    async def delete(self, key):
        self.values.pop(key, None)


async def test_session_round_trip() -> None:
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="test", session_ttl_seconds=60, pending_ttl_seconds=30)

    await store.save_session("s1", {"user_id": "u1", "phase": "idle"})
    loaded = await store.load_session("s1")

    assert loaded == {"user_id": "u1", "phase": "idle"}
    assert redis.ttls["test:session:s1"] == 60


async def test_pending_action_round_trip() -> None:
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="test", session_ttl_seconds=60, pending_ttl_seconds=30)

    await store.save_pending_action("c1", {"type": "appointment.create"})
    loaded = await store.load_pending_action("c1")

    assert loaded == {"type": "appointment.create"}
    assert json.loads(redis.values["test:pending:c1"])["type"] == "appointment.create"


async def test_delete_pending_action() -> None:
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="test", session_ttl_seconds=60, pending_ttl_seconds=30)

    await store.save_pending_action("c1", {"type": "appointment.create"})
    await store.delete_pending_action("c1")

    assert await store.load_pending_action("c1") is None


async def test_load_nonexistent_returns_none() -> None:
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="test", session_ttl_seconds=60, pending_ttl_seconds=30)

    assert await store.load_session("nonexistent") is None
    assert await store.load_pending_action("nonexistent") is None
