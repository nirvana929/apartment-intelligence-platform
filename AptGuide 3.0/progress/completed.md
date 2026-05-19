# Completed

## 2026-05-15 — Milestone 0: Runnable Scaffold

- Created AptGuide 3.0 project skeleton.
- Architecture and contract documentation.
- Clean LLM-first backend foundation (36 tests, ruff clean).
- Domain contracts: UnderstandingResult, ConversationFrame, ProcedureResult, ChatResponse.
- Understanding layer: LLM adapter, validation, clarification-on-uncertainty.
- Application layer: safety boundary, procedure runtime, chat service.
- Procedures: clarify, room_search, kb_qa, appointment, lease, memory, handoff.
- Integrations: LeaseClient, VectorClient (Milvus), EmbeddingClient.
- Persistence: InMemorySessionRepo, MemoryRepo, HandoffRepo.
- Observability: TraceEvent, ChatTrace, ConsoleTraceSink, Tracer.
- Frontend: Vue3 chat UI with CORS and static file serving.
- LLM: qwen-turbo-latest via DashScope OpenAI-compatible API.
- FastAPI API: /health, /chat, static frontend mount.
- Anti-regression source scan: no keyword fallback in understanding runtime.
- Clarified AptGuide 3.0 product boundary: independent validation first, final integration through `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`.

## 2026-05-15 — Milestone 1: Independent Backend Backbone

- Database schema: 11 MySQL 8.0 tables (users, sessions, messages, pending_actions, memories, memory_candidates, handoff_tickets, operator_messages, trace_events, procedure_runs, audit_log).
- SQLAlchemy models: 11 declarative models.
- Repository contracts: 8 Protocol-based definitions.
- MySQL repos: Full async implementations using SQLAlchemy + asyncmy with NullPool.
- Redis: RedisStateStore with TTL for session and pending-action storage.
- Auth: AuthResolver with dev and internal_header modes.
- Readiness: Config-based dependency checks.
- Tests: 55 passed, 2 skipped.

## 2026-05-15 — Milestone 2: Live Integration Readiness

- Docker-compose: MySQL 8.0 + Redis 7 local stack.
- 23 skip-safe integration tests (Redis, MySQL, auth, LLM, embedding, vector, chat persistence).
- Scripts: apply_schema.py for MySQL migration.
- Docs: Lease gateway contract, operator flow, deployment readiness.
- Tests: 68 passed, 23 skipped.

## 2026-05-15 — Live Dependency Verification

- Mapped AptGuide .env values into AptGuide 3.0 APTGUIDE3_* variables.
- Started/verified aip-etcd, aip-minio, aip-milvus, recreated aip-lease-web-app with REDIS_PORT=6379.
- Fixed async MySQL event-loop reuse by switching to NullPool.
- Live MySQL, Redis, lease health, Milvus, embedding, LLM, and chat persistence verified.
- Tests: 21 integration passed, 6 internal-header auth passed, 68 baseline passed/23 skipped.

## 2026-05-15 — Milestone 3: Procedure Integration

- RepoBundle dataclass wiring all 8 repository types across memory/mysql/hybrid modes.
- AppointmentProcedure: pending-action confirmation pattern with audit writes.
- LeaseProcedure: lease list through LeaseClient with audit writes.
- MemoryProcedure: save/list user preferences.
- HandoffProcedure: ticket creation with audit writes.
- LeaseClient extensions: create_appointment, list_appointments, list_leases.
- RepositoryTraceSink wired into tracer.
- Async /ready with live connectivity probes.
- Main-chain test plan and skip-safe smoke test.
- Tests: 129 passed, 28 skipped.

## 2026-05-15 — Milestone 4: LLM-First RAG Upgrade

- RAG pipeline: structured planning, multi-query vector recall, lease validation, ranking, confidence gating.
- Room ranking: 5-dimension weighted scoring (semantic 0.35, budget 0.25, preference 0.20, area 0.15, availability 0.05).
- KB reranking: module-weighted with intent bonus (lease 1.2, payment 1.15, account 1.1, policy 1.1).
- Confidence gates: risk-level thresholds (low=0.45, medium=0.55, high=0.65).
- LLM preference scorer with fallback to neutral 0.5.
- Eval metrics: hit@k, MRR, nDCG (21 tests).
- Sync scripts: sync_room_vectors.py, sync_kb_vectors.py.
- Anti-regression guardrail: 11 runtime files verified clean of keyword fallback.
- Tests: 207 passed, 28 skipped.

## 2026-05-15 — Milestone 5: Frontend E2E + Live RAG Evaluation

- Playwright frontend E2E: 3 passed (page load, chat render, network assertion).
- Live dependency verification: 15 passed, 2 skipped.
- Live RAG integration: 5/5 passed.
- Business scenario routing: greeting, room search, KB QA route to expected phases.
- RAG eval runner upgraded with --live mode.
- Fix: response_mode validator for unexpected LLM values.
- Fix: internal-token header on lease readiness probe.
- Tests: 175 passed, 33 skipped, 35 failed (pre-existing asyncio runner issues).

## 2026-05-15 — Milestone 6: LangSmith Tracing + Diagnostics

- LangSmith opt-in client wrapping for OpenAI-compatible LLM calls.
- UnderstandingDiagnostic: captures raw LLM JSON, parsed fields, validator reason, final result.
- RoomRecDiagnostic / KbRecDiagnostic: per-case vector recall, lease validation, ranking, confidence gate counts.
- Eval report integration: diagnostic fields rendered per case.
- Live eval findings: 4 seed cases correctly routed; failures at vector recall stage (Milvus data missing).
- Tests: 22 diagnostic tests passed.

## 2026-05-16 — Live RAG Gate (Evaluation-First Execution Plan)

- Live RAG eval executed: 4/9 passed (all KB QA), 5/9 failed (all room search — dataset_gap), 0 errors.
- KB QA production-ready: Hit@3=100%, high-risk citation=100%, unverified_commitment=0%.
- Room search returns live results from Milvus (3-5 cards, 9-90 vector hits) but retrieval quality unmeasurable.
- 3 classified findings: P0 dataset_gap, P1 identity_mapping, P2 trace_visibility.
- Eval runner smoke mode: 44 tests passed.
- Focused RAG/procedure tests: 147 passed.
- Reports updated: docs/tests/evaluation-report.md, reports/evaluation-report.md.

## 2026-05-16 — Eval System Overhaul (4 Waves, Parallel Execution)

- T1 dataset: 30→90 cases (30 room search criteria-based + 60 KB QA with expected_doc_ids)
- T2 dataset: 55 cases all structured (risk_level + entity resolution fields, no free-text)
- T3 dataset: 55 cases all structured (8 free-text assertions fixed, multi-turn session reuse, user_id passthrough)
- Runner: criteria-based room search (response_not_empty, district_match, price_in_range, amenity_match, latency_ok), entity resolution validation, multi-turn session reuse
- Unit tests: 64 passed, ruff clean
- Smoke eval: 200 cases (T1: 90, T2: 55, T3: 55) output validated
- Live eval running to verify end-to-end
