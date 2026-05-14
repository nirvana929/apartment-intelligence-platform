from types import SimpleNamespace

from evals.runners import run_rag_v2


def test_eval_kb_retrieval_passes_v2_dependencies(monkeypatch):
    captured = {}

    def fake_pipeline(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            task="kb_qa",
            kb_sources=[SimpleNamespace(doc_id="KB-LEASE-005")],
            rooms=[],
            is_confident=True,
        )

    deps = run_rag_v2.RagV2EvalDependencies(
        vector_adapter=object(),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=object(),
    )
    monkeypatch.setattr(run_rag_v2, "run_pipeline_v2", fake_pipeline)

    result = run_rag_v2.eval_kb_retrieval(
        {"query": "押金退还多久到账", "expected_doc_ids": ["KB-LEASE-005"]},
        deps,
    )

    assert result["status"] == "pass"
    assert captured["vector_adapter"] is deps.vector_adapter
    assert captured["embed_fn"] is deps.embed_fn
    assert captured["lease_validator"] is deps.lease_validator


def test_eval_room_retrieval_passes_lease_validator(monkeypatch):
    captured = {}

    def fake_pipeline(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            task="room_search",
            kb_sources=[],
            rooms=[SimpleNamespace(room_id=101)],
            is_confident=False,
        )

    deps = run_rag_v2.RagV2EvalDependencies(
        vector_adapter=object(),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=object(),
    )
    monkeypatch.setattr(run_rag_v2, "run_pipeline_v2", fake_pipeline)

    result = run_rag_v2.eval_room_retrieval(
        {"query": "番禺1500以内安静房源", "positive_room_ids": [101]},
        deps,
    )

    assert result["status"] == "pass"
    assert captured["lease_validator"] is deps.lease_validator
