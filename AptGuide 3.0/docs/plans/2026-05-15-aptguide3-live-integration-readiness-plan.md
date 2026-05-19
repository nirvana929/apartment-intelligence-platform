# AptGuide 3.0 Live Integration Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move AptGuide 3.0 from an independently verified backend backbone to a live-dependency verified service ready for the `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat` integration path.

**Architecture:** AptGuide 3.0 keeps ownership of Agent runtime state while lease remains the source of truth for users, rooms, appointments, leases, contracts, and sensitive business data. This phase wires real MySQL and Redis into the dependency graph, verifies external service boundaries, and adds integration tests before expanding business procedures. The independent frontend remains a validation UI, not the final production entry.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy async, asyncmy, redis.asyncio, MySQL, Redis, httpx, pymilvus, OpenAI-compatible LLM/embedding clients, pytest, ruff.

---

## Direction

Milestone 2 should focus on **live integration readiness**, not more scaffold work.

The immediate direction is:

1. Replace in-memory runtime dependencies with configurable Redis/MySQL-backed implementations.
2. Prove the service can start, answer readiness, and process chat with real infrastructure.
3. Validate the internal-header auth boundary expected from `lease`.
4. Verify Milvus, embedding, LLM, and lease tool clients at the boundary level.
5. Only after those pass, expand room search, appointment, lease, memory, and handoff behavior.

## Completion Estimate

Current state:

- Milestone 0 runnable scaffold: complete.
- Milestone 1 independent backend backbone: complete by checkpoint evidence, with `55 passed, 2 skipped` and ruff clean.
- Production/live integration: not complete.

Practical completion estimate:

- Backend foundation: about 60-65% complete.
- Production readiness: about 35-40% complete.
- Main-system launch readiness: about 25-30% complete.

Remaining work is mostly integration and verification risk, not raw code volume. The largest unknowns are real MySQL/Redis behavior, lease gateway contract details, Milvus/embedding data quality, and end-to-end chat behavior through the main-system chain.

## Acceptance Gates

- `backend/src/aptguide3/api/deps.py` can select in-memory, Redis, and MySQL-backed dependencies from settings.
- Real MySQL schema can be applied cleanly from `backend/src/aptguide3/database/schema.sql`.
- Real Redis can store and expire sessions and pending actions.
- `/ready` reports real MySQL, Redis, lease, vector, embedding, and LLM readiness accurately.
- `/api/chat` works in dev auth mode and integrated internal-header auth mode.
- Chat messages, procedure runs, trace events, memories, handoff tickets, and audit events persist durably when MySQL is enabled.
- The lease gateway can call AptGuide 3.0 using `X-Internal-Token`, `X-User-Id`, and `X-Request-Id`.
- Frontend validation UI still works against the backend.
- `uv run pytest -q` passes.
- `uv run ruff check src tests` passes.
- A live-dependency verification report records what passed, failed, or was skipped.

## Non-Goals

- Do not make AptGuide 3.0 the source of truth for rooms, users, appointments, leases, contracts, or sensitive customer data.
- Do not let `rentHouseH5` call AptGuide 3.0 directly in production.
- Do not copy AptGuide 2.0 keyword routing or RAG v2 runtime behavior.
- Do not expand all business procedures before the live persistence and service boundaries are verified.
- Do not claim production readiness while MySQL, Redis, lease, Milvus, embedding, or LLM checks are skipped.

## Task 1: Sync Project State

**Files:**
- Modify: `project/feature-list.json`
- Modify: `project/sprint-plan.json`
- Modify: `docs/plans/current-plan.md`
- Modify: `progress/current-plan.md`

- [ ] Mark `independent_backend_backbone` as completed with evidence `55 passed, 2 skipped; ruff clean`.
- [ ] Add new feature `live_integration_readiness` with status `planned`.
- [ ] Add sprint `sprint-003` named `Live integration readiness`.
- [ ] Set the active objective to Milestone 2.
- [ ] Do not mark Milestone 2 as passing until live verification has run.

## Task 2: Configure Runtime Persistence Selection

**Files:**
- Modify: `backend/src/aptguide3/config.py`
- Modify: `backend/src/aptguide3/api/deps.py`
- Test: `backend/tests/unit/api/test_deps.py`

- [ ] Add settings that select persistence mode: `memory`, `mysql`, or `hybrid`.
- [ ] Keep local dev default safe: memory mode unless MySQL/Redis settings are explicitly enabled.
- [ ] Wire MySQL repositories behind existing repository contracts.
- [ ] Wire RedisStateStore for hot session and pending-action TTL when Redis is enabled.
- [ ] Add tests proving dependency selection does not require live MySQL/Redis in unit tests.

## Task 3: Add Local Live Dependency Compose

**Files:**
- Create: `backend/docker-compose.local.yml`
- Create: `backend/scripts/apply_schema.py`
- Modify: `backend/.env.example`
- Test: `backend/tests/integration/test_mysql_schema.py`

- [ ] Add local MySQL and Redis services for developer verification.
- [ ] Add a schema application script that loads `database/schema.sql`.
- [ ] Document exact env vars for MySQL, Redis, auth mode, lease URL, vector URL/config, embedding, and LLM.
- [ ] Add an integration test that can be skipped unless live dependency env vars are present.

## Task 4: Verify Real Redis and MySQL Behavior

**Files:**
- Create: `backend/tests/integration/test_redis_state_store_live.py`
- Create: `backend/tests/integration/test_mysql_repos_live.py`
- Modify: `docs/tests/verification-log.md`
- Modify: `docs/tests/evaluation-report.md`

- [ ] Test Redis session write/read and TTL expiry.
- [ ] Test Redis pending-action write/read and TTL expiry.
- [ ] Test MySQL session/message/procedure-run/trace persistence.
- [ ] Record exact commands and results.
- [ ] If live services are unavailable, record skipped status explicitly.

## Task 5: Verify Auth and Lease Gateway Boundary

**Files:**
- Create: `backend/tests/integration/test_internal_header_auth_live.py`
- Create: `docs/system/lease-gateway-contract.md`
- Modify: `backend/src/aptguide3/api/auth.py`
- Modify: `backend/src/aptguide3/api/app.py`

- [ ] Define the minimum lease-to-AptGuide request contract: path, headers, request body, response body, and error behavior.
- [ ] Verify AptGuide 3.0 rejects missing or invalid `X-Internal-Token` in integrated mode.
- [ ] Verify AptGuide 3.0 trusts `X-User-Id` from lease, not body-provided user identity.
- [ ] Verify `X-Request-Id` propagates into response metadata and trace records.

## Task 6: Verify External AI and Retrieval Boundaries

**Files:**
- Create: `backend/tests/integration/test_llm_live.py`
- Create: `backend/tests/integration/test_embedding_live.py`
- Create: `backend/tests/integration/test_vector_live.py`
- Modify: `docs/tests/evaluation-report.md`

- [ ] Run one minimal live LLM structured-understanding check when API credentials are present.
- [ ] Run one embedding call when credentials are present.
- [ ] Run one Milvus/vector search boundary check when configuration is present.
- [ ] Keep all tests skip-safe when credentials are absent.
- [ ] Record skipped checks as not verified, not passed.

## Task 7: End-to-End Chat Persistence Verification

**Files:**
- Create: `backend/tests/integration/test_chat_live_persistence.py`
- Modify: `backend/src/aptguide3/application/chat_service.py`
- Modify: `backend/src/aptguide3/observability/repository_sink.py`

- [ ] Start with a chat request in dev mode and verify response shape.
- [ ] Verify inbound and outbound messages are persisted.
- [ ] Verify procedure run is persisted with request/session/user ids.
- [ ] Verify trace event is persisted with request/session metadata.
- [ ] Verify the service remains usable if optional external dependencies are unavailable and readiness reports the degraded state.

## Task 8: Procedure Integration Readiness Review

**Files:**
- Modify: `backend/src/aptguide3/procedures/room_search.py`
- Modify: `backend/src/aptguide3/procedures/kb_qa.py`
- Modify: `backend/src/aptguide3/procedures/appointment.py`
- Modify: `backend/src/aptguide3/procedures/lease.py`
- Modify: `backend/src/aptguide3/procedures/memory.py`
- Modify: `backend/src/aptguide3/procedures/handoff.py`
- Create: `docs/plans/2026-05-15-aptguide3-procedure-integration-plan.md`

- [ ] Review each procedure for missing repository or lease-client integration points.
- [ ] Do not expand behavior in this task unless a small wiring fix is required.
- [ ] Produce the next procedure-specific implementation plan only after live persistence/auth checks pass.

## Task 9: Operator Flow and Deployment Gap List

**Files:**
- Create: `docs/system/operator-flow.md`
- Create: `docs/system/deployment-readiness.md`
- Modify: `docs/plans/known-issues.md`

- [ ] Define the minimum handoff/operator workflow required for production.
- [ ] List required runtime env vars and deployment dependencies.
- [ ] List operational risks: retries, idempotency, data retention, audit, alerting, and secret handling.
- [ ] Keep this as a readiness checklist unless implementation is explicitly requested.

## Verification Commands

Run from `AptGuide 3.0/backend`:

```bash
uv run pytest -q
uv run ruff check src tests
```

Run only when live dependencies are configured:

```bash
uv run pytest tests/integration -q
```

Expected final state for this milestone:

- Unit tests pass.
- Ruff passes.
- Live integration tests either pass or are explicitly skipped with missing dependency evidence.
- Evaluation report clearly separates verified behavior from unverified external dependencies.

## Recommended Execution Order

1. State sync.
2. Runtime persistence selection.
3. Local MySQL/Redis compose and schema application.
4. Real Redis/MySQL verification.
5. Auth and lease gateway boundary.
6. LLM/embedding/vector boundary verification.
7. End-to-end chat persistence.
8. Procedure integration readiness review.
9. Operator/deployment gap list.

## Stop Conditions

- Stop expanding procedures if Redis/MySQL cannot be verified.
- Stop production-readiness claims if any live dependency is skipped.
- Stop main-system integration if the lease gateway contract is not confirmed.
- Stop frontend integration if `/api/chat` does not pass internal-header auth and persistence verification.
