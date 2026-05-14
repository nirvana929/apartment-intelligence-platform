from aptguide2.rag.hybrid import HybridCandidate
from aptguide2.rag.planning import RetrievalPlan
from aptguide2.rag.rerank import RerankWeights, rerank_kb_sources


def test_rerank_uses_dense_sparse_module_and_risk_features():
    plan = RetrievalPlan(
        task="kb_qa",
        raw_message="押金退还多久到账",
        semantic_queries=["押金退还多久到账"],
        recall_channels=["dense", "sparse", "step_back"],
        module_intent="lease",
        risk_level="high",
        validation_mode="source_required",
        source_policy="high_risk_source_required",
    )
    candidates = [
        HybridCandidate(
            id="bad",
            dense_score=0.9,
            sparse_score=0.0,
            payload={"module": "life", "risk_level": "low", "title": "生活维修"},
        ),
        HybridCandidate(
            id="good",
            dense_score=0.82,
            sparse_score=0.7,
            payload={"module": "lease", "risk_level": "high", "title": "押金退还规则"},
        ),
    ]

    ranked = rerank_kb_sources(candidates, plan)

    assert ranked[0].id == "good"
    assert ranked[0].payload["rerank_features"]["module_score"] == 1.0
    assert ranked[0].payload["rerank_features"]["risk_score"] == 1.0


def test_character_overlap_weight_is_capped():
    weights = RerankWeights()

    assert weights.lexical_score <= 0.20
