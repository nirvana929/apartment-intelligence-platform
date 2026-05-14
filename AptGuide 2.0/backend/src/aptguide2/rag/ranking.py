"""Room fine-ranking with multi-dimensional scoring.

向量召回解决“语义上像不像”的问题，但租房推荐还需要考虑预算、区域、
偏好标签和可预约状态。这个文件就是召回之后的业务重排层。
"""

from __future__ import annotations

from aptguide2.rag.schemas import QueryUnderstandingResult, RankedRoom

# 最终分数由多个维度加权组成。
# MVP 阶段权重是人工设定的，后续可以用评估集或线上反馈做调参。
W_SEMANTIC = 0.35
W_BUDGET = 0.25
W_AREA = 0.20
W_TAG = 0.15
W_AVAILABILITY = 0.05


def rank_rooms(
    candidates: list[dict],
    query_result: QueryUnderstandingResult,
    top_n: int = 5,
) -> list[RankedRoom]:
    """Rank room candidates with multi-dimensional scoring.

    Args:
        candidates: List of enriched room dicts from room_retrieval.
        query_result: Parsed query understanding for scoring context.
        top_n: Number of top results to return.

    Returns:
        List of RankedRoom sorted by final_score descending.
    """
    if not candidates:
        return []

    budget = query_result.hard_filters.get("max_rent")
    district_id = query_result.hard_filters.get("district_id")
    preferences = query_result.soft_preferences

    scored: list[RankedRoom] = []
    for c in candidates:
        # semantic_score 来自向量检索，表示“文本语义匹配程度”。
        semantic_score = c.get("semantic_score", 0.0)
        # 以下分数来自业务规则，避免“语义像但预算/区域不合适”的房源排到前面。
        budget_score = _score_budget(c.get("rent", 0), budget)
        area_score = _score_area(c.get("district_id", 0), district_id)
        tag_score = _score_tags(c, preferences)
        # 默认可用；真实可租/可预约应由 lease validation 层确认。
        availability_score = 1.0

        # 加权融合：RAG 推荐系统常见做法是“召回粗排 + 业务精排”。
        final_score = (
            W_SEMANTIC * semantic_score
            + W_BUDGET * budget_score
            + W_AREA * area_score
            + W_TAG * tag_score
            + W_AVAILABILITY * availability_score
        )

        reason = _build_recommendation_reason(
            c, semantic_score, budget_score, area_score, tag_score, budget, district_id, preferences
        )

        scored.append(RankedRoom(
            room_id=c.get("room_id", 0),
            apartment_id=c.get("apartment_id", 0),
            apartment_name=c.get("apartment_name", ""),
            room_number=c.get("room_number", ""),
            rent=c.get("rent", 0),
            payment_types=c.get("payment_types", []),
            lease_terms=c.get("lease_terms", []),
            tags=c.get("tags", []),
            facilities=c.get("facilities", []),
            is_appointable=c.get("is_appointable", False),
            final_score=round(final_score, 4),
            semantic_score=round(semantic_score, 4),
            budget_score=round(budget_score, 4),
            area_score=round(area_score, 4),
            tag_score=round(tag_score, 4),
            availability_score=round(availability_score, 4),
            matched_query=c.get("matched_query", ""),
            recommendation_reason=reason,
        ))

    scored.sort(key=lambda r: r.final_score, reverse=True)
    return scored[:top_n]


def _score_budget(rent: int, max_rent: int | None) -> float:
    """Score how well the rent fits the budget.

    - Perfect match (well under budget): 1.0
    - Slightly over budget: 0.3
    - Way over budget: 0.0
    - No budget set: 0.5 (neutral)
    """
    if max_rent is None or max_rent <= 0:
        return 0.5
    if rent <= 0:
        return 0.5

    ratio = rent / max_rent
    if ratio <= 0.7:
        return 1.0  # well under budget
    if ratio <= 0.9:
        return 0.85  # good value
    if ratio <= 1.0:
        return 0.65  # within budget
    if ratio <= 1.1:
        return 0.3  # slightly over
    return 0.0  # way over


def _score_area(room_district_id: int, target_district_id: int | None) -> float:
    """Score district match.

    - Exact match: 1.0
    - No target set: 0.5 (neutral)
    - Mismatch: 0.0
    """
    if target_district_id is None:
        return 0.5
    if room_district_id == target_district_id:
        return 1.0
    return 0.0


def _score_tags(room: dict, preferences: list[str]) -> float:
    """Score tag/preference overlap.

    Counts how many user preferences appear in the room's tags or facilities.
    """
    if not preferences:
        return 0.5

    # 这里只看 tags/facilities 的包含关系，属于轻量规则匹配。
    # 如果后续标签体系复杂，可以改成标准化标签 ID 或单独的偏好模型。
    room_text = " ".join(room.get("tags", [])) + " " + " ".join(room.get("facilities", []))
    matches = sum(1 for p in preferences if p in room_text)
    return min(matches / max(len(preferences), 1), 1.0)


def _build_recommendation_reason(
    room: dict,
    semantic_score: float,
    budget_score: float,
    area_score: float,
    tag_score: float,
    max_rent: int | None,
    district_id: int | None,
    preferences: list[str],
) -> str:
    """Build a concise Chinese recommendation reason."""
    parts = []
    rent = room.get("rent", 0)

    # Budget mention
    if max_rent and rent > 0:
        if budget_score >= 0.85:
            parts.append(f"租金{rent}元，性价比高")
        elif budget_score >= 0.65:
            parts.append(f"租金{rent}元，在预算内")
        elif budget_score >= 0.3:
            parts.append(f"租金{rent}元，略超预算")

    # Area mention
    district_name = room.get("district_name", "")
    if area_score >= 1.0 and district_name:
        parts.append(f"位于{district_name}")

    # Tag matches
    room_tags = room.get("tags", [])
    matched_prefs = [p for p in preferences if any(p in t for t in room_tags)]
    if matched_prefs:
        parts.append("符合偏好：" + "、".join(matched_prefs[:3]))

    # Semantic quality
    if semantic_score >= 0.8 and not parts:
        parts.append("与搜索需求高度匹配")

    if not parts:
        parts.append("综合评分较高")

    return "，".join(parts)
