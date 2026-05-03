"""
会话记忆管理 —— 存储跨轮次的会话状态。

【学习要点】
1. 降级模式（Fallback）：
   - 优先用 Redis（生产环境，持久化、支持多实例共享）
   - Redis 不可用时降级到内存（开发环境，进程重启数据丢失）
2. TTL（Time-To-Live）：数据过期时间，1 小时后自动清除
3. 为什么要存会话状态？
   - 用户说"确认"时，系统需要知道"确认什么"（待确认的预约操作）
   - 用户说"刚才推荐的第一个"时，系统需要知道"推荐了哪些"
4. await 关键字：所有方法都是 async 的，因为 Redis 操作是异步的
"""

import json
from typing import Any


class SessionMemory:
    """
    会话状态管理（Redis / 内存降级）。

    设计思路：
    - store/get/update 是通用的会话读写接口
    - store_pending_confirmation 等是业务特定的便捷方法
    - 底层存储透明切换（Redis 或内存）
    """

    def __init__(self, redis_client):
        self.redis = redis_client       # Redis 客户端（None 表示用内存）
        self.ttl = 3600                 # 数据过期时间：1 小时（秒）
        self._memory: dict[str, dict] = {}  # 内存降级存储

    async def store(self, session_id: str, data: dict[str, Any]) -> None:
        """
        存储会话状态。

        Redis 模式：
        - key 格式："session:{session_id}"（如 "session:abc123"）
        - value 是 JSON 字符串
        - ex=self.ttl 设置过期时间

        内存模式：
        - 直接存入 self._memory 字典
        """
        if self.redis:
            key = f"session:{session_id}"
            value = json.dumps(data, ensure_ascii=False)
            await self.redis.set(key, value, ex=self.ttl)
        else:
            self._memory[session_id] = data

    async def get(self, session_id: str) -> dict[str, Any] | None:
        """
        获取会话状态。

        返回 None 表示会话不存在或已过期。
        """
        if self.redis:
            key = f"session:{session_id}"
            value = await self.redis.get(key)
            if value:
                return json.loads(value)  # JSON 字符串 → Python dict
            return None
        return self._memory.get(session_id)  # dict.get() 不存在返回 None

    async def update(self, session_id: str, updates: dict[str, Any]) -> None:
        """
        更新会话状态（增量合并）。

        流程：获取已有数据 → 合并新数据 → 存回去
        dict.update() 会把 updates 中的键值对合并到 data 中，
        已有的键被覆盖，没有的键被添加。
        """
        data = await self.get(session_id) or {}
        data.update(updates)
        await self.store(session_id, data)

    # ========== 业务特定的便捷方法 ==========

    async def store_pending_confirmation(
        self,
        session_id: str,
        confirmation: dict[str, Any],
    ) -> None:
        """
        存储待确认操作。

        当 confirm_node 生成确认摘要后，调用这个方法保存，
        以便用户下次回复"确认"时能恢复操作信息。
        """
        await self.update(session_id, {"pending_confirmation": confirmation})

    async def get_pending_confirmation(self, session_id: str) -> dict[str, Any] | None:
        """
        获取待确认操作。

        返回 None 表示没有待确认的操作。
        """
        data = await self.get(session_id)
        if data:
            return data.get("pending_confirmation")
        return None

    async def clear_pending_confirmation(self, session_id: str) -> None:
        """
        清除待确认操作。

        tool_node 执行完操作后调用，表示"已确认，已执行"。
        dict.pop(key, None) —— 删除键，不存在也不报错。
        """
        data = await self.get(session_id) or {}
        data.pop("pending_confirmation", None)
        await self.store(session_id, data)

    async def store_last_recommendations(
        self,
        session_id: str,
        recommendations: list[dict],
    ) -> None:
        """
        存储最近推荐。

        用户说"刚才推荐的第一个"时，系统需要知道推荐了哪些房间。
        """
        await self.update(session_id, {"last_recommendations": recommendations})

    async def get_last_recommendations(self, session_id: str) -> list[dict]:
        """
        获取最近推荐。

        返回空列表表示没有推荐历史。
        """
        data = await self.get(session_id)
        if data:
            return data.get("last_recommendations", [])
        return []
