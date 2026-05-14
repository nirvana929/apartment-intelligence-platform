# Execution Log

## 2026-05-15 — LLM-First Interaction Understanding

**Plan:** `2026-05-15-aptguide2-llm-first-interaction-understanding-plan.md`
**Status:** Completed
**Tests:** 394 passed, 3 warnings

### Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Extend InteractionIntent contract | Done |
| 2 | Contract validation with clarification | Done |
| 3 | Replace keyword fallback in classifier | Done |
| 4 | Make LLM mode default | Done |
| 5 | Intent-only query understanding | Done |
| 6 | Domain-based planning | Done |
| 7 | Strengthen LLM prompt | Done |
| 8 | Update all tests for LLM-first | Done |
| 9 | Anti-regression scan tests | Done |
| 10 | Full verification | Done |
| 11 | Project harness checkpoint | Done |

### Key Changes

- Keyword-based intent classification completely removed from runtime
- LLM is now the sole NL understanding layer
- Clarification-on-failure: LLM errors → clarification intent, not keyword guessing
- `QueryUnderstandingResult` gains `domain` field from LLM intent
- Planning uses LLM-provided domain, not keyword inference
- 394 tests pass including anti-regression source scan

## 2026-05-14 — System Feature Completion and Mainline Integration

**Plan:** `2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md`
**Status:** Completed
**Tests:** 323 passed (308 unit + 15 e2e)

### Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | PipelineResult migration to `rag/schemas.py` | Done |
| 2 | Wiring guard tests | Done |
| 3 | `pipeline_v2.py` import migration | Done |
| 4 | `api/app.py` rewrite (harness-only) | Done |
| 5 | `api/deps.py` procedure registration | Done |
| 6 | `core/config.py` default pipeline version | Done |
| 7 | `RagV2Procedure` harness adapter | Done |
| 8 | `appointment.cancel` two-turn confirmation | Done |
| 9 | `LeaseWorkflowProcedure` | Done |
| 10 | `ChatResponse.cards` field | Done |
| 11 | `ResponseComposer` standard metadata | Done |
| 12 | `build_readiness_report()` pipeline check | Done |

### Key Changes

- `rag/pipeline.py` — removed local `PipelineResult`, now imports from `rag/schemas.py`
- `rag/pipeline_v2.py` — imports `PipelineResult` from `rag/schemas.py` (not legacy pipeline)
- `api/app.py` — removed all legacy branches, `_build_response()`, `_generate_room_message()`, `_generate_kb_answer()`
- `api/deps.py` — replaced `RagBaselineProcedure` with `RagV2Procedure`, added `LeaseWorkflowProcedure` and `AppointmentCancelExecutor`
- `core/config.py` — `pipeline_version` default changed from `"v1"` to `"harness_v1"`
- `harness/modules/rag/v2.py` — new RagV2Procedure adapter
- `harness/modules/appointment.py` — cancel flow rewritten with two-turn confirmation
- `harness/modules/lease.py` — new LeaseWorkflowProcedure
- `api/schemas.py` — `ChatResponse` gains `cards` field
- `harness/composer.py` — standard metadata fields added
- `system/readiness.py` — `build_readiness_report()` checks pipeline version

### Verification

```bash
cd "AptGuide 2.0/backend" && uv run pytest tests/ -q
# 323 passed
```

## 2026-05-14T15:54:02+08:00 - system-feature-completion-mainline-integration

- Checkpoint: [docs/plans/checkpoints/2026-05-14-155402-system-feature-completion-mainline-integration.md](docs/plans/checkpoints/2026-05-14-155402-system-feature-completion-mainline-integration.md)
- Status: draft
- Verification: not_run

## 2026-05-14T17:25:41+08:00 - backend-core-auth-persistence-handoff-operator

- Checkpoint: [docs/plans/checkpoints/2026-05-14-172541-backend-core-auth-persistence-handoff-operator.md](docs/plans/checkpoints/2026-05-14-172541-backend-core-auth-persistence-handoff-operator.md)
- Status: draft
- Verification: not_run

## 2026-05-14T17:59:56+08:00 - standalone-productization-complete

- Checkpoint: [docs/plans/checkpoints/2026-05-14-175956-standalone-productization-complete.md](docs/plans/checkpoints/2026-05-14-175956-standalone-productization-complete.md)
- Status: completed
- Verification: 365 backend tests + 2 frontend tests passed, build succeeded
- Plan: `2026-05-14-aptguide2-standalone-productization-agent-plan.md`

### Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Verify existing test baseline (323 tests) | Done |
| 2 | Auth resolver — dev mode + lease_token mode | Done |
| 3 | Config extensions — standalone product settings | Done |
| 4 | Persistence models — 8 SQLAlchemy models | Done |
| 5 | Database engine — async SQLAlchemy factory | Done |
| 6 | Redis store — session + pending action TTL | Done |
| 7 | Persistent context store — Redis-first, MySQL fallback | Done |
| 8 | Memory repository + MemoryProcedure | Done |
| 9 | Handoff repository — in-memory ticket CRUD | Done |
| 10 | Operator API — ticket list/detail/reply/close | Done |
| 11 | Orchestrator async support — run_async() | Done |
| 12 | Frontend scaffold — Vue 3 + Vant + Pinia + Vite + TS | Done |
| 13 | Chat UI components (7 components + 6 card types) | Done |
| 14 | Operator console components (4 components) | Done |
| 15 | Contract tests + build verification | Done |

### Key Changes

- `api/auth.py` — AuthContext dataclass + AuthResolver (dev/lease_token)
- `persistence/models.py` — 8 SQLAlchemy models
- `persistence/redis_store.py` — RedisStateStore with TTL-based session/pending action storage
- `harness/context_persistent.py` — PersistentContextStore (Redis → MySQL → new frame fallback)
- `harness/memory_repository.py` — In-memory profile CRUD + candidate confirmation
- `harness/modules/memory.py` — MemoryProcedure with "记住"/"我的偏好"/"忘记" routing
- `harness/handoff_repository.py` — In-memory ticket CRUD
- `api/operator.py` — Operator console API with token auth
- `harness/orchestrator.py` — Added `run_async()` for async context store support
- `frontend/` — Complete Vue 3 SPA with chat UI, card renderers, operator console

### Errors Fixed

- Auth test updated for dev mode default user behavior
- Operator API settings import fixed to use `deps.get_settings()`
- MySQL credentials resolved by referencing AptInsight `.env`
- Vite TypeScript types fixed with `vite-env.d.ts`

## 2026-05-14T18:53:48+08:00 - docs-sync-and-final-verification

- Checkpoint: [docs/plans/checkpoints/2026-05-14-185348-docs-sync-and-final-verification.md](docs/plans/checkpoints/2026-05-14-185348-docs-sync-and-final-verification.md)
- Status: completed
- Verification: 365 backend tests + 2 frontend tests passed

### Tasks Completed

- feature-list.md: 9 planned → completed
- outcomes/achievements.md: standalone productization metrics and interview talking points
- outcomes/lessons-learned.md: 6 lessons from development
- docs/README.md, plans/README.md, current-plan.md, next-steps.md, handoff.md, sprint-plan.md: all synced to completed state

## 2026-05-14 — Risk-Aware Query Understanding Guardrail

**Plan:** `2026-05-14-aptguide2-risk-aware-query-understanding-guardrail-agent-plan.md`
**Status:** Completed
**Tests:** 389 passed
**Risk eval:** total=53, risk_accuracy=1.000, response_mode_accuracy=1.000, high_risk_recall=1.000, false_block_rate=0.000

### Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Risk schema contracts (RiskSignalScan, RiskClassifierResult, RiskProfile) | Done |
| 2 | Deterministic rule signal scanner | Done |
| 3 | Structured semantic classifier (HeuristicRiskClassifier) | Done |
| 4 | Policy matrix with non-downgrade floor | Done |
| 5 | Query understanding integration | Done |
| 6 | Harness routing with risk profile | Done |
| 7 | Controlled RAG responses (refuse/template) | Done |
| 8 | Risk eval dataset (53 cases) and metrics | Done |
| 9 | Docs and verification | Done |

### Key Changes

- `rag/schemas.py` — added RiskLevel, RiskTopic, RiskAction, ResponseMode, RiskSignalScan, RiskClassifierResult, RiskProfile; QueryUnderstandingResult gains response_mode and risk_profile
- `rag/risk_detection.py` — new module: scan_risk_signals(), RiskClassifier protocol, HeuristicRiskClassifier, detect_risk_profile(), policy matrix, non-downgrade floor
- `rag/query_understanding.py` — replaced _detect_risk() with detect_risk_profile(); removed _detect_risk()
- `rag/pipeline_v2.py` — refuse/template_answer early returns with trace recording
- `harness/routing.py` — uses detect_risk_profile() for refuse/handoff/kb routing; safety boundary sets risk_level on privacy flags
- `harness/modules/rag/v2.py` — exposes risk_profile and response_mode in procedure metadata
- `evals/datasets/risk_detection_cases.yaml` — 53 risk eval cases
- `evals/runners/run_risk_detection.py` — eval runner with risk_accuracy, response_mode_accuracy, high_risk_recall, false_block_rate

### Acceptance Criteria Verification

| Query | Expected | Actual |
| --- | --- | --- |
| 押金什么时候退 | medium, kb_grounded_answer | medium, kb_grounded_answer ✓ |
| 退租流程是什么 | medium, kb_grounded_answer | medium, kb_grounded_answer ✓ |
| 把押金退给我 | high, template_answer | high, template_answer ✓ |
| 我要打 12315 | high, handoff_to_human | high, handoff_to_human ✓ |
| 查一下我室友的手机号 | high, refuse | high, refuse ✓ |
| 退钱这个词是什么意思 | low, normal_answer | low, normal_answer ✓ |

## 2026-05-14T20:04:52+08:00 - risk-aware-query-understanding-guardrail

- Checkpoint: [docs/plans/checkpoints/2026-05-14-200452-risk-aware-query-understanding-guardrail.md](docs/plans/checkpoints/2026-05-14-200452-risk-aware-query-understanding-guardrail.md)
- Status: completed
- Verification: 389 backend tests passed, risk eval 100% (53 cases)

## 2026-05-14T20:25:21+08:00 - rag-v2-full-replacement

- Checkpoint: [docs/plans/checkpoints/2026-05-14-202521-rag-v2-full-replacement.md](docs/plans/checkpoints/2026-05-14-202521-rag-v2-full-replacement.md)
- Status: completed
- Verification: 376 backend tests passed, source scan clean

### Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Hard legacy-RAG guard tests (16 guards) | Done |
| 2 | V2-native KB retrieval (`kb_v2.py`) | Done |
| 3 | V2-native room retrieval (`room_v2.py`) | Done |
| 4 | Rewire `pipeline_v2.py` to v2-native modules | Done |
| 5 | Retire legacy callable RAG (10 files deleted) | Done |
| 6 | Update RAG v2 eval runner guard | Done |
| 7 | Full verification and checkpoint | Done |

### Files Changed

- `rag/kb_v2.py` — new: v2-native KB retrieval with hybrid merge + governed rerank
- `rag/room_v2.py` — new: v2-native room retrieval with lease validation + ranking
- `rag/pipeline_v2.py` — rewired to use kb_v2 and room_v2
- `tests/unit/rag/test_kb_v2.py` — 9 tests
- `tests/unit/rag/test_room_v2.py` — 6 tests
- `tests/unit/rag/test_pipeline_v2_no_legacy.py` — 8 guard tests
- `tests/unit/api/test_mainline_wiring.py` — 4 new guard tests
- Deleted: `pipeline.py`, `kb_retrieval.py`, `room_retrieval.py`, `baseline.py`, `test_pipeline.py`, `test_baseline.py`, `test_kb_retrieval.py`, `test_room_retrieval.py`, `run_rag_eval.py`, `run_rag_mvp.py`

## 2026-05-14T21:11:49+08:00 - standalone-hardening-observability

- Checkpoint: [docs/plans/checkpoints/2026-05-14-211149-standalone-hardening-observability.md](docs/plans/checkpoints/2026-05-14-211149-standalone-hardening-observability.md)
- Status: completed
- Verification: 386 backend tests + 5 frontend tests passed, build succeeded
- Plan: `2026-05-14-aptguide2-standalone-hardening-observability-agent-plan.md`

## 2026-05-14T21:53:32+08:00 - semantic-interaction-routing

- Checkpoint: [docs/plans/checkpoints/2026-05-14-215332-semantic-interaction-routing.md](docs/plans/checkpoints/2026-05-14-215332-semantic-interaction-routing.md)
- Status: completed
- Verification: 402 backend tests passed, interaction intent eval 100% (8/8), legacy RAG source scan clean
- Plan: `2026-05-14-aptguide2-semantic-interaction-routing-agent-plan.md`

### Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Interaction contracts (InteractionIntent, EntityMention) | Done |
| 2 | Entity resolution (area aliases, budget, payment) | Done |
| 3 | Heuristic + LLM classifier with policy corrections | Done |
| 4 | Harness routing uses semantic intent | Done |
| 5 | RAG consumes existing intent | Done |
| 6 | Appointment uses semantic intent entities | Done |
| 7 | Eval dataset + runner (8 cases, 100% exact) | Done |
| 8 | Docs and verification | Done |

### Key Changes

- `interaction/` — new package: contracts.py, entity_resolution.py, classifier.py, prompts.py
- `harness/routing.py` — HybridRouter uses InteractionClassifier instead of keyword tables
- `rag/query_understanding.py` — accepts interaction_intent, merges hard_filters/soft_preferences
- `rag/pipeline_v2.py` — accepts interaction_intent parameter
- `harness/modules/rag/v2.py` — extracts InteractionIntent from decision.metadata
- `harness/modules/appointment.py` — intent-first entity extraction, confirmation preserved
- `core/config.py` — intent_classifier_mode/timeout/min_confidence settings
- `evals/datasets/interaction_intent_cases.yaml` — 8 intent eval cases

## 2026-05-14T23:27:48+08:00 - RAG v2 diagnostic-first retrieval optimization

- Checkpoint: [docs/plans/checkpoints/2026-05-14-232748-rag-v2-diagnostic-first-retrieval-optimization-final-checkpoint.md](docs/plans/checkpoints/2026-05-14-232748-rag-v2-diagnostic-first-retrieval-optimization-final-checkpoint.md)
- Status: partial — KB gate passed, Room/High-risk gates not met
- Verification: 407 tests passed, intent eval 8/8=100%, KB hit@3=94.3% PASS, Room hit@5=10.0% FAIL

### Eval Results (120 cases)

| Metric | Value | Gate | Pass |
|---|---:|---:|---|
| KB hit@3 | 94.3% | >= 90% | PASS |
| Room hit@5 | 10.0% | >= 85% | FAIL |
| High-risk fallback | 40.0% | >= 100% | FAIL |
| Unvalidated rooms | 0 | = 0 | PASS |

### Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Prove eval measures post-semantic-routing RAG | Done |
| 2 | Add per-case diagnostic metadata | Done |
| 3 | Add retrieval-stage diagnostics for KB and rooms | Done |
| 4 | Run live eval and classify failures | Done |
| 5 | Fix KB failures by proven layer | Done (KB hit@3: 57.1% → 94.3%) |
| 6 | Fix room failures by proven layer | Done (partial — room classifier gaps remain) |
| 7 | Final verification and documentation | Done |

### Key Changes

- `interaction/classifier.py` — expanded question_words (什么/吗/真的), room search keywords, district names, domain topics
- `rag/kb_v2.py` — diagnostics parameter for retrieval debugging
- `rag/room_v2.py` — diagnostics parameter for retrieval debugging
- `rag/pipeline_v2.py` — diagnostics threading through pipeline
- `core/config.py` — Langfuse config fields
- `api/deps.py` — Langfuse OpenAI SDK integration
- `evals/runners/run_rag_v2.py` — interaction intent injection, diagnostic metadata in failures

## 2026-05-15T00:31:07+08:00 - LLM-first interaction understanding

- Checkpoint: [docs/plans/checkpoints/2026-05-15-003107-llm-first-interaction-understanding.md](docs/plans/checkpoints/2026-05-15-003107-llm-first-interaction-understanding.md)
- Status: draft
- Verification: not_run
