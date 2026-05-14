from types import SimpleNamespace

import pytest

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


def test_eval_kb_retrieval_passes_interaction_intent(monkeypatch):
    """Prove eval classifies query and passes interaction_intent into pipeline."""
    captured = {}

    class FakeClassifier:
        def classify(self, message):
            from aptguide2.interaction.contracts import InteractionIntent
            return InteractionIntent(
                raw_message=message,
                route="rag",
                rag_task="kb_qa",
                domain="payment",
                action="ask_policy",
                needs_kb=True,
                confidence=0.9,
            )

    def fake_pipeline(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            task="kb_qa",
            kb_sources=[SimpleNamespace(doc_id="KB-PAY-002")],
            rooms=[],
            is_confident=True,
            query_understanding=None,
            fallback_reason="",
        )

    deps = run_rag_v2.RagV2EvalDependencies(
        vector_adapter=object(),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=object(),
        interaction_classifier=FakeClassifier(),
    )
    monkeypatch.setattr(run_rag_v2, "run_pipeline_v2", fake_pipeline)

    result = run_rag_v2.eval_kb_retrieval(
        {"query": "可以用花呗付房租吗", "expected_doc_ids": ["KB-PAY-002"]},
        deps,
    )

    assert result["status"] == "pass"
    assert captured["interaction_intent"].route == "rag"
    assert captured["interaction_intent"].rag_task == "kb_qa"
    assert captured["interaction_intent"].domain == "payment"


def test_eval_failure_includes_route_query_and_fallback_metadata(monkeypatch):
    """Failed case dicts must expose intent and query-understanding metadata."""
    from aptguide2.interaction.contracts import InteractionIntent

    intent = InteractionIntent(
        raw_message="可以用花呗付房租吗",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
        confidence=0.9,
    )

    class FakeClassifier:
        def classify(self, message):
            return intent

    def fake_pipeline(**kwargs):
        return SimpleNamespace(
            task="kb_qa",
            kb_sources=[],
            rooms=[],
            is_confident=False,
            fallback_reason="confidence_gate_blocked",
            query_understanding=SimpleNamespace(
                task="kb_qa",
                risk_level="low",
                response_mode="normal_answer",
                hard_filters={},
                soft_preferences=[],
                retrieval_queries=[],
            ),
        )

    deps = run_rag_v2.RagV2EvalDependencies(
        vector_adapter=object(),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=object(),
        interaction_classifier=FakeClassifier(),
    )
    monkeypatch.setattr(run_rag_v2, "run_pipeline_v2", fake_pipeline)

    result = run_rag_v2.eval_kb_retrieval(
        {"query": "可以用花呗付房租吗", "expected_doc_ids": ["KB-PAY-002"]},
        deps,
    )

    assert result["status"] == "fail"
    assert result["route"] == "rag"
    assert result["rag_task"] == "kb_qa"
    assert result["domain"] == "payment"
    assert result["action"] == "ask_policy"
    assert result["parsed_task"] == "kb_qa"
    assert result["risk_level"] == "low"
    assert result["response_mode"] == "normal_answer"
    assert result["fallback_reason"] == "confidence_gate_blocked"


def test_eval_kb_retrieval_includes_retrieval_diagnostics(monkeypatch):
    """KB eval failure must include kb_raw_doc_ids and kb_final_doc_ids from diagnostics."""
    from aptguide2.interaction.contracts import InteractionIntent

    class FakeClassifier:
        def classify(self, message):
            return InteractionIntent(
                raw_message=message,
                route="rag",
                rag_task="kb_qa",
                domain="lease",
                action="ask_policy",
                confidence=0.8,
            )

    def fake_pipeline(**kwargs):
        # Simulate diagnostics being populated by kb_v2
        diag = kwargs.get("diagnostics")
        if diag is not None:
            diag["kb_raw_doc_ids"] = ["KB-PAY-002", "KB-LEASE-001"]
            diag["kb_final_doc_ids"] = []
            diag["kb_confident"] = False
        return SimpleNamespace(
            task="kb_qa",
            kb_sources=[],
            rooms=[],
            is_confident=False,
            fallback_reason="confidence_gate_blocked",
            query_understanding=SimpleNamespace(
                task="kb_qa",
                risk_level="low",
                response_mode="normal_answer",
                hard_filters={},
                soft_preferences=[],
                retrieval_queries=[],
            ),
        )

    deps = run_rag_v2.RagV2EvalDependencies(
        vector_adapter=object(),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=object(),
        interaction_classifier=FakeClassifier(),
    )
    monkeypatch.setattr(run_rag_v2, "run_pipeline_v2", fake_pipeline)

    result = run_rag_v2.eval_kb_retrieval(
        {"query": "押金退还", "expected_doc_ids": ["KB-PAY-002"]},
        deps,
    )

    assert result["status"] == "fail"
    assert result["kb_raw_doc_ids"] == ["KB-PAY-002", "KB-LEASE-001"]
    assert result["kb_final_doc_ids"] == []
    assert result["kb_confident"] is False
