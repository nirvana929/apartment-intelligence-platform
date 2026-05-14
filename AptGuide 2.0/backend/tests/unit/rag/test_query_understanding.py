"""Tests for query understanding — now intent-only."""

from aptguide2.interaction.contracts import InteractionIntent
from aptguide2.rag.query_understanding import understand_query


# ---------------------------------------------------------------------------
# Intent-only behavior
# ---------------------------------------------------------------------------

def test_understand_query_requires_interaction_intent():
    result = understand_query("有阳台的房间吗", interaction_intent=None)

    assert result.task == "fallback"
    assert result.response_mode == "ask_clarification"


def test_understand_query_uses_llm_intent_filters_preferences_and_queries():
    intent = InteractionIntent(
        raw_message="珠江新城3000以内有阳台的房间",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.92,
        hard_filters={"district_id": 1, "area_text": "珠江新城", "max_rent": 3000},
        soft_preferences=["有阳台"],
        retrieval_queries=["珠江新城 3000以内 有阳台 房源"],
    )

    result = understand_query("珠江新城3000以内有阳台的房间", interaction_intent=intent)

    assert result.task == "room_search"
    assert result.domain == "room"
    assert result.hard_filters == {"district_id": 1, "area_text": "珠江新城", "max_rent": 3000}
    assert result.soft_preferences == ["有阳台"]
    assert result.retrieval_queries == ["珠江新城 3000以内 有阳台 房源"]


def test_understand_query_clarifies_non_rag_intent():
    intent = InteractionIntent(
        raw_message="查看我的合同",
        route="lease",
        rag_task="none",
        domain="lease",
        action="list",
        confidence=0.9,
    )

    result = understand_query("查看我的合同", interaction_intent=intent)

    assert result.task == "fallback"
    assert result.response_mode == "ask_clarification"


# ---------------------------------------------------------------------------
# Interaction intent passthrough
# ---------------------------------------------------------------------------

def test_understand_query_uses_provided_interaction_intent_task():
    intent = InteractionIntent(
        raw_message="月付和季付有什么区别",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
        hard_filters={"payment_type": "MONTHLY"},
        confidence=0.9,
    )

    result = understand_query("月付和季付有什么区别", interaction_intent=intent)

    assert result.task == "kb_qa"
    assert result.domain == "payment"
    assert result.hard_filters["payment_type"] == "MONTHLY"


def test_understand_query_room_search_with_full_intent():
    intent = InteractionIntent(
        raw_message="找大学城南亭附近1500以内安静点的房子",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.92,
        hard_filters={"district_id": 4, "area_text": "大学城南亭", "max_rent": 1500},
        soft_preferences=["安静", "低噪音"],
        retrieval_queries=["大学城南亭附近 1500以内 安静 低噪音 房源"],
    )

    result = understand_query("找大学城南亭附近1500以内安静点的房子", interaction_intent=intent)

    assert result.task == "room_search"
    assert result.domain == "room"
    assert result.hard_filters.get("max_rent") == 1500
    assert result.hard_filters.get("area_text") == "大学城南亭"
    assert "安静" in result.soft_preferences


def test_understand_query_kb_with_risk():
    intent = InteractionIntent(
        raw_message="押金退还多久到账",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
        confidence=0.88,
        risk_level="medium",
        response_mode="kb_grounded_answer",
    )

    result = understand_query("押金退还多久到账", interaction_intent=intent)

    assert result.task == "kb_qa"
    assert result.risk_level == "medium"
    assert result.response_mode == "kb_grounded_answer"
