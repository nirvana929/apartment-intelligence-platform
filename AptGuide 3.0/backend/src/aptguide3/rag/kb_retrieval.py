from __future__ import annotations

from typing import Any

from aptguide3.rag.diagnostics import KbRecDiagnostic
from aptguide3.rag.kb_rerank import rerank_sources
from aptguide3.rag.schemas import KBSource, RetrievalPlan


def retrieve_kb_sources(
    plan: RetrievalPlan,
    vector_client: Any,
    embedding_client: Any,
    top_k: int = 10,
    diagnostic: KbRecDiagnostic | None = None,
) -> list[KBSource]:
    if plan.task != "kb_qa":
        return []
    if diagnostic is not None:
        diagnostic.semantic_queries = list(plan.semantic_queries)
        diagnostic.module_intent = getattr(plan, "module_intent", None)
        diagnostic.risk_level = getattr(plan, "risk_level", "low")
    raw_hits: list[dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()
    for query in plan.semantic_queries:
        if diagnostic is not None:
            diagnostic.embedding_queries_attempted += 1
        vector = embedding_client.embed(query)
        if not vector:
            if diagnostic is not None:
                diagnostic.embedding_empty_count += 1
            continue
        hits = vector_client.search_kb(vector, top_k=top_k)
        if diagnostic is not None:
            diagnostic.vector_hits_total += len(hits)
        for hit in hits:
            chunk_id = str(hit.get("chunk_id", ""))
            if chunk_id and chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk_id)
                hit["matched_query"] = query
                raw_hits.append(hit)
    if diagnostic is not None:
        diagnostic.unique_chunk_count = len(raw_hits)
    if not raw_hits:
        if diagnostic is not None:
            diagnostic.failure_stage = "kb_vector_recall_empty"
        return []
    sources = rerank_sources(raw_hits, plan)
    if diagnostic is not None:
        diagnostic.returned_doc_ids = (
            list({getattr(s, "doc_id", "") or s.get("doc_id", "") for s in sources})
            if sources else []
        )
        diagnostic.returned_chunk_ids = (
            [getattr(s, "chunk_id", "") or s.get("chunk_id", "") for s in sources[:5]]
            if sources else []
        )
        for s in sources[:3]:
            if hasattr(s, "model_dump"):
                diagnostic.top_sources.append(s.model_dump())
            elif isinstance(s, dict):
                diagnostic.top_sources.append({k: v for k, v in s.items() if k != "content"})
        if not sources:
            diagnostic.failure_stage = "kb_rerank_empty"
    return sources
