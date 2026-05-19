from aptguide3.domain.understanding import RiskDecision, UnderstandingResult
from aptguide3.rag.planning import build_retrieval_plan


def test_room_search_plan_uses_llm_understanding_fields():
    understanding = UnderstandingResult(
        raw_message="找番禺1500以内安静的房子",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.92,
        hard_filters={"district_name": "番禺区", "max_rent": 1500},
        soft_preferences=["安静", "低噪音"],
        retrieval_queries=["番禺 1500以内 安静 房源", "低噪音 适合学习 公寓"],
        risk=RiskDecision(level="low", response_mode="normal_answer"),
    )

    plan = build_retrieval_plan(understanding)

    assert plan.task == "room_search"
    assert plan.hard_filters["max_rent"] == 1500
    assert plan.soft_preferences == ["安静", "低噪音"]
    assert plan.semantic_queries[0] == "找番禺1500以内安静的房子"
    assert "番禺 1500以内 安静 房源" in plan.semantic_queries
    assert plan.validation_mode == "lease_required"


def test_high_risk_kb_plan_requires_high_risk_sources():
    understanding = UnderstandingResult(
        raw_message="押金不退怎么办",
        route="rag",
        task="kb_qa",
        domain="lease",
        action="ask_policy",
        confidence=0.9,
        retrieval_queries=["押金退还规则", "押金扣除和退租流程"],
        risk=RiskDecision(level="high", response_mode="kb_grounded_answer"),
    )

    plan = build_retrieval_plan(understanding)

    assert plan.task == "kb_qa"
    assert plan.module_intent == "lease"
    assert plan.risk_level == "high"
    assert plan.source_policy == "high_risk_source_required"


def test_non_rag_route_returns_fallback():
    understanding = UnderstandingResult(
        raw_message="你好",
        route="clarify",
        task="clarify",
    )
    plan = build_retrieval_plan(understanding)
    assert plan.task == "fallback"


def test_step_back_query_for_lease_domain():
    understanding = UnderstandingResult(
        raw_message="押金怎么退",
        route="rag",
        task="kb_qa",
        domain="lease",
        retrieval_queries=["押金退还"],
    )
    plan = build_retrieval_plan(understanding)
    assert any("租赁合同" in q or "押金" in q for q in plan.semantic_queries)
