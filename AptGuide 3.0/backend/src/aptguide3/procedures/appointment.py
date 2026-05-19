from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


def _run_async(coro: Any) -> Any:
    """Bridge sync-to-async: run *coro* and return its result."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    new_loop = asyncio.new_event_loop()
    try:
        return new_loop.run_until_complete(coro)
    finally:
        new_loop.close()


class AppointmentProcedure:
    name = "appointment"

    def __init__(
        self,
        pending_action_repo: Any = None,
        lease_client: Any = None,
        audit_repo: Any = None,
    ):
        self.pending_action_repo = pending_action_repo
        self.lease_client = lease_client
        self.audit_repo = audit_repo

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        # 1. If there's a pending_action in frame, this is a confirmation
        if frame.pending_action:
            return self._handle_confirmation(frame)

        # 2. Parse required fields from understanding
        apartment_id = understanding.hard_filters.get("apartment_id")
        appointment_time = understanding.hard_filters.get("appointment_time")

        if not apartment_id or not appointment_time:
            return ProcedureResult(
                message="请提供房间号和预约时间，我来帮您预约看房。",
                phase="appointment",
                actions=[{"type": "ask_fields", "fields": ["apartment_id", "appointment_time"]}],
                metadata={"needs_fields": True},
            )

        # 3. Save pending action
        pending_id = uuid.uuid4().hex[:12]
        payload = {
            "apartment_id": apartment_id,
            "appointment_time": appointment_time,
            "remark": frame.message,
        }

        if self.pending_action_repo:
            try:
                _run_async(
                    self.pending_action_repo.save_pending_action(
                        pending_id,
                        frame.session_id,
                        frame.user_id or "",
                        "appointment",
                        payload,
                        datetime.now(UTC) + timedelta(minutes=30),
                    )
                )
            except Exception:
                pass

        # 4. Return confirmation card
        return ProcedureResult(
            message=f"确认预约看房？房间 {apartment_id}，时间 {appointment_time}",
            phase="appointment",
            actions=[{"type": "confirm", "pending_action_id": pending_id}],
            pending_action={"id": pending_id, "type": "appointment"},
            metadata={"pending_action_id": pending_id},
        )

    def _handle_confirmation(self, frame: ConversationFrame) -> ProcedureResult:
        pending = frame.pending_action
        pending_id = pending.get("id", "") if pending else ""

        if not self.pending_action_repo or not self.lease_client:
            return ProcedureResult(message="预约服务暂时不可用，请稍后重试。", phase="appointment")

        # Load and validate pending action
        try:
            action = _run_async(self.pending_action_repo.load_pending_action(pending_id))
        except Exception:
            action = None

        if not action:
            return ProcedureResult(message="预约请求已过期，请重新发起。", phase="appointment")

        if action.get("status") == "completed":
            return ProcedureResult(message="该预约已完成处理。", phase="appointment")

        payload = action.get("payload", {})

        # Call lease to create appointment
        try:
            uid = int(frame.user_id) if frame.user_id and frame.user_id.isdigit() else 0
            result = _run_async(
                self.lease_client.create_appointment(
                    user_id=uid,
                    apartment_id=payload.get("apartment_id", 0),
                    appointment_time=payload.get("appointment_time", ""),
                    remark=payload.get("remark", "AI assistant booking"),
                )
            )
        except Exception:
            result = {"ok": False, "error": "请求异常"}

        # Mark pending completed
        try:
            _run_async(self.pending_action_repo.mark_completed(pending_id))
        except Exception:
            pass

        # Audit
        if self.audit_repo:
            try:
                _run_async(
                    self.audit_repo.append_audit_event(
                        frame.user_id or "",
                        frame.session_id,
                        "appointment_create",
                        {"apartment_id": payload.get("apartment_id"), "success": result.get("ok", False)},
                    )
                )
            except Exception:
                pass

        if result.get("ok"):
            return ProcedureResult(
                message="预约成功！我们会尽快确认，请留意通知。",
                phase="appointment",
                metadata={"appointment_created": True, "pending_action_id": pending_id},
            )
        return ProcedureResult(
            message=f"预约失败：{result.get('error', '未知错误')}，请稍后重试。",
            phase="appointment",
            metadata={"error": result.get("error")},
        )
