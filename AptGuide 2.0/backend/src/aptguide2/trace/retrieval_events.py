"""Retrieval trace events for AptGuide 2.0 RAG layer."""

from __future__ import annotations

import time
import uuid
from typing import Any

from aptguide2.rag.schemas import RetrievalTracePayload

# PII keys that must never appear in trace payloads
PII_KEYS = frozenset({
    "phone",
    "id_card",
    "contract_no",
    "address_detail",
    "bank_card",
    "email",
    "real_name",
    "id_number",
    "passport",
    "payment_account",
})


class TracePIIError(Exception):
    """Raised when PII is detected in a trace payload."""
    pass


def validate_no_pii(data: dict[str, Any]) -> None:
    """Recursively check that no PII keys appear in the data.

    Raises TracePIIError if PII is found.
    """
    if isinstance(data, dict):
        for key in data:
            if key.lower() in PII_KEYS:
                raise TracePIIError(f"PII key '{key}' must not appear in trace")
            validate_no_pii(data[key])
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                validate_no_pii(item)


def build_retrieval_finished_event(
    payload: RetrievalTracePayload,
    trace_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Build a retrieval_finished trace event.

    Validates that the payload contains no PII keys.

    Args:
        payload: The retrieval trace payload.
        trace_id: Optional trace ID; generated if not provided.
        session_id: Optional session ID.

    Returns:
        Complete trace event dict.

    Raises:
        TracePIIError if PII is detected in filters or payload.
    """
    # Validate no PII in filters
    validate_no_pii(payload.filters)

    event = {
        "event": "retrieval_finished",
        "trace_id": trace_id or f"trace-{uuid.uuid4().hex[:12]}",
        "session_id": session_id,
        "timestamp": int(time.time() * 1000),
        "payload": {
            "task": payload.task,
            "rewrite_count": payload.rewrite_count,
            "collections": payload.collections,
            "top_k": payload.top_k,
            "filters": payload.filters,
            "candidate_count": payload.candidate_count,
            "validated_count": payload.validated_count,
            "latency": {
                "rewrite_latency_ms": payload.latency.rewrite_latency_ms,
                "embedding_latency_ms": payload.latency.embedding_latency_ms,
                "vector_search_latency_ms": payload.latency.vector_search_latency_ms,
                "merge_latency_ms": payload.latency.merge_latency_ms,
                "lease_validation_latency_ms": payload.latency.lease_validation_latency_ms,
                "rerank_latency_ms": payload.latency.rerank_latency_ms,
                "retrieval_total_latency_ms": payload.latency.retrieval_total_latency_ms,
            },
        },
    }

    return event


def build_tool_trace_event(
    tool_name: str,
    backend: str,
    latency_ms: float,
    ok: bool,
    error_code: str | None = None,
    result_count: int | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Build a tool call trace event."""
    return {
        "event": "tool_call",
        "trace_id": trace_id or f"trace-{uuid.uuid4().hex[:12]}",
        "timestamp": int(time.time() * 1000),
        "payload": {
            "tool_name": tool_name,
            "backend": backend,
            "latency_ms": latency_ms,
            "ok": ok,
            "error_code": error_code,
            "result_count": result_count,
        },
    }
