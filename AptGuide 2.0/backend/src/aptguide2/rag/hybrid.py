"""Hybrid retrieval merge helpers for RAG v2."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HybridCandidate(BaseModel):
    id: str
    dense_score: float = 0.0
    sparse_score: float = 0.0
    metadata_score: float = 0.0
    channel: str = ""
    recall_channels: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


def normalize_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if high == low:
        return [1.0 for _ in values]
    return [(v - low) / (high - low) for v in values]


def merge_hybrid_candidates(groups: list[list[HybridCandidate]]) -> list[HybridCandidate]:
    merged: dict[str, HybridCandidate] = {}
    order: list[str] = []
    for group in groups:
        for candidate in group:
            if candidate.id not in merged:
                item = candidate.model_copy(deep=True)
                item.recall_channels = [candidate.channel] if candidate.channel else []
                merged[candidate.id] = item
                order.append(candidate.id)
                continue
            current = merged[candidate.id]
            current.dense_score = max(current.dense_score, candidate.dense_score)
            current.sparse_score = max(current.sparse_score, candidate.sparse_score)
            current.metadata_score = max(current.metadata_score, candidate.metadata_score)
            if candidate.channel and candidate.channel not in current.recall_channels:
                current.recall_channels.append(candidate.channel)
            current.payload.update(candidate.payload)
    return [merged[key] for key in order]
