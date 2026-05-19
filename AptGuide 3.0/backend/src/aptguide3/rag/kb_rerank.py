from __future__ import annotations

from aptguide3.rag.schemas import KBSource, RetrievalPlan

MODULE_WEIGHTS = {
    "lease": 1.2,
    "payment": 1.15,
    "account": 1.1,
    "appointment": 1.05,
    "policy": 1.1,
    "life": 1.0,
}


def rerank_sources(hits: list[dict], plan: RetrievalPlan) -> list[KBSource]:
    sources: list[KBSource] = []
    for hit in hits:
        distance = float(hit.get("distance", 1.0))
        base_score = max(0.0, min(1.0, 1.0 - distance))
        module = hit.get("module", "")
        module_weight = MODULE_WEIGHTS.get(module, 1.0)
        intent_bonus = 1.1 if plan.module_intent and module == plan.module_intent else 1.0
        final_score = min(1.0, base_score * module_weight * intent_bonus)
        sources.append(KBSource(
            chunk_id=str(hit.get("chunk_id", "")),
            doc_id=str(hit.get("doc_id", "")),
            title=hit.get("title", ""),
            module=module,
            content=hit.get("content", ""),
            score=round(final_score, 4),
            risk_level=hit.get("risk_level", "low"),
            matched_query=hit.get("matched_query", ""),
            recall_source="dense",
        ))
    sources.sort(key=lambda s: s.score, reverse=True)
    return sources[:10]
