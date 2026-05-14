from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.understanding.validation import validate_or_clarify


def test_low_confidence_becomes_clarification():
    result = UnderstandingResult(
        raw_message="这个可以吗",
        route="rag",
        task="kb_qa",
        domain="policy",
        action="ask_policy",
        confidence=0.2,
    )

    validated = validate_or_clarify(result, min_confidence=0.65)

    assert validated.route == "clarify"
    assert validated.task == "clarify"
    assert validated.action == "ask_clarification"
    assert validated.clarification.needed is True


def test_invalid_rag_task_shape_becomes_clarification():
    result = UnderstandingResult(
        raw_message="有阳台的房间吗",
        route="rag",
        task="fallback",
        domain="room",
        action="search",
        confidence=0.9,
    )

    validated = validate_or_clarify(result, min_confidence=0.65)

    assert validated.route == "clarify"
    assert validated.task == "clarify"


def test_invalid_hard_filter_type_becomes_clarification():
    result = UnderstandingResult(
        raw_message="3000以内",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
        hard_filters={"max_rent": "三千"},
    )

    validated = validate_or_clarify(result, min_confidence=0.65)

    assert validated.route == "clarify"
    assert validated.clarification.needed is True


def test_valid_understanding_passes_through():
    result = UnderstandingResult(
        raw_message="3000以内有阳台的房间",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
        hard_filters={"max_rent": 3000},
        soft_preferences=["有阳台"],
        retrieval_queries=["3000以内 有阳台 房源"],
    )

    validated = validate_or_clarify(result, min_confidence=0.65)

    assert validated.route == "rag"
    assert validated.task == "room_search"
