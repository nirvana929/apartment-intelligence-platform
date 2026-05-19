# AptGuide 3.0 Procedure Integration Plan

> **Date:** 2026-05-15
> **Task:** 8 of Live Integration Readiness -- Procedure Integration Readiness Review
> **Status:** Plan only. Do NOT implement until live persistence/auth checks (Tasks 4-7) pass.

---

## Summary

This plan covers wiring each procedure to its required repository and lease-client dependencies. The review identified that **deps.py builds only 3 of 8 repository types** despite MySql implementations existing for all 8. Four skeleton procedures need implementation. Two procedures (kb_qa, clarify) are already complete or near-complete.

---

## Critical Wiring Gap in deps.py

`_build_mysql_repos()` and `_build_hybrid_repos()` return only `(session_repo, message_repo, procedure_run_repo)`. The following repository implementations exist in `persistence/mysql_repos.py` but are never instantiated or passed to any consumer:

| Repository | MySql Implementation | Used By |
|---|---|---|
| `MySqlMemoryRepository` | exists | nothing (MemoryProcedure needs it) |
| `MySqlHandoffRepository` | exists | nothing (HandoffProcedure needs it) |
| `MySqlPendingActionRepository` | exists | nothing (AppointmentProcedure needs it) |
| `MySqlTraceRepository` | exists | nothing (Tracer could use it instead of ConsoleTraceSink) |
| `MySqlAuditRepository` | exists | nothing (no audit events are written anywhere) |

Additionally, two sync-protocol repos exist with in-memory implementations that are also never wired:
- `memory_repo.py` has `InMemoryMemoryRepo` (sync protocol, not wired)
- `handoff_repo.py` has `InMemoryHandoffRepo` (sync protocol, not wired)

---

## Procedure-by-Procedure Review

### 1. room_search.py -- Room Search

**Current state:** Partially functional. Accepts optional `lease_client` in constructor. If lease_client is present and returns rooms, produces room cards. Otherwise falls back to a placeholder message.

**What works:**
- LeaseClient is wired via `build_runtime()` in deps.py (line 66)
- `LeaseClient.validate_rooms()` is called correctly
- Async-to-sync bridge via `concurrent.futures.ThreadPoolExecutor` works
- Room card formatting is complete

**Missing lease-client integration:**
- None for basic search. LeaseClient is already wired.

**Missing repository integration:**
- None required for the search action itself. Room search is stateless -- it queries lease and returns results.
- Optional: TraceRepository / AuditRepository could log search queries for analytics, but this is not required for MVP.

**Missing behavior:**
- The placeholder message mentions "vector" integration for semantic room search. If the LLM produces `retrieval_queries` in understanding for room search (route=rag, task=room_search), the procedure could also query VectorClient for semantically similar rooms. This is an enhancement, not a gap.
- No pagination support -- currently caps at `rooms[:10]`.

**Effort:** Small (already mostly wired)

**Acceptance criteria:**
- When lease_client is configured and lease service is running, room search returns real room cards
- When lease_client is unavailable, graceful fallback to placeholder
- No errors propagate to user on lease timeout

---

### 2. kb_qa.py -- Knowledge Base Q&A

**Current state:** Fully functional when VectorClient and EmbeddingClient are configured.

**What works:**
- Both clients are wired via `get_kb_clients()` in deps.py
- Embedding query -> vector search -> hit-to-card pipeline is complete
- Risk level assessment is implemented
- Graceful fallback to placeholder when clients are None

**Missing lease-client integration:** N/A (uses vector/embedding, not lease)

**Missing repository integration:**
- None required for Q&A itself. The procedure is stateless.
- Optional: ProcedureRunRepository could log which KB hits were returned per query for quality tracking.

**Missing behavior:**
- No re-ranking of results beyond vector distance
- No source URL or document link in cards (only title + snippet)
- No caching of frequently asked queries

**Effort:** Small (already complete for MVP)

**Acceptance criteria:**
- When embedding + vector are configured and Milvus has data, kb_qa returns grounded cards
- When either client is unavailable, graceful fallback
- Top-k=5 results returned with risk levels

---

### 3. appointment.py -- Appointment Booking

**Current state:** Pure skeleton. Returns a static placeholder message.

**What works:**
- Procedure is registered in `build_runtime()` (line 68)
- UnderstandingResult provides `domain`, `action` fields that could drive appointment logic

**Missing lease-client integration:**
- `LeaseClient` needs an `create_appointment()` method to POST appointment requests to lease's `/internal/ai/tools/appointment/create` (or similar endpoint)
- `LeaseClient` may need a `list_appointments()` method for appointment status queries
- `LeaseClient` may need a `cancel_appointment()` method

**Missing repository integration:**
- `PendingActionRepository` is needed for the confirmation flow:
  1. User says "I want to book a viewing for room 101 on Saturday"
  2. Procedure creates a pending action with appointment details
  3. Returns confirmation card to user
  4. User confirms -> pending action is loaded and executed via LeaseClient
  5. Pending action is marked completed
- `AuditRepository` should log appointment creation/cancellation for compliance

**Required wiring changes:**
- `AppointmentProcedure.__init__()` needs `lease_client`, `pending_action_repo`, `audit_repo` parameters
- `build_runtime()` needs to pass these dependencies
- `_build_mysql_repos()` / `_build_hybrid_repos()` need to return `PendingActionRepository` and `AuditRepository`
- `_build_memory_repos()` needs `InMemoryPendingActionRepo` (does not exist yet) or a simple in-memory version

**Missing in-memory repos:**
- No `InMemoryPendingActionRepo` exists. `memory_repo.py` and `handoff_repo.py` have in-memory versions but `PendingActionRepository` does not.

**Effort:** Large (new LeaseClient methods + pending action flow + repo wiring)

**Acceptance criteria:**
- User can initiate appointment booking through natural language
- Pending action is created and persisted
- Confirmation flow works (user confirms -> appointment created via lease)
- Pending action TTL expires if user does not confirm
- Appointment creation is audit-logged

---

### 4. lease.py -- Lease Info Query

**Current state:** Pure skeleton. Returns a static placeholder message.

**What works:**
- Procedure is registered in `build_runtime()` (line 69)
- UnderstandingResult provides `domain`, `action` fields

**Missing lease-client integration:**
- `LeaseClient` needs a `get_lease_info(user_id, lease_id?)` method to query lease's `/internal/ai/tools/lease/info` (or similar)
- `LeaseClient` may need a `list_leases(user_id)` method for listing active leases
- `LeaseClient` may need a `get_payment_history(lease_id)` method

**Missing repository integration:**
- `AuditRepository` should log lease info queries (sensitive data access)
- No other repositories needed -- lease queries are read-only and stateless

**Required wiring changes:**
- `LeaseProcedure.__init__()` needs `lease_client` and `audit_repo` parameters
- `build_runtime()` needs to pass these dependencies
- `_build_*_repos()` needs to return `AuditRepository`

**Effort:** Medium (new LeaseClient methods + wiring, no pending action flow)

**Acceptance criteria:**
- User can query lease info through natural language
- LeaseClient calls lease API and returns structured data
- Sensitive queries are audit-logged
- Graceful fallback when lease service is unavailable

---

### 5. memory.py -- User Memory Management

**Current state:** Pure skeleton. Returns a static placeholder message.

**What works:**
- Procedure is registered in `build_runtime()` (line 70)
- `MemoryRepositoryContract` (async) exists in `contracts.py` with `list_memories()` and `upsert_memory()`
- `MySqlMemoryRepository` fully implements `MemoryRepositoryContract`
- `InMemoryMemoryRepo` (sync) exists in `memory_repo.py` but uses a different protocol (save/load_all/delete vs list_memories/upsert_memory)

**Missing lease-client integration:** N/A (memory is AptGuide-internal)

**Missing repository integration:**
- `MemoryRepositoryContract` needs to be wired into `MemoryProcedure`
- The sync `InMemoryMemoryRepo` protocol (`save/load_all/delete`) does NOT match the async `MemoryRepositoryContract` protocol (`list_memories/upsert_memory`) -- this is a protocol mismatch that needs resolution

**Protocol mismatch detail:**
```
# memory_repo.py (sync, in-memory):
def save(user_id, key, value) -> None
def load_all(user_id) -> dict[str, str]
def delete(user_id, key) -> None

# contracts.py (async, MySQL):
async def list_memories(user_id) -> list[dict]
async def upsert_memory(memory_id, user_id, kind, key_name, value_json) -> None
```

**Required wiring changes:**
- `MemoryProcedure.__init__()` needs `memory_repo` parameter (either sync or async protocol)
- `build_runtime()` needs to pass memory repo
- `_build_mysql_repos()` needs to return `MySqlMemoryRepository`
- `_build_memory_repos()` needs to return `InMemoryMemoryRepo` (or adapt it to async contract)
- Decide on sync vs async protocol: procedures currently run synchronously (called from `ProcedureRuntime.run()` which is sync), so either:
  - (a) Use sync `InMemoryMemoryRepo` for memory mode and wrap `MySqlMemoryRepository` in a sync bridge for mysql/hybrid mode
  - (b) Make `MemoryProcedure.run()` async and update `ProcedureRuntime` accordingly (larger change)

**Effort:** Medium (protocol reconciliation + wiring + basic CRUD logic)

**Acceptance criteria:**
- User can save preferences (e.g., "remember I prefer 2-bedroom apartments")
- User can list their saved memories
- User can delete memories
- Memories persist across sessions when MySQL is enabled
- In-memory mode works for local development

---

### 6. handoff.py -- Human Handoff

**Current state:** Pure skeleton. Returns a static placeholder message.

**What works:**
- Procedure is registered in `build_runtime()` (line 71)
- `HandoffRepositoryContract` (async) exists in `contracts.py` with `create_ticket()` and `list_tickets()`
- `MySqlHandoffRepository` fully implements `HandoffRepositoryContract`
- `InMemoryHandoffRepo` (sync) exists in `handoff_repo.py` with `create/list_open/resolve`

**Missing lease-client integration:**
- Optional: LeaseClient may need a `notify_handoff(session_id, reason)` endpoint to alert human operators in the lease system
- This is not strictly required for MVP -- tickets can be created in AptGuide DB and operators can query them

**Missing repository integration:**
- `HandoffRepositoryContract` needs to be wired into `HandoffProcedure`
- Same sync vs async protocol mismatch as memory:
```
# handoff_repo.py (sync):
def create(session_id, reason, context) -> str
def list_open() -> list[dict]
def resolve(handoff_id) -> None

# contracts.py (async):
async def create_ticket(ticket_id, session_id, user_id, trigger_type, summary) -> None
async def list_tickets(status) -> list[dict]
```

**Required wiring changes:**
- `HandoffProcedure.__init__()` needs `handoff_repo` parameter
- `build_runtime()` needs to pass handoff repo
- `_build_mysql_repos()` needs to return `MySqlHandoffRepository`
- `_build_memory_repos()` needs to return `InMemoryHandoffRepo`
- `AuditRepository` should log handoff events

**Effort:** Medium (protocol reconciliation + wiring + ticket creation logic)

**Acceptance criteria:**
- User can request human handoff through natural language or explicit command
- Handoff ticket is created and persisted
- Ticket includes session context and trigger reason
- Operators can list open tickets (via API or admin interface)
- Handoff is audit-logged

---

### 7. clarify.py -- Clarification

**Current state:** Complete. No external dependencies needed.

**What works:**
- Uses `understanding.clarification.question` directly
- Falls back to default question if none provided
- No repository or client integration needed

**Missing lease-client integration:** N/A

**Missing repository integration:**
- None required. Clarification is a pure understanding-driven response.
- Optional: MessageRepository could log clarification requests for understanding quality analysis.

**Effort:** None (already complete)

**Acceptance criteria:**
- Already met: clarification question is returned to user

---

## Dependency Wiring Summary

### What deps.py build_runtime() currently passes:

| Procedure | Constructor Args Wired |
|---|---|
| ClarifyProcedure | (none needed) |
| RoomSearchProcedure | lease_client |
| KbQaProcedure | vector_client, embedding_client |
| AppointmentProcedure | (none -- skeleton) |
| LeaseProcedure | (none -- skeleton) |
| MemoryProcedure | (none -- skeleton) |
| HandoffProcedure | (none -- skeleton) |

### What each procedure needs:

| Procedure | lease_client | pending_action_repo | memory_repo | handoff_repo | audit_repo |
|---|---|---|---|---|---|
| room_search | DONE | -- | -- | -- | optional |
| kb_qa | -- | -- | -- | -- | optional |
| appointment | NEEDED | NEEDED | -- | -- | NEEDED |
| lease | NEEDED | -- | -- | -- | NEEDED |
| memory | -- | -- | NEEDED | -- | optional |
| handoff | -- | -- | -- | NEEDED | NEEDED |
| clarify | -- | -- | -- | -- | -- |

### What _build_*_repos() needs to return (currently only 3 of 8):

Current: `(session_repo, message_repo, procedure_run_repo)`

Needed: `(session_repo, message_repo, procedure_run_repo, memory_repo, handoff_repo, pending_action_repo, trace_repo, audit_repo)`

Or: use a structured container (dataclass/dict) instead of a growing tuple.

---

## Recommended Execution Order

### Phase 1: deps.py Repository Wiring (no procedure behavior changes)

**Goal:** Make all 8 repository types available from `_build_repos()`.

1. Expand `_build_mysql_repos()` to instantiate and return all 8 MySql repos
2. Expand `_build_hybrid_repos()` similarly
3. Expand `_build_memory_repos()` to return in-memory versions (create `InMemoryPendingActionRepo`)
4. Update `get_chat_service()` to accept and pass the new repos
5. Pass repos to `build_runtime()` so procedures can receive them

**Parallelism:** This is a single task with no parallelism.

**Effort:** Small

**Dependencies:** None (can proceed immediately)

### Phase 2: Skeleton Procedure Implementation (requires Phase 1)

**Goal:** Wire repos + lease_client into skeleton procedures. Implement basic CRUD logic.

Execute in this order, with items marked [P] eligible for parallel execution:

1. **memory.py** [P] -- Wire MemoryRepositoryContract. Implement list/upsert/delete actions based on `understanding.action`. No lease dependency.
2. **handoff.py** [P] -- Wire HandoffRepositoryContract. Implement ticket creation. No lease dependency.
3. **lease.py** -- Add LeaseClient methods first, then wire into procedure. Depends on LeaseClient extension.
4. **appointment.py** -- Add LeaseClient methods + wire PendingActionRepository. Most complex procedure. Depends on LeaseClient extension.

**Parallelism:** memory.py and handoff.py can be implemented in parallel (no shared dependency beyond Phase 1). lease.py and appointment.py both need LeaseClient extensions, so lease.py should come first.

**Effort:** memory=Medium, handoff=Medium, lease=Medium, appointment=Large

### Phase 3: LeaseClient Extension (can start in parallel with Phase 2 items 1-2)

**Goal:** Add methods to LeaseClient that appointment.py and lease.py need.

1. `get_lease_info(user_id, lease_id?)` -- for lease.py
2. `create_appointment(user_id, room_id, datetime, ...)` -- for appointment.py
3. `list_appointments(user_id)` -- optional, for appointment queries
4. `cancel_appointment(appointment_id)` -- optional

**Parallelism:** Can be done in parallel with memory.py and handoff.py implementation.

**Effort:** Medium

### Phase 4: Audit Logging (requires Phase 1, can parallel with Phase 2)

**Goal:** Wire AuditRepository into procedures that handle sensitive operations.

1. Create an `AuditService` or pass `audit_repo` into `ChatService` / `ProcedureRuntime`
2. Log appointment creation/cancellation
3. Log lease info queries
4. Log handoff events
5. Wire `MySqlAuditRepository` (or `RepositoryTraceSink` to also write audit events)

**Effort:** Small

---

## Acceptance Criteria (Overall)

- [ ] `build_runtime()` passes all required dependencies to each procedure
- [ ] `_build_repos()` returns all 8 repository types for each persistence mode
- [ ] `room_search` returns real room cards when lease service is available
- [ ] `kb_qa` returns grounded answers when embedding + vector are available
- [ ] `appointment` creates pending actions and processes confirmations via lease
- [ ] `lease` queries lease info via LeaseClient and returns structured results
- [ ] `memory` supports list/upsert/delete operations persisted to MySQL
- [ ] `handoff` creates tickets persisted to MySQL with session context
- [ ] `clarify` continues to work unchanged
- [ ] All procedures degrade gracefully when external services are unavailable
- [ ] `uv run pytest -q` still passes
- [ ] `uv run ruff check src tests` still passes

---

## Risks

1. **Protocol mismatch:** sync vs async repo protocols will require either a sync bridge or async procedure refactor. Recommend sync bridge to minimize blast radius.
2. **LeaseClient contract unknown:** The exact lease API endpoints for appointments and lease queries have not been confirmed with the lease team. Implementation may need adjustment.
3. **Pending action TTL:** The confirmation flow for appointments depends on Redis TTL working correctly in hybrid mode. Memory mode has no TTL.
4. **Procedure execution is synchronous:** `ProcedureRuntime.run()` is sync, but MySQL repos are async. All procedure-repo interactions will need the same `asyncio.get_running_loop` bridge pattern used in ChatService._persist_message.
