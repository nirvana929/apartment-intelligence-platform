"""Room retrieval with multi-channel vector recall.

学习 RAG 时可以把这个文件看成“房源检索段”：
query_understanding 负责理解用户要什么，本文件负责把这些条件变成
Milvus 过滤条件和多路向量召回结果。
"""

from __future__ import annotations

import json
from typing import Any

from aptguide2.rag.schemas import QueryUnderstandingResult, RoomCandidate
from aptguide2.tools.vector_adapter import VectorAdapter


def retrieve_rooms(
    query_result: QueryUnderstandingResult,
    vector_adapter: VectorAdapter,
    embed_fn,
    top_k: int = 30,
) -> list[RoomCandidate]:
    """Retrieve room candidates via multi-channel vector recall.

    Channels:
    - original user query
    - generated retrieval queries from query understanding (up to 3)

    Results are deduplicated by room_id, keeping the best semantic score.

    Args:
        query_result: Parsed query understanding result.
        vector_adapter: Vector adapter for Milvus search.
        embed_fn: Function to embed text -> list[float].
        top_k: Number of results per recall channel.

    Returns:
        List of RoomCandidate sorted by semantic_score descending.
    """
    if query_result.task != "room_search":
        return []

    # 1. 先把预算、区域等硬条件转成 Milvus filter。
    # 这样向量召回只在符合硬约束的候选池里发生，结果更可控。
    filters = _build_filters(query_result)

    # 2. 多路召回 query：原始问题 + query_understanding 生成的改写 query。
    # 原始 query 保真，改写 query 补足业务语义。
    recall_queries: list[tuple[str, str]] = []
    recall_queries.append((query_result.raw_message, "original"))
    for i, rq in enumerate(query_result.retrieval_queries):
        recall_queries.append((rq, f"generated_{i}"))

    # 3. 多路检索并按 room_id 去重。
    # 同一房源被多路命中时，保留最高语义分和对应的 matched_query。
    seen_rooms: dict[int, RoomCandidate] = {}

    for query_text, recall_source in recall_queries:
        vector = embed_fn(query_text)
        results = vector_adapter.search_rooms(
            vector=vector,
            filters=filters,
            top_k=top_k,
        )
        for r in results:
            room_id = r.get("room_id", 0)
            if not room_id:
                continue
            distance = r.get("distance", 0.0)
            if room_id in seen_rooms:
                if distance > seen_rooms[room_id].semantic_score:
                    seen_rooms[room_id].semantic_score = distance
                    seen_rooms[room_id].matched_query = query_text
                    seen_rooms[room_id].recall_source = recall_source
            else:
                seen_rooms[room_id] = RoomCandidate(
                    room_id=room_id,
                    apartment_id=r.get("apartment_id"),
                    semantic_score=distance,
                    matched_query=query_text,
                    recall_source=recall_source,
                )

    # 4. 这里只按语义分排序；预算、区域、标签等多维评分在 ranking.py 做。
    candidates = sorted(seen_rooms.values(), key=lambda c: c.semantic_score, reverse=True)
    return candidates


def _build_filters(query_result: QueryUnderstandingResult) -> dict[str, Any]:
    """Extract Milvus-compatible hard filters from query understanding."""
    filters: dict[str, Any] = {}
    hf = query_result.hard_filters

    if "district_id" in hf and hf["district_id"] is not None:
        filters["district_id"] = hf["district_id"]
    if "max_rent" in hf and hf["max_rent"] is not None:
        filters["max_rent"] = hf["max_rent"]
    if "min_rent" in hf and hf["min_rent"] is not None:
        filters["min_rent"] = hf["min_rent"]

    return filters


def enrich_candidates_from_vector(
    candidates: list[RoomCandidate],
    vector_adapter: VectorAdapter,
) -> list[dict]:
    """Enrich room candidates with full vector record data.

    Returns list of dicts with room details from Milvus for ranking.
    """
    if not candidates:
        return []

    room_ids = [c.room_id for c in candidates]
    raw = vector_adapter.get_room_by_ids(room_ids)

    # 检索阶段的 RoomCandidate 只保留 ID、语义分等轻量信息。
    # 排序阶段需要租金、标签、设施等字段，所以这里再按 room_id 批量取详情。
    by_id: dict[int, dict] = {}
    for r in raw:
        rid = r.get("room_id", 0)
        if rid:
            by_id[rid] = r

    enriched = []
    for c in candidates:
        data = by_id.get(c.room_id, {})
        entry = {
            "room_id": c.room_id,
            "apartment_id": c.apartment_id or data.get("apartment_id", 0),
            "apartment_name": data.get("apartment_name", ""),
            "semantic_score": c.semantic_score,
            "matched_query": c.matched_query,
            "district_id": data.get("district_id", 0),
            "district_name": data.get("district_name", ""),
            "rent": data.get("rent", 0),
            "payment_types": _parse_json_field(data.get("payment_types", "[]")),
            "lease_terms": _parse_json_field(data.get("lease_terms", "[]")),
            "tags": _parse_json_field(data.get("tags", "[]")),
            "facilities": _parse_json_field(data.get("facilities", "[]")),
        }
        enriched.append(entry)

    return enriched


def _parse_json_field(value: Any) -> list:
    """Parse a JSON string field, returning empty list on failure."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    return []
