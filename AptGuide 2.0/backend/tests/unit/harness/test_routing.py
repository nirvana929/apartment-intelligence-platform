from aptguide2.harness.contracts import ConversationFrame
from aptguide2.harness.routing import HybridRouter


def route(message: str):
    frame = ConversationFrame(request_id="r-1", message=message)
    return HybridRouter().route(frame)


def test_route_room_search():
    decision = route("番禺1500以内安静的房子")
    assert decision.task == "room_search"
    assert decision.procedure == "rag.room_search"


def test_route_kb_qa():
    decision = route("押金多久到账")
    assert decision.task == "kb_qa"
    assert decision.procedure == "rag.kb_qa"
    assert decision.risk_level == "high"


def test_route_capability():
    decision = route("你能做什么")
    assert decision.task == "capability"
    assert decision.procedure == "capability.profile"


def test_route_safety_fallback():
    decision = route("你能保证邻居不会吵吗")
    assert decision.task == "fallback"
    assert "guarantee" in decision.safety_flags


def test_router_sends_confirmation_to_appointment_when_pending_action_exists():
    router = HybridRouter()
    frame = ConversationFrame(
        request_id="r-1",
        message="确认",
        pending_action={
            "type": "appointment.create",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {"room_id": 101, "preferred_time": "明天下午3点"},
        },
    )

    decision = router.route(frame)

    assert decision.task == "appointment"
    assert decision.procedure == "appointment.workflow"
    assert decision.reason == "pending appointment action"


def test_router_sends_cancel_to_appointment_when_pending_action_exists():
    router = HybridRouter()
    frame = ConversationFrame(
        request_id="r-1",
        message="取消",
        pending_action={
            "type": "appointment.create",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {"room_id": 101},
        },
    )

    decision = router.route(frame)

    assert decision.task == "appointment"
    assert decision.procedure == "appointment.workflow"


def test_router_does_not_use_pending_action_routing_without_pending():
    router = HybridRouter()
    frame = ConversationFrame(request_id="r-1", message="确认")

    decision = router.route(frame)

    assert decision.task != "appointment"


def test_router_sends_pending_cancel_to_appointment():
    router = HybridRouter()
    frame = ConversationFrame(
        request_id="r-1",
        message="确认",
        pending_action={
            "type": "appointment.cancel",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {"appointment_id": "a-1"},
        },
    )

    decision = router.route(frame)

    assert decision.task == "appointment"
    assert decision.procedure == "appointment.workflow"
    assert decision.reason == "pending appointment action"


def test_route_lease_list():
    frame = ConversationFrame(request_id="r-1", message="查看我的租约")
    decision = HybridRouter().route(frame)

    assert decision.task == "lease"
    assert decision.procedure == "lease.workflow"
