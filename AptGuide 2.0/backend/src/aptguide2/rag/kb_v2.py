"""KB retrieval v2 using RetrievalPlan, hybrid merge, and governed rerank.

This replaces the old rag.kb_retrieval.retrieve_kb with a plan-driven
pipeline that uses v2 modules (planning, hybrid, sparse, rerank, confidence).
"""

from __future__ import annotations

from typing import Any

from aptguide2.rag.confidence import check_confidence
from aptguide2.rag.hybrid import HybridCandidate, merge_hybrid_candidates
from aptguide2.rag.planning import RetrievalPlan
from aptguide2.rag.rerank import rerank_kb_sources
from aptguide2.rag.schemas import KBSource
from aptguide2.rag.sparse import sparse_score


def retrieve_kb_v2(
    plan: RetrievalPlan,
    vector_adapter,
    embed_fn,
    top_k: int = 10,
    diagnostics: dict[str, Any] | None = None,
) -> tuple[list[KBSource], bool]:
    """Retrieve KB sources using v2 hybrid retrieval and governed rerank.

    Pipeline:
    1. Embed each semantic query and search the vector store.
    2. Convert raw hits into HybridCandidate objects.
    3. Merge candidates across queries (one group per query).
    4. Compute sparse lexical scores.
    5. Rerank with governed weights.
    6. Convert to KBSource list.
    7. Run confidence gate.

    Args:
        plan: RetrievalPlan from the planning module.
        vector_adapter: Adapter with search_kb(vector, filters, top_k).
        embed_fn: Callable that maps text -> list[float].
        top_k: Number of results per semantic query.

    Returns:
        Tuple of (sources, is_confident).
    """
    if diagnostics is not None:
        diagnostics["module_intent"] = plan.module_intent
        diagnostics["semantic_queries"] = list(plan.semantic_queries)
        diagnostics["hard_filters"] = dict(plan.hard_filters)

    # 1. Multi-query dense recall: one group of candidates per semantic query.
    groups: list[list[HybridCandidate]] = []
    first_channel = plan.recall_channels[0] if plan.recall_channels else "dense"

    for query_text in plan.semantic_queries:
        vector = embed_fn(query_text)
        raw_results = vector_adapter.search_kb(
            vector=vector,
            filters={"module": None, "risk_level": None},
            top_k=top_k,
        )
        group: list[HybridCandidate] = []
        for r in raw_results:
            group.append(HybridCandidate(
                id=r.get("chunk_id", ""),
                dense_score=r.get("distance", 0.0),
                channel=first_channel,
                payload={
                    "chunk_id": r.get("chunk_id", ""),
                    "doc_id": r.get("doc_id", ""),
                    "title": r.get("title", ""),
                    "module": r.get("module", ""),
                    "content": r.get("content", ""),
                    "risk_level": r.get("risk_level", "low"),
                    "matched_query": query_text,
                    "recall_source": first_channel,
                },
            ))
        groups.append(group)

    # 2. Merge candidates across queries (dedup by chunk id, keep best scores).
    merged = merge_hybrid_candidates(groups)

    if diagnostics is not None:
        diagnostics["kb_raw_doc_ids"] = [
            c.payload.get("doc_id", "")
            for group in groups
            for c in group
            if c.payload.get("doc_id")
        ]

    # 3. Compute sparse lexical scores on the merged set.
    for candidate in merged:
        text = f"{candidate.payload.get('title', '')} {candidate.payload.get('content', '')}"
        candidate.sparse_score = sparse_score(plan.raw_message, text)

    # 4. Governed rerank.
    reranked = rerank_kb_sources(merged, plan)

    if diagnostics is not None:
        diagnostics["kb_rerank_features"] = [
            {
                "doc_id": c.payload.get("doc_id", ""),
                "chunk_id": c.payload.get("chunk_id", c.id),
                "rerank_score": c.payload.get("rerank_score"),
                "features": c.payload.get("rerank_features", {}),
            }
            for c in reranked[:10]
        ]

    # 5. Convert to KBSource list.
    sources: list[KBSource] = []
    for c in reranked:
        sources.append(KBSource(
            chunk_id=c.payload.get("chunk_id", c.id),
            doc_id=c.payload.get("doc_id", ""),
            title=c.payload.get("title", ""),
            module=c.payload.get("module", ""),
            content=c.payload.get("content", ""),
            score=c.payload.get("rerank_score", c.dense_score),
            risk_level=c.payload.get("risk_level", "low"),
            matched_query=c.payload.get("matched_query", ""),
            recall_source=",".join(c.recall_channels) if c.recall_channels else c.payload.get("recall_source", "original"),
        ))

    # 6. Confidence gate.
    is_confident = check_confidence(sources, plan.risk_level)

    if diagnostics is not None:
        diagnostics["kb_final_doc_ids"] = [source.doc_id for source in sources]
        diagnostics["kb_confident"] = is_confident

    return sources, is_confident
