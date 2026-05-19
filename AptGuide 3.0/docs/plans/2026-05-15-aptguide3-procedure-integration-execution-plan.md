# AptGuide 3.0 Procedure Integration Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn AptGuide 3.0 procedures from validated skeletons into repository-backed and lease-backed user workflows for appointment, lease, memory, handoff, and audit-sensitive operations.

**Architecture:** AptGuide 3.0 keeps the LLM-first understanding layer and typed procedure runtime. lease remains the source of truth for users, rooms, appointments, leases, contracts, and sensitive business data. AptGuide 3.0 owns Agent runtime state in MySQL/Redis and calls lease only through internal tool endpoints.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy async, asyncmy, Redis, MySQL, httpx, pytest, ruff, lease-web-app internal AI tools.

---

## Current Baseline

- Milestone 0 runnable scaffold: complete.
- Milestone 1 independent backend backbone: complete.
- Milestone 2 live integration readiness: locally verified.
- Live dependency evidence:
  - Redis live tests: 4 passed.
  - MySQL schema/repo live tests: 6 passed.
  - `/chat` + MySQL persistence: 8 passed.
  - LLM live: 1 passed.
  - Embedding live: 1 passed.
  - Milvus/vector live: 1 passed.
  - Internal-header auth: 6 passed.
  - Baseline regression: 68 passed, 23 skipped.
  - Ruff: all checks passed.
- Active known gap: procedure integration and repo wiring.

## Direction

This milestone should focus on real user workflows:

1. Wire all 8 repository types through `deps.py`.
2. Normalize in-memory repositories to match the same async contracts as MySQL repositories.
3. Extend `LeaseClient` for appointment and lease internal tool endpoints.
4. Implement `appointment`, `lease`, `memory`, and `handoff` procedures with persistence and graceful fallback.
5. Add audit writes for sensitive operations.
6. Add tests first, then implementation.

## Non-Goals

- Do not change the LLM-first understanding contract unless a test proves it is necessary.
- Do not make AptGuide 3.0 the source of truth for lease business entities.
- Do not call public `/app/*` lease endpoints from AptGuide 3.0; use `/internal/ai/tools/*`.
- Do not build the final operator console in this milestone.
- Do not perform full `rentHouseH5 -> lease -> AptGuide 3.0` production rollout in this milestone.

## Acceptance Gates

- `deps.py` wires session, message, pending action, memory, handoff, trace, procedure run, and audit repositories.
- Memory and handoff in-memory repositories match the async contracts or are wrapped behind compatible adapters.
- `InMemoryPendingActionRepo` exists for local/test confirmation flows.
- `LeaseClient` supports:
  - `create_appointment()`
  - `list_appointments()`
  - `list_leases()`
- `AppointmentProcedure` creates a pending action before writing to lease and can complete the confirmation path.
- `LeaseProcedure` queries lease list data and writes audit events.
- `MemoryProcedure` can save/list preferences through the memory repository.
- `HandoffProcedure` creates durable handoff tickets and writes audit events.
- Existing scaffold behavior and `/chat` shape do not regress.
- `uv run pytest -q` passes.
- `uv run ruff check src tests` passes.
- Live tests against MySQL/Redis/lease still pass when the local environment is running.

## Lease Tool Endpoints

Use the existing lease-web-app internal tools:

```text
GET  /internal/ai/tools/health
POST /internal/ai/tools/room/search
POST /internal/ai/tools/appointment/create
GET  /internal/ai/tools/appointment/list-mine
GET  /internal/ai/tools/lease/list-mine
```

Required headers:

```text
X-Internal-Token: <shared internal token>
X-User-Id: <lease user id>
```

Appointment create request body:

```json
{
  "apartmentId": 10001,
  "appointmentTime": "2026-05-20 10:00",
  "remark": "AI assistant booking"
}
```

## Task 1: Sync Project State

**Files:**
- Modify: `project/feature-list.json`
- Modify: `project/sprint-plan.json`
- Modify: `docs/plans/current-plan.md`
- Modify: `progress/current-plan.md`
- Modify: `docs/plans/next-steps.md`
- Modify: `progress/next-steps.md`

- [ ] Mark `live_integration_readiness` completed with live verification evidence.
- [ ] Add `procedure_integration` as the active planned feature.
- [ ] Add `sprint-004` named `Procedure integration`.
- [ ] Set the active plan to this document.
- [ ] Keep `procedure_integration.passes=false` until tests pass.

## Task 2: Repository Bundle and Wiring

**Files:**
- Modify: `backend/src/aptguide3/api/deps.py`
- Modify: `backend/src/aptguide3/persistence/contracts.py`
- Test: `backend/tests/unit/api/test_deps.py`

- [ ] Define a small repository bundle object containing:
  - `session_repo`
  - `message_repo`
  - `pending_action_repo`
  - `memory_repo`
  - `handoff_repo`
  - `trace_repo`
  - `procedure_run_repo`
  - `audit_repo`
- [ ] Update `_build_memory_repos()`, `_build_mysql_repos()`, and `_build_hybrid_repos()` to return the same bundle shape.
- [ ] Preserve existing `ChatService` constructor wiring for session/message/procedure-run repositories.
- [ ] Pass memory, handoff, pending action, audit, and lease dependencies into `build_runtime()`.
- [ ] Add unit tests proving every persistence mode returns all expected bundle attributes.

## Task 3: In-Memory Contract Compatibility

**Files:**
- Modify: `backend/src/aptguide3/persistence/memory_repo.py`
- Modify: `backend/src/aptguide3/persistence/handoff_repo.py`
- Create: `backend/src/aptguide3/persistence/pending_action_repo.py`
- Test: `backend/tests/unit/persistence/test_in_memory_contracts.py`

- [ ] Add async `list_memories()` and `upsert_memory()` compatibility methods to memory repo.
- [ ] Add async `create_ticket()` and `list_tickets()` compatibility methods to handoff repo.
- [ ] Create `InMemoryPendingActionRepo` with async `save_pending_action()`, `load_pending_action()`, and `mark_completed()`.
- [ ] Keep existing sync helper methods if tests or older code still use them.
- [ ] Add tests for memory, handoff, and pending action in-memory behavior.

## Task 4: LeaseClient Appointment and Lease Methods

**Files:**
- Modify: `backend/src/aptguide3/integrations/lease_client.py`
- Test: `backend/tests/unit/integrations/test_lease_client.py`
- Test: `backend/tests/integration/test_lease_client_live.py`

- [ ] Add internal token and request header support if not already supplied by caller.
- [ ] Implement `create_appointment(user_id, apartment_id, appointment_time, remark)`.
- [ ] Implement `list_appointments(user_id)`.
- [ ] Implement `list_leases(user_id)`.
- [ ] Normalize lease response `Result<T>` envelopes into plain Python dictionaries/lists.
- [ ] Return empty or `None` values on timeout/HTTP failure without raising into user-facing chat.
- [ ] Add unit tests using mocked HTTP responses.
- [ ] Add skip-safe live tests for the running lease service.

## Task 5: Appointment Procedure

**Files:**
- Modify: `backend/src/aptguide3/procedures/appointment.py`
- Modify: `backend/src/aptguide3/application/chat_service.py`
- Test: `backend/tests/unit/procedures/test_appointment.py`
- Test: `backend/tests/integration/test_appointment_live.py`

- [ ] Parse required appointment fields from `UnderstandingResult.slots` or metadata: apartment/room id, appointment time, remark.
- [ ] If required fields are missing, return a clarification response.
- [ ] On first valid request, save a pending action with TTL and return a confirmation action card.
- [ ] On confirmation, load pending action and call `LeaseClient.create_appointment()`.
- [ ] Mark pending action completed after lease returns success.
- [ ] Write an audit event for appointment creation.
- [ ] Add unit tests for missing fields, pending creation, confirmation success, lease failure fallback, and audit write.

## Task 6: Lease Procedure

**Files:**
- Modify: `backend/src/aptguide3/procedures/lease.py`
- Test: `backend/tests/unit/procedures/test_lease.py`
- Test: `backend/tests/integration/test_lease_live.py`

- [ ] Call `LeaseClient.list_leases(user_id)` for lease-list queries.
- [ ] Render lease result cards with lease id, apartment name, room number, status, dates, and rent.
- [ ] Return a clear empty-state message when no lease exists.
- [ ] Write an audit event for every lease query.
- [ ] Add unit tests for success, empty list, lease service unavailable, and audit write.

## Task 7: Memory Procedure

**Files:**
- Modify: `backend/src/aptguide3/procedures/memory.py`
- Test: `backend/tests/unit/procedures/test_memory.py`
- Test: `backend/tests/integration/test_memory_mysql.py`

- [ ] Support saving user preferences through `memory_repo.upsert_memory()`.
- [ ] Support listing current user memories through `memory_repo.list_memories()`.
- [ ] Use deterministic memory ids such as `<user_id>:preference:<key>` for idempotent upsert.
- [ ] Return user-readable confirmation messages and metadata.
- [ ] Add unit tests for save/list behavior.
- [ ] Add MySQL-backed integration test for persistence across sessions.

## Task 8: Handoff Procedure

**Files:**
- Modify: `backend/src/aptguide3/procedures/handoff.py`
- Test: `backend/tests/unit/procedures/test_handoff.py`
- Test: `backend/tests/integration/test_handoff_mysql.py`

- [ ] Create a handoff ticket with session id, user id, trigger type, and summary.
- [ ] Include recent conversation context when available from session metadata.
- [ ] Write an audit event for handoff creation.
- [ ] Return a response containing ticket id and handoff phase metadata.
- [ ] Add unit tests for ticket creation and audit write.
- [ ] Add MySQL-backed integration test for durable ticket persistence.

## Task 9: Durable Trace and Audit Wiring

**Files:**
- Modify: `backend/src/aptguide3/api/deps.py`
- Modify: `backend/src/aptguide3/observability/repository_sink.py`
- Test: `backend/tests/unit/observability/test_repository_sink.py`
- Test: `backend/tests/integration/test_trace_audit_live.py`

- [ ] Use `RepositoryTraceSink` when a trace repository is configured.
- [ ] Keep console trace sink for memory/local mode unless explicitly configured otherwise.
- [ ] Add audit writes for appointment, lease, and handoff sensitive operations.
- [ ] Add integration tests proving trace and audit rows are inserted in MySQL mode.

## Task 10: Readiness Connectivity Probes

**Files:**
- Modify: `backend/src/aptguide3/api/readiness.py`
- Test: `backend/tests/unit/api/test_readiness.py`
- Test: `backend/tests/integration/test_readiness_live.py`

- [ ] Change `/ready` from config-presence-only to optional live probes.
- [ ] Probe MySQL with a lightweight `SELECT 1`.
- [ ] Probe Redis with `PING`.
- [ ] Probe lease with `GET /internal/ai/tools/health`.
- [ ] Probe Milvus with `list_collections()`.
- [ ] Keep LLM/embedding probes configurable so readiness does not spend tokens by default.
- [ ] Report degraded services without crashing.

## Task 11: Main-System Chain Test Plan

**Files:**
- Create: `docs/plans/2026-05-15-aptguide3-main-chain-test-plan.md`
- Test: `backend/tests/integration/test_lease_gateway_chain.py`

- [ ] Document how to start AptGuide 3.0 on `8100` with internal-header auth.
- [ ] Document how to start lease-web-app with `APTGUIDE_URL=http://host.docker.internal:8100`.
- [ ] Add a smoke test for `lease /app/ai/chat -> AptGuide 3.0 /api/chat` when a test user/JWT path is available.
- [ ] If login/JWT setup is unavailable, record the exact blocker and keep this test skip-safe.

## Verification Commands

Run from `AptGuide 3.0/backend`:

```bash
uv run pytest -q
uv run ruff check src tests
```

Run with local live dependencies:

```bash
APTGUIDE3_REDIS_URL=redis://127.0.0.1:6379/3 \
APTGUIDE3_MYSQL_DSN=mysql+asyncmy://chove:123456@127.0.0.1:3306/least \
APTGUIDE3_PERSISTENCE_MODE=mysql \
APTGUIDE3_LEASE_BASE_URL=http://127.0.0.1:8081 \
APTGUIDE3_VECTOR_URI=http://127.0.0.1:19530 \
uv run pytest tests/integration -q
```

Expected final state:

- All unit tests pass.
- Live tests pass when services are running.
- Skip-safe tests skip only when an external dependency is intentionally absent.
- Ruff passes.

## Execution Order

1. Sync harness state.
2. Repository bundle and wiring.
3. In-memory contract compatibility.
4. LeaseClient extensions.
5. Appointment procedure.
6. Lease procedure.
7. Memory procedure.
8. Handoff procedure.
9. Trace and audit wiring.
10. Readiness connectivity probes.
11. Main-system chain test plan.

## Stop Conditions

- Stop procedure expansion if repository contracts cannot be made consistent across memory and MySQL modes.
- Stop appointment implementation if lease appointment endpoint contract changes or rejects the expected payload.
- Stop main-system chain claims if lease `/app/ai/chat` cannot be tested with a real authenticated user context.
