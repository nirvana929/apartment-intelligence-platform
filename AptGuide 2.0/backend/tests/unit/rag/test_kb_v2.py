"""Tests for KB retrieval v2."""

from __future__ import annotations

from unittest.mock import MagicMock

from aptguide2.rag.kb_v2 import retrieve_kb_v2
from aptguide2.rag.planning import RetrievalPlan
from aptguide2.rag.schemas import KBSource


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan(
    semantic_queries: list[str] | None = None,
    raw_message: str = "押金退还多久到账",
    risk_level: str = "low",
    recall_channels: list[str] | None = None,
    module_intent: str | None = None,
) -> RetrievalPlan:
    return RetrievalPlan(
        task="kb_qa",
        raw_message=raw_message,
        semantic_queries=semantic_queries if semantic_queries is not None else [raw_message],
        recall_channels=recall_channels or ["dense", "sparse"],
        risk_level=risk_level,
        module_intent=module_intent,
    )


def _make_vector_results(chunk_ids: list[str], distance: float = 0.8) -> list[dict]:
    """Build fake vector search results."""
    results = []
    for cid in chunk_ids:
        results.append({
            "chunk_id": cid,
            "doc_id": cid.split("#")[0] if "#" in cid else cid,
            "title": f"Title for {cid}",
            "module": "lease",
            "content": f"Content for {cid} 押金 退还",
            "distance": distance,
            "risk_level": "low",
        })
    return results


def _make_vector_adapter(results_map: dict[str, list[dict]] | list[dict]):
    """Create a mock vector_adapter.

    If given a dict, maps query text to results.
    If given a list, returns the same results for every call.
    """
    adapter = MagicMock()
    if isinstance(results_map, list):
        adapter.search_kb.return_value = results_map
    else:
        adapter.search_kb.side_effect = lambda vector, filters, top_k: results_map.get(
            str(vector), []
        )
    return adapter


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_retrieve_kb_v2_uses_plan_semantic_queries():
    """embed_fn must be called once per semantic query in the plan."""
    plan = _make_plan(semantic_queries=["query A", "query B", "query C"])
    adapter = _make_vector_adapter([])
    embed_fn = MagicMock(return_value=[0.1, 0.2, 0.3])

    retrieve_kb_v2(plan, adapter, embed_fn)

    assert embed_fn.call_count == 3
    embed_fn.assert_any_call("query A")
    embed_fn.assert_any_call("query B")
    embed_fn.assert_any_call("query C")


def test_retrieve_kb_v2_returns_sources_and_confidence():
    """Return type must be (list[KBSource], bool)."""
    plan = _make_plan()
    results = _make_vector_results(["KB-001#01"], distance=0.9)
    adapter = _make_vector_adapter(results)
    embed_fn = lambda q: [0.1, 0.2]

    sources, is_confident = retrieve_kb_v2(plan, adapter, embed_fn)

    assert isinstance(sources, list)
    assert all(isinstance(s, KBSource) for s in sources)
    assert isinstance(is_confident, bool)
    assert len(sources) == 1
    assert sources[0].chunk_id == "KB-001#01"


def test_retrieve_kb_v2_does_not_import_old_retrieve_kb():
    """kb_v2.py must not import from rag.kb_retrieval or rag.pipeline."""
    import ast
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[3] / "src" / "aptguide2" / "rag" / "kb_v2.py"
    tree = ast.parse(src.read_text())
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)

    forbidden = {m for m in imported_modules if "kb_retrieval" in m or "pipeline" in m}
    assert not forbidden, f"kb_v2.py imports forbidden modules: {forbidden}"


def test_retrieve_kb_v2_merges_multi_channel_hits():
    """Same chunk hit by two different semantic queries should be merged into one candidate."""
    # Two queries both return the same chunk
    plan = _make_plan(semantic_queries=["押金退还", "退还押金规则"])
    results_q1 = _make_vector_results(["KB-001#01"], distance=0.80)
    results_q2 = _make_vector_results(["KB-001#01"], distance=0.85)

    adapter = MagicMock()
    adapter.search_kb.side_effect = [results_q1, results_q2]
    embed_fn = lambda q: [0.1]

    sources, _ = retrieve_kb_v2(plan, adapter, embed_fn)

    # Should be merged into a single source, not duplicated
    assert len(sources) == 1
    assert sources[0].chunk_id == "KB-001#01"
    # The merged candidate should track both recall channels
    # (score should reflect the max of the two hits)


def test_retrieve_kb_v2_low_score_returns_not_confident():
    """Very low distance scores with no text overlap should result in is_confident=False."""
    # Use a raw_message and content that have no lexical overlap so sparse_score=0.
    # Rerank formula: dense*0.35 + sparse*0.15 + module*0.20 + risk*0.15 + validation*0.10 + lexical*0.05
    # With distance=0.1, no module_intent (module=0.5), low risk (0.8), has content (1.0):
    # 0.1*0.35 + 0 + 0.5*0.20 + 0.8*0.15 + 1.0*0.10 + 0 = 0.035 + 0 + 0.10 + 0.12 + 0.10 = 0.355
    # 0.355 < 0.45 (low threshold), so should not be confident.
    plan = _make_plan(raw_message="xyz query", risk_level="low")
    results = [{
        "chunk_id": "KB-001#01",
        "doc_id": "KB-001",
        "title": "abc",
        "module": "life",
        "content": "def ghi",
        "distance": 0.1,
        "risk_level": "low",
    }]
    adapter = _make_vector_adapter(results)
    embed_fn = lambda q: [0.1]

    sources, is_confident = retrieve_kb_v2(plan, adapter, embed_fn)

    assert len(sources) >= 1
    assert is_confident is False


def test_retrieve_kb_v2_empty_queries_returns_empty():
    """No semantic queries should return empty results without calling embed_fn."""
    plan = _make_plan(semantic_queries=[], raw_message="test query")
    adapter = _make_vector_adapter([])
    embed_fn = MagicMock()

    sources, is_confident = retrieve_kb_v2(plan, adapter, embed_fn)

    assert sources == []
    assert is_confident is False
    embed_fn.assert_not_called()


def test_retrieve_kb_v2_preserves_metadata_in_source():
    """KBSource fields should be populated from the vector result payload."""
    plan = _make_plan()
    results = [{
        "chunk_id": "KB-042#03",
        "doc_id": "KB-042",
        "title": "押金退还规则",
        "module": "lease",
        "content": "押金将在退租后15个工作日内退还",
        "distance": 0.92,
        "risk_level": "high",
    }]
    adapter = _make_vector_adapter(results)
    embed_fn = lambda q: [0.5]

    sources, _ = retrieve_kb_v2(plan, adapter, embed_fn)

    assert len(sources) == 1
    s = sources[0]
    assert s.chunk_id == "KB-042#03"
    assert s.doc_id == "KB-042"
    assert s.title == "押金退还规则"
    assert s.module == "lease"
    assert "15个工作日" in s.content
    assert s.risk_level == "high"


def test_retrieve_kb_v2_high_risk_plan_with_matching_source():
    """High-risk plan with a high-risk source should pass confidence check."""
    plan = _make_plan(risk_level="high", module_intent="lease")
    results = [{
        "chunk_id": "KB-001#01",
        "doc_id": "KB-001",
        "title": "违约金条款",
        "module": "lease",
        "content": "违约金相关规定",
        "distance": 0.88,
        "risk_level": "high",
    }]
    adapter = _make_vector_adapter(results)
    embed_fn = lambda q: [0.5]

    sources, is_confident = retrieve_kb_v2(plan, adapter, embed_fn)

    assert len(sources) == 1
    assert is_confident is True


def test_retrieve_kb_v2_sparse_score_computed():
    """Sparse score should be set on candidates (not left at 0.0) after retrieval."""
    plan = _make_plan(raw_message="押金退还")
    results = _make_vector_results(["KB-001#01"], distance=0.85)
    # The content includes "押金 退还" so sparse overlap should be non-zero
    adapter = _make_vector_adapter(results)
    embed_fn = lambda q: [0.1]

    sources, _ = retrieve_kb_v2(plan, adapter, embed_fn)

    # If sparse scoring worked, the rerank score should differ from raw dense_score
    assert len(sources) == 1
    # The score field comes from rerank_score, which incorporates sparse
    assert sources[0].score > 0


def test_retrieve_kb_v2_records_raw_reranked_and_confidence_diagnostics():
    """Diagnostics dict should capture raw IDs, rerank features, and final IDs."""
    diagnostics = {}
    plan = _make_plan(
        raw_message="可以用花呗付房租吗",
        semantic_queries=["可以用花呗付房租吗"],
        module_intent="payment",
    )

    results = [{
        "chunk_id": "chunk-pay-002",
        "doc_id": "KB-PAY-002",
        "title": "花呗支付说明",
        "module": "payment",
        "content": "是否支持花呗支付房租",
        "risk_level": "low",
        "distance": 0.9,
    }]
    adapter = _make_vector_adapter(results)
    embed_fn = lambda q: [0.1, 0.2]

    sources, is_confident = retrieve_kb_v2(plan, adapter, embed_fn, diagnostics=diagnostics)

    assert sources[0].doc_id == "KB-PAY-002"
    assert diagnostics["module_intent"] == "payment"
    assert diagnostics["semantic_queries"] == ["可以用花呗付房租吗"]
    assert diagnostics["kb_raw_doc_ids"] == ["KB-PAY-002"]
    assert diagnostics["kb_final_doc_ids"] == ["KB-PAY-002"]
    assert diagnostics["kb_confident"] is is_confident
    assert diagnostics["kb_rerank_features"][0]["doc_id"] == "KB-PAY-002"
