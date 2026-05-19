from __future__ import annotations

from aptguide3.rag.kb_retrieval import retrieve_kb_sources
from aptguide3.rag.schemas import RetrievalPlan


class StubEmbedding:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return [0.1, 0.2, 0.3]


class StubVector:
    def __init__(self, hits_per_query: list[list[dict]] | None = None) -> None:
        self._hits_per_query = hits_per_query or [[]]
        self._call_idx = 0

    def search_kb(self, vector: list[float], top_k: int = 10) -> list[dict]:
        hits = self._hits_per_query[self._call_idx] if self._call_idx < len(self._hits_per_query) else []
        self._call_idx += 1
        return hits


def test_returns_empty_for_non_kb_qa_task():
    plan = RetrievalPlan(task="room_search", raw_message="test", semantic_queries=["q1"])
    emb = StubEmbedding()
    vec = StubVector(hits_per_query=[[{"chunk_id": "c1"}]])
    result = retrieve_kb_sources(plan, vec, emb)
    assert result == []
    assert emb.calls == []


def test_merges_and_dedupes_across_queries():
    plan = RetrievalPlan(
        task="kb_qa",
        raw_message="test",
        semantic_queries=["query1", "query2"],
        module_intent="lease",
    )
    hits_q1 = [
        {"chunk_id": "c1", "doc_id": "d1", "title": "t1", "module": "lease", "content": "a", "distance": 0.1},
        {"chunk_id": "c2", "doc_id": "d1", "title": "t2", "module": "lease", "content": "b", "distance": 0.2},
    ]
    hits_q2 = [
        {"chunk_id": "c2", "doc_id": "d1", "title": "t2", "module": "lease", "content": "b", "distance": 0.2},
        {"chunk_id": "c3", "doc_id": "d1", "title": "t3", "module": "lease", "content": "c", "distance": 0.3},
    ]
    emb = StubEmbedding()
    vec = StubVector(hits_per_query=[hits_q1, hits_q2])
    result = retrieve_kb_sources(plan, vec, emb, top_k=10)
    chunk_ids = [s.chunk_id for s in result]
    assert "c1" in chunk_ids
    assert "c2" in chunk_ids
    assert "c3" in chunk_ids
    assert chunk_ids.count("c2") == 1
    assert len(emb.calls) == 2


def test_returns_empty_when_no_hits():
    plan = RetrievalPlan(task="kb_qa", raw_message="test", semantic_queries=["q1"])
    emb = StubEmbedding()
    vec = StubVector(hits_per_query=[[]])
    result = retrieve_kb_sources(plan, vec, emb)
    assert result == []
