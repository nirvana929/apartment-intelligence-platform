# AptGuide 2.0 RAG Diagnostic-First Retrieval Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise live RAG v2 quality to KB source hit@3 >= 90%, Room hit@5 >= 85%, High-risk fallback = 100%, and Unvalidated room count = 0 by diagnosing the failing retrieval layer before tuning recall or ranking.

**Architecture:** Treat RAG quality as a staged system: interaction intent -> query understanding -> retrieval plan -> raw recall -> validation -> rerank/ranking -> confidence/fallback -> eval report. The first implementation task must prove the eval runner is measuring the post-Semantic Interaction Routing path by injecting `InteractionIntent` into `run_pipeline_v2()`, then all remaining fixes are driven by failed-case diagnostics.

**Tech Stack:** Python 3.13, pytest, Pydantic, YAML eval cases, AptGuide 2.0 harness, `aptguide2.interaction`, `aptguide2.rag.pipeline_v2`, v2 KB/room retrieval, Milvus `VectorAdapter`, OpenAI-compatible embeddings, lease validation through `ToolRuntimeRoomValidator`.

---

## Scope And Guardrails

This plan is for retrieval quality only. Do not use it to redesign appointment, auth, handoff, frontend, persistence, or operator console behavior.

Hard constraints:

- Do not reintroduce `aptguide2.rag.pipeline`, `RagBaselineProcedure`, `kb_retrieval.py`, or `room_retrieval.py`.
- Do not bypass lease validation for rooms.
- Do not use LLM output as business fact authority.
- Do not lower or skip high-risk fallback behavior.
- Do not change eval cases to improve metrics unless diagnostics prove an expected doc/room is stale, inactive, unavailable, or contradictory to the query.
- Do not make keyword-primary routing the main strategy. Keywords may be used only for fallback, hard-filter extraction, entity normalization, safety rules, or deterministic policy corrections.

## File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `backend/evals/runners/run_rag_v2.py` | Modify | Ensure eval uses interaction intent; include failed-case diagnostics in report data. |
| `backend/tests/unit/evals/test_run_rag_v2.py` | Modify | Test intent injection and diagnostic metadata. |
| `backend/evals/runners/run_rag_v2_diagnostics.py` | Create if needed | Generate detailed failure-stage report without changing retrieval behavior. |
| `backend/tests/unit/evals/test_run_rag_v2_diagnostics.py` | Create if needed | Test diagnostic grouping/report helpers. |
| `backend/src/aptguide2/rag/pipeline_v2.py` | Modify | Pass optional diagnostics through KB and room retrieval. |
| `backend/src/aptguide2/rag/kb_v2.py` | Modify | Record raw KB IDs, rerank features, final IDs, and confidence decision. |
| `backend/src/aptguide2/rag/room_v2.py` | Modify | Record raw room IDs, validated IDs, final ranked IDs, and hard filters. |
| `backend/src/aptguide2/rag/query_understanding.py` | Modify only if diagnostics prove needed | Correct intent consumption or fallback query-understanding gaps. |
| `backend/src/aptguide2/rag/planning.py` | Modify only if diagnostics prove needed | Improve module intent, semantic queries, and hard filters. |
| `backend/src/aptguide2/rag/rerank.py` | Modify only if raw recall contains expected KB docs but ranking loses them. |
| `backend/src/aptguide2/rag/ranking.py` | Modify only if validated expected rooms are present but ranked outside top 5. |
| `reports/rag-v2-live-evaluation-report.md` | Update | Final live eval output. |
| `reports/rag-v2-hit-rate-root-cause-analysis.md` | Update | Mark resolved/current root causes. |
| `reports/rag-v2-diagnostic-report.md` | Create | Evidence for failed cases and layer classification. |
| `docs/tests/verification-log.md` | Update | Commands and results. |
| `docs/plans/current-plan.md` | Update | Point to this plan. |
| `docs/plans/next-steps.md` | Update | Keep immediate next steps accurate after execution. |
| `progress/current-plan.md` | Update | Mirror current plan status. |
| `progress/next-steps.md` | Update | Mirror next steps. |
| `progress/completed.md` or `progress/known-issues.md` | Update after execution | Record completion or documented blockers. |

## Success Criteria

- Post-routing live eval baseline is recorded before retrieval fixes.
- Failed cases include route/rag_task/domain/action, query understanding, retrieval plan, raw/final KB IDs, raw/validated/final room IDs, confidence decision, and fallback reason where available.
- KB source hit@3 >= 90%.
- Room hit@5 >= 85%, or a data consistency report proves specific room eval cases need product review.
- High-risk fallback remains 100%.
- Unvalidated room count remains 0.
- Full backend tests pass.
- Legacy RAG source scan has no runtime matches.

## Task 1: Prove The Eval Measures Post-Semantic-Routing RAG

**Files:**
- Modify: `backend/evals/runners/run_rag_v2.py`
- Modify: `backend/tests/unit/evals/test_run_rag_v2.py`

- [ ] **Step 1: Write an intent-injection regression test**

Add a test to `backend/tests/unit/evals/test_run_rag_v2.py` proving `eval_kb_retrieval()` classifies the query and passes `interaction_intent` into `run_pipeline_v2()`:

```python
def test_eval_kb_retrieval_passes_interaction_intent(monkeypatch):
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
```

- [ ] **Step 2: Run the test and confirm it fails before implementation**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py::test_eval_kb_retrieval_passes_interaction_intent -q
```

Expected before implementation: fail because `RagV2EvalDependencies` has no `interaction_classifier` and the runner does not pass `interaction_intent`.

- [ ] **Step 3: Extend eval dependencies**

Modify `RagV2EvalDependencies` in `backend/evals/runners/run_rag_v2.py`:

```python
@dataclass
class RagV2EvalDependencies:
    vector_adapter: object
    embed_fn: Callable[[str], list[float]]
    lease_validator: object | None
    interaction_classifier: object | None = None
```

- [ ] **Step 4: Build live classifier dependency**

Modify `build_live_dependencies()` in `backend/evals/runners/run_rag_v2.py`:

```python
from aptguide2.api.deps import get_interaction_classifier, get_tool_runtime
```

Return the classifier:

```python
return RagV2EvalDependencies(
    vector_adapter=adapter,
    embed_fn=embed_fn,
    lease_validator=ToolRuntimeRoomValidator(get_tool_runtime()),
    interaction_classifier=get_interaction_classifier(settings),
)
```

If `get_interaction_classifier()` accepts no `settings` argument in the current code, use the actual local signature and keep the same test behavior.

- [ ] **Step 5: Add a helper to classify intent**

Add to `backend/evals/runners/run_rag_v2.py`:

```python
def classify_interaction_intent(query: str, deps: RagV2EvalDependencies) -> object | None:
    if deps.interaction_classifier is None:
        return None
    return deps.interaction_classifier.classify(query)
```

- [ ] **Step 6: Pass interaction intent into all eval pipeline calls**

In `eval_kb_retrieval()`, `eval_room_retrieval()`, and `eval_fallback_retrieval()`, compute:

```python
interaction_intent = classify_interaction_intent(query, deps)
```

Then call:

```python
result = run_pipeline_v2(
    message=query,
    vector_adapter=deps.vector_adapter,
    embed_fn=deps.embed_fn,
    lease_validator=deps.lease_validator,
    interaction_intent=interaction_intent,
)
```

- [ ] **Step 7: Run eval runner unit tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py -q
```

Expected: all eval runner tests pass.

## Task 2: Add Per-Case Diagnostic Metadata Without Changing Retrieval Behavior

**Files:**
- Modify: `backend/evals/runners/run_rag_v2.py`
- Modify: `backend/tests/unit/evals/test_run_rag_v2.py`

- [ ] **Step 1: Write metadata extraction test**

Add to `backend/tests/unit/evals/test_run_rag_v2.py`:

```python
def test_eval_failure_includes_route_query_and_fallback_metadata(monkeypatch):
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
```

- [ ] **Step 2: Run the test and confirm it fails before implementation**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py::test_eval_failure_includes_route_query_and_fallback_metadata -q
```

Expected before implementation: fail because failure dicts do not expose this metadata.

- [ ] **Step 3: Add metadata helper**

Add to `backend/evals/runners/run_rag_v2.py`:

```python
def extract_result_metadata(result: object, interaction_intent: object | None) -> dict[str, Any]:
    qr = getattr(result, "query_understanding", None)
    return {
        "route": getattr(interaction_intent, "route", ""),
        "rag_task": getattr(interaction_intent, "rag_task", ""),
        "domain": getattr(interaction_intent, "domain", ""),
        "action": getattr(interaction_intent, "action", ""),
        "intent_confidence": getattr(interaction_intent, "confidence", None),
        "parsed_task": getattr(qr, "task", getattr(result, "task", "")),
        "risk_level": getattr(qr, "risk_level", ""),
        "response_mode": getattr(qr, "response_mode", ""),
        "hard_filters": dict(getattr(qr, "hard_filters", {}) or {}),
        "soft_preferences": list(getattr(qr, "soft_preferences", []) or []),
        "retrieval_queries": list(getattr(qr, "retrieval_queries", []) or []),
        "fallback_reason": getattr(result, "fallback_reason", ""),
    }
```

- [ ] **Step 4: Merge metadata into failure returns**

In `eval_kb_retrieval()`, `eval_room_retrieval()`, and `eval_fallback_retrieval()`, add metadata to failure dicts:

```python
metadata = extract_result_metadata(result, interaction_intent)
return {
    "status": "fail",
    "reason": "no KB sources returned",
    "expected": sorted(expected_doc_ids),
    **metadata,
}
```

Apply the same pattern to every failure path. For successful cases, metadata is optional; do not bloat the report unless needed.

- [ ] **Step 5: Render diagnostic metadata in failed-case report**

In `write_report()`, under each failed case, add compact details:

```python
details = []
for key in ("route", "rag_task", "domain", "action", "parsed_task", "risk_level", "response_mode", "fallback_reason"):
    value = fail.get(key)
    if value not in (None, "", []):
        details.append(f"{key}={value}")
if details:
    f.write(f"  - diagnostics: {', '.join(details)}\n")
if fail.get("hard_filters"):
    f.write(f"  - hard_filters: `{fail['hard_filters']}`\n")
if fail.get("soft_preferences"):
    f.write(f"  - soft_preferences: `{fail['soft_preferences']}`\n")
if fail.get("retrieval_queries"):
    f.write(f"  - retrieval_queries: `{fail['retrieval_queries']}`\n")
```

- [ ] **Step 6: Run unit tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py -q
```

Expected: all tests pass.

## Task 3: Add Retrieval-Stage Diagnostics For KB And Rooms

**Files:**
- Modify: `backend/src/aptguide2/rag/pipeline_v2.py`
- Modify: `backend/src/aptguide2/rag/kb_v2.py`
- Modify: `backend/src/aptguide2/rag/room_v2.py`
- Modify: `backend/evals/runners/run_rag_v2.py`
- Modify: `backend/tests/unit/rag/test_kb_v2.py`
- Modify: `backend/tests/unit/rag/test_room_v2.py`

- [ ] **Step 1: Add KB diagnostics unit test**

Add to `backend/tests/unit/rag/test_kb_v2.py`:

```python
def test_retrieve_kb_v2_records_raw_reranked_and_confidence_diagnostics():
    diagnostics = {}
    plan = RetrievalPlan(
        task="kb_qa",
        raw_message="可以用花呗付房租吗",
        semantic_queries=["可以用花呗付房租吗"],
        module_intent="payment",
        risk_level="low",
    )

    class FakeVectorAdapter:
        def search_kb(self, vector, filters, top_k):
            return [
                {
                    "chunk_id": "chunk-pay-002",
                    "doc_id": "KB-PAY-002",
                    "title": "花呗支付说明",
                    "module": "payment",
                    "content": "是否支持花呗支付房租",
                    "risk_level": "low",
                    "distance": 0.9,
                }
            ]

    sources, is_confident = retrieve_kb_v2(
        plan,
        FakeVectorAdapter(),
        lambda text: [0.1, 0.2],
        diagnostics=diagnostics,
    )

    assert sources[0].doc_id == "KB-PAY-002"
    assert diagnostics["kb_raw_doc_ids"] == ["KB-PAY-002"]
    assert diagnostics["kb_final_doc_ids"] == ["KB-PAY-002"]
    assert diagnostics["kb_confident"] is is_confident
    assert diagnostics["kb_rerank_features"][0]["doc_id"] == "KB-PAY-002"
```

- [ ] **Step 2: Add optional KB diagnostics parameter**

Modify `retrieve_kb_v2()` signature:

```python
def retrieve_kb_v2(
    plan: RetrievalPlan,
    vector_adapter,
    embed_fn,
    top_k: int = 10,
    diagnostics: dict[str, Any] | None = None,
) -> tuple[list[KBSource], bool]:
```

Import `Any` from `typing`. Record:

```python
if diagnostics is not None:
    diagnostics["module_intent"] = plan.module_intent
    diagnostics["semantic_queries"] = list(plan.semantic_queries)
    diagnostics["hard_filters"] = dict(plan.hard_filters)
    diagnostics["kb_raw_doc_ids"] = [
        c.payload.get("doc_id", "")
        for group in groups
        for c in group
        if c.payload.get("doc_id")
    ]
```

After rerank:

```python
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
```

After confidence:

```python
if diagnostics is not None:
    diagnostics["kb_final_doc_ids"] = [source.doc_id for source in sources]
    diagnostics["kb_confident"] = is_confident
```

- [ ] **Step 3: Add room diagnostics unit test**

Add to `backend/tests/unit/rag/test_room_v2.py` using the existing fake adapters in that file. If helper names differ, adapt the class names but keep this assertion contract:

```python
def test_room_v2_records_raw_validated_and_ranked_diagnostics():
    diagnostics = {}
    ranked = retrieve_ranked_rooms_v2(
        plan=RetrievalPlan(
            task="room_search",
            raw_message="番禺区2000以内适合考研",
            hard_filters={"district_id": 4, "max_rent": 2000},
            semantic_queries=["番禺区2000以内适合考研"],
        ),
        query_result=QueryUnderstandingResult(
            raw_message="番禺区2000以内适合考研",
            task="room_search",
            hard_filters={"district_id": 4, "max_rent": 2000},
            soft_preferences=["适合考研"],
        ),
        vector_adapter=FakeRoomVectorAdapter(room_ids=[200013]),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=FakeLeaseValidator(valid_room_ids=[200013]),
        diagnostics=diagnostics,
    )

    assert [room.room_id for room in ranked] == [200013]
    assert diagnostics["room_raw_room_ids"] == [200013]
    assert diagnostics["room_validated_room_ids"] == [200013]
    assert diagnostics["room_final_room_ids"] == [200013]
```

- [ ] **Step 4: Add optional room diagnostics parameter**

Modify `retrieve_ranked_rooms_v2()` signature:

```python
def retrieve_ranked_rooms_v2(
    plan: RetrievalPlan,
    query_result: QueryUnderstandingResult,
    vector_adapter: Any,
    embed_fn: Any,
    lease_validator: Any,
    top_n: int = 5,
    top_k: int = 30,
    diagnostics: dict[str, Any] | None = None,
) -> list[RankedRoom]:
```

After vector recall:

```python
if diagnostics is not None:
    diagnostics["room_hard_filters"] = dict(plan.hard_filters)
    diagnostics["room_semantic_queries"] = list(plan.semantic_queries)
    diagnostics["room_raw_room_ids"] = list(best_by_room.keys())
```

After validation:

```python
if diagnostics is not None:
    diagnostics["room_validated_room_ids"] = [room.get("room_id") for room in validated]
```

Before return:

```python
ranked = rank_rooms(validated, query_result, top_n=top_n)
if diagnostics is not None:
    diagnostics["room_final_room_ids"] = [room.room_id for room in ranked]
return ranked
```

- [ ] **Step 5: Thread diagnostics through pipeline**

Modify `run_pipeline_v2()` signature:

```python
def run_pipeline_v2(..., interaction_intent=None, diagnostics: dict[str, Any] | None = None) -> PipelineResult:
```

Import `Any` from `typing`. After `plan = build_retrieval_plan(qr)`, record:

```python
if diagnostics is not None:
    diagnostics["query_understanding"] = qr.model_dump()
    diagnostics["retrieval_plan"] = plan.model_dump()
```

Pass `diagnostics=diagnostics` into `retrieve_kb_v2()` and `retrieve_ranked_rooms_v2()`.

- [ ] **Step 6: Thread diagnostics through eval runner**

In each eval function:

```python
diagnostics: dict[str, Any] = {}
result = run_pipeline_v2(..., diagnostics=diagnostics)
```

Include `**diagnostics` in failure dicts. Do not include full content bodies in reports; IDs and feature scores are enough.

- [ ] **Step 7: Run focused tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_kb_v2.py tests/unit/rag/test_room_v2.py tests/unit/evals/test_run_rag_v2.py -q
```

Expected: all tests pass.

## Task 4: Run Reality Audit And Classify Failures

**Files:**
- Update: `reports/rag-v2-live-evaluation-report.md`
- Create/Update: `reports/rag-v2-diagnostic-report.md`
- Update: `reports/rag-v2-hit-rate-root-cause-analysis.md`

- [ ] **Step 1: Run live eval after diagnostic instrumentation**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_rag_v2 \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Record exact metrics:

- KB source hit@3
- KB source hit@5
- Room hit@5
- High-risk fallback
- Unvalidated rooms

- [ ] **Step 2: Classify each failed case**

Create or update `reports/rag-v2-diagnostic-report.md` with these sections:

```markdown
# RAG v2 Diagnostic Report

## Baseline After Semantic Interaction Routing

| Metric | Value |
| --- | ---: |
| KB source hit@3 | ... |
| Room hit@5 | ... |
| High-risk fallback | ... |
| Unvalidated rooms | ... |

## Failure Classification

| Case | Type | Layer | Evidence | Next action |
| --- | --- | --- | --- | --- |
| kb-005 | KB | intent/query planning/raw recall/rerank/confidence/data | ... | ... |

## Data Consistency Findings

Only include a case here when diagnostics prove expected docs or rooms are unavailable, inactive, or contradictory to the query.
```

Layer labels must be one of:

- `interaction_intent`
- `query_understanding`
- `retrieval_plan`
- `kb_raw_recall`
- `kb_rerank`
- `confidence_gate`
- `room_raw_recall`
- `lease_validation`
- `room_ranking`
- `eval_data_consistency`

- [ ] **Step 3: Update root-cause analysis**

Update `reports/rag-v2-hit-rate-root-cause-analysis.md` with a new section:

```markdown
## Post-Semantic-Routing Diagnostic Status

- Resolved:
  - ...
- Still present:
  - ...
- Newly discovered:
  - ...
```

Do not mark a root cause resolved unless the diagnostic report or eval output proves it.

## Task 5: Fix KB Failures By Proven Layer

**Files:** modify only the files implicated by Task 4 diagnostics.

- [ ] **Step 1: If intent is wrong, fix interaction classifier policy**

When a KB eval query produces `route != rag` or `rag_task != kb_qa`, add focused tests in `backend/tests/unit/interaction/` and patch `backend/src/aptguide2/interaction/classifier.py`.

Required test shape:

```python
def test_policy_question_routes_to_kb_qa():
    intent = HeuristicInteractionClassifier().classify("可以用花呗付房租吗")

    assert intent.route == "rag"
    assert intent.rag_task == "kb_qa"
    assert intent.domain == "payment"
```

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/interaction -q
```

- [ ] **Step 2: If query understanding ignores correct intent, fix intent consumption**

When `interaction_intent.rag_task == kb_qa` but `query_understanding.task != kb_qa`, add a test to `backend/tests/unit/rag/test_query_understanding.py`:

```python
def test_understand_query_uses_interaction_intent_for_kb_task():
    intent = InteractionIntent(
        raw_message="月付和季付有什么区别",
        route="rag",
        rag_task="kb_qa",
        domain="payment",
        action="ask_policy",
    )

    result = understand_query("月付和季付有什么区别", interaction_intent=intent)

    assert result.task == "kb_qa"
```

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_query_understanding.py -q
```

- [ ] **Step 3: If retrieval plan is weak, fix module intent and semantic queries**

When `task == kb_qa` but `module_intent` or `semantic_queries` do not match the expected domain, add tests in `backend/tests/unit/rag/test_planning.py`:

```python
def test_payment_policy_plan_uses_payment_module_and_queries():
    qr = understand_query(
        "电费怎么算",
        interaction_intent=InteractionIntent(
            raw_message="电费怎么算",
            route="rag",
            rag_task="kb_qa",
            domain="payment",
            action="ask_policy",
        ),
    )

    plan = build_retrieval_plan(qr)

    assert plan.module_intent == "payment"
    assert any("支付" in query or "费用" in query or "电费" in query for query in plan.semantic_queries)
```

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_planning.py -q
```

- [ ] **Step 4: If raw recall misses expected docs, fix query expansion or index mapping**

Only after diagnostics show `expected_doc_id not in kb_raw_doc_ids`, inspect:

- `semantic_queries`
- `module_intent`
- vector adapter collection mapping
- KB chunk/source mapping
- embedding query text

Do not tune rerank weights for this failure type.

- [ ] **Step 5: If raw recall contains expected docs but rerank loses them, tune features narrowly**

Only after diagnostics show `expected_doc_id in kb_raw_doc_ids` and not in `kb_final_doc_ids[:3]`, add a test in `backend/tests/unit/rag/test_rerank.py` for that feature interaction. Keep lexical score weak and do not make character overlap dominant.

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_rerank.py tests/unit/rag/test_kb_v2.py -q
```

- [ ] **Step 6: Re-run live eval after KB fixes**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_rag_v2 \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected: KB source hit@3 moves toward or reaches >= 90%. If not, update diagnostic report before further changes.

## Task 6: Fix Room Failures By Proven Layer

**Files:** modify only the files implicated by Task 4 diagnostics.

- [ ] **Step 1: If raw recall misses expected rooms, inspect semantic queries and vector data**

When `expected_room_id not in room_raw_room_ids`, do not bypass validation. Inspect:

- `room_semantic_queries`
- `room_hard_filters`
- `VectorAdapter.search_rooms()` filters
- whether expected room IDs exist in vector data

If the room is missing from vector data, document it in `reports/rag-v2-diagnostic-report.md`.

- [ ] **Step 2: If lease validation removes expected rooms, verify data consistency**

When `expected_room_id in room_raw_room_ids` but not in `room_validated_room_ids`, inspect lease validator output and filters:

- district
- max rent
- payment type
- availability/status
- appointability

If expected IDs are inactive or unavailable, do not change eval cases. Document the data consistency issue for product decision.

- [ ] **Step 3: If validated expected rooms rank outside top 5, patch ranking**

When `expected_room_id in room_validated_room_ids` but not in `room_final_room_ids[:5]`, add a test in `backend/tests/unit/rag/test_ranking.py` proving the needed scoring correction. Tune ranking only for validated rooms.

Run:

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_ranking.py tests/unit/rag/test_room_v2.py -q
```

- [ ] **Step 4: Re-run live eval after room fixes**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_rag_v2 \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected: Room hit@5 reaches >= 85%, or diagnostic report identifies invalid/inactive room labels requiring product decision.

## Task 7: Final Verification And Documentation

**Files:**
- Update: `reports/rag-v2-live-evaluation-report.md`
- Update: `reports/rag-v2-hit-rate-root-cause-analysis.md`
- Update: `reports/rag-v2-diagnostic-report.md`
- Update: `docs/tests/verification-log.md`
- Update: `docs/plans/current-plan.md`
- Update: `docs/plans/next-steps.md`
- Update: `progress/current-plan.md`
- Update: `progress/next-steps.md`
- Update: `progress/completed.md` or `progress/known-issues.md`

- [ ] **Step 1: Run required focused tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/interaction -q
uv run pytest tests/unit/rag tests/unit/evals/test_run_rag_v2.py -q
uv run pytest tests/unit/harness/test_routing.py tests/unit/harness/modules/test_rag_v2.py -q
```

Expected: all pass.

- [ ] **Step 2: Run required evals**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_interaction_intent_eval --cases evals/datasets/interaction_intent_cases.yaml
uv run python -m evals.runners.run_rag_v2 \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected:

- interaction intent exact_rate remains 1.0
- KB source hit@3 >= 90%
- Room hit@5 >= 85%, unless documented data consistency blockers remain
- High-risk fallback = 100%
- Unvalidated rooms = 0

- [ ] **Step 3: Run full backend tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/ -q
```

Expected: all pass. Record the exact count and warnings.

- [ ] **Step 4: Run legacy RAG source scan**

```bash
cd "AptGuide 2.0/backend"
rg -n "aptguide2\\.rag\\.pipeline[^_]|RagBaselineProcedure|rag_mvp_baseline|from aptguide2\\.rag\\.kb_retrieval|from aptguide2\\.rag\\.room_retrieval" src tests evals
```

Expected: no legacy runtime matches. Guard-test assertions are acceptable if they intentionally prevent old RAG reintroduction.

- [ ] **Step 5: Update documentation**

Append a new section to `docs/tests/verification-log.md`:

```markdown
## 2026-05-14 - RAG Diagnostic-First Retrieval Optimization

**Focused tests:** ...
**Interaction intent eval:** ...
**RAG v2 live eval:** ...
**Backend full:** ...
**Legacy source scan:** ...

### Metrics

| Metric | Value | Gate | Status |
| --- | ---: | ---: | --- |
| KB source hit@3 | ... | >= 90% | ... |
| Room hit@5 | ... | >= 85% | ... |
| High-risk fallback | ... | = 100% | ... |
| Unvalidated rooms | ... | = 0 | ... |
```

Update plan/progress files with factual status only. If any gate fails due to data inconsistency, write that into `progress/known-issues.md` and do not mark the optimization complete.

## Final Worker Response Requirements

The executing worker must report:

- Current live RAG v2 metrics.
- Which failure types were fixed.
- Which cases still fail and why.
- Which tests/evals were run.
- Whether KB hit@3 >= 90%, Room hit@5 >= 85%, High-risk fallback = 100%, and Unvalidated rooms = 0 were achieved.

## Self-Review

- Scope is limited to RAG retrieval quality and eval diagnostics.
- The plan starts by fixing measurement validity before retrieval tuning.
- Every optimization path is conditional on diagnostic evidence.
- Room validation is preserved.
- Old RAG reintroduction is explicitly forbidden and verified by source scan.
- Documentation updates are required before completion.
