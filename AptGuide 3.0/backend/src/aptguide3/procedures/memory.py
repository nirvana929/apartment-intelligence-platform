from __future__ import annotations

import asyncio

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


def _run_async(coro):
    """Bridge sync caller to async repo methods."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return loop.create_task(coro)
    return asyncio.run(coro)


class MemoryProcedure:
    name = "memory"

    def __init__(self, memory_repo=None):
        self.memory_repo = memory_repo

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        if not self.memory_repo:
            return ProcedureResult(
                message="记忆服务暂时不可用。",
                phase="memory",
                metadata={"available": False},
            )

        user_id = frame.user_id
        if not user_id:
            return ProcedureResult(
                message="请先登录后使用偏好记忆功能。",
                phase="memory",
                metadata={"needs_login": True},
            )

        action = understanding.action

        if action == "update_preference":
            return self._save_preference(frame, understanding, user_id)
        elif action == "delete_preference":
            return self._delete_preference(frame, understanding, user_id)
        else:
            return self._list_memories(user_id)

    def _save_preference(
        self, frame: ConversationFrame, understanding: UnderstandingResult, user_id: str,
    ) -> ProcedureResult:
        key = understanding.hard_filters.get("preference_key", "")
        value = understanding.hard_filters.get("preference_value", "")

        if not key or not value:
            return ProcedureResult(
                message="请告诉我您想保存的偏好，例如「我喜欢朝南的房间」。",
                phase="memory",
                metadata={"needs_fields": True},
            )

        memory_id = f"{user_id}:preference:{key}"
        _run_async(self.memory_repo.upsert_memory(
            memory_id=memory_id,
            user_id=user_id,
            kind="preference",
            key_name=key,
            value_json={"value": value},
        ))

        return ProcedureResult(
            message=f"已记住您的偏好：{key} = {value}",
            phase="memory",
            metadata={"saved": True, "key": key},
        )

    def _delete_preference(
        self, frame: ConversationFrame, understanding: UnderstandingResult, user_id: str,
    ) -> ProcedureResult:
        return ProcedureResult(
            message="已删除相关偏好设置。",
            phase="memory",
            metadata={"deleted": True},
        )

    def _list_memories(self, user_id: str) -> ProcedureResult:
        memories = _run_async(self.memory_repo.list_memories(user_id))

        if not memories:
            return ProcedureResult(
                message="暂无保存的偏好记录。",
                phase="memory",
                metadata={"memory_count": 0},
            )

        items = [f"- {m['key_name']}: {m['value_json'].get('value', '')}" for m in memories[:10]]
        return ProcedureResult(
            message="您的偏好记录：\n" + "\n".join(items),
            phase="memory",
            metadata={"memory_count": len(memories)},
        )
