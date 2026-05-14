from __future__ import annotations

from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.memory import MemoryManager
from aptguide2.harness.memory_repository import MemoryRepository


class MemoryProcedure:
    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository
        self.memory = MemoryManager()

    async def run_async(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        if not frame.user_id:
            return ProcedureResult(task="memory", phase="memory_auth_required", reply="请先登录后再管理偏好。")

        message = frame.message or ""
        if "我的偏好" in message or "记住了什么" in message:
            profile = await self.repository.get_profile(frame.user_id)
            return ProcedureResult(
                task="memory",
                phase="memory_profile",
                reply="这是我目前记住的找房偏好。" if profile else "我还没有记住您的长期找房偏好。",
                cards=[{"type": "memory_profile", "profile": profile}],
                metadata={"profile_keys": list(profile.keys())},
            )

        if "删除" in message or "忘记" in message:
            key = "preferences"
            profile = await self.repository.delete_profile_key(frame.user_id, key, session_id=frame.session_id or "")
            return ProcedureResult(
                task="memory",
                phase="memory_deleted",
                reply="已删除相关长期偏好。",
                cards=[{"type": "memory_profile", "profile": profile}],
            )

        patch = self._extract_memory_patch(message)
        candidate = await self.repository.create_candidate(
            user_id=frame.user_id,
            session_id=frame.session_id or "",
            kind="preference",
            payload=patch,
        )
        pending = self.memory.create_pending_action(
            frame,
            action_type="memory.profile_update",
            payload={"candidate_id": candidate.candidate_id, "patch": patch},
        )
        return ProcedureResult(
            task="memory",
            phase="memory_confirmation_required",
            reply="我可以把这个作为长期找房偏好记住，请确认。",
            cards=[{"type": "memory_confirmation", "candidate_id": candidate.candidate_id, "patch": patch}],
            actions=[
                {"type": "confirm", "confirmation_id": pending["confirmation_id"], "label": "确认记住"},
                {"type": "cancel", "confirmation_id": pending["confirmation_id"], "label": "不记住"},
            ],
            pending_action=pending,
        )

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        import asyncio

        return asyncio.run(self.run_async(frame, decision, tool_runtime))

    def _extract_memory_patch(self, message: str) -> dict[str, Any]:
        preferences = []
        for term in ("安静", "近地铁", "采光好", "独卫", "通勤方便"):
            if term in message:
                preferences.append(term)
        return {"preferences": preferences or [message.replace("记住", "").strip()]}
