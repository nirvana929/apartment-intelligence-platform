"""Room retrieval v2 — plan-driven retrieval with lease validation and ranking.

Replaces the old ``room_retrieval.retrieve_rooms`` with a flow that:
1. Accepts a ``RetrievalPlan`` (not raw query result).
2. Embeds and searches each semantic query via the vector adapter.
3. Deduplicates candidates, keeping the best semantic score per room.
4. Validates candidates through the lease validator.
5. Ranks validated rooms with multi-dimensional scoring.
"""

from __future__ import annotations

from typing import Any

from aptguide2.rag.planning import RetrievalPlan
from aptguide2.rag.ranking import rank_rooms
from aptguide2.rag.schemas import QueryUnderstandingResult, RankedRoom, RoomCandidate
from aptguide2.rag.validation import validate_room_candidates


def retrieve_ranked_rooms_v2(
    plan: RetrievalPlan,
    query_result: QueryUnderstandingResult,
    vector_adapter: Any,
    embed_fn: Any,
    lease_validator: Any,
    top_n: int = 5,
    top_k: int = 30,
    diagnostics: dict[str, Any] | None = None,
) -> list[RankedRoom]:
    """Retrieve, validate and rank rooms using a retrieval plan.

    Args:
        plan: The retrieval plan containing semantic queries and hard filters.
        query_result: The original query understanding result (used by ranker).
        vector_adapter: Object with ``search_rooms(vector=..., filters=..., top_k=...)``.
        embed_fn: Callable that returns an embedding vector for a text string.
        lease_validator: Object satisfying the ``LeaseRoomValidator`` protocol.
        top_n: Number of final ranked rooms to return.
        top_k: Number of candidates to fetch per semantic query.

    Returns:
        List of ``RankedRoom`` sorted by final_score, or ``[]`` if the plan
        task is not ``room_search`` or no candidates survive validation.
    """
    if plan.task != "room_search":
        return []

    # ------------------------------------------------------------------
    # 1. Vector recall — one search per semantic query
    # ------------------------------------------------------------------
    best_by_room: dict[int, RoomCandidate] = {}

    for query_text in plan.semantic_queries:
        vector = embed_fn(query_text)
        raw_results = vector_adapter.search_rooms(
            vector=vector,
            filters=plan.hard_filters,
            top_k=top_k,
        )
        for hit in raw_results:
            room_id = hit["room_id"]
            distance = hit.get("distance", 0.0)
            # Lower distance = better match; invert to a 0-1 "score".
            semantic_score = max(0.0, 1.0 - distance)

            existing = best_by_room.get(room_id)
            if existing is None or semantic_score > existing.semantic_score:
                best_by_room[room_id] = RoomCandidate(
                    room_id=room_id,
                    apartment_id=hit.get("apartment_id"),
                    semantic_score=semantic_score,
                    matched_query=query_text,
                    recall_source="vector",
                )

    if not best_by_room:
        return []

    if diagnostics is not None:
        diagnostics["room_hard_filters"] = dict(plan.hard_filters)
        diagnostics["room_semantic_queries"] = list(plan.semantic_queries)
        diagnostics["room_raw_room_ids"] = list(best_by_room.keys())

    # ------------------------------------------------------------------
    # 2. Lease validation
    # ------------------------------------------------------------------
    candidates = list(best_by_room.values())
    validated = validate_room_candidates(
        candidates,
        plan.hard_filters,
        lease_validator,
    )

    if not validated:
        return []

    if diagnostics is not None:
        diagnostics["room_validated_room_ids"] = [room.get("room_id") for room in validated]

    # ------------------------------------------------------------------
    # 3. Fine ranking
    # ------------------------------------------------------------------
    ranked = rank_rooms(validated, query_result, top_n=top_n)
    if diagnostics is not None:
        diagnostics["room_final_room_ids"] = [room.room_id for room in ranked]
    return ranked
