"""Tests for KB retrieval and confidence gate."""

from aptguide2.rag.confidence import check_confidence, get_fallback_message, THRESHOLDS
from aptguide2.rag.kb_retrieval import (
    _build_recall_queries,
    _build_step_back_query,
    _merge_by_chunk_id,
    _source_rerank,
)
from aptguide2.rag.schemas import KBSource, QueryUnderstandingResult


# ---------------------------------------------------------------------------
# Confidence gate
# ---------------------------------------------------------------------------

def test_confidence_low_pass():
    sources = [KBSource(
        chunk_id="KB-001#01", doc_id="KB-001", title="test",
        module="lease", content="test", score=0.50,
    )]
    assert check_confidence(sources, "low") is True


def test_confidence_low_fail():
    sources = [KBSource(
        chunk_id="KB-001#01", doc_id="KB-001", title="test",
        module="lease", content="test", score=0.30,
    )]
    assert check_confidence(sources, "low") is False


def test_confidence_medium_needs_module_match():
    sources = [KBSource(
        chunk_id="KB-001#01", doc_id="KB-001", title="test",
        module="life", content="test", score=0.60,
    )]
    # Score passes but no high-risk module
    assert check_confidence(sources, "medium") is False


def test_confidence_medium_pass_with_module():
    sources = [
        KBSource(chunk_id="KB-001#01", doc_id="KB-001", title="t",
                 module="life", content="c", score=0.60),
        KBSource(chunk_id="KB-002#01", doc_id="KB-002", title="t",
                 module="lease", content="c", score=0.58),
    ]
    assert check_confidence(sources, "medium") is True


def test_confidence_high_needs_high_risk_source():
    sources = [KBSource(
        chunk_id="KB-001#01", doc_id="KB-001", title="test",
        module="lease", content="test", score=0.70, risk_level="low",
    )]
    # Score passes but no high-risk source
    assert check_confidence(sources, "high") is False


def test_confidence_high_pass():
    sources = [KBSource(
        chunk_id="KB-001#01", doc_id="KB-001", title="test",
        module="lease", content="test", score=0.70, risk_level="high",
    )]
    assert check_confidence(sources, "high") is True


def test_confidence_empty_sources():
    assert check_confidence([], "low") is False


# ---------------------------------------------------------------------------
# Fallback messages
# ---------------------------------------------------------------------------

def test_fallback_message_high():
    msg = get_fallback_message("high")
    assert "门店" in msg or "合同" in msg


def test_fallback_message_medium():
    msg = get_fallback_message("medium")
    assert "门店" in msg


def test_fallback_message_low():
    msg = get_fallback_message("low")
    assert "抱歉" in msg or "找不到" in msg


# ---------------------------------------------------------------------------
# Recall queries
# ---------------------------------------------------------------------------

def test_build_recall_queries_room_search():
    qr = QueryUnderstandingResult(
        raw_message="找安静点的房子",
        task="room_search",
        soft_preferences=["安静", "低噪音"],
    )
    queries = _build_recall_queries(qr)
    assert len(queries) >= 2
    assert queries[0][1] == "original"


def test_build_recall_queries_kb_high_risk():
    qr = QueryUnderstandingResult(
        raw_message="押金退还多久到账",
        task="kb_qa",
        risk_level="high",
    )
    queries = _build_recall_queries(qr)
    sources = [q[1] for q in queries]
    assert "step_back" in sources


def test_step_back_query_deposit():
    result = _build_step_back_query("押金退还多久到账")
    assert result is not None
    assert "押金" in result


def test_step_back_query_none():
    result = _build_step_back_query("找安静的房子")
    assert result is None


# ---------------------------------------------------------------------------
# Merge by chunk_id
# ---------------------------------------------------------------------------

def test_merge_by_chunk_id_dedup():
    results = [
        {"chunk_id": "KB-001#01", "distance": 0.8, "_recall_source": "original", "_matched_query": "q1"},
        {"chunk_id": "KB-001#01", "distance": 0.9, "_recall_source": "normalized", "_matched_query": "q2"},
        {"chunk_id": "KB-002#01", "distance": 0.7, "_recall_source": "original", "_matched_query": "q1"},
    ]
    merged = _merge_by_chunk_id(results)
    assert len(merged) == 2
    # Best score preserved
    kb001 = next(r for r in merged if r["chunk_id"] == "KB-001#01")
    assert kb001["_best_score"] == 0.9


# ---------------------------------------------------------------------------
# Source rerank
# ---------------------------------------------------------------------------

def test_source_rerank_boosts_high_risk_module():
    qr = QueryUnderstandingResult(
        raw_message="押金退还",
        task="kb_qa",
        risk_level="high",
    )
    results = [
        {"chunk_id": "KB-001#01", "module": "life", "risk_level": "low", "_best_score": 0.7},
        {"chunk_id": "KB-002#01", "module": "lease", "risk_level": "high", "_best_score": 0.68},
    ]
    reranked = _source_rerank(results, qr)
    # lease module should be boosted above life
    assert reranked[0]["chunk_id"] == "KB-002#01"
