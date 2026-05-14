"""RAG pipeline orchestrator.

Wires: query understanding → retrieval → ranking → response.
Handles all 3 task paths: room_search, kb_qa, fallback.
"""

from __future__ import annotations

from typing import Any

from aptguide2.rag.confidence import get_fallback_message
from aptguide2.rag.kb_retrieval import retrieve_kb
from aptguide2.rag.query_understanding import understand_query
from aptguide2.rag.ranking import rank_rooms
from aptguide2.rag.room_retrieval import enrich_candidates_from_vector, retrieve_rooms
from aptguide2.rag.schemas import PipelineResult, QueryUnderstandingResult
from aptguide2.tools.vector_adapter import VectorAdapter


def run_pipeline(
    message: str,
    vector_adapter: VectorAdapter,
    embed_fn,
    previous_state: dict[str, Any] | None = None,
    top_n_rooms: int = 5,
) -> PipelineResult:
    """Execute the full RAG pipeline.

    Args:
        message: User's raw message.
        vector_adapter: Milvus vector adapter.
        embed_fn: Function to embed text -> list[float].
        previous_state: Previous conversation state for multi-turn.
        top_n_rooms: Number of top rooms to return.

    Returns:
        PipelineResult with task-specific data.
    """
    # 1. Query understanding — deterministic, no LLM
    qr = understand_query(message, previous_state)

    # 2. Route to task-specific retrieval
    if qr.task == "room_search":
        return _handle_room_search(qr, vector_adapter, embed_fn, top_n_rooms)
    elif qr.task == "kb_qa":
        return _handle_kb_qa(qr, vector_adapter, embed_fn)
    else:
        return _handle_fallback(qr)


def _handle_room_search(
    qr: QueryUnderstandingResult,
    vector_adapter: VectorAdapter,
    embed_fn,
    top_n: int,
) -> PipelineResult:
    """Handle room search task: retrieve → enrich → rank."""
    # Multi-channel vector recall
    candidates = retrieve_rooms(qr, vector_adapter, embed_fn)

    if not candidates:
        return PipelineResult(
            task="room_search",
            message="抱歉，没有找到符合条件的房源。您可以尝试放宽预算或区域条件。",
            query_understanding=qr,
        )

    # Enrich with full vector record data for ranking
    enriched = enrich_candidates_from_vector(candidates, vector_adapter)

    # Multi-dimensional ranking
    ranked = rank_rooms(enriched, qr, top_n=top_n)

    return PipelineResult(
        task="room_search",
        rooms=ranked,
        query_understanding=qr,
    )


def _handle_kb_qa(
    qr: QueryUnderstandingResult,
    vector_adapter: VectorAdapter,
    embed_fn,
) -> PipelineResult:
    """Handle KB QA task: retrieve → confidence check."""
    sources, is_confident = retrieve_kb(qr, vector_adapter, embed_fn)

    if not is_confident:
        fallback_msg = get_fallback_message(qr.risk_level)
        return PipelineResult(
            task="kb_qa",
            message=fallback_msg,
            kb_sources=sources,
            is_confident=False,
            fallback_reason="confidence_gate_blocked",
            query_understanding=qr,
        )

    return PipelineResult(
        task="kb_qa",
        kb_sources=sources,
        is_confident=True,
        query_understanding=qr,
    )


def _handle_fallback(qr: QueryUnderstandingResult) -> PipelineResult:
    """Handle fallback task: return safe default message."""
    return PipelineResult(
        task="fallback",
        message="抱歉，这个问题超出了我的服务范围。我是租房助手，可以帮您找房或回答租房相关问题。",
        fallback_reason="out_of_scope",
        query_understanding=qr,
    )
