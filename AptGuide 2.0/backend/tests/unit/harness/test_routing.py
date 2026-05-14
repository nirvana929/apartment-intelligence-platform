from aptguide2.harness.contracts import ConversationFrame
from aptguide2.harness.routing import HybridRouter
from aptguide2.interaction.contracts import InteractionIntent


class StubClassifier:
    def __init__(self, intent: InteractionIntent) -> None:
        self.intent = intent

    def classify(self, message: str) -> InteractionIntent:
        return self.intent.model_copy(update={"raw_message": message})


def _router(intent: InteractionIntent) -> HybridRouter:
    return HybridRouter(intent_classifier=StubClassifier(intent))


def test_route_room_search():
    router = _router(InteractionIntent(
        raw_message="",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        needs_room_search=True,
        hard_filters={"district_id": 4},
        soft_preferences=["安静"],
        confidence=0.9,
    ))
    decision = router.route(ConversationFrame(request_id="r-1", message="番禺1500以内安静的房子"))
    assert decision.task == "room_search"
    assert decision.procedure == "rag.room_search"


def test_route_kb_qa():
    router = _router(InteractionIntent(
        raw_message="",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
        needs_kb=True,
        risk_level="medium",
        response_mode="kb_grounded_answer",
        confidence=0.88,
    ))
    decision = router.route(ConversationFrame(request_id="r-1", message="押金多久到账"))
    assert decision.task == "kb_qa"
    assert decision.procedure == "rag.kb_qa"
    assert decision.risk_level == "medium"


def test_route_capability():
    router = _router(InteractionIntent(
        raw_message="",
        route="capability",
        domain="capability",
        action="ask_capability",
        confidence=0.95,
    ))
    decision = router.route(ConversationFrame(request_id="r-1", message="你能做什么"))
    assert decision.task == "capability"
    assert decision.procedure == "capability.profile"


def test_route_safety_fallback():
    router = _router(InteractionIntent(
        raw_message="",
        route="fallback",
        confidence=0.4,
    ))
    decision = router.route(ConversationFrame(request_id="r-1", message="你能保证邻居不会吵吗"))
    assert decision.task == "fallback"
    assert "guarantee" in decision.safety_flags


def test_router_sends_confirmation_to_appointment_when_pending_action_exists():
    router = HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
        raw_message="",
        route="fallback",
        action="clarify",
        confidence=0.0,
    )))
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
    router = HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
        raw_message="",
        route="fallback",
        action="clarify",
        confidence=0.0,
    )))
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
    router = HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
        raw_message="",
        route="fallback",
        action="clarify",
        confidence=0.0,
    )))
    frame = ConversationFrame(request_id="r-1", message="确认")

    decision = router.route(frame)

    assert decision.task != "appointment"


def test_router_sends_pending_cancel_to_appointment():
    router = HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
        raw_message="",
        route="fallback",
        action="clarify",
        confidence=0.0,
    )))
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
    router = _router(InteractionIntent(
        raw_message="",
        route="lease",
        domain="lease",
        action="list",
        needs_tool=True,
        confidence=0.86,
    ))
    frame = ConversationFrame(request_id="r-1", message="查看我的租约")
    decision = router.route(frame)

    assert decision.task == "lease"
    assert decision.procedure == "lease.workflow"


def test_deposit_policy_routes_to_kb_not_handoff():
    router = _router(InteractionIntent(
        raw_message="",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
        needs_kb=True,
        risk_level="medium",
        response_mode="kb_grounded_answer",
        confidence=0.88,
    ))
    decision = router.route(ConversationFrame(request_id="r1", message="押金什么时候退"))

    assert decision.task == "kb_qa"
    assert decision.procedure == "rag.kb_qa"
    assert decision.risk_level == "medium"


def test_external_complaint_routes_to_handoff():
    router = _router(InteractionIntent(
        raw_message="",
        route="handoff",
        domain="handoff",
        action="request_handoff",
        risk_level="high",
        response_mode="handoff_to_human",
        confidence=0.9,
    ))
    decision = router.route(ConversationFrame(request_id="r2", message="我要打 12315"))

    assert decision.task == "handoff"
    assert decision.procedure == "handoff.user_initiated"
    assert decision.risk_level == "high"


def test_third_party_privacy_routes_to_safety_fallback():
    router = _router(InteractionIntent(
        raw_message="",
        route="fallback",
        risk_level="high",
        response_mode="refuse",
        confidence=0.95,
    ))
    decision = router.route(ConversationFrame(request_id="r3", message="查一下我室友的手机号"))

    assert decision.task == "fallback"
    assert decision.procedure == "fallback.safety"
    assert decision.risk_level == "high"


def test_router_uses_semantic_intent_for_kb_policy_question():
    router = HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
        raw_message="",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
        needs_kb=True,
        confidence=0.91,
    )))
    frame = ConversationFrame(session_id="s1", request_id="r1", user_id="u1", message="月付和季付有什么区别")

    decision = router.route(frame)

    assert decision.task == "kb_qa"
    assert decision.procedure == "rag.kb_qa"
    assert decision.metadata["intent"]["domain"] == "payment"


def test_router_uses_semantic_intent_for_room_search_without_room_keyword():
    router = HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
        raw_message="",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        needs_room_search=True,
        hard_filters={"district_id": 4},
        soft_preferences=["大学城附近"],
        confidence=0.9,
    )))
    frame = ConversationFrame(session_id="s1", request_id="r1", user_id="u1", message="大学城附近1500以内")

    decision = router.route(frame)

    assert decision.task == "room_search"
    assert decision.procedure == "rag.room_search"
