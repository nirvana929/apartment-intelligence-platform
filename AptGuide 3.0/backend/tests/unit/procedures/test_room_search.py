from __future__ import annotations

from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.room_search import RoomSearchProcedure
from aptguide3.rag.schemas import PreferenceScore, RankedRoom


class StubLeaseClient:
    def __init__(self, rooms: list[dict[str, Any]] | None = None, fail: bool = False):
        self._rooms = rooms or []
        self._fail = fail
        self.calls: list[tuple[list[int], dict]] = []

    async def validate_rooms(self, room_ids: list[int], filters: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append((room_ids, filters))
        if self._fail:
            raise ConnectionError("lease unavailable")
        return self._rooms


class StubVectorClient:
    def __init__(self, hits: list[dict[str, Any]] | None = None):
        self._hits = hits or []

    def search_rooms(
        self, vector: list[float], filters: dict[str, Any] | None = None, top_k: int = 50,
    ) -> list[dict[str, Any]]:
        return self._hits


class StubEmbeddingClient:
    def embed(self, text: str) -> list[float]:
        return [0.1] * 8


class StubScorer:
    def score(self, raw_message: str, soft_preferences: list[str], rooms: list) -> dict[int, PreferenceScore]:
        return {room.room_id: PreferenceScore(room_id=room.room_id, score=0.5) for room in rooms}


def _frame() -> ConversationFrame:
    return ConversationFrame(message="找房", session_id="s-1")


def _understanding(**overrides: Any) -> UnderstandingResult:
    defaults = dict(
        raw_message="找房",
        route="rag",
        task="room_search",
        domain="room",
        action="search",
        confidence=0.9,
        hard_filters={},
        soft_preferences=[],
    )
    defaults.update(overrides)
    return UnderstandingResult(**defaults)


def test_conservative_fallback_when_deps_missing():
    proc = RoomSearchProcedure()
    result = proc.run(_frame(), _understanding())
    assert result.phase == "room_search"
    assert result.cards == []
    assert "找房需求" in result.message


def test_conservative_fallback_when_only_lease_client():
    proc = RoomSearchProcedure(lease_client=StubLeaseClient())
    result = proc.run(_frame(), _understanding())
    assert result.phase == "room_search"
    assert result.cards == []
    assert "找房需求" in result.message


def test_successful_retrieval_with_mocked_deps():
    from unittest.mock import MagicMock

    ranked = [
        RankedRoom(
            room_id=1, apartment_id=10, apartment_name="天河公寓", room_number="101",
            district_name="天河区", rent=1500, payment_types=["月付"], tags=["近地铁"],
            facilities=["空调"], is_appointable=True, final_score=0.85,
            semantic_score=0.9, budget_score=0.75, area_score=1.0,
            preference_score=0.8, availability_score=1.0,
            matched_query="天河租房", recommendation_reason="偏好匹配",
        ),
    ]

    mock_retrieval = MagicMock(return_value=ranked)

    proc = RoomSearchProcedure(
        lease_client=StubLeaseClient(),
        vector_client=StubVectorClient(),
        embedding_client=StubEmbeddingClient(),
        preference_scorer=StubScorer(),
    )

    import aptguide3.rag.room_retrieval as retrieval_mod
    original_retrieval = retrieval_mod.retrieve_ranked_rooms

    try:
        retrieval_mod.retrieve_ranked_rooms = mock_retrieval
        result = proc.run(_frame(), _understanding(hard_filters={"max_rent": 2000}))

        assert result.phase == "room_search"
        assert len(result.cards) == 1
        assert result.cards[0]["type"] == "room_card"
        assert result.cards[0]["room_id"] == 1
        assert result.cards[0]["apartment_name"] == "天河公寓"
        assert result.metadata["room_count"] == 1
    finally:
        retrieval_mod.retrieve_ranked_rooms = original_retrieval


def test_empty_retrieval_returns_no_results_message():
    from unittest.mock import MagicMock

    proc = RoomSearchProcedure(
        lease_client=StubLeaseClient(),
        vector_client=StubVectorClient(),
        embedding_client=StubEmbeddingClient(),
        preference_scorer=StubScorer(),
    )

    import aptguide3.rag.room_retrieval as retrieval_mod
    original = retrieval_mod.retrieve_ranked_rooms

    try:
        retrieval_mod.retrieve_ranked_rooms = MagicMock(return_value=[])
        result = proc.run(_frame(), _understanding())

        assert result.phase == "room_search"
        assert result.cards == []
        assert "暂未找到" in result.message
        assert result.metadata["room_count"] == 0
    finally:
        retrieval_mod.retrieve_ranked_rooms = original


def test_conservative_fallback_includes_filters_in_metadata():
    proc = RoomSearchProcedure()
    result = proc.run(
        _frame(),
        _understanding(hard_filters={"max_rent": 2000}, soft_preferences=["安静"]),
    )
    assert result.metadata["hard_filters"]["max_rent"] == 2000
    assert result.metadata["soft_preferences"] == ["安静"]


def test_medium_risk_room_search_disclaimer_without_lease_validation():
    """Medium-risk room search with vector_only cards must include disclaimer."""
    from unittest.mock import MagicMock

    from aptguide3.domain.understanding import RiskDecision

    ranked = [
        RankedRoom(
            room_id=1, apartment_id=10, apartment_name="天河公寓", room_number="101",
            district_name="天河区", rent=1500, payment_types=["月付"], tags=["近地铁"],
            facilities=["空调"], is_appointable=True, final_score=0.85,
            semantic_score=0.9, budget_score=0.75, area_score=1.0,
            preference_score=0.8, availability_score=1.0,
            matched_query="天河租房", recommendation_reason="偏好匹配",
        ),
    ]

    proc = RoomSearchProcedure(
        lease_client=StubLeaseClient(),
        vector_client=StubVectorClient(),
        embedding_client=StubEmbeddingClient(),
        preference_scorer=StubScorer(),
    )

    import aptguide3.rag.room_retrieval as retrieval_mod
    original_retrieval = retrieval_mod.retrieve_ranked_rooms

    try:
        retrieval_mod.retrieve_ranked_rooms = MagicMock(return_value=ranked)
        medium_understanding = _understanding(
            risk=RiskDecision(level="medium", response_mode="normal_answer"),
        )
        result = proc.run(_frame(), medium_understanding)

        assert result.phase == "room_search"
        assert len(result.cards) == 1
        # Without evidence_level/lease_validation_status on cards,
        # medium risk should produce disclaimer
        assert "尚未通过租赁系统验证" in result.message
        assert result.metadata.get("risk_level") == "medium"
    finally:
        retrieval_mod.retrieve_ranked_rooms = original_retrieval


def test_low_risk_room_search_no_disclaimer():
    """Low-risk room search should not add disclaimer even without lease validation."""
    from unittest.mock import MagicMock

    ranked = [
        RankedRoom(
            room_id=1, apartment_id=10, apartment_name="天河公寓", room_number="101",
            district_name="天河区", rent=1500, payment_types=["月付"], tags=["近地铁"],
            facilities=["空调"], is_appointable=True, final_score=0.85,
            semantic_score=0.9, budget_score=0.75, area_score=1.0,
            preference_score=0.8, availability_score=1.0,
            matched_query="天河租房", recommendation_reason="偏好匹配",
        ),
    ]

    proc = RoomSearchProcedure(
        lease_client=StubLeaseClient(),
        vector_client=StubVectorClient(),
        embedding_client=StubEmbeddingClient(),
        preference_scorer=StubScorer(),
    )

    import aptguide3.rag.room_retrieval as retrieval_mod
    original_retrieval = retrieval_mod.retrieve_ranked_rooms

    try:
        retrieval_mod.retrieve_ranked_rooms = MagicMock(return_value=ranked)
        result = proc.run(_frame(), _understanding())

        assert result.phase == "room_search"
        assert "找到 1 间符合条件的房源" in result.message
        assert "尚未通过" not in result.message
        assert result.metadata.get("risk_level") == "low"
    finally:
        retrieval_mod.retrieve_ranked_rooms = original_retrieval


def test_room_cards_carry_evidence_fields():
    """Room cards must include evidence fields from the evidence contract."""
    from unittest.mock import MagicMock

    ranked = [
        RankedRoom(
            room_id=1, apartment_id=10, apartment_name="天河公寓", room_number="101",
            district_name="天河区", rent=1500, payment_types=["月付"], tags=["近地铁"],
            facilities=["空调"], is_appointable=True, final_score=0.85,
            semantic_score=0.9, budget_score=0.75, area_score=1.0,
            preference_score=0.8, availability_score=1.0,
            matched_query="天河租房", recommendation_reason="偏好匹配",
            wechat_room_id="wx_123", lease_room_id=None,
            source_collection="wechat_room_index", source_record_id="wx_123",
            lease_validation_status="not_checked", evidence_level="vector_only",
        ),
    ]

    proc = RoomSearchProcedure(
        lease_client=StubLeaseClient(),
        vector_client=StubVectorClient(),
        embedding_client=StubEmbeddingClient(),
        preference_scorer=StubScorer(),
    )

    import aptguide3.rag.room_retrieval as retrieval_mod
    original_retrieval = retrieval_mod.retrieve_ranked_rooms

    try:
        retrieval_mod.retrieve_ranked_rooms = MagicMock(return_value=ranked)
        result = proc.run(_frame(), _understanding())

        assert len(result.cards) == 1
        card = result.cards[0]
        assert card["wechat_room_id"] == "wx_123"
        assert card["lease_room_id"] is None
        assert card["source_collection"] == "wechat_room_index"
        assert card["source_record_id"] == "wx_123"
        assert card["lease_validation_status"] == "not_checked"
        assert card["evidence_level"] == "vector_only"
        assert card["matched_query"] == "天河租房"
        assert card["semantic_score"] == 0.9
        assert "availability_status" in card
    finally:
        retrieval_mod.retrieve_ranked_rooms = original_retrieval


def test_room_card_lease_validated_status_text():
    """Room card with lease_validation_status=passed shows verified text."""
    from unittest.mock import MagicMock

    ranked = [
        RankedRoom(
            room_id=1, apartment_id=10, apartment_name="天河公寓", room_number="101",
            district_name="天河区", rent=1500, payment_types=["月付"], tags=["近地铁"],
            facilities=["空调"], is_appointable=True, final_score=0.85,
            semantic_score=0.9, budget_score=0.75, area_score=1.0,
            preference_score=0.8, availability_score=1.0,
            matched_query="天河租房", recommendation_reason="偏好匹配",
            wechat_room_id="wx_123", lease_room_id=100,
            source_collection="wechat_room_index", source_record_id="wx_123",
            lease_validation_status="passed", evidence_level="lease_validated",
        ),
    ]

    proc = RoomSearchProcedure(
        lease_client=StubLeaseClient(),
        vector_client=StubVectorClient(),
        embedding_client=StubEmbeddingClient(),
        preference_scorer=StubScorer(),
    )

    import aptguide3.rag.room_retrieval as retrieval_mod
    original_retrieval = retrieval_mod.retrieve_ranked_rooms

    try:
        retrieval_mod.retrieve_ranked_rooms = MagicMock(return_value=ranked)
        result = proc.run(_frame(), _understanding())

        card = result.cards[0]
        assert card["lease_validation_status"] == "passed"
        assert card["availability_status"] == "已验证可租"
    finally:
        retrieval_mod.retrieve_ranked_rooms = original_retrieval
