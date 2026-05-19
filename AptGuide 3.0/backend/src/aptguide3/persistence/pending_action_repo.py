from __future__ import annotations

from datetime import datetime


class InMemoryPendingActionRepo:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    async def save_pending_action(
        self,
        pending_action_id: str,
        session_id: str,
        user_id: str,
        action_type: str,
        payload: dict,
        expires_at: datetime,
    ) -> None:
        self._store[pending_action_id] = {
            "pending_action_id": pending_action_id,
            "session_id": session_id,
            "user_id": user_id,
            "action_type": action_type,
            "payload": payload,
            "expires_at": expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at),
            "status": "pending",
        }

    async def load_pending_action(self, pending_action_id: str) -> dict | None:
        return self._store.get(pending_action_id)

    async def mark_completed(self, pending_action_id: str) -> None:
        if pending_action_id in self._store:
            self._store[pending_action_id]["status"] = "completed"
