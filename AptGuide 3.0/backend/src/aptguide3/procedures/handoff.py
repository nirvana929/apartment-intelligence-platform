from __future__ import annotations

import asyncio
import uuid
from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


def _run_async(coro: Any) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        loop.create_task(coro)
    else:
        asyncio.run(coro)


class HandoffProcedure:
    name = "handoff"

    def __init__(
        self,
        handoff_repo: Any | None = None,
        audit_repo: Any | None = None,
    ) -> None:
        self.handoff_repo = handoff_repo
        self.audit_repo = audit_repo

    def run(
        self, frame: ConversationFrame, understanding: UnderstandingResult
    ) -> ProcedureResult:
        if not self.handoff_repo:
            return ProcedureResult(
                message="人工客服转接服务暂时不可用，请拨打客服电话。",
                phase="handoff",
            )

        ticket_id = uuid.uuid4().hex[:12]
        summary: dict[str, Any] = {
            "reason": understanding.reason or "user_requested_handoff",
            "message": frame.message,
            "domain": understanding.domain,
            "task": understanding.task,
        }

        _run_async(
            self.handoff_repo.create_ticket(
                ticket_id=ticket_id,
                session_id=frame.session_id,
                user_id=frame.user_id or "",
                trigger_type="user_request",
                summary=summary,
            )
        )

        if self.audit_repo:
            _run_async(
                self.audit_repo.append_audit_event(
                    frame.user_id or "",
                    frame.session_id,
                    "handoff_create",
                    {"ticket_id": ticket_id, "trigger_type": "user_request"},
                )
            )

        return ProcedureResult(
            message="正在为您转接人工客服，请稍候。工单号：" + ticket_id,
            phase="handoff",
            metadata={"ticket_id": ticket_id, "handoff_created": True},
        )
