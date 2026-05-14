import pytest
from pydantic import ValidationError

from aptguide3.domain.understanding import (
    Clarification,
    RiskDecision,
    UnderstandingResult,
)


def test_valid_room_search_understanding_contract():
    result = UnderstandingResult(
        raw_message="珠江新城3000以内有阳台的房间",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.91,
        hard_filters={"max_rent": 3000, "district_id": 1, "area_text": "珠江新城"},
        soft_preferences=["有阳台"],
        retrieval_queries=["珠江新城 3000以内 有阳台 房源"],
        risk=RiskDecision(level="low", response_mode="normal_answer"),
        clarification=Clarification(needed=False, question=""),
    )

    assert result.route == "rag"
    assert result.task == "room_search"
    assert result.hard_filters["max_rent"] == 3000
    assert result.retrieval_queries == ["珠江新城 3000以内 有阳台 房源"]


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        UnderstandingResult(
            raw_message="x",
            route="rag",
            task="kb_qa",
            domain="policy",
            action="ask_policy",
            confidence=1.2,
        )
