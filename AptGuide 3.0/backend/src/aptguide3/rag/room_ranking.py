from __future__ import annotations

from aptguide3.rag.schemas import PreferenceScore, RankedRoom, RetrievalPlan, ValidatedRoom

W_SEMANTIC = 0.35
W_BUDGET = 0.25
W_AREA = 0.15
W_PREFERENCE = 0.20
W_AVAILABILITY = 0.05


def rank_rooms(
    rooms: list[ValidatedRoom],
    plan: RetrievalPlan,
    preference_scores: dict[int, PreferenceScore],
    top_n: int = 5,
) -> list[RankedRoom]:
    ranked: list[RankedRoom] = []
    for room in rooms:
        pref = preference_scores.get(room.room_id, PreferenceScore(room_id=room.room_id, score=0.5))
        budget_score = _score_budget(room.rent, plan.hard_filters.get("max_rent"))
        area_score = _score_area(room.district_id, plan.hard_filters.get("district_id"))
        availability_score = 1.0 if room.is_appointable else 0.5
        final_score = (
            W_SEMANTIC * room.semantic_score
            + W_BUDGET * budget_score
            + W_AREA * area_score
            + W_PREFERENCE * pref.score
            + W_AVAILABILITY * availability_score
        )
        ranked.append(RankedRoom(
            room_id=room.room_id,
            apartment_id=room.apartment_id,
            apartment_name=room.apartment_name,
            room_number=room.room_number,
            district_name=room.district_name,
            rent=room.rent,
            payment_types=room.payment_types,
            lease_terms=room.lease_terms,
            tags=room.tags,
            facilities=room.facilities,
            is_appointable=room.is_appointable,
            final_score=round(final_score, 4),
            semantic_score=round(room.semantic_score, 4),
            budget_score=round(budget_score, 4),
            area_score=round(area_score, 4),
            preference_score=round(pref.score, 4),
            availability_score=round(availability_score, 4),
            matched_query=room.matched_query,
            recommendation_reason=pref.reason or "综合匹配度较高。",
            wechat_room_id=room.wechat_room_id,
            lease_room_id=room.lease_room_id,
            source_collection=room.source_collection,
            source_record_id=room.source_record_id,
            lease_validation_status=room.lease_validation_status,
            evidence_level=room.evidence_level,
        ))
    return sorted(ranked, key=lambda item: item.final_score, reverse=True)[:top_n]


def _score_budget(rent: int, max_rent: int | None) -> float:
    if max_rent is None or max_rent <= 0 or rent <= 0:
        return 0.5
    ratio = rent / max_rent
    if ratio <= 0.8:
        return 1.0
    if ratio <= 1.0:
        return 0.75
    if ratio <= 1.1:
        return 0.3
    return 0.0


def _score_area(room_district_id: int | None, target_district_id: int | None) -> float:
    if target_district_id is None:
        return 0.5
    return 1.0 if room_district_id == target_district_id else 0.0
