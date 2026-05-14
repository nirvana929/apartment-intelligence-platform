from __future__ import annotations

import json
from typing import Any


class RedisStateStore:
    def __init__(
        self,
        redis_client: Any,
        prefix: str,
        session_ttl_seconds: int,
        pending_ttl_seconds: int,
    ) -> None:
        self.redis = redis_client
        self.prefix = prefix.rstrip(":")
        self.session_ttl_seconds = session_ttl_seconds
        self.pending_ttl_seconds = pending_ttl_seconds

    def session_key(self, session_id: str) -> str:
        return f"{self.prefix}:session:{session_id}"

    def pending_key(self, confirmation_id: str) -> str:
        return f"{self.prefix}:pending:{confirmation_id}"

    async def save_session(self, session_id: str, payload: dict[str, Any]) -> None:
        await self.redis.set(
            self.session_key(session_id),
            json.dumps(payload, ensure_ascii=False),
            ex=self.session_ttl_seconds,
        )

    async def load_session(self, session_id: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self.session_key(session_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    async def save_pending_action(self, confirmation_id: str, payload: dict[str, Any]) -> None:
        await self.redis.set(
            self.pending_key(confirmation_id),
            json.dumps(payload, ensure_ascii=False),
            ex=self.pending_ttl_seconds,
        )

    async def load_pending_action(self, confirmation_id: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self.pending_key(confirmation_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    async def delete_pending_action(self, confirmation_id: str) -> None:
        await self.redis.delete(self.pending_key(confirmation_id))
