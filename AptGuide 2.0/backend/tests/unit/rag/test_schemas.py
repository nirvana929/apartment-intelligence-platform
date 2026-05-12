"""Tests for RAG schemas."""

from aptguide2.rag.schemas import (
    KBChunk,
    KBSource,
    QueryUnderstandingResult,
    RankedRoom,
    RetrievalEvalCase,
    RetrievalLatency,
    RetrievalTracePayload,
    RoomCandidate,
    RoomVectorRecord,
    ValidatedRoom,
)


def test_query_understanding_defaults_to_empty_lists():
    result = QueryUnderstandingResult(raw_message="找安静点的房子", task="room_search")
    assert result.soft_preferences == []
    assert result.retrieval_queries == []
    assert result.risk_level == "low"
    assert result.reference_resolution is None


def test_query_understanding_with_filters():
    result = QueryUnderstandingResult(
        raw_message="天河区3000以内可月付",
        task="room_search",
        hard_filters={"district": "天河区", "max_rent": 3000},
        soft_preferences=["可月付"],
        retrieval_queries=["天河区 可月付 房源"],
    )
    assert result.hard_filters["max_rent"] == 3000
    assert "可月付" in result.soft_preferences


def test_room_vector_record_defaults():
    record = RoomVectorRecord(
        vector_id="room-3001",
        room_id=3001,
        apartment_id=2001,
        content="test content",
        content_hash="sha256:abc",
        source_version=1,
    )
    assert record.status == "active"
    assert record.profile_type == "room"
    assert record.payment_types == []
    assert record.tags == []


def test_kb_chunk_requires_source_fields():
    chunk = KBChunk(
        chunk_id="KB-LEASE-005#01",
        doc_id="KB-LEASE-005",
        doc_type="rule",
        module="lease",
        title="押金退还规则",
        tags=["押金"],
        content="押金退还以验房和费用结清为前提。",
        content_hash="sha256:test",
        version=1,
        release_id="20260511-001",
        status="active",
        risk_level="high",
    )
    assert chunk.doc_id == "KB-LEASE-005"
    assert chunk.risk_level == "high"
    assert chunk.status == "active"


def test_kb_chunk_status_values():
    for status in ("candidate", "reviewed", "indexed", "evaluated", "active", "inactive"):
        chunk = KBChunk(
            chunk_id="KB-001#01",
            doc_id="KB-001",
            doc_type="faq",
            module="lease",
            title="test",
            content="test",
            content_hash="sha256:x",
            version=1,
            release_id="r1",
            status=status,
        )
        assert chunk.status == status


def test_room_candidate():
    c = RoomCandidate(room_id=3001, semantic_score=0.85, matched_query="安静房子")
    assert c.recall_source == "vector"
    assert c.semantic_score == 0.85


def test_validated_room():
    r = ValidatedRoom(room_id=3001, apartment_id=2001, rent=1800, is_appointable=True)
    assert r.is_appointable is True


def test_ranked_room_scores():
    r = RankedRoom(
        room_id=3001,
        apartment_id=2001,
        final_score=0.82,
        semantic_score=0.9,
        budget_score=1.0,
        area_score=0.8,
        tag_score=0.7,
        availability_score=1.0,
    )
    assert r.final_score == 0.82


def test_kb_source():
    s = KBSource(
        chunk_id="KB-LEASE-005#01",
        doc_id="KB-LEASE-005",
        title="押金退还规则",
        module="lease",
        content="押金退还以验房为前提",
        score=0.82,
        risk_level="high",
    )
    assert s.score == 0.82
    assert s.recall_source == "original"


def test_retrieval_trace_payload():
    payload = RetrievalTracePayload(
        task="room_search",
        rewrite_count=3,
        collections=["apt_room_vector"],
        top_k=50,
        filters={"district_id": 1005, "max_rent": 1800},
        candidate_count=42,
        validated_count=5,
        latency=RetrievalLatency(
            rewrite_latency_ms=10,
            embedding_latency_ms=80,
            vector_search_latency_ms=25,
            merge_latency_ms=3,
            lease_validation_latency_ms=130,
            rerank_latency_ms=8,
            retrieval_total_latency_ms=256,
        ),
    )
    assert payload.latency.retrieval_total_latency_ms == 256
    assert payload.collections == ["apt_room_vector"]


def test_retrieval_eval_case():
    case = RetrievalEvalCase(
        case_id="room-001",
        case_type="room_retrieval",
        query="找大学城南亭附近1500以内安静点的",
        expected_room_ids=[3001, 3002],
        expected_task="room_search",
    )
    assert case.case_type == "room_retrieval"
    assert 3001 in case.expected_room_ids
