# AptGuide 2.0 RAG v2 Full Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop AptGuide 2.0 from using any legacy/MVP RAG runtime path and make RAG v2 the only callable RAG implementation for product runtime, harness runtime, and RAG evaluation.

**Architecture:** Product `/chat` already enters the harness and registers `RagV2Procedure`, but `pipeline_v2.py` still calls old retrieval modules (`retrieve_kb`, `retrieve_rooms`) and legacy `rag/pipeline.py` plus `RagBaselineProcedure` remain importable. This plan adds hard wiring guards, migrates v2 runtime to v2-native retrieval contracts, removes legacy callable paths, and updates eval/reporting so future hit-rate debugging cannot accidentally measure old RAG.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest, Milvus `VectorAdapter`, AptGuide harness `ProcedureRuntime`, lease validation through `ToolRuntimeRoomValidator`, YAML eval runners.

---

## 0. User Requirement Description

The user has repeatedly asked to stop using the old RAG implementation. The urgent requirement is:

1. Scan the codebase and identify every place where old/MVP RAG is still callable.
2. Ensure AptGuide 2.0 no longer uses old RAG for product runtime, harness runtime, or eval runtime.
3. Replace legacy RAG internals with the new RAG v2 path rather than keeping v2 as a wrapper around old retrieval functions.
4. Add tests that fail if old RAG is imported, registered, called, or silently used again.
5. Preserve mandatory safety rules:
   - room recommendations must pass lease validation;
   - KB answers must be source-bound;
   - high-risk questions must not become free-form policy promises;
   - no mock backend should be registered in runtime.
6. Only after old RAG is fully removed from runtime should hit-rate optimization continue.

## 1. Current Code Findings

| Path | Finding | Required decision |
| --- | --- | --- |
| `backend/src/aptguide2/rag/pipeline.py` | Legacy/MVP direct RAG pipeline still exists and is imported by tests and baseline adapter. | Remove from callable runtime or move outside active runtime package. |
| `backend/src/aptguide2/harness/modules/rag/baseline.py` | `RagBaselineProcedure` imports `aptguide2.rag.pipeline.run_pipeline`. | Delete or quarantine; runtime must never reference it. |
| `backend/src/aptguide2/rag/pipeline_v2.py` | Builds `RetrievalPlan`, but KB path calls old `retrieve_kb(qr, ...)` and room path calls old `retrieve_rooms(qr, ...)`. | Replace with v2-native retrieval orchestration. |
| `backend/src/aptguide2/rag/kb_retrieval.py` | MVP KB dense recall plus light keyword rerank. | Stop importing from v2 runtime; replace with `kb_v2.py`. |
| `backend/src/aptguide2/rag/room_retrieval.py` | MVP room vector recall. | Stop importing from v2 runtime; replace with `room_v2.py`. |
| `backend/tests/e2e/test_pipeline.py` | Imports old `aptguide2.rag.pipeline.run_pipeline`. | Replace with v2/harness tests or delete after equivalent coverage exists. |
| `backend/tests/unit/harness/modules/rag/test_baseline.py` | Tests old baseline adapter. | Delete or convert into a guard proving baseline adapter no longer exists. |
| `backend/tests/unit/api/test_mainline_wiring.py` | Has some guard tests, but does not block `pipeline_v2.py` from calling old retrieval functions. | Expand guard tests. |

## 2. Non-Negotiable Constraints

- Do not preserve old RAG as a fallback path.
- Do not keep `RagBaselineProcedure` importable from runtime modules.
- Do not let `pipeline_v2.py` call MVP `retrieve_kb()` or `retrieve_rooms()`.
- Do not remove lease validation when replacing room retrieval.
- Do not weaken high-risk KB confidence gates.
- Do not change eval cases merely to improve hit-rate.
- Do not mark the task complete until guard tests prove old RAG cannot be called.

## 3. Target File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `backend/src/aptguide2/rag/pipeline_v2.py` | Modify | Become the only RAG runtime orchestration path. |
| `backend/src/aptguide2/rag/kb_v2.py` | Create | V2-native KB retrieval using retrieval plan, dense recall, sparse scoring, hybrid merge, governed rerank, and confidence gate. |
| `backend/src/aptguide2/rag/room_v2.py` | Create | V2-native room retrieval using retrieval plan, dense recall, metadata filters, lease validation, and final ranking. |
| `backend/src/aptguide2/rag/pipeline.py` | Delete/quarantine | Retire old product RAG pipeline. |
| `backend/src/aptguide2/harness/modules/rag/baseline.py` | Delete/quarantine | Retire old harness adapter. |
| `backend/src/aptguide2/api/deps.py` | Verify | Register only `RagV2Procedure`. |
| `backend/evals/runners/run_rag_v2.py` | Modify | Record v2 diagnostic traces and never call old RAG. |
| `backend/tests/unit/api/test_mainline_wiring.py` | Modify | Add hard guards against legacy RAG imports and v2-to-MVP calls. |
| `backend/tests/unit/rag/test_pipeline_v2_no_legacy.py` | Create | Verify v2 pipeline does not import or call legacy retrieval modules. |
| `backend/tests/unit/rag/test_kb_v2.py` | Create | Verify KB v2 uses plan/hybrid/rerank and preserves confidence behavior. |
| `backend/tests/unit/rag/test_room_v2.py` | Create | Verify room v2 validates through lease and ranks only validated rooms. |
| `backend/tests/e2e/test_pipeline.py` | Delete/replace | Remove old `run_pipeline` e2e coverage. |
| `backend/tests/unit/harness/modules/rag/test_baseline.py` | Delete/replace | Remove old baseline adapter coverage. |
| `reports/rag-v2-hit-rate-root-cause-analysis.md` | Update | Add post-replacement evidence. |

## 4. Task 1: Add Hard Legacy-RAG Guard Tests

**Files:**
- Modify: `backend/tests/unit/api/test_mainline_wiring.py`
- Create: `backend/tests/unit/rag/test_pipeline_v2_no_legacy.py`

- [ ] **Step 1: Add wiring guards that fail on current code**

Add tests that scan runtime source files:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pipeline_v2_does_not_call_mvp_retrieval_functions() -> None:
    source = read("src/aptguide2/rag/pipeline_v2.py")

    assert "from aptguide2.rag.kb_retrieval import retrieve_kb" not in source
    assert "from aptguide2.rag.room_retrieval import retrieve_rooms" not in source
    assert "retrieve_kb(qr" not in source
    assert "retrieve_rooms(qr" not in source


def test_runtime_does_not_expose_rag_baseline_adapter() -> None:
    baseline = ROOT / "src/aptguide2/harness/modules/rag/baseline.py"

    assert not baseline.exists()
```

- [ ] **Step 2: Run the guards and confirm they fail**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/api/test_mainline_wiring.py tests/unit/rag/test_pipeline_v2_no_legacy.py -q
```

Expected before implementation: failure showing `pipeline_v2.py` still imports/calls MVP retrieval or `baseline.py` still exists.

## 5. Task 2: Create V2-Native KB Retrieval

**Files:**
- Create: `backend/src/aptguide2/rag/kb_v2.py`
- Test: `backend/tests/unit/rag/test_kb_v2.py`

- [ ] **Step 1: Write tests for plan-driven KB v2 behavior**

Test expectations:

- accepts a `RetrievalPlan`;
- uses `plan.semantic_queries`;
- creates dense candidates from vector search;
- creates sparse scores from source title/content;
- calls `rerank_kb_sources`;
- returns `KBSource` list and confidence decision;
- does not import `retrieve_kb`.

- [ ] **Step 2: Implement `retrieve_kb_v2`**

Required signature:

```python
def retrieve_kb_v2(
    plan: RetrievalPlan,
    vector_adapter: VectorAdapter,
    embed_fn,
    top_k: int = 10,
) -> tuple[list[KBSource], bool]:
    ...
```

Implementation contract:

1. Iterate over `plan.semantic_queries`.
2. Embed each query and call `vector_adapter.search_kb(...)`.
3. Convert dense results to `HybridCandidate`.
4. Compute sparse scores with `sparse_score(plan.raw_message, title + content)`.
5. Merge duplicate chunks with `merge_hybrid_candidates`.
6. Rerank with `rerank_kb_sources`.
7. Convert final candidates to `KBSource`.
8. Run `check_confidence(sources, plan.risk_level)`.

- [ ] **Step 3: Run focused tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_kb_v2.py tests/unit/rag/test_rerank.py tests/unit/rag/test_hybrid.py -q
```

Expected: all pass.

## 6. Task 3: Create V2-Native Room Retrieval

**Files:**
- Create: `backend/src/aptguide2/rag/room_v2.py`
- Test: `backend/tests/unit/rag/test_room_v2.py`

- [ ] **Step 1: Write tests for validated room v2 behavior**

Test expectations:

- accepts a `RetrievalPlan`;
- uses `plan.semantic_queries`;
- builds hard filters from `plan.hard_filters`;
- calls `vector_adapter.search_rooms`;
- sends candidate IDs to `validate_room_candidates`;
- never ranks unvalidated rooms;
- returns empty result if lease validation returns no rooms.

- [ ] **Step 2: Implement `retrieve_ranked_rooms_v2`**

Required signature:

```python
def retrieve_ranked_rooms_v2(
    plan: RetrievalPlan,
    query_result: QueryUnderstandingResult,
    vector_adapter: VectorAdapter,
    embed_fn,
    lease_validator: LeaseRoomValidator,
    top_n: int = 5,
    top_k: int = 30,
) -> list[RankedRoom]:
    ...
```

Implementation contract:

1. Iterate over `plan.semantic_queries`.
2. Embed each query and call `vector_adapter.search_rooms(vector, filters=plan.hard_filters, top_k=top_k)`.
3. Deduplicate candidates by room ID.
4. Validate all candidates through `validate_room_candidates(candidates, plan.hard_filters, lease_validator)`.
5. Rank only validated rooms with `rank_rooms`.
6. Return top N ranked rooms.

- [ ] **Step 3: Run focused tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_room_v2.py tests/unit/rag/test_validation.py tests/unit/rag/test_ranking.py -q
```

Expected: all pass.

## 7. Task 4: Rewire Pipeline v2 To V2-Native Modules

**Files:**
- Modify: `backend/src/aptguide2/rag/pipeline_v2.py`
- Test: `backend/tests/unit/rag/test_pipeline_v2_trace.py`
- Test: `backend/tests/unit/rag/test_pipeline_v2_no_legacy.py`
- Test: `backend/tests/unit/harness/modules/test_rag_v2.py`

- [ ] **Step 1: Replace old imports**

Remove imports of `retrieve_kb`, `retrieve_rooms`, direct ranking, and direct validation from `pipeline_v2.py`. Add:

```python
from aptguide2.rag.kb_v2 import retrieve_kb_v2
from aptguide2.rag.room_v2 import retrieve_ranked_rooms_v2
```

- [ ] **Step 2: Rewire KB branch**

Replace:

```python
sources, is_confident = retrieve_kb(qr, vector_adapter, embed_fn)
```

with:

```python
sources, is_confident = retrieve_kb_v2(plan, vector_adapter, embed_fn)
```

- [ ] **Step 3: Rewire room branch**

Replace candidate retrieval + validation + ranking with:

```python
ranked = retrieve_ranked_rooms_v2(
    plan=plan,
    query_result=qr,
    vector_adapter=vector_adapter,
    embed_fn=embed_fn,
    lease_validator=lease_validator,
    top_n=top_n_rooms,
)
```

If `ranked` is empty, return the existing `lease_validation_empty` fallback message.

- [ ] **Step 4: Run v2 pipeline tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag/test_pipeline_v2_no_legacy.py tests/unit/rag/test_pipeline_v2_trace.py tests/unit/harness/modules/test_rag_v2.py -q
```

Expected: all pass.

## 8. Task 5: Retire Legacy Callable RAG

**Files:**
- Delete/quarantine: `backend/src/aptguide2/rag/pipeline.py`
- Delete/quarantine: `backend/src/aptguide2/harness/modules/rag/baseline.py`
- Modify/delete: `backend/tests/e2e/test_pipeline.py`
- Modify/delete: `backend/tests/unit/harness/modules/rag/test_baseline.py`
- Modify: `backend/tests/unit/api/test_mainline_wiring.py`

- [ ] **Step 1: Remove old runtime adapter**

Remove `backend/src/aptguide2/harness/modules/rag/baseline.py` or move it outside `src/aptguide2` so it is not importable by runtime code.

- [ ] **Step 2: Remove old direct pipeline test**

Delete or replace `backend/tests/e2e/test_pipeline.py`, because it imports:

```python
from aptguide2.rag.pipeline import run_pipeline
```

Replacement coverage should exercise `RagV2Procedure` through the harness or `run_pipeline_v2`.

- [ ] **Step 3: Replace baseline adapter tests with guard tests**

Delete `backend/tests/unit/harness/modules/rag/test_baseline.py` or rewrite it to assert the baseline adapter file no longer exists.

- [ ] **Step 4: Run legacy scan**

```bash
cd "AptGuide 2.0/backend"
rg -n "aptguide2\\.rag\\.pipeline|RagBaselineProcedure|rag_mvp_baseline|run_pipeline\\(" src tests
```

Expected: no runtime import or callable test remains. Historical docs may mention old names, but `src/` and active tests must not call them.

## 9. Task 6: Update RAG v2 Eval Reporting So Old RAG Cannot Hide Again

**Files:**
- Modify: `backend/evals/runners/run_rag_v2.py`
- Test: `backend/tests/unit/evals/test_run_rag_v2.py`

- [ ] **Step 1: Add per-case runtime metadata**

For every case, report:

- `pipeline: rag_v2`;
- parsed task;
- expected case type;
- fallback reason;
- actual doc IDs or room IDs;
- whether result came from v2 metadata.

- [ ] **Step 2: Add a runner guard**

The runner must import only:

```python
from aptguide2.rag.pipeline_v2 import run_pipeline_v2
```

It must not import `aptguide2.rag.pipeline`, `retrieve_kb`, or `retrieve_rooms`.

- [ ] **Step 3: Run eval runner tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py -q
```

Expected: all pass.

## 10. Task 7: Full Verification

**Files:**
- Update: `reports/rag-v2-hit-rate-root-cause-analysis.md`
- Update: `docs/tests/verification-log.md`
- Update: `docs/plans/execution-log.md`

- [ ] **Step 1: Run focused RAG and wiring tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/api/test_mainline_wiring.py tests/unit/rag tests/unit/harness/modules/test_rag_v2.py tests/unit/evals/test_run_rag_v2.py -q
```

Expected: all pass.

- [ ] **Step 2: Run full backend tests**

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/ -q
```

Expected: pass, or record exact failures as blockers.

- [ ] **Step 3: Run source scan**

```bash
cd "AptGuide 2.0/backend"
rg -n "aptguide2\\.rag\\.pipeline|RagBaselineProcedure|rag_mvp_baseline|retrieve_kb\\(|retrieve_rooms\\(" src tests
```

Expected:

- no `aptguide2.rag.pipeline` import;
- no `RagBaselineProcedure`;
- no `rag_mvp_baseline`;
- no v2 runtime call to MVP `retrieve_kb` or `retrieve_rooms`.

- [ ] **Step 4: Run live RAG v2 eval only after old-RAG scan passes**

```bash
cd "AptGuide 2.0/backend"
uv run python evals/runners/run_rag_v2.py \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected:

- report identifies pipeline as `rag_v2`;
- no old RAG path appears in report metadata;
- hit-rate may still fail, but failures are now true v2 failures rather than old-RAG contamination.

## 11. Completion Criteria

This plan is complete only when:

- `pipeline_v2.py` no longer imports or calls old MVP retrieval functions;
- old direct `rag/pipeline.py` is not callable by product runtime or active tests;
- `RagBaselineProcedure` is removed or non-importable from runtime modules;
- API/harness runtime registers only `RagV2Procedure` for RAG routes;
- RAG v2 eval runner cannot call old RAG;
- guard tests fail if old RAG is reintroduced;
- verification log records the source scan and test results.
