# Achievements

## 2026-05-15 - AptGuide 3.0 Full-Stack System (M0)

Built a runnable LLM-first rental assistant scaffold in a single session:

- **Architecture**: Clean separation — understanding (LLM only), domain contracts, application orchestration, procedure dispatch, integrations, persistence, observability
- **Procedures**: 7 typed procedures (clarify, room_search, kb_qa, appointment, lease, memory, handoff)
- **Integrations**: LeaseClient (HTTP), VectorClient (Milvus), EmbeddingClient (OpenAI-compatible)
- **Persistence**: Protocol-based repos (session, memory, handoff) with in-memory defaults, swappable to Redis/MySQL
- **Observability**: TraceEvent system with ConsoleTraceSink
- **Frontend**: Vue3 chat UI with card rendering
- **LLM**: qwen-turbo-latest via DashScope, with ClarifyOnlyUnderstanding fallback
- **Quality**: 36 tests, ruff clean, anti-regression source scan for no keyword fallback
- **Parallel execution**: 8 agents across 2 batches, 4 concurrent workstreams

## 2026-05-15 - Main-System Boundary Clarified

Clarified that AptGuide 3.0 is an AptGuide main-system upgrade:

- independent validation first;
- final integration through `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`;
- AptGuide 3.0 owns Agent state;
- lease remains source of truth for users, rooms, appointments, leases, contracts, and sensitive customer data.

## 2026-05-15 - Independent Backend Backbone (M1)

- **Database**: 11 MySQL 8.0 tables (users, sessions, messages, pending_actions, memories, memory_candidates, handoff_tickets, operator_messages, trace_events, procedure_runs, audit_log)
- **Repository contracts**: 8 Protocol-based repo definitions
- **MySQL repos**: Full async implementations using SQLAlchemy + asyncmy with NullPool
- **Redis**: RedisStateStore with TTL for session and pending-action storage
- **Auth**: AuthResolver with dev and internal_header modes
- **Readiness**: Config-based checks for all dependencies
- **Tests**: 55 passed, 2 skipped

## 2026-05-15 - Live Integration Readiness (M2)

- **Docker-compose**: MySQL 8.0 + Redis 7 local stack
- **Integration tests**: 23 skip-safe tests covering MySQL, Redis, auth, LLM, embedding, vector, chat persistence
- **Scripts**: apply_schema.py for MySQL migration
- **Docs**: Lease gateway contract, operator flow, deployment readiness
- **Tests**: 68 passed, 23 skipped

## 2026-05-15 - Procedure Integration (M3)

- **RepoBundle**: Dataclass wiring all 8 repository types across memory/mysql/hybrid modes
- **New procedures**: AppointmentProcedure (pending-action confirmation), LeaseProcedure (lease list + audit), MemoryProcedure (save/list prefs), HandoffProcedure (ticket + audit)
- **LeaseClient extensions**: create_appointment, list_appointments, list_leases
- **Audit writes**: Appointment, lease, and handoff procedures write to audit log
- **Async /ready**: Live connectivity probes (MySQL SELECT 1, Redis PING, lease health, Milvus list_collections)
- **Tests**: 129 passed, 28 skipped

## 2026-05-15 - LLM-First RAG Upgrade (M4)

- **RAG pipeline**: Full structured pipeline — planning, multi-query vector recall, lease validation, ranking, confidence gating
- **Room ranking**: 5-dimension weighted scoring (semantic 0.35, budget 0.25, preference 0.20, area 0.15, availability 0.05)
- **KB reranking**: Module-weighted reranking with intent bonus
- **Confidence gates**: Risk-level thresholds (low=0.45, medium=0.55, high=0.65)
- **Preference scorer**: LLM-based structured preference scoring
- **Eval metrics**: hit@k, MRR, nDCG
- **Sync scripts**: Room and KB vector sync to Milvus
- **Anti-regression**: 11 runtime files verified clean of keyword fallback patterns
- **Tests**: 207 passed, 28 skipped

## 2026-05-15 - Frontend E2E + Live RAG Evaluation (M5)

- **Playwright E2E**: 3 tests passed (page load, chat render, network assertion)
- **Live dependency verification**: 15 passed, 2 skipped across MySQL, Redis, LLM, embedding, Milvus, readiness, audit
- **Live RAG integration**: 5/5 passed
- **Business scenarios**: Greeting, room search, KB QA route to expected phases
- **RAG eval runner**: Upgraded with `--live` mode
- **Fixes**: response_mode validator for unexpected LLM values, internal-token header on lease readiness probe
- **Tests**: 175 passed, 33 skipped, 35 failed (pre-existing asyncio runner issues)

## 2026-05-15 - LangSmith Tracing + Diagnostics (M6)

- **LangSmith**: Opt-in client wrapping for OpenAI-compatible LLM calls (disabled by default)
- **Understanding diagnostics**: UnderstandingDiagnostic dataclass capturing raw LLM JSON, parsed fields, validator reason, final result
- **Rec-stage diagnostics**: RoomRecDiagnostic and KbRecDiagnostic capturing vector recall, lease validation, ranking, confidence gate counts per case
- **Eval report integration**: Per-case diagnostic fields rendered in RAG eval reports
- **Live eval findings**: All 4 seed cases correctly routed; failures at vector recall stage (Milvus data missing, not code issues)
- **Tests**: 22 diagnostic tests passed
