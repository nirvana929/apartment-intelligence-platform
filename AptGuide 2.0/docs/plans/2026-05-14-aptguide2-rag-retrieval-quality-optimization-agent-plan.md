# AptGuide 2.0 RAG Retrieval Quality Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise live RAG v2 retrieval quality from the current baseline of KB hit@3=48.6% and Room hit@5=40% to the project gates of KB hit@3 >= 90% and Room hit@5 >= 85%, while preserving high-risk fallback at 100% and unvalidated room count at 0.

**Architecture:** Treat retrieval quality as a staged pipeline problem, not a single ranking tweak. First create post-full-replacement diagnostics, then fix task routing so KB cases actually enter KB retrieval, then tune v2-native KB recall/rerank, then diagnose room recall versus lease validation. Risk-aware guardrail work remains separate: it owns `risk_level` and `response_mode`; this plan owns `task` routing, retrieval evidence, recall, rerank, and eval gates.

**Tech Stack:** Python 3.13, Pydantic, pytest, YAML eval datasets, Milvus `VectorAdapter`, OpenAI-compatible embeddings, AptGuide RAG v2 (`query_understanding.py`, `planning.py`, `kb_v2.py`, `room_v2.py`, `pipeline_v2.py`), lease validation through `ToolRuntimeRoomValidator`.

---

## 0. Context And Non-Negotiable Constraints

### Current Evidence

- `reports/rag-v2-live-evaluation-report.md` from 2026-05-14 03:15 reports:
  - KB source hit@3 = 48.6% (gate >= 90%)
  - KB source hit@5 = 51.4%
  - Room hit@5 = 40.0% (gate >= 85%)
  - High-risk fallback = 100.0%
  - Unvalidated rooms = 0
- `docs/tests/verification-log.md` later confirms RAG v2 full replacement:
  - `pipeline_v2.py` imports `kb_v2.retrieve_kb_v2`
  - `pipeline_v2.py` imports `room_v2.retrieve_ranked_rooms_v2`
  - old `pipeline.py`, `kb_retrieval.py`, `room_retrieval.py`, and `baseline.py` are deleted
  - full backend suite: 376 passed
- A fresh static `understand_query()` check still shows failed KB cases routed to `fallback` or `room_search`. This is a task-routing gap, not a risk-guardrail conflict.

### Distinction From Risk Guardrail

The completed risk-aware query understanding plan changed:

- `risk_level`
- `response_mode`
- `risk_profile`

This plan changes:

- `task` routing into `kb_qa`, `room_search`, or `fallback`
- per-stage diagnostic evidence
- KB recall and rerank quality
- room recall, lease validation diagnosis, and ranking quality

Do not reframe this work as "risk detection is broken" unless a test proves a risk-profile regression.

### Guardrails

- Do not reintroduce legacy/MVP RAG.
- Do not change eval cases merely to improve metrics.
- Do not weaken high-risk fallback behavior.
- Do not display a room unless it passed lease validation.
- Do not bypass `ToolRuntimeRoomValidator`.
- Do not mark retrieval gates as passing without running live eval evidence.
- Do not optimize aggregate hit rates before separating routing, recall, rerank, validation, and data-label failures.

## 1. Target File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `backend/src/aptguide2/rag/query_understanding.py` | Modify | Improve business task routing for KB policy/life/payment/appointment questions without weakening room search. |
| `backend/tests/unit/rag/test_query_understanding.py` | Modify | Add regression tests for failed KB cases and anti-regression room-search cases. |
| `backend/src/aptguide2/rag/kb_v2.py` | Modify | Preserve v2-native retrieval, expose diagnostic information, and support improved recall inputs. |
| `backend/src/aptguide2/rag/room_v2.py` | Modify | Expose pre-validation and post-validation diagnostic evidence. |
| `backend/src/aptguide2/rag/planning.py` | Modify | Improve KB module intent and semantic query rewrites after routing is fixed. |
| `backend/src/aptguide2/rag/schemas.py` | Modify | Add diagnostic models only if plain dict trace evidence is not enough. |
| `backend/evals/runners/run_rag_v2.py` | Modify | Include parsed task, risk mode, doc IDs, room IDs, and fallback reasons in failed-case output. |
| `backend/evals/runners/run_rag_v2_diagnostics.py` | Create | Produce per-case diagnostic Markdown/JSON without changing retrieval behavior. |
| `backend/tests/unit/evals/test_run_rag_v2.py` | Modify | Cover richer failed-case metadata. |
| `backend/tests/unit/evals/test_run_rag_v2_diagnostics.py` | Create | Smoke-test diagnostic runner with fake dependencies. |
| `reports/rag-v2-hit-rate-root-cause-analysis.md` | Update | Mark fixed historical root causes and keep current root causes accurate. |
| `reports/rag-v2-diagnostic-report.md` | Create by runner | Store diagnostic evidence for routing, KB, and room failures. |
| `reports/rag-v2-live-evaluation-report.md` | Update by runner | Store final live eval evidence after fixes. |
| `docs/tests/verification-log.md` | Modify | Record focused tests, full backend tests, diagnostic runner, and live eval results. |

## 2. Success Criteria

The work is complete only when all criteria are met:

1. All 35 KB eval cases route to `kb_qa`, except cases intentionally classified as safe fallback by documented rule.
2. KB source hit@3 >= 90% on live RAG v2 eval.
3. Room hit@5 >= 85% on live RAG v2 eval, or a diagnostic report proves specific room cases are invalid/inactive and must be quarantined by product decision.
4. High-risk fallback remains 100%.
5. Unvalidated room count remains 0.
6. `uv run pytest tests/ -q` passes.
7. Source scan still proves no legacy RAG runtime path:

```bash
cd "AptGuide 2.0/backend"
rg -n "aptguide2\\.rag\\.pipeline[^_]|RagBaselineProcedure|rag_mvp_baseline|kb_retrieval|room_retrieval" src tests evals
```

Expected: no runtime matches for legacy imports. Documentation references are acceptable only if clearly historical.

## 3. Task 1: Establish Post-Replacement Baseline And Diagnostics

**Files:**
- Modify: `backend/evals/runners/run_rag_v2.py`
- Create: `backend/evals/runners/run_rag_v2_diagnostics.py`
- Modify: `backend/tests/unit/evals/test_run_rag_v2.py`
- Create: `backend/tests/unit/evals/test_run_rag_v2_diagnostics.py`
- Output: `reports/rag-v2-diagnostic-report.md`

- [ ] **Step 1: Add failed-case metadata test for KB eval**

Add this test to `backend/tests/unit/evals/test_run_rag_v2.py`:

```python
def test_eval_kb_failure_includes_query_understanding_metadata(monkeypatch):
    result_obj = SimpleNamespace(
        task="fallback",
        kb_sources=[],
        rooms=[],
        is_confident=False,
        fallback_reason="out_of_scope",
        query_understanding=SimpleNamespace(
            task="fallback",
            risk_level="low",
            response_mode="normal_answer",
            hard_filters={},
            soft_preferences=[],
        ),
    )

    monkeypatch.setattr(run_rag_v2, "run_pipeline_v2", lambda **kwargs: result_obj)

    deps = run_rag_v2.RagV2EvalDependencies(
        vector_adapter=object(),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=object(),
    )

    result = run_rag_v2.eval_kb_retrieval(
        {"query": "可以用花呗付房租吗", "expected_doc_ids": ["KB-PAY-002"]},
        deps,
    )

    assert result["status"] == "fail"
    assert result["reason"] == "no KB sources returned"
    assert result["parsed_task"] == "fallback"
    assert result["risk_level"] == "low"
    assert result["response_mode"] == "normal_answer"
    assert result["fallback_reason"] == "out_of_scope"
```

- [ ] **Step 2: Run the targeted eval tests and confirm failure**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py::test_eval_kb_failure_includes_query_understanding_metadata -q
```

Expected before implementation: fails because `eval_kb_retrieval()` does not include `parsed_task`, `risk_level`, `response_mode`, or `fallback_reason`.

- [ ] **Step 3: Add metadata extraction helper**

Modify `backend/evals/runners/run_rag_v2.py`:

```python
def extract_result_metadata(result: object) -> dict[str, Any]:
    qr = getattr(result, "query_understanding", None)
    return {
        "parsed_task": getattr(qr, "task", getattr(result, "task", "")),
        "risk_level": getattr(qr, "risk_level", ""),
        "response_mode": getattr(qr, "response_mode", ""),
        "hard_filters": dict(getattr(qr, "hard_filters", {}) or {}),
        "soft_preferences": list(getattr(qr, "soft_preferences", []) or []),
        "fallback_reason": getattr(result, "fallback_reason", ""),
    }
```

In each failure return path in `eval_kb_retrieval()` and `eval_room_retrieval()`, merge `extract_result_metadata(result)` into the returned dict.

- [ ] **Step 4: Run eval tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Create diagnostic runner smoke test**

Create `backend/tests/unit/evals/test_run_rag_v2_diagnostics.py`:

```python
from evals.runners import run_rag_v2_diagnostics


def test_group_failures_by_stage():
    failures = [
        {"case_id": "kb-005", "category": "kb_retrieval", "reason": "no KB sources returned", "parsed_task": "fallback"},
        {"case_id": "kb-018", "category": "kb_retrieval", "reason": "expected source not in top-5", "parsed_task": "kb_qa"},
        {"case_id": "room-002", "category": "room_retrieval", "reason": "no rooms returned", "parsed_task": "room_search"},
    ]

    grouped = run_rag_v2_diagnostics.group_failures_by_stage(failures)

    assert grouped["task_routing"] == ["kb-005"]
    assert grouped["kb_rerank_or_recall"] == ["kb-018"]
    assert grouped["room_recall_or_validation"] == ["room-002"]
```

- [ ] **Step 6: Create diagnostic runner**

Create `backend/evals/runners/run_rag_v2_diagnostics.py`:

```python
"""Diagnostic report helpers for RAG v2 evaluation failures."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def group_failures_by_stage(failures: list[dict[str, Any]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for failure in failures:
        case_id = failure.get("case_id", "unknown")
        category = failure.get("category", "")
        reason = failure.get("reason", "")
        parsed_task = failure.get("parsed_task", "")

        if category == "kb_retrieval" and parsed_task != "kb_qa":
            grouped["task_routing"].append(case_id)
        elif category == "kb_retrieval" and "top-5" in reason:
            grouped["kb_rerank_or_recall"].append(case_id)
        elif category == "kb_retrieval":
            grouped["kb_empty_after_retrieval"].append(case_id)
        elif category == "room_retrieval":
            grouped["room_recall_or_validation"].append(case_id)
        else:
            grouped["fallback_or_other"].append(case_id)
    return dict(grouped)
```

- [ ] **Step 7: Run diagnostic tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py tests/unit/evals/test_run_rag_v2_diagnostics.py -q
```

Expected: all tests pass.

- [ ] **Step 8: Run post-replacement live baseline**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_rag_v2 \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected: report regenerated with current v2-native runtime. Record exact metrics before making routing changes.

## 4. Task 2: Fix KB Versus Room Task Routing

**Files:**
- Modify: `backend/src/aptguide2/rag/query_understanding.py`
- Modify: `backend/tests/unit/rag/test_query_understanding.py`

- [ ] **Step 1: Add regression tests for failed KB routing cases**

Add this block to `backend/tests/unit/rag/test_query_understanding.py`:

```python
def test_kb_policy_questions_from_live_eval_route_to_kb():
    cases = [
        "可以用花呗付房租吗",
        "月付和季付有什么区别",
        "入住需要带什么",
        "房间空调坏了找谁修",
        "可以养宠物吗",
        "合租可以带朋友住吗",
        "租房需要什么材料",
        "电费怎么算",
        "可以转租吗",
        "公共区域卫生谁打扫",
        "预约后迟到怎么办",
        "换房间可以吗",
    ]

    for query in cases:
        result = understand_query(query)
        assert result.task == "kb_qa", query
```

- [ ] **Step 2: Add anti-regression tests for real room search**

Add this block to the same file:

```python
def test_room_search_with_payment_and_pet_preferences_stays_room_search():
    cases = [
        "找天河区3000以内可月付的房子",
        "帮我找可以养宠物的合租房",
        "番禺区2000以内适合考研",
        "白云区大面积低预算",
    ]

    for query in cases:
        result = understand_query(query)
        assert result.task == "room_search", query
```

- [ ] **Step 3: Run tests and confirm failure**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_query_understanding.py::test_kb_policy_questions_from_live_eval_route_to_kb tests/unit/rag/test_query_understanding.py::test_room_search_with_payment_and_pet_preferences_stays_room_search -q
```

Expected before implementation: KB routing test fails for current known cases.

- [ ] **Step 4: Implement policy-question task detector**

Modify `backend/src/aptguide2/rag/query_understanding.py`. Add this helper near `_detect_task()`:

```python
KB_POLICY_QUESTION_TERMS = (
    "可以", "能不能", "能否", "怎么", "怎么办", "怎么算", "谁", "需要",
    "区别", "有什么区别", "迟到", "坏了", "维修", "报修",
)

KB_BUSINESS_TERMS = (
    "花呗", "房租", "月付", "季付", "入住", "材料", "空调", "维修",
    "报修", "养宠物", "宠物", "合租", "朋友住", "租房", "电费",
    "水费", "公共区域", "卫生", "转租", "预约", "迟到", "换房间",
    "同住", "登记", "合同", "签约", "退租", "续租",
)

ROOM_SEARCH_ACTION_TERMS = (
    "找", "找房", "推荐", "有没有", "有吗", "看看", "帮我找",
    "帮我看看", "预算", "以内", "附近", "房源", "房子", "公寓",
)


def _looks_like_kb_policy_question(message: str) -> bool:
    has_question = any(term in message for term in KB_POLICY_QUESTION_TERMS)
    has_business_term = any(term in message for term in KB_BUSINESS_TERMS)
    has_room_search_action = any(term in message for term in ROOM_SEARCH_ACTION_TERMS)

    if not has_question or not has_business_term:
        return False

    if has_room_search_action and not any(term in message for term in ("怎么办", "怎么算", "区别", "谁", "需要")):
        return False

    return True
```

Then update `_detect_task()` after `fallback_patterns` and before `kb_keywords`:

```python
    if _looks_like_kb_policy_question(message):
        return "kb_qa"
```

- [ ] **Step 5: Run query-understanding tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_query_understanding.py tests/unit/rag/test_risk_detection.py tests/unit/rag/test_planning.py -q
```

Expected: all pass. If risk tests fail, do not weaken risk guardrail; adjust only task-routing conditions.

## 5. Task 3: Improve KB Planning And Module Intent

**Files:**
- Modify: `backend/src/aptguide2/rag/planning.py`
- Modify: `backend/tests/unit/rag/test_planning.py`

- [ ] **Step 1: Add planning tests for newly routed KB categories**

Add to `backend/tests/unit/rag/test_planning.py`:

```python
def test_kb_payment_policy_plan_uses_payment_module():
    qr = understand_query("可以用花呗付房租吗")
    plan = build_retrieval_plan(qr)

    assert plan.task == "kb_qa"
    assert plan.module_intent == "payment"
    assert any("支付" in query or "租金" in query for query in plan.semantic_queries)


def test_kb_life_policy_plan_uses_life_module():
    qr = understand_query("房间空调坏了找谁修")
    plan = build_retrieval_plan(qr)

    assert plan.task == "kb_qa"
    assert plan.module_intent == "life"
    assert any("维修" in query or "生活" in query for query in plan.semantic_queries)


def test_kb_appointment_policy_plan_uses_appointment_module():
    qr = understand_query("预约后迟到怎么办")
    plan = build_retrieval_plan(qr)

    assert plan.task == "kb_qa"
    assert plan.module_intent == "appointment"
    assert any("预约" in query or "看房" in query for query in plan.semantic_queries)
```

- [ ] **Step 2: Run planning tests and confirm failure if module rewrites are incomplete**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_planning.py -q
```

Expected before implementation: at least life/payment/appointment rewrite expectations may fail.

- [ ] **Step 3: Extend module intent terms**

Modify `_infer_kb_module_intent()` in `backend/src/aptguide2/rag/planning.py`:

```python
module_terms = {
    "lease": ("合同", "租约", "签约", "退租", "押金", "续租", "违约", "转租", "入住", "材料", "换房间"),
    "payment": ("支付", "租金", "房租", "水电", "水费", "电费", "退款", "发票", "逾期", "花呗", "月付", "季付"),
    "appointment": ("预约", "看房", "取消", "改期", "迟到"),
    "life": ("报修", "维修", "噪音", "宠物", "养宠物", "电器", "空调", "卫生", "公共区域", "快递", "朋友住", "合租"),
    "account": ("注册", "密码", "实名", "隐私", "注销", "账号"),
    "policy": ("优惠", "投诉", "换锁", "安全", "同住", "节假日"),
}
```

- [ ] **Step 4: Extend step-back queries**

Modify `_step_back_query()`:

```python
if module_intent == "life":
    return f"入住生活 报修 维修 宠物 卫生 同住 规则 {message}"
if module_intent == "appointment":
    return f"看房预约 迟到 取消 改期 流程 {message}"
```

- [ ] **Step 5: Run planning and KB unit tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_planning.py tests/unit/rag/test_kb_v2.py tests/unit/rag/test_rerank.py -q
```

Expected: all pass.

## 6. Task 4: Improve KB v2 Recall And Rerank With Evidence

**Files:**
- Modify: `backend/src/aptguide2/rag/kb_v2.py`
- Modify: `backend/src/aptguide2/rag/rerank.py`
- Modify: `backend/tests/unit/rag/test_kb_v2.py`
- Modify: `backend/tests/unit/rag/test_rerank.py`

- [ ] **Step 1: Add regression tests for module-intent rerank**

Add to `backend/tests/unit/rag/test_rerank.py`:

```python
def test_rerank_prefers_matching_module_when_dense_scores_are_close():
    plan = RetrievalPlan(
        task="kb_qa",
        raw_message="可以用花呗付房租吗",
        module_intent="payment",
        risk_level="low",
    )
    candidates = [
        HybridCandidate(
            id="life-1",
            dense_score=0.82,
            sparse_score=0.1,
            payload={"module": "life", "content": "房间生活规则", "title": "生活规则"},
        ),
        HybridCandidate(
            id="pay-1",
            dense_score=0.78,
            sparse_score=0.8,
            payload={"module": "payment", "content": "花呗支付房租规则", "title": "支付方式"},
        ),
    ]

    reranked = rerank_kb_sources(candidates, plan)

    assert reranked[0].id == "pay-1"
```

- [ ] **Step 2: Run rerank tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_rerank.py -q
```

Expected: pass if current weights already support this; fail if dense score dominates too much.

- [ ] **Step 3: Tune only explicit feature weights if test fails**

If needed, adjust `RerankWeights` in `backend/src/aptguide2/rag/rerank.py` with a bounded change:

```python
class RerankWeights(BaseModel):
    dense_score: float = 0.30
    sparse_score: float = 0.20
    module_match: float = 0.25
    risk_match: float = 0.10
    validation_score: float = 0.10
    lexical_score: float = 0.05
```

Do not increase character-overlap/lexical score beyond 0.05.

- [ ] **Step 4: Run KB-focused tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_kb_v2.py tests/unit/rag/test_rerank.py tests/unit/rag/test_hybrid.py tests/unit/rag/test_sparse.py -q
```

Expected: all pass.

- [ ] **Step 5: Run live eval and inspect KB failures**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_rag_v2 \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected:

- KB no-source failures caused by task routing should drop sharply.
- Remaining KB failures should be `expected source not in top-5`, not `no KB sources returned`.
- If KB hit@3 is still below 90%, inspect failed cases before changing weights again.

## 7. Task 5: Diagnose Room Recall Versus Lease Validation

**Files:**
- Modify: `backend/src/aptguide2/rag/room_v2.py`
- Modify: `backend/tests/unit/rag/test_room_v2.py`
- Modify: `backend/evals/runners/run_rag_v2.py`

- [ ] **Step 1: Add test proving room diagnostics expose raw and validated IDs**

Add to `backend/tests/unit/rag/test_room_v2.py`:

```python
def test_room_v2_can_return_diagnostics_for_validation_empty():
    diagnostics = {}

    ranked = retrieve_ranked_rooms_v2(
        plan=RetrievalPlan(
            task="room_search",
            raw_message="番禺区2000以内适合考研",
            hard_filters={"district_id": 4, "max_rent": 2000},
            semantic_queries=["番禺区2000以内适合考研"],
        ),
        query_result=QueryUnderstandingResult(raw_message="番禺区2000以内适合考研", task="room_search"),
        vector_adapter=FakeRoomVectorAdapter(room_ids=[200098, 200105]),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=FakeLeaseValidator(valid_room_ids=[]),
        diagnostics=diagnostics,
    )

    assert ranked == []
    assert diagnostics["raw_room_ids"] == [200098, 200105]
    assert diagnostics["validated_room_ids"] == []
```

If the existing test fakes use different names, keep the assertion behavior and adapt imports to existing helpers.

- [ ] **Step 2: Run room test and confirm failure**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_room_v2.py::test_room_v2_can_return_diagnostics_for_validation_empty -q
```

Expected before implementation: fails because `retrieve_ranked_rooms_v2()` has no `diagnostics` parameter.

- [ ] **Step 3: Add optional diagnostics parameter**

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
    diagnostics["raw_room_ids"] = list(best_by_room.keys())
    diagnostics["hard_filters"] = dict(plan.hard_filters)
    diagnostics["semantic_queries"] = list(plan.semantic_queries)
```

After validation:

```python
if diagnostics is not None:
    diagnostics["validated_room_ids"] = [room.get("room_id") for room in validated]
```

- [ ] **Step 4: Run room tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_room_v2.py tests/unit/rag/test_validation.py tests/unit/rag/test_ranking.py -q
```

Expected: all pass.

- [ ] **Step 5: Run live eval and classify room failures**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_rag_v2 \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected diagnostic decision:

- Expected room ID absent from raw IDs: recall/query/index issue.
- Expected room ID present in raw IDs but absent from validated IDs: lease data/filter issue.
- Expected room ID validated but below top 5: ranking issue.

## 8. Task 6: Validate Eval Data Consistency

**Files:**
- Create: `backend/evals/runners/check_rag_v2_data_consistency.py`
- Create: `backend/tests/unit/evals/test_check_rag_v2_data_consistency.py`
- Output: `reports/rag-v2-data-consistency-report.md`

- [ ] **Step 1: Add pure helper tests**

Create `backend/tests/unit/evals/test_check_rag_v2_data_consistency.py`:

```python
from evals.runners import check_rag_v2_data_consistency as checker


def test_flag_room_hard_filter_mismatch():
    case = {
        "id": "room-004",
        "query": "番禺区2000以内适合考研",
        "hard_filters": {"district_id": 5},
    }

    issues = checker.detect_static_case_issues(case)

    assert "query_mentions_panyu_but_filter_is_not_4" in issues


def test_payment_kb_case_has_expected_source():
    case = {
        "id": "kb-005",
        "query": "可以用花呗付房租吗",
        "expected_sources": ["KB-PAY-002"],
    }

    issues = checker.detect_static_case_issues(case)

    assert issues == []
```

- [ ] **Step 2: Create static consistency checker**

Create `backend/evals/runners/check_rag_v2_data_consistency.py`:

```python
"""Static and live data consistency checks for RAG v2 eval cases."""

from __future__ import annotations

from typing import Any


def detect_static_case_issues(case: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    query = case.get("query", "")
    hard_filters = case.get("hard_filters", {}) or {}

    if "番禺" in query and hard_filters.get("district_id") not in (None, 4):
        issues.append("query_mentions_panyu_but_filter_is_not_4")
    if "白云" in query and hard_filters.get("district_id") not in (None, 5):
        issues.append("query_mentions_baiyun_but_filter_is_not_5")
    if case.get("case_type") == "kb_retrieval" and not case.get("expected_sources", case.get("expected_doc_ids", [])):
        issues.append("kb_case_missing_expected_sources")
    if case.get("case_type") == "room_retrieval" and not case.get("positive_room_ids", case.get("expected_room_ids", [])):
        issues.append("room_case_missing_positive_room_ids")

    return issues
```

- [ ] **Step 3: Run checker tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_check_rag_v2_data_consistency.py -q
```

Expected: all pass.

- [ ] **Step 4: Generate data consistency report**

Extend the checker with a CLI that reads `evals/datasets/rag_mvp_eval_cases.yaml` and writes `../reports/rag-v2-data-consistency-report.md`.

Run:

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.check_rag_v2_data_consistency \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-data-consistency-report.md
```

Expected: report identifies static label mismatches such as room district mismatches without modifying the dataset.

## 9. Task 7: Update Root-Cause Report And Verification Logs

**Files:**
- Modify: `reports/rag-v2-hit-rate-root-cause-analysis.md`
- Modify: `docs/tests/verification-log.md`
- Modify: `docs/plans/next-steps.md`

- [ ] **Step 1: Update root-cause report status**

In `reports/rag-v2-hit-rate-root-cause-analysis.md`, add a top section:

```markdown
## Post-Report Status Update

This report was originally written against the 2026-05-14 03:15 live eval and the pre-full-replacement RAG runtime.

Later updates changed the root-cause status:

- Risk-aware query understanding guardrail completed at 2026-05-14 20:04. It fixed `risk_level`, `response_mode`, and `risk_profile`; it did not fully fix business `task` routing.
- RAG v2 full replacement completed at 2026-05-14 20:25. The old MVP RAG runtime was removed, and `pipeline_v2.py` now calls `retrieve_kb_v2()` and `retrieve_ranked_rooms_v2()`.
- Therefore the old H2 claim that v2 hybrid/rerank is not wired into `pipeline_v2.py` is historical and resolved.
- The current leading root cause is KB task routing coverage: policy/payment/life/appointment questions can still be classified as `fallback` or `room_search` before retrieval.
```

- [ ] **Step 2: Mark old H2 as resolved**

Change H2 status to:

```markdown
Status: historical root cause, resolved by RAG v2 full replacement. Keep as timeline evidence only; do not use it to explain current post-replacement metrics.
```

- [ ] **Step 3: Add verification log entry**

Append to `docs/tests/verification-log.md`:

```markdown
## 2026-05-14 — RAG Retrieval Quality Optimization

**Task-routing focused:** `uv run pytest tests/unit/rag/test_query_understanding.py tests/unit/rag/test_planning.py -q`
**Result:** Write the exact pytest summary from the command run in this task.

**Eval diagnostics:** `uv run pytest tests/unit/evals/test_run_rag_v2.py tests/unit/evals/test_run_rag_v2_diagnostics.py tests/unit/evals/test_check_rag_v2_data_consistency.py -q`
**Result:** Write the exact pytest summary from the command run in this task.

**Live RAG v2 eval:** `uv run python -m evals.runners.run_rag_v2 --cases evals/datasets/rag_mvp_eval_cases.yaml --report ../reports/rag-v2-live-evaluation-report.md`
**Result:** record exact KB hit@3, Room hit@5, high-risk fallback, and unvalidated room count.
```

Do not write "passed" or "failed" from memory. Copy the exact command summaries and metric values from the terminal output before completing the task.

## 10. Task 8: Final Verification Gate

**Files:**
- No new code files unless previous tasks require fixes.

- [ ] **Step 1: Run focused RAG tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag tests/unit/evals/test_run_rag_v2.py tests/unit/evals/test_run_rag_v2_diagnostics.py tests/unit/evals/test_check_rag_v2_data_consistency.py -q
```

Expected: all pass.

- [ ] **Step 2: Run full backend tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/ -q
```

Expected: all pass. Existing warnings must be recorded, not hidden.

- [ ] **Step 3: Run source scan**

```bash
cd "AptGuide 2.0/backend"
rg -n "aptguide2\\.rag\\.pipeline[^_]|RagBaselineProcedure|rag_mvp_baseline|from aptguide2\\.rag\\.kb_retrieval|from aptguide2\\.rag\\.room_retrieval" src tests evals
```

Expected: no matches.

- [ ] **Step 4: Run live dependency eval**

```bash
cd "AptGuide 2.0/backend"
uv run python -m evals.runners.run_rag_v2 \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected:

- KB source hit@3 >= 90%
- Room hit@5 >= 85%, or documented data inconsistency decision exists
- High-risk fallback = 100%
- Unvalidated rooms = 0

- [ ] **Step 5: Update project next steps**

If all gates pass, move RAG retrieval quality improvement from active/immediate to completed in:

- `docs/plans/next-steps.md`
- `progress/next-steps.md`
- `progress/current-plan.md`

If any gate fails, leave it active and record the exact remaining failure class in `progress/known-issues.md`.

## 11. Execution Notes

- Work in this order. Do not tune rerank before routing diagnostics are visible.
- Keep commits small if committing:
  1. diagnostic metadata
  2. task routing tests and fix
  3. planning/module intent improvements
  4. KB rerank adjustments
  5. room diagnostics and data consistency report
  6. docs and verification updates
- Do not use live services in unit tests.
- Do not update final project state to "passed" without the live eval command output.
