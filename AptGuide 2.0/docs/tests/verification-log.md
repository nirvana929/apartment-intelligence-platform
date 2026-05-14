# Verification Log

## 2026-05-15 — LLM-First Interaction Understanding

**Interaction unit tests:** `uv run pytest tests/unit/interaction -q`
**Result:** 19 passed

**Query understanding/planning:** `uv run pytest tests/unit/rag/test_query_understanding.py tests/unit/rag/test_planning.py -q`
**Result:** 10 passed

**Harness/orchestrator:** `uv run pytest tests/unit/harness/test_routing.py tests/unit/harness/test_orchestrator.py tests/unit/harness/modules/test_handoff.py -q`
**Result:** 24 passed

**Mainline wiring:** `uv run pytest tests/unit/api/test_mainline_wiring.py -q`
**Result:** 9 passed, 1 warning

**Backend full:** `uv run pytest tests/ -q`
**Result:** 394 passed, 3 warnings

**Keyword fallback source scan:** `uv run pytest tests/unit/interaction/test_no_keyword_fallback.py -q`
**Result:** passed — no keyword helpers in classifier.py or query_understanding.py

### Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Extend InteractionIntent (retrieval_queries, clarification_needed) | Done |
| 2 | Contract validation with clarification (validation.py) | Done |
| 3 | Replace keyword fallback (ClarifyingInteractionClassifier) | Done |
| 4 | LLM mode default in config and deps | Done |
| 5 | Intent-only query understanding | Done |
| 6 | Domain-based planning (no keyword inference) | Done |
| 7 | Strengthened LLM prompt | Done |
| 8 | All tests updated for LLM-first | Done |
| 9 | Anti-regression source scan tests | Done |
| 10 | Full verification (394 passed) | Done |
| 11 | Project harness checkpoint | Done |
| 12 | Live RAG v2 eval (post raw_message fix) | Done — all gates FAIL, see below |

### Live RAG v2 Eval Results

| Metric | Value | Gate | Pass |
|---|---:|---:|---|
| KB source hit@3 | 71.4% | >= 90% | FAIL |
| KB source hit@5 | 74.3% | - | PASS |
| KB MRR | 0.626 | - | PASS |
| Room hit@5 | 8.6% | >= 85% | FAIL |
| Room MRR | 0.003 | - | PASS |
| High-risk fallback | 40.0% | >= 100% | FAIL |
| Unvalidated rooms | 0 | = 0 | PASS |

Improvement: first run had 100/120 clarification (raw_message bug); post-fix only 15/120 clarification.
Report: `reports/rag-v2-llm-first-evaluation-report.md`

### Key Changes

- `interaction/contracts.py` — added `retrieval_queries: list[str]`, `clarification_needed: bool`
- `interaction/validation.py` — new: `validate_or_clarify_intent()`, `build_clarification_intent()`
- `interaction/classifier.py` — `ClarifyingInteractionClassifier` replaces `HeuristicInteractionClassifier`; `LLMInteractionClassifier` returns clarification on failure
- `interaction/prompts.py` — stricter schema-oriented prompt with `retrieval_queries` and `clarification_needed`
- `core/config.py` — `intent_classifier_mode` default changed from `"heuristic"` to `"llm"`
- `api/deps.py` — default builds `LLMInteractionClassifier` with `min_confidence`
- `rag/schemas.py` — `QueryUnderstandingResult` gains `domain` field
- `rag/query_understanding.py` — intent-only; no keyword extraction
- `rag/planning.py` — uses `qr.domain` for module_intent instead of `_infer_kb_module_intent()`
- All runtime keyword helpers removed: `_looks_like_room_search`, `_looks_like_kb_policy`, `_looks_like_policy_question`, `_infer_kb_domain`, `_detect_task`, `_extract_budget`, `_extract_district`, `_extract_payment`, `_extract_preferences`, `_extract_reference`, `_generate_retrieval_queries`

---

## 2026-05-14 — Semantic Interaction Routing

**Interaction unit tests:** `uv run pytest tests/unit/interaction -q`
**Result:** 9 passed

**Routing/RAG focused:** `uv run pytest tests/unit/harness/test_routing.py tests/unit/rag/test_query_understanding.py tests/unit/harness/modules/test_rag_v2.py -q`
**Result:** 40 passed

**Appointment focused:** `uv run pytest tests/unit/harness/modules/test_appointment.py -q`
**Result:** 22 passed

**Intent eval:** `uv run python -m evals.runners.run_interaction_intent_eval --cases evals/datasets/interaction_intent_cases.yaml`
**Result:** total=8, exact=8, exact_rate=1.0

**Backend full:** `uv run pytest tests/ -q`
**Result:** 402 passed, 3 warnings

**Source scan:** `rg -n "aptguide2\\.rag\\.pipeline[^_]|RagBaselineProcedure|rag_mvp_baseline|from aptguide2\\.rag\\.kb_retrieval|from aptguide2\\.rag\\.room_retrieval" src tests evals`
**Result:** No legacy RAG runtime references (only guard test assertions)

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

- `interaction/__init__.py` — exports EntityMention, InteractionIntent
- `interaction/contracts.py` — InteractionIntent with route/rag_task/domain/action/entities/hard_filters/soft_preferences
- `interaction/entity_resolution.py` — area alias normalization, budget/payment extraction, hard/soft filter policy
- `interaction/classifier.py` — InteractionClassifier protocol, HeuristicInteractionClassifier, LLMInteractionClassifier, apply_policy_corrections
- `interaction/prompts.py` — LLM structured intent prompt
- `core/config.py` — intent_classifier_mode, intent_classifier_timeout_seconds, intent_classifier_min_confidence
- `harness/contracts.py` — RouteDecision gains metadata field
- `harness/routing.py` — HybridRouter uses InteractionClassifier instead of keyword tables
- `api/deps.py` — get_interaction_classifier() factory, wires into HybridRouter
- `rag/query_understanding.py` — accepts optional interaction_intent, uses its rag_task and merges hard_filters/soft_preferences
- `rag/pipeline_v2.py` — accepts optional interaction_intent, passes to understand_query
- `harness/modules/rag/v2.py` — extracts InteractionIntent from decision.metadata, passes to pipeline
- `harness/modules/appointment.py` — _get_intent/_extract_room_id_from_intent, tries intent entities before regex
- `evals/datasets/interaction_intent_cases.yaml` — 8 intent eval cases
- `evals/runners/run_interaction_intent_eval.py` — eval runner with route/domain/action accuracy

---

## 2026-05-14 — Standalone Hardening And Observability

**Backend:** `cd backend && uv run pytest tests/ -q`
**Result:** 386 passed, 3 warnings

**Frontend:** `cd frontend && npm run test && npm run build`
**Result:** 5 tests passed, build succeeded

### Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Deployment config + runbook | Done |
| 2 | Dependency readiness + `/ready` endpoint | Done |
| 3 | Security/permission hardening | Done |
| 4 | Backend observability events | Done |
| 5 | Frontend chat UX hardening | Done |
| 6 | Operator console UX hardening | Done |
| 7 | Final verification and docs sync | Done |

### Key Changes

- `core/config.py` — added environment, service_name, service_version, cors_allow_origins, log_level, structured_logs_enabled, expose_trace_to_frontend; added parsed_cors_origins property
- `.env.example` — reorganized with deployment/observability sections and staging/production example
- `docs/system/standalone-deployment-runbook.md` — new: startup, verification, restart, rollback
- `system/readiness.py` — DependencyCheck gains category field; build_readiness_report returns 7 checks (pipeline, auth_mode, mysql_config, redis_config, lease_config, milvus_config, embedding_config)
- `api/app.py` — added `/ready` endpoint; CORS uses parsed_cors_origins; emits chat.received/chat.completed events
- `api/schemas.py` — added ReadinessResponse
- `api/auth.py` — httpx errors normalized to PermissionError
- `api/operator.py` — default token rejected in staging/prod; disabled console returns 403
- `observability/events.py` — new: emit_event() structured logging helper
- `harness/orchestrator.py` — emits harness.completed event
- `frontend/src/stores/chat.ts` — error/lastDraft/lastAction state; duplicate send guard; retryLast()
- `frontend/src/components/chat/ChatShell.vue` — error banner with retry
- `frontend/src/components/chat/TracePanel.vue` — shows trace_id
- `frontend/src/stores/operator.ts` — statusFilter, error state, setStatusFilter()
- `frontend/src/components/operator/OperatorConsole.vue` — loading/error/empty states
- `frontend/src/components/operator/TicketList.vue` — status filter buttons
- `frontend/src/components/operator/OperatorReplyBox.vue` — disabled when loading

---

## 2026-05-14 — RAG v2 Diagnostic-First Retrieval Optimization

**Backend full:** `cd backend && uv run pytest tests/ -q`
**Result:** 407 passed, 3 warnings

**Intent eval:** `uv run python -m evals.runners.run_interaction_intent_eval --cases evals/datasets/interaction_intent_cases.yaml`
**Result:** total=8, exact=8, exact_rate=1.0

**RAG eval:** `uv run python -m evals.runners.run_rag_v2 --cases evals/datasets/rag_mvp_retrieval_cases.yaml --report ../reports/rag-v2-live-evaluation-report.md`
**Result (120 cases):**

| Metric | Value | Gate | Pass |
|---|---:|---:|---|
| KB hit@3 | 94.3% | >= 90% | PASS |
| KB hit@5 | 94.3% | - | PASS |
| KB MRR | 0.848 | - | PASS |
| KB NDCG@5 | 0.872 | - | PASS |
| Room hit@5 | 10.0% | >= 85% | FAIL |
| Room MRR | 0.010 | - | PASS |
| Room NDCG@5 | 0.007 | - | PASS |
| High-risk fallback | 40.0% | >= 100% | FAIL |
| Unvalidated rooms | 0 | = 0 | PASS |

### Root Causes for Remaining Failures

- Room: 40+ cases misclassified as fallback (missing room attribute keywords in classifier)
- Room: 10+ cases misclassified as kb_qa ("吗" question marker overlap)
- Room: 7 cases correct route but expected rooms not in top-5 (embedding/retrieval quality)
- High-risk: risk detection patterns incomplete for some edge cases

---

## 2026-05-14 — RAG v2 Full Replacement

**Backend focused:** `uv run pytest tests/unit/api/test_mainline_wiring.py tests/unit/rag tests/unit/harness/modules/test_rag_v2.py tests/unit/evals/test_run_rag_v2.py -q`
**Result:** 140 passed

**Backend full:** `uv run pytest tests/ -q`
**Result:** 376 passed, 3 warnings

**Source scan:** `rg -n "aptguide2\\.rag\\.pipeline[^_]|RagBaselineProcedure|rag_mvp_baseline" src/ tests/ evals/`
**Result:** No legacy RAG runtime references

### Verification Evidence

- `pipeline_v2.py` imports only `kb_v2.retrieve_kb_v2` and `room_v2.retrieve_ranked_rooms_v2`
- `baseline.py` deleted — `RagBaselineProcedure` no longer exists
- `pipeline.py` deleted — old `run_pipeline` no longer callable
- `kb_retrieval.py` and `room_retrieval.py` deleted — old retrieval functions removed
- 16 guard tests fail if old RAG is reintroduced
- Eval runner (`run_rag_v2.py`) imports only from `pipeline_v2`

---

## 2026-05-14 — Risk-Aware Query Understanding Guardrail

**Backend targeted:** `uv run pytest tests/unit/rag/test_risk_detection.py tests/unit/rag/test_query_understanding.py tests/unit/harness/test_routing.py tests/unit/evals/test_run_risk_detection.py -q`
**Result:** 67 passed

**Backend full:** `uv run pytest tests/ -q`
**Result:** 389 passed

**Risk eval:** `uv run python -m evals.runners.run_risk_detection`
**Targets:** high_risk_recall >= 0.95, false_block_rate <= 0.05, response_mode_accuracy >= 0.90
**Result:** total=53, risk_accuracy=1.000, response_mode_accuracy=1.000, high_risk_recall=1.000, false_block_rate=0.000

---

## 2026-05-14 — Standalone Productization (Backend Core + Frontend)

**Backend:** `cd backend && uv run pytest tests/ -q`
**Result:** 365 passed
**Lint:** 15 pre-existing E402 issues (not introduced by this work)

**Frontend:** `cd frontend && npm run test && npm run build`
**Result:** 2 tests passed, build succeeded

### Backend Coverage

- `tests/unit/harness/` — harness framework, tools, modules, composer, routing, memory, handoff
- `tests/unit/rag/` — RAG v2 pipeline, hybrid retrieval, rerank, planning, validation
- `tests/unit/tools/` — lease adapter, vector adapter
- `tests/unit/api/` — mainline wiring guards, auth resolver, operator API
- `tests/unit/persistence/` — database models, Redis store
- `tests/unit/system/` — readiness report
- `tests/e2e/` — API endpoint tests (capability, room search, fallback, handoff, appointment)

### Frontend Coverage

- `tests/chat-contract.test.ts` — ChatResponse contract validation
- `tests/operator-contract.test.ts` — HandoffTicket contract validation
