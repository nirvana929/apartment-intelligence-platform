"""Appointment workflow procedure for AptGuide 2.0 harness."""

from __future__ import annotations

import re
import time
import uuid
from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.tools.contracts import ToolCallRequest


class AppointmentWorkflowProcedure:
    """Handles appointment creation and listing through governed tool runtime."""

    def _get_intent(self, decision: RouteDecision):
        payload = decision.metadata.get("intent") if decision.metadata else None
        if not payload:
            return None
        from aptguide2.interaction.contracts import InteractionIntent
        return InteractionIntent.model_validate(payload)

    def _extract_room_id_from_intent(self, intent) -> int | None:
        if intent is None:
            return None
        for entity in intent.entities:
            if entity.kind == "room_id" and entity.normalized_value is not None:
                return int(entity.normalized_value)
        return None

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        message = frame.message or ""

        if self._is_list_request(message):
            return self._list_appointments(frame, tool_runtime)

        # Handle pending cancel confirmation before new requests
        if self._is_pending_cancel_action(frame):
            return self._handle_cancel_confirmation(frame, tool_runtime)

        # Handle pending create confirmation before new requests
        if frame.pending_action and frame.pending_action.get("type") == "appointment.create":
            return self._handle_confirmation(frame, tool_runtime)

        if self._is_cancel_request(message):
            return self._create_cancel_confirmation(frame, message)

        return self._create_appointment(frame, message, tool_runtime, decision)

    def _is_list_request(self, message: str) -> bool:
        list_terms = ("我的预约", "查看预约", "预约列表", "预约记录", "看预约")
        return any(term in message for term in list_terms)

    def _is_cancel_request(self, message: str) -> bool:
        cancel_terms = ("取消预约", "取消看房", "不去了")
        return any(term in message for term in cancel_terms)

    def _is_pending_cancel_action(self, frame: ConversationFrame) -> bool:
        return bool(frame.pending_action and frame.pending_action.get("type") == "appointment.cancel")

    def _extract_appointment_id(self, frame: ConversationFrame, message: str) -> str | None:
        """Extract appointment_id with priority: action payload > pending_action payload > regex."""
        action_payload = (frame.action or {}).get("payload", {})
        if isinstance(action_payload, dict) and action_payload.get("appointment_id"):
            return str(action_payload["appointment_id"])

        pending_payload = (frame.pending_action or {}).get("payload", {})
        if isinstance(pending_payload, dict) and pending_payload.get("appointment_id"):
            return str(pending_payload["appointment_id"])

        patterns = [
            r"预约(?:编号)?\s*([A-Za-z0-9_-]{2,32})",
            r"取消预约\s*([A-Za-z0-9_-]{2,32})",
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        return None

    def _create_cancel_confirmation(self, frame: ConversationFrame, message: str) -> ProcedureResult:
        if not frame.user_id:
            return ProcedureResult(
                task="appointment",
                phase="appointment_auth_required",
                reply="请先登录后再取消预约。",
                fallback_reason="missing_user_id",
            )
        appointment_id = self._extract_appointment_id(frame, message)
        if not appointment_id:
            return ProcedureResult(
                task="appointment",
                phase="appointment_needs_info",
                reply="请提供要取消的预约编号。",
                metadata={"missing": "appointment_id"},
            )
        confirmation_id = str(uuid.uuid4())[:8]
        now = time.time()
        pending_action = {
            "type": "appointment.cancel",
            "confirmation_id": confirmation_id,
            "status": "pending",
            "payload": {"appointment_id": appointment_id, "user_id": frame.user_id},
            "created_at": now,
            "expires_at": now + 300,
        }
        return ProcedureResult(
            task="appointment",
            phase="appointment_cancel_needs_confirmation",
            reply=f"请确认取消预约 {appointment_id}。回复'确认'继续，或'取消'放弃。",
            pending_action=pending_action,
            actions=[
                {"type": "confirm", "confirmation_id": confirmation_id, "label": "确认取消"},
                {"type": "cancel", "confirmation_id": confirmation_id, "label": "保留预约"},
            ],
            metadata={"appointment_id": appointment_id},
        )

    def _handle_cancel_confirmation(self, frame: ConversationFrame, tool_runtime: Any | None) -> ProcedureResult:
        message = frame.message or ""
        action_type = (frame.action or {}).get("type")
        is_confirm = action_type == "confirm" or any(term in message for term in ("确认", "好的", "是的", "确定", "行", "可以", "yes", "ok"))
        is_cancel = action_type == "cancel" or any(term in message for term in ("取消", "不要了", "算了", "no"))

        if is_cancel:
            frame.pending_action = None
            return ProcedureResult(task="appointment", phase="appointment_cancel_aborted", reply="好的，已保留该预约。")

        if not is_confirm:
            return ProcedureResult(
                task="appointment",
                phase="appointment_cancel_needs_confirmation",
                reply="请确认是否取消预约？回复'确认'继续，或'取消'放弃。",
                pending_action=frame.pending_action,
            )

        if tool_runtime is None:
            return ProcedureResult(
                task="appointment",
                phase="appointment_tool_unavailable",
                reply="预约服务暂时不可用，请稍后再试。",
                fallback_reason="tool_runtime_missing",
            )
        pending = frame.pending_action or {}
        payload = dict(pending.get("payload", {}))
        appointment_id = payload.get("appointment_id")
        request = ToolCallRequest(
            tool="appointment.cancel",
            request_id=frame.request_id,
            user_id=frame.user_id or "",
            confirmation_id=pending.get("confirmation_id", ""),
            payload={**payload, "user_id": frame.user_id or payload.get("user_id", "")},
        )
        result = tool_runtime.execute(request)
        frame.pending_action = None
        if result.ok:
            return ProcedureResult(
                task="appointment",
                phase="appointment_cancelled",
                reply=f"已取消预约：{appointment_id}。",
                metadata={"appointment_id": appointment_id},
            )
        return ProcedureResult(
            task="appointment",
            phase="appointment_cancel_failed",
            reply="取消预约失败，请稍后再试或联系人工客服。",
            fallback_reason="appointment_cancel_failed",
        )

    def _extract_room_id(self, message: str) -> int | None:
        """Extract room_id from message like '预约第101号房' or '预约房间101'."""
        patterns = [
            r"预约.*?(\d{3,6})",
            r"房间.*?(\d{3,6})",
            r"(\d{3,6}).*?号房",
            r"room.*?(\d{3,6})",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_time(self, message: str) -> str:
        """Extract preferred time from message."""
        time_patterns = [
            r"明天.*?(\d{1,2}[:.：]?\d{0,2})",
            r"后天.*?(\d{1,2}[:.：]?\d{0,2})",
            r"周[一二三四五六日].*?(\d{1,2}[:.：]?\d{0,2})",
            r"(\d{1,2}月\d{1,2}日).*?(\d{1,2}[:.：]?\d{0,2})",
            r"下午",
            r"上午",
            r"晚上",
        ]
        for pattern in time_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(0)
        return ""

    def _create_appointment(self, frame: ConversationFrame, message: str, tool_runtime: Any | None, decision: RouteDecision | None = None) -> ProcedureResult:
        # Try intent entities first, then fall back to regex
        intent = self._get_intent(decision) if decision else None
        room_id = self._extract_room_id_from_intent(intent) if intent else None
        if room_id is None:
            room_id = self._extract_room_id(message)
        preferred_time = self._extract_time(message)

        if room_id is None:
            return ProcedureResult(
                task="appointment",
                phase="appointment_needs_info",
                reply="请问您想预约哪个房间的看房？请提供房间号，例如'预约101号房'。",
                metadata={"missing": "room_id"},
            )

        if not preferred_time:
            return ProcedureResult(
                task="appointment",
                phase="appointment_needs_info",
                reply=f"您想预约看{room_id}号房，请问什么时间方便？例如'明天下午3点'。",
                metadata={"missing": "preferred_time", "room_id": room_id},
            )

        if not frame.user_id:
            return ProcedureResult(
                task="appointment",
                phase="appointment_auth_required",
                reply="请先登录后再预约看房。",
                fallback_reason="missing_user_id",
            )

        if tool_runtime is None:
            return ProcedureResult(
                task="appointment",
                phase="appointment_tool_unavailable",
                reply="预约服务暂时不可用，请稍后再试或拨打客服电话。",
                fallback_reason="tool_runtime_missing",
            )

        confirmation_id = str(uuid.uuid4())[:8]
        now = time.time()
        pending_action = {
            "type": "appointment.create",
            "confirmation_id": confirmation_id,
            "status": "pending",
            "payload": {
                "room_id": room_id,
                "user_id": frame.user_id,
                "preferred_time": preferred_time,
                "notes": "",
            },
            "created_at": now,
            "expires_at": now + 300,
        }
        return ProcedureResult(
            task="appointment",
            phase="appointment_needs_confirmation",
            reply=f"请确认预约{room_id}号房，时间为{preferred_time}。回复'确认'继续，或'取消'放弃。",
            pending_action=pending_action,
            actions=[
                {
                    "type": "confirm",
                    "confirmation_id": confirmation_id,
                    "label": "确认预约",
                },
                {
                    "type": "cancel",
                    "confirmation_id": confirmation_id,
                    "label": "取消",
                },
            ],
            metadata={"room_id": room_id, "preferred_time": preferred_time},
        )

    def _handle_confirmation(self, frame: ConversationFrame, tool_runtime: Any | None) -> ProcedureResult:
        """Handle user confirmation of a pending appointment."""
        message = frame.message or ""
        confirm_terms = ("确认", "好的", "是的", "确定", "行", "可以", "yes", "ok")
        cancel_terms = ("取消", "不要了", "算了", "no")

        action_type = (frame.action or {}).get("type")
        is_confirm = action_type == "confirm" or any(term in message for term in confirm_terms)
        is_cancel = action_type == "cancel" or any(term in message for term in cancel_terms)

        if is_confirm:
            pending = frame.pending_action
            if pending and tool_runtime:
                confirmation_id = pending.get("confirmation_id", "")
                request = ToolCallRequest(
                    tool="appointment.create",
                    request_id=frame.request_id,
                    user_id=frame.user_id or "",
                    confirmation_id=confirmation_id,
                    payload={
                        **pending.get("payload", {}),
                        "user_id": frame.user_id or pending.get("payload", {}).get("user_id", ""),
                    },
                )
                result = tool_runtime.execute(request)
                frame.pending_action = None

                if result.ok:
                    appointment_id = result.data.get("appointment_id", "")
                    return ProcedureResult(
                        task="appointment",
                        phase="appointment_created",
                        reply=f"已为您成功预约，预约编号：{appointment_id}。",
                        cards=[{"type": "appointment_confirmation", "appointment_id": appointment_id}],
                    )
                else:
                    return ProcedureResult(
                        task="appointment",
                        phase="appointment_failed",
                        reply=f"预约失败：{result.error.message if result.error else '未知错误'}。",
                    )

        if is_cancel:
            frame.pending_action = None
            return ProcedureResult(
                task="appointment",
                phase="appointment_cancelled",
                reply="好的，已取消预约操作。",
            )

        return ProcedureResult(
            task="appointment",
            phase="appointment_needs_confirmation",
            reply="请确认是否要预约？回复'确认'继续，或'取消'放弃。",
        )

    def _list_appointments(self, frame: ConversationFrame, tool_runtime: Any | None) -> ProcedureResult:
        if not frame.user_id:
            return ProcedureResult(
                task="appointment",
                phase="appointment_auth_required",
                reply="请先登录后再查看您的预约记录。",
                fallback_reason="missing_user_id",
            )

        if tool_runtime is None:
            return ProcedureResult(
                task="appointment",
                phase="appointment_tool_unavailable",
                reply="预约服务暂时不可用，请稍后再试。",
                fallback_reason="tool_runtime_missing",
            )

        request = ToolCallRequest(
            tool="appointment.list_mine",
            request_id=frame.request_id,
            user_id=frame.user_id or "",
            payload={"user_id": frame.user_id or "", "limit": 10},
        )

        result = tool_runtime.execute(request)

        if not result.ok:
            return ProcedureResult(
                task="appointment",
                phase="appointment_list_failed",
                reply="查询预约记录失败，请稍后再试。",
                fallback_reason="appointment_list_failed",
            )

        appointments = result.data.get("appointments", [])
        if not appointments:
            return ProcedureResult(
                task="appointment",
                phase="appointment_list_empty",
                reply="您还没有预约记录。",
            )

        cards = []
        for apt in appointments[:5]:
            cards.append({
                "type": "appointment_record",
                "appointment_id": apt.get("appointment_id", ""),
                "room_id": apt.get("room_id", ""),
                "preferred_time": apt.get("preferred_time", ""),
                "status": apt.get("status", ""),
            })

        return ProcedureResult(
            task="appointment",
            phase="appointment_list",
            reply=f"您有{len(appointments)}条预约记录。",
            cards=cards,
            metadata={"appointment_count": len(appointments)},
        )
