"""Tests for retrieval trace events."""

import pytest

from aptguide2.rag.schemas import RetrievalLatency, RetrievalTracePayload
from aptguide2.trace.retrieval_events import (
    TracePIIError,
    build_retrieval_finished_event,
    build_tool_trace_event,
    validate_no_pii,
)


# ---------------------------------------------------------------------------
# PII validation
# ---------------------------------------------------------------------------

def test_validate_no_pii_clean():
    """Clean data should pass."""
    validate_no_pii({"district_id": 1005, "max_rent": 1800})


def test_validate_no_pii_phone():
    """Phone key should be rejected."""
    with pytest.raises(TracePIIError, match="phone"):
        validate_no_pii({"phone": "13800138000"})


def test_validate_no_pii_id_card():
    """id_card key should be rejected."""
    with pytest.raises(TracePIIError, match="id_card"):
        validate_no_pii({"id_card": "440100200001011234"})


def test_validate_no_pii_contract_no():
    """contract_no key should be rejected."""
    with pytest.raises(TracePIIError, match="contract_no"):
        validate_no_pii({"contract_no": "C-001"})


def test_validate_no_pii_nested():
    """PII in nested dict should be rejected."""
    with pytest.raises(TracePIIError, match="bank_card"):
        validate_no_pii({"user": {"bank_card": "6222000000000000"}})


def test_validate_no_pii_in_list():
    """PII in list of dicts should be rejected."""
    with pytest.raises(TracePIIError, match="address_detail"):
        validate_no_pii({"items": [{"address_detail": "某路某号"}]})


def test_validate_no_pii_case_insensitive():
    """PII check should be case insensitive."""
    with pytest.raises(TracePIIError):
        validate_no_pii({"Phone": "13800138000"})


# ---------------------------------------------------------------------------
# Build retrieval finished event
# ---------------------------------------------------------------------------

def test_build_retrieval_finished_event():
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
    event = build_retrieval_finished_event(payload, trace_id="t-001")

    assert event["event"] == "retrieval_finished"
    assert event["trace_id"] == "t-001"
    assert event["payload"]["task"] == "room_search"
    assert event["payload"]["candidate_count"] == 42
    assert event["payload"]["latency"]["retrieval_total_latency_ms"] == 256


def test_build_retrieval_finished_auto_trace_id():
    payload = RetrievalTracePayload(task="kb_qa")
    event = build_retrieval_finished_event(payload)
    assert event["trace_id"].startswith("trace-")


def test_build_retrieval_finished_rejects_pii():
    payload = RetrievalTracePayload(
        task="room_search",
        filters={"phone": "13800138000"},
    )
    with pytest.raises(TracePIIError):
        build_retrieval_finished_event(payload)


# ---------------------------------------------------------------------------
# Build tool trace event
# ---------------------------------------------------------------------------

def test_build_tool_trace_event():
    event = build_tool_trace_event(
        tool_name="room.search",
        backend="lease",
        latency_ms=120,
        ok=True,
        result_count=5,
        trace_id="t-002",
    )
    assert event["event"] == "tool_call"
    assert event["payload"]["tool_name"] == "room.search"
    assert event["payload"]["ok"] is True
    assert event["payload"]["result_count"] == 5


def test_build_tool_trace_event_error():
    event = build_tool_trace_event(
        tool_name="room.search",
        backend="lease",
        latency_ms=5000,
        ok=False,
        error_code="TOOL_TIMEOUT",
    )
    assert event["payload"]["ok"] is False
    assert event["payload"]["error_code"] == "TOOL_TIMEOUT"
