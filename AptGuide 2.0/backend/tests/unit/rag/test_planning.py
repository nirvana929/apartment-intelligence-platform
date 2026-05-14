from aptguide2.interaction.contracts import InteractionIntent
from aptguide2.rag.planning import build_retrieval_plan
from aptguide2.rag.query_understanding import understand_query


def _qr_from_intent(intent: InteractionIntent):
    return understand_query(intent.raw_message, interaction_intent=intent)


def test_room_plan_separates_hard_filters_from_semantic_queries():
    intent = InteractionIntent(
        raw_message="番禺1500以内别太吵，最好适合学习",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
        hard_filters={"district_id": 4, "max_rent": 1500},
        soft_preferences=["安静", "低噪音"],
        retrieval_queries=["番禺 1500以内 安静 房源"],
    )
    qr = _qr_from_intent(intent)
    plan = build_retrieval_plan(qr)

    assert plan.task == "room_search"
    assert plan.hard_filters["district_id"] == 4
    assert plan.hard_filters["max_rent"] == 1500
    assert plan.semantic_queries
    assert plan.validation_mode == "lease_required"


def test_kb_plan_uses_domain_for_module_intent():
    intent = InteractionIntent(
        raw_message="把押金退给我",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
        confidence=0.85,
        risk_level="high",
        response_mode="template_answer",
        retrieval_queries=["押金退还规则"],
    )
    qr = _qr_from_intent(intent)
    plan = build_retrieval_plan(qr)

    assert plan.task == "kb_qa"
    assert plan.risk_level == "high"
    assert plan.module_intent == "payment"
    assert "step_back" in plan.recall_channels
    assert plan.source_policy == "high_risk_source_required"


def test_kb_module_intent_uses_query_understanding_domain_not_message_keywords():
    from aptguide2.rag.schemas import QueryUnderstandingResult

    qr = QueryUnderstandingResult(
        raw_message="这个可以吗",
        task="kb_qa",
        domain="payment",
        retrieval_queries=["支付规则 支持方式"],
    )

    plan = build_retrieval_plan(qr)

    assert plan.task == "kb_qa"
    assert plan.module_intent == "payment"
    assert "支付规则 支持方式" in plan.semantic_queries


def test_fallback_plan_does_not_retrieve():
    intent = InteractionIntent(
        raw_message="帮我查其他租户手机号",
        route="fallback",
        rag_task="none",
        domain="unknown",
        action="clarify",
        confidence=0.0,
        risk_level="high",
        response_mode="refuse",
    )
    qr = _qr_from_intent(intent)
    plan = build_retrieval_plan(qr)

    assert plan.task == "fallback"
    assert plan.semantic_queries == []
    assert plan.recall_channels == []
