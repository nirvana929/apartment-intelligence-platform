from aptguide2.interaction.contracts import InteractionIntent
from aptguide2.interaction.validation import validate_or_clarify_intent


def test_low_confidence_intent_becomes_clarification():
    intent = InteractionIntent(
        raw_message="这个可以吗",
        route="rag",
        rag_task="kb_qa",
        domain="policy",
        action="ask_policy",
        confidence=0.31,
    )

    result = validate_or_clarify_intent(intent, min_confidence=0.65)

    assert result.route == "fallback"
    assert result.action == "clarify"
    assert result.response_mode == "ask_clarification"
    assert result.clarification_needed is True
    assert "请补充" in result.clarification_question


def test_contradictory_rag_intent_becomes_clarification():
    intent = InteractionIntent(
        raw_message="有阳台的房间吗",
        route="rag",
        rag_task="none",
        domain="room",
        action="search",
        confidence=0.9,
    )

    result = validate_or_clarify_intent(intent, min_confidence=0.65)

    assert result.route == "fallback"
    assert result.action == "clarify"
    assert result.response_mode == "ask_clarification"


def test_valid_room_intent_passes_through_without_keyword_inference():
    intent = InteractionIntent(
        raw_message="有阳台的房间吗",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.92,
        needs_room_search=True,
        hard_filters={"max_rent": 3000, "district_id": 1, "area_text": "珠江新城"},
        soft_preferences=["有阳台"],
        retrieval_queries=["珠江新城 3000以内 有阳台 房源"],
    )

    result = validate_or_clarify_intent(intent, min_confidence=0.65)

    assert result.route == "rag"
    assert result.rag_task == "room_search"
    assert result.hard_filters["max_rent"] == 3000
    assert result.retrieval_queries == ["珠江新城 3000以内 有阳台 房源"]


def test_invalid_filter_type_becomes_clarification():
    intent = InteractionIntent(
        raw_message="珠江新城3000以内",
        route="rag",
        rag_task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
        hard_filters={"max_rent": "三千以内"},
    )

    result = validate_or_clarify_intent(intent, min_confidence=0.65)

    assert result.route == "fallback"
    assert result.action == "clarify"
