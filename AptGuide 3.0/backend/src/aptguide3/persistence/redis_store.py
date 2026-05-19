from __future__ import annotations

import json
from typing import Any


class RedisStateStore:
    def __init__(self, redis, *, prefix: str, session_ttl_seconds: int, pending_ttl_seconds: int) -> None:
        self.redis = redis
        self.prefix = prefix
        self.session_ttl_seconds = session_ttl_seconds
        self.pending_ttl_seconds = pending_ttl_seconds

    def _key(self, namespace: str, key: str) -> str:
        return f"{self.prefix}:{namespace}:{key}"

    async def save_session(self, session_id: str, data: dict[str, Any]) -> None:
        await self.redis.set(
            self._key("session", session_id),
            json.dumps(data, ensure_ascii=False),
            ex=self.session_ttl_seconds,
        )

    async def load_session(self, session_id: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self._key("session", session_id))
        if raw is None:
            return None
        return json.loads(raw)

    async def delete_session(self, session_id: str) -> None:
        await self.redis.delete(self._key("session", session_id))

    async def save_pending_action(self, pending_action_id: str, data: dict[str, Any]) -> None:
        await self.redis.set(
            self._key("pending", pending_action_id),
            json.dumps(data, ensure_ascii=False),
            ex=self.pending_ttl_seconds,
        )

    async def load_pending_action(self, pending_action_id: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self._key("pending", pending_action_id))
        if raw is None:
            return None
        return json.loads(raw)

    async def delete_pending_action(self, pending_action_id: str) -> None:
        await self.redis.delete(self._key("pending", pending_action_id))
