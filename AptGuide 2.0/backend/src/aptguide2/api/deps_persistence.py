from __future__ import annotations

from functools import lru_cache

import redis.asyncio as redis

from aptguide2.api.deps import get_settings
from aptguide2.persistence.redis_store import RedisStateStore


@lru_cache
def get_redis_client():
    return redis.from_url(get_settings().redis_url, decode_responses=True)


@lru_cache
def get_redis_state_store() -> RedisStateStore:
    s = get_settings()
    return RedisStateStore(
        redis_client=get_redis_client(),
        prefix=s.redis_key_prefix,
        session_ttl_seconds=s.session_ttl_seconds,
        pending_ttl_seconds=s.pending_action_ttl_seconds,
    )
