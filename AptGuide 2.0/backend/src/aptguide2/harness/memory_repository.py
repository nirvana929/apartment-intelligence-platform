from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MemoryCandidate:
    """候选记忆 —— 用户表达的偏好不会直接写入长期画像，而是先作为候选，
    经过确认后才提升为正式的 profile 条目。"""

    candidate_id: str
    user_id: str
    session_id: str
    kind: str                              # 候选类型（如 "preference"）
    payload: dict[str, Any]                # 候选内容（如 {"area": "番禺", "budget": 1500}）
    status: str = "pending"                # pending → confirmed


class MemoryRepository:
    """长期用户记忆仓库 —— 管理用户画像(profile)和候选记忆(candidate)。

    当前为内存实现，用于测试。生产环境应替换为 SQL/Redis 实现。
    所有写操作都会记录 audit 日志。
    """

    def __init__(self) -> None:
        self.profiles: dict[str, dict[str, Any]] = {}    # user_id → 偏好键值对
        self.candidates: dict[str, dict[str, Any]] = {}  # candidate_id → 候选记录
        self.audit: list[dict[str, Any]] = []             # 审计日志（所有变更）

    async def get_profile(self, user_id: str) -> dict[str, Any]:
        """获取用户的长期偏好画像，返回副本避免外部修改。"""
        return dict(self.profiles.get(user_id, {}))

    async def upsert_profile(self, user_id: str, patch: dict[str, Any], session_id: str = "") -> dict[str, Any]:
        """合并更新用户画像。patch 中的键会覆盖已有值，其余保留。"""
        current = dict(self.profiles.get(user_id, {}))
        current.update(patch)
        self.profiles[user_id] = current
        self.audit.append({"user_id": user_id, "session_id": session_id, "event_type": "memory.profile_update", "payload": patch})
        return current

    async def delete_profile_key(self, user_id: str, key: str, session_id: str = "") -> dict[str, Any]:
        """删除用户画像中的指定键。"""
        current = dict(self.profiles.get(user_id, {}))
        current.pop(key, None)
        self.profiles[user_id] = current
        self.audit.append({"user_id": user_id, "session_id": session_id, "event_type": "memory.profile_delete", "payload": {"key": key}})
        return current

    async def create_candidate(self, user_id: str, session_id: str, kind: str, payload: dict[str, Any]) -> MemoryCandidate:
        """创建候选记忆。用户一次性表达的偏好先存为候选，确认后才写入 profile。"""
        candidate_id = f"mem-{uuid.uuid4().hex[:12]}"
        record = {
            "candidate_id": candidate_id,
            "user_id": user_id,
            "session_id": session_id,
            "kind": kind,
            "payload": payload,
            "status": "pending",
        }
        self.candidates[candidate_id] = record
        return MemoryCandidate(**record)

    async def confirm_candidate(self, candidate_id: str) -> MemoryCandidate | None:
        """确认候选记忆。确认后由调用方决定是否提升为 profile。"""
        record = self.candidates.get(candidate_id)
        if record is None:
            return None
        record["status"] = "confirmed"
        return MemoryCandidate(**record)
