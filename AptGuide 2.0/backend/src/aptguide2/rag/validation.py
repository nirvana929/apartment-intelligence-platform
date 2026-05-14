"""Lease validation gate for room candidates."""

from __future__ import annotations

from typing import Protocol

from aptguide2.rag.schemas import RoomCandidate


class LeaseRoomValidator(Protocol):
    def search_rooms(self, payload: dict) -> dict:
        ...


def validate_room_candidates(
    candidates: list[RoomCandidate],
    hard_filters: dict,
    validator: LeaseRoomValidator,
    limit: int = 20,
) -> list[dict]:
    if not candidates:
        return []
    semantic_by_room_id = {c.room_id: c for c in candidates}
    payload = {
        "room_ids": [c.room_id for c in candidates],
        "limit": limit,
        "strategy": "rag_v2_vector_validated_search",
    }
    if hard_filters.get("district_id") is not None:
        payload["district_id"] = hard_filters["district_id"]
    if hard_filters.get("max_rent") is not None:
        payload["max_rent"] = hard_filters["max_rent"]
    if hard_filters.get("payment_type") is not None:
        payload["payment_type"] = hard_filters["payment_type"]

    result = validator.search_rooms(payload)
    rooms = result.get("rooms", []) if isinstance(result, dict) else []
    validated: list[dict] = []
    for room in rooms:
        room_id = room.get("room_id")
        if room_id not in semantic_by_room_id:
            continue
        candidate = semantic_by_room_id[room_id]
        merged = dict(room)
        merged["semantic_score"] = candidate.semantic_score
        merged["matched_query"] = candidate.matched_query
        merged["recall_source"] = candidate.recall_source
        validated.append(merged)
    return validated
