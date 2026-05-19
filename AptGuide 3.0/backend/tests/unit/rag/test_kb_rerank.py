from __future__ import annotations

from aptguide3.rag.kb_rerank import rerank_sources
from aptguide3.rag.schemas import RetrievalPlan


def _hit(chunk_id: str = "c1", module: str = "life", distance: float = 0.2) -> dict:
    return {
        "chunk_id": chunk_id,
        "doc_id": "d1",
        "title": "t",
        "module": module,
        "content": "content",
        "distance": distance,
    }


def test_module_weight_boosting_lease_over_life():
    plan = RetrievalPlan(task="kb_qa", raw_message="test")
    hits = [_hit(chunk_id="c1", module="life", distance=0.2), _hit(chunk_id="c2", module="lease", distance=0.2)]
    sources = rerank_sources(hits, plan)
    lease_score = next(s.score for s in sources if s.module == "lease")
    life_score = next(s.score for s in sources if s.module == "life")
    assert lease_score > life_score


def test_intent_bonus_when_module_matches():
    plan = RetrievalPlan(task="kb_qa", raw_message="test", module_intent="lease")
    hits = [_hit(chunk_id="c1", module="payment", distance=0.2), _hit(chunk_id="c2", module="lease", distance=0.2)]
    sources = rerank_sources(hits, plan)
    lease_score = next(s.score for s in sources if s.module == "lease")
    payment_score = next(s.score for s in sources if s.module == "payment")
    assert lease_score > payment_score


def test_results_sorted_descending():
    plan = RetrievalPlan(task="kb_qa", raw_message="test")
    hits = [_hit(chunk_id="c1", distance=0.5), _hit(chunk_id="c2", distance=0.1), _hit(chunk_id="c3", distance=0.3)]
    sources = rerank_sources(hits, plan)
    scores = [s.score for s in sources]
    assert scores == sorted(scores, reverse=True)


def test_max_ten_sources():
    plan = RetrievalPlan(task="kb_qa", raw_message="test")
    hits = [_hit(chunk_id=f"c{i}", distance=0.1 * (i % 10)) for i in range(15)]
    sources = rerank_sources(hits, plan)
    assert len(sources) == 10


def test_score_clamped_to_one():
    plan = RetrievalPlan(task="kb_qa", raw_message="test", module_intent="lease")
    hits = [_hit(chunk_id="c1", module="lease", distance=0.0)]
    sources = rerank_sources(hits, plan)
    assert sources[0].score <= 1.0
