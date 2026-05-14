from aptguide2.rag.planning import build_retrieval_plan
from aptguide2.rag.query_understanding import understand_query


def test_room_plan_separates_hard_filters_from_semantic_queries():
    qr = understand_query("番禺1500以内别太吵，最好适合学习")

    plan = build_retrieval_plan(qr)

    assert plan.task == "room_search"
    assert plan.hard_filters["district_id"] == 4
    assert plan.hard_filters["max_rent"] == 1500
    assert plan.semantic_queries
    assert any("安静" in q or "低噪音" in q for q in plan.semantic_queries)
    assert plan.validation_mode == "lease_required"


def test_kb_plan_adds_step_back_for_high_risk_policy_question():
    qr = understand_query("提前退租会扣多少钱")

    plan = build_retrieval_plan(qr)

    assert plan.task == "kb_qa"
    assert plan.risk_level == "high"
    assert plan.module_intent in {"lease", "payment"}
    assert "step_back" in plan.recall_channels
    assert plan.source_policy == "high_risk_source_required"


def test_fallback_plan_does_not_retrieve():
    qr = understand_query("帮我查其他租户手机号")

    plan = build_retrieval_plan(qr)

    assert plan.task == "fallback"
    assert plan.semantic_queries == []
    assert plan.recall_channels == []
