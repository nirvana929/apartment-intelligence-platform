"""Tests for appointment workflow procedure."""

from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.appointment import AppointmentWorkflowProcedure
from aptguide2.harness.tools.contracts import ToolCallResult


class FakeToolRuntime:
    def __init__(self, ok=True, data=None, error=None):
        self.ok = ok
        self.data = data or {}
        self.error = error
        self.last_request = None

    def execute(self, request):
        self.last_request = request
        if self.ok:
            return ToolCallResult.ok_result(
                tool=request.tool,
                data=self.data,
                backend="lease",
            )
        return ToolCallResult.error_result(
            tool=request.tool,
            code="UNKNOWN_TOOL_ERROR",
            message="test error",
            backend="lease",
        )


def test_extract_room_id():
    proc = AppointmentWorkflowProcedure()
    assert proc._extract_room_id("预约101号房") == 101
    assert proc._extract_room_id("我想预约201房间") == 201
    assert proc._extract_room_id("帮我预约第301号") == 301
    assert proc._extract_room_id("预约room401") == 401
    assert proc._extract_room_id("随便聊聊") is None


def test_is_list_request():
    proc = AppointmentWorkflowProcedure()
    assert proc._is_list_request("我的预约") is True
    assert proc._is_list_request("查看预约") is True
    assert proc._is_list_request("预约列表") is True
    assert proc._is_list_request("帮我找房") is False


def test_is_cancel_request():
    proc = AppointmentWorkflowProcedure()
    assert proc._is_cancel_request("取消预约") is True
    assert proc._is_cancel_request("不去了") is True
    assert proc._is_cancel_request("帮我找房") is False


def test_create_appointment_missing_room_id():
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", message="帮我预约看房")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision)

    assert result.task == "appointment"
    assert result.phase == "appointment_needs_info"
    assert "房间号" in result.reply


def test_create_appointment_missing_time():
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", message="预约101号房")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision)

    assert result.task == "appointment"
    assert result.phase == "appointment_needs_info"
    assert "时间" in result.reply


def test_create_appointment_first_turn_returns_pending_action_without_tool_call():
    proc = AppointmentWorkflowProcedure()
    runtime = FakeToolRuntime(ok=True, data={"appointment_id": "APT-001"})
    frame = ConversationFrame(request_id="r-1", user_id="u-1", message="预约101号房明天下午3点")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.task == "appointment"
    assert result.phase == "appointment_needs_confirmation"
    assert result.pending_action is not None
    assert result.pending_action["type"] == "appointment.create"
    assert result.pending_action["payload"]["room_id"] == 101
    assert "明天" in result.pending_action["payload"]["preferred_time"]
    assert runtime.last_request is None


def test_create_appointment_confirmed_turn_calls_tool_with_confirmation_id():
    proc = AppointmentWorkflowProcedure()
    runtime = FakeToolRuntime(ok=True, data={"appointment_id": "APT-001", "status": "pending"})
    frame = ConversationFrame(
        request_id="r-2",
        user_id="u-1",
        message="确认",
        pending_action={
            "type": "appointment.create",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {
                "room_id": 101,
                "user_id": "u-1",
                "preferred_time": "明天下午3点",
                "notes": "",
            },
        },
    )
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.98)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.phase == "appointment_created"
    assert frame.pending_action is None
    assert runtime.last_request.tool == "appointment.create"
    assert runtime.last_request.user_id == "u-1"
    assert runtime.last_request.confirmation_id == "c-1"
    assert runtime.last_request.payload["room_id"] == 101


def test_create_appointment_pending_turn_can_be_cancelled():
    proc = AppointmentWorkflowProcedure()
    runtime = FakeToolRuntime(ok=True, data={"appointment_id": "APT-001"})
    frame = ConversationFrame(
        request_id="r-2",
        user_id="u-1",
        message="取消",
        pending_action={
            "type": "appointment.create",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {"room_id": 101, "user_id": "u-1", "preferred_time": "明天下午3点"},
        },
    )
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.98)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.phase == "appointment_cancelled"
    assert frame.pending_action is None
    assert runtime.last_request is None


def test_create_appointment_confirmed_turn_failure():
    proc = AppointmentWorkflowProcedure()
    runtime = FakeToolRuntime(ok=False)
    frame = ConversationFrame(
        request_id="r-2",
        user_id="u-1",
        message="确认",
        pending_action={
            "type": "appointment.create",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {
                "room_id": 101,
                "user_id": "u-1",
                "preferred_time": "明天下午3点",
                "notes": "",
            },
        },
    )
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.98)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.phase == "appointment_failed"
    assert "失败" in result.reply
    assert frame.pending_action is None


def test_create_appointment_requires_user_id():
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", message="预约101号房明天下午3点")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=FakeToolRuntime())

    assert result.phase == "appointment_auth_required"
    assert "登录" in result.reply


def test_create_appointment_no_tool_runtime():
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", user_id="u-1", message="预约101号房明天下午3点")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=None)

    assert result.task == "appointment"
    assert result.phase == "appointment_tool_unavailable"


def test_list_appointments_empty():
    proc = AppointmentWorkflowProcedure()
    runtime = FakeToolRuntime(ok=True, data={"appointments": [], "total": 0})
    frame = ConversationFrame(request_id="r-1", user_id="u-1", message="我的预约")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.task == "appointment"
    assert result.phase == "appointment_list_empty"


def test_list_appointments_with_data():
    proc = AppointmentWorkflowProcedure()
    runtime = FakeToolRuntime(ok=True, data={
        "appointments": [
            {"appointment_id": "APT-001", "room_id": 101, "preferred_time": "明天下午3点", "status": "pending"},
            {"appointment_id": "APT-002", "room_id": 202, "preferred_time": "后天上午10点", "status": "confirmed"},
        ],
        "total": 2,
    })
    frame = ConversationFrame(request_id="r-1", user_id="u-1", message="查看预约")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.task == "appointment"
    assert result.phase == "appointment_list"
    assert len(result.cards) == 2
    assert result.metadata["appointment_count"] == 2


def test_cancel_request():
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", user_id="u-1", message="取消预约a-1")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision)

    assert result.task == "appointment"
    assert result.phase == "appointment_cancel_needs_confirmation"
    assert result.pending_action is not None
    assert result.pending_action["type"] == "appointment.cancel"
    assert result.pending_action["payload"]["appointment_id"] == "a-1"


def test_list_appointments_requires_user_id():
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", message="我的预约")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=FakeToolRuntime())

    assert result.phase == "appointment_auth_required"
    assert "登录" in result.reply


def test_cancel_appointment_requires_user_id():
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id=None, message="取消预约a-1")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=FakeToolRuntime())

    assert result.phase == "appointment_auth_required"
    assert result.fallback_reason == "missing_user_id"


def test_cancel_appointment_first_turn_returns_pending_action_without_tool_call():
    runtime = FakeToolRuntime(ok=True, data={"appointment_id": "a-1", "status": "cancelled"})
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", session_id="s-1", user_id="u-1", message="取消预约a-1")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.phase == "appointment_cancel_needs_confirmation"
    assert result.pending_action["type"] == "appointment.cancel"
    assert result.pending_action["payload"]["appointment_id"] == "a-1"
    assert runtime.last_request is None


def test_cancel_appointment_confirm_calls_tool_runtime_from_pending_action():
    runtime = FakeToolRuntime(ok=True, data={"appointment_id": "a-1", "status": "cancelled"})
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(
        request_id="r-1",
        session_id="s-1",
        user_id="u-1",
        message="确认",
        pending_action={
            "type": "appointment.cancel",
            "confirmation_id": "c-cancel",
            "status": "pending",
            "payload": {"appointment_id": "a-1", "user_id": "u-1"},
        },
    )
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.98)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.phase == "appointment_cancelled"
    assert runtime.last_request.tool == "appointment.cancel"
    assert runtime.last_request.payload["appointment_id"] == "a-1"
    assert runtime.last_request.confirmation_id == "c-cancel"


def test_cancel_appointment_aborted():
    runtime = FakeToolRuntime(ok=True, data={})
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(
        request_id="r-1",
        session_id="s-1",
        user_id="u-1",
        message="不要了",
        pending_action={
            "type": "appointment.cancel",
            "confirmation_id": "c-cancel",
            "status": "pending",
            "payload": {"appointment_id": "a-1", "user_id": "u-1"},
        },
    )
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.98)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.phase == "appointment_cancel_aborted"
    assert frame.pending_action is None
    assert runtime.last_request is None


def test_cancel_appointment_uses_action_payload_before_message_regex():
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(
        request_id="r-1",
        session_id="s-1",
        user_id="u-1",
        message="取消预约",
        action={"type": "cancel_appointment", "payload": {"appointment_id": "a-from-action"}},
    )
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=FakeToolRuntime())

    assert result.pending_action["payload"]["appointment_id"] == "a-from-action"


def test_cancel_appointment_failure():
    runtime = FakeToolRuntime(ok=False)
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(
        request_id="r-1",
        session_id="s-1",
        user_id="u-1",
        message="确认",
        pending_action={
            "type": "appointment.cancel",
            "confirmation_id": "c-cancel",
            "status": "pending",
            "payload": {"appointment_id": "a-1", "user_id": "u-1"},
        },
    )
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.98)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.phase == "appointment_cancel_failed"
    assert frame.pending_action is None


def test_semantic_appointment_create_still_requires_confirmation():
    from aptguide2.interaction.contracts import EntityMention, InteractionIntent

    intent = InteractionIntent(
        raw_message="帮我预约200101明天下午看房",
        route="appointment",
        domain="appointment",
        action="create",
        needs_confirmation=True,
        entities=[
            EntityMention(kind="room_id", raw_text="200101", normalized_value=200101, confidence=0.95),
            EntityMention(kind="time", raw_text="明天下午", normalized_value="明天下午", confidence=0.9),
        ],
    )
    decision = RouteDecision(
        task="appointment",
        procedure="appointment.workflow",
        confidence=0.9,
        metadata={"intent": intent.model_dump(mode="json")},
    )
    frame = ConversationFrame(session_id="s1", request_id="r1", user_id="u1", message="帮我预约200101明天下午看房")

    proc = AppointmentWorkflowProcedure()
    result = proc.run(frame, decision, tool_runtime=FakeToolRuntime())

    assert result.phase == "appointment_needs_confirmation"
    assert result.pending_action["type"] == "appointment.create"
