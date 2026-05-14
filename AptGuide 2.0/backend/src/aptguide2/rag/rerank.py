"""Governed rerank for RAG v2.

Character overlap is capped as a weak lexical feature. It must not dominate
semantic, module, risk, and validation signals.
"""

from __future__ import annotations

from pydantic import BaseModel

from aptguide2.rag.hybrid import HybridCandidate
from aptguide2.rag.planning import RetrievalPlan


class RerankWeights(BaseModel):
    dense_score: float = 0.35
    sparse_score: float = 0.15
    module_score: float = 0.20
    risk_score: float = 0.15
    validation_score: float = 0.10
    lexical_score: float = 0.05


def rerank_kb_sources(
    candidates: list[HybridCandidate],
    plan: RetrievalPlan,
    weights: RerankWeights | None = None,
) -> list[HybridCandidate]:
    weights = weights or RerankWeights()
    ranked: list[HybridCandidate] = []
    for candidate in candidates:
        module_score = _module_score(candidate, plan)
        risk_score = _risk_score(candidate, plan)
        validation_score = 1.0 if candidate.payload.get("content") or candidate.payload.get("title") else 0.0
        lexical_score = min(candidate.sparse_score, 1.0)
        final_score = (
            weights.dense_score * candidate.dense_score
            + weights.sparse_score * candidate.sparse_score
            + weights.module_score * module_score
            + weights.risk_score * risk_score
            + weights.validation_score * validation_score
            + weights.lexical_score * lexical_score
        )
        item = candidate.model_copy(deep=True)
        item.payload["rerank_score"] = round(final_score, 6)
        item.payload["rerank_features"] = {
            "dense_score": candidate.dense_score,
            "sparse_score": candidate.sparse_score,
            "module_score": module_score,
            "risk_score": risk_score,
            "validation_score": validation_score,
            "lexical_score": lexical_score,
        }
        ranked.append(item)
    return sorted(ranked, key=lambda c: c.payload.get("rerank_score", 0.0), reverse=True)


def _module_score(candidate: HybridCandidate, plan: RetrievalPlan) -> float:
    if not plan.module_intent:
        return 0.5
    return 1.0 if candidate.payload.get("module") == plan.module_intent else 0.0


def _risk_score(candidate: HybridCandidate, plan: RetrievalPlan) -> float:
    source_risk = candidate.payload.get("risk_level", "low")
    if plan.risk_level == "high":
        return 1.0 if source_risk == "high" else 0.0
    if plan.risk_level == "medium":
        return 1.0 if source_risk in {"medium", "high"} else 0.3
    return 0.8
