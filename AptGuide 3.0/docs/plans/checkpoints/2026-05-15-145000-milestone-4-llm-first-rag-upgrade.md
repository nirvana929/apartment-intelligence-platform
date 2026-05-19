# Checkpoint: Milestone 4: LLM-first RAG Upgrade

## Metadata

- Created at: 2026-05-15T14:50:00+08:00
- Task: Milestone 4: LLM-first RAG Upgrade
- Status: complete
- Test status: 207 passed, 33 skipped (28 existing + 5 new RAG live), ruff clean

## Goal

Upgrade AptGuide 3.0 from direct lease-client calls to a full LLM-first RAG pipeline: vector recall, lease validation, LLM preference scoring, deterministic score fusion, KB multi-query recall, rerank, confidence gates, sync scripts, eval metrics, and anti-regression guardrails.

## Context

Plan: `docs/plans/2026-05-15-aptguide3-llm-first-rag-upgrade-plan.md`
Milestone 3 (Procedure Integration) was complete with 129 tests. This milestone adds the RAG retrieval layer.

## Completed Work

### Wave 1 (3 parallel agents — independent foundation)
- **Task 1:** `rag/schemas.py` + `rag/planning.py` — RetrievalPlan builder from LLM UnderstandingResult
- **Task 2:** `integrations/vector_client.py` — search_rooms() with Milvus COSINE search + filters
- **Task 3:** `rag/preference_scorer.py` — LLM structured preference scoring via OpenAI JSON mode

### Wave 2 (3 parallel agents — depend on Wave 1)
- **Task 4:** `rag/room_retrieval.py` + `rag/room_ranking.py` — Multi-query vector recall, lease validation, 5-dimension weighted scoring (semantic 0.35, budget 0.25, area 0.15, preference 0.20, availability 0.05). Upgraded `procedures/room_search.py`.
- **Task 5:** `rag/kb_retrieval.py` + `rag/kb_rerank.py` + `rag/confidence.py` — Multi-query KB recall, module-weighted reranking, risk-level confidence gates. Upgraded `procedures/kb_qa.py`.
- **Task 7:** `rag/chunking.py` + `scripts/sync_room_vectors.py` + `scripts/sync_kb_vectors.py` — Content-hash based incremental sync, PII regex validation.

### Wave 3 (1 agent — depends on Waves 1+2)
- **Task 6:** Added RAG settings to `config.py` (rag_room_top_k, rag_room_top_n, rag_kb_top_k, rag_preference_scorer_enabled). Wired vector/embedding/preference_scorer into `build_runtime()` in `deps.py`.

### Wave 4 (2 parallel agents — depend on Wave 3)
- **Task 8:** `rag/eval_metrics.py` (hit@k, MRR, nDCG) + `evals/datasets/rag_retrieval_cases.yaml` + `evals/runners/run_rag_eval.py`
- **Task 9:** Extended `test_no_keyword_fallback.py` to scan 11 RAG runtime files for 8 forbidden patterns

### Wave 5 (1 agent — depends on Wave 4)
- **Task 10:** `tests/integration/test_rag_live.py` (5 skip-safe tests) + updated verification-log.md and evaluation-report.md

## Files Changed

### New files (16)
- `src/aptguide3/rag/__init__.py`
- `src/aptguide3/rag/schemas.py`
- `src/aptguide3/rag/planning.py`
- `src/aptguide3/rag/room_retrieval.py`
- `src/aptguide3/rag/room_ranking.py`
- `src/aptguide3/rag/kb_retrieval.py`
- `src/aptguide3/rag/kb_rerank.py`
- `src/aptguide3/rag/confidence.py`
- `src/aptguide3/rag/preference_scorer.py`
- `src/aptguide3/rag/chunking.py`
- `src/aptguide3/rag/eval_metrics.py`
- `scripts/sync_room_vectors.py`
- `scripts/sync_kb_vectors.py`
- `evals/datasets/rag_retrieval_cases.yaml`
- `evals/runners/run_rag_eval.py`
- `tests/integration/test_rag_live.py`

### Modified files (6)
- `src/aptguide3/config.py` — Added 4 RAG settings
- `src/aptguide3/api/deps.py` — Wired preference_scorer, vector_client, embedding_client into build_runtime()
- `src/aptguide3/procedures/room_search.py` — Full RAG pipeline with vector recall + lease validation + preference scoring
- `src/aptguide3/procedures/kb_qa.py` — Multi-query recall + rerank + confidence gate
- `tests/unit/test_no_keyword_fallback.py` — Extended to scan 11 RAG runtime files
- `pyproject.toml` — Added pyyaml dependency

### New test files (10)
- `tests/unit/rag/test_planning.py` (4 tests)
- `tests/unit/rag/test_preference_scorer.py` (3 tests)
- `tests/unit/rag/test_room_retrieval.py` (7 tests)
- `tests/unit/rag/test_room_ranking.py` (11 tests)
- `tests/unit/rag/test_kb_retrieval.py` (3 tests)
- `tests/unit/rag/test_kb_rerank.py` (5 tests)
- `tests/unit/rag/test_confidence.py` (10 tests)
- `tests/unit/rag/test_chunking.py` (8 tests)
- `tests/unit/rag/test_eval_metrics.py` (21 tests)
- `tests/unit/procedures/test_room_search.py` (5 tests, rewritten)
- `tests/unit/procedures/test_kb_qa.py` (rewritten)
- `tests/unit/api/test_deps.py` (4 new tests added)

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| Wave 2 | test_budget_scoring_over_budget: assert 0.0 == 0.3 | rent=1200/max_rent=1000 ratio=1.2 > 1.1 threshold, returns 0.0 not 0.3 | Changed test to rent=1050 (ratio=1.05 <= 1.1) to test the 0.3 tier | fixed |
| Wave 3 | ruff I001 import sort error in deps.py | LLMPreferenceScorer import was out of order | `ruff --fix` auto-sorted imports | fixed |
| Wave 3 | test_deps AttributeError: 'str' object has no attribute 'name' | _procedures is a dict keyed by name, not a list | Changed to `runtime._procedures["room_search"]` | fixed |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `uv run pytest -q` | 207 passed, 33 skipped, 6 warnings | Full regression clean |
| `uv run ruff check src tests` | All checks passed | No lint errors |
| `uv run pytest tests/integration/test_rag_live.py -q` | 5 skipped | Clean skip (no live env vars) |
| `uv run pytest tests/unit/test_no_keyword_fallback.py -q` | 2 passed | All 11 runtime files clean |
| `uv run pytest tests/unit/rag -q` | 67 passed | All RAG unit tests pass |

## Known Issues

- Live RAG smoke tests require 5 env vars (LLM_API_KEY, EMBEDDING_API_KEY, VECTOR_URI, LEASE_BASE_URL, LIVE_TESTS=1) — not yet configured in CI
- Main-system chain test (rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat) still pending
- Lepton preference scorer adds latency; batch size should be kept small in production

## Next Steps

1. Run main-system chain test when live services are available
2. Run live RAG smoke: `APTGUIDE3_LIVE_TESTS=1 uv run pytest tests/integration/test_rag_live.py -q`
3. Add production operator flow and deployment hardening
4. Add retry, idempotency, rate limiting, metrics, alerting

## Outcome Notes

Milestone 4 completes the LLM-first RAG upgrade. The system now has:
- Vector-based room recall with lease validation and 5-dimension ranking
- KB multi-query recall with module-weighted reranking and confidence gates
- Content-hash based incremental sync for room and KB vectors
- Eval metrics (hit@k, MRR, nDCG) and anti-regression guardrails
- 207 unit tests passing with 33 skip-safe integration tests ready
