import json
from typing import Any


class SessionMemory:
    """会话状态管理（Redis）"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 小时过期

    async def store(self, session_id: str, data: dict[str, Any]) -> None:
        """存储会话状态"""
        key = f"session:{session_id}"
        value = json.dumps(data, ensure_ascii=False)
        await self.redis.set(key, value, ex=self.ttl)

    async def get(self, session_id: str) -> dict[str, Any] | None:
        """获取会话状态"""
        key = f"session:{session_id}"
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def update(self, session_id: str, updates: dict[str, Any]) -> None:
        """更新会话状态"""
        data = await self.get(session_id) or {}
        data.update(updates)
        await self.store(session_id, data)

    async def store_pending_confirmation(
        self,
        session_id: str,
        confirmation: dict[str, Any],
    ) -> None:
        """存储待确认操作"""
        await self.update(session_id, {"pending_confirmation": confirmation})

    async def get_pending_confirmation(self, session_id: str) -> dict[str, Any] | None:
        """获取待确认操作"""
        data = await self.get(session_id)
        if data:
            return data.get("pending_confirmation")
        return None

    async def clear_pending_confirmation(self, session_id: str) -> None:
        """清除待确认操作"""
        data = await self.get(session_id) or {}
        data.pop("pending_confirmation", None)
        await self.store(session_id, data)

    async def store_last_recommendations(
        self,
        session_id: str,
        recommendations: list[dict],
    ) -> None:
        """存储最近推荐"""
        await self.update(session_id, {"last_recommendations": recommendations})

    async def get_last_recommendations(self, session_id: str) -> list[dict]:
        """获取最近推荐"""
        data = await self.get(session_id)
        if data:
            return data.get("last_recommendations", [])
        return []
