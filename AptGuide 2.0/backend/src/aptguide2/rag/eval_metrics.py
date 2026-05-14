"""RAG v2 evaluation metrics: hit@k, MRR, and NDCG."""

from __future__ import annotations

import math


def hit_at_k(actual_ids: list[str | int], expected_ids: set[str | int], k: int) -> bool:
    """Return True if any expected item appears in the top-k actual results."""
    return bool(set(actual_ids[:k]) & expected_ids)


def mean_reciprocal_rank(actual_ids: list[str | int], expected_ids: set[str | int]) -> float:
    """Return 1/rank for the first relevant item, or 0 if none found."""
    for rank, item_id in enumerate(actual_ids, 1):
        if item_id in expected_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(actual_ids: list[str | int], expected_ids: set[str | int], k: int) -> float:
    """Normalized discounted cumulative gain at k.

    Assumes binary relevance: items in expected_ids are relevant (1),
    all others are not (0).
    """
    dcg = 0.0
    for index, item_id in enumerate(actual_ids[:k], 1):
        if item_id in expected_ids:
            dcg += 1.0 / math.log2(index + 1)

    ideal_hits = min(len(expected_ids), k)
    if ideal_hits == 0:
        return 0.0

    idcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return round(dcg / idcg, 6)
