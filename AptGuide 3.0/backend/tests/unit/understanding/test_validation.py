from aptguide3.domain.understanding import Clarification, RiskDecision, UnderstandingResult
from aptguide3.understanding.validation import validate_or_clarify, validation_failure_reason


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


def test_validation_failure_reason_low_confidence():
    result = UnderstandingResult(
        raw_message="找番禺1500以内安静一点的房子",
        route="rag",
        task="room_search",
        confidence=0.5,
    )

    assert validation_failure_reason(result, 0.65) == "low_confidence"


def test_validation_failure_reason_model_requested_clarification():
    result = UnderstandingResult(
        raw_message="我想租房",
        route="clarify",
        task="clarify",
        action="ask_clarification",
        confidence=0.8,
        risk=RiskDecision(response_mode="ask_clarification"),
        clarification=Clarification(needed=True, question="预算是多少？"),
        reason="missing_budget",
    )

    assert validation_failure_reason(result, 0.65) == "missing_budget"


def test_validation_failure_reason_invalid_hard_filters():
    result = UnderstandingResult(
        raw_message="找番禺1500以内安静一点的房子",
        route="rag",
        task="room_search",
        confidence=0.9,
        hard_filters={"max_rent": "1500"},
    )

    assert validation_failure_reason(result, 0.65) == "invalid_hard_filters"
