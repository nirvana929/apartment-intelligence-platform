# AptGuide 3.0 Independent Backend Backbone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the runnable AptGuide 3.0 scaffold into an independently verifiable backend service that can later integrate into the AptGuide main-system chain through `lease /app/ai/chat`.

**Architecture:** AptGuide 3.0 owns Agent runtime state, while lease remains the source of truth for users, rooms, appointments, leases, contracts, and sensitive business data. The backend persists sessions, messages, pending actions, memories, handoff tickets, traces, procedure runs, and audit events through repository contracts backed by MySQL, with Redis used for hot session state and pending-action TTL. The LLM-first understanding layer remains the only natural-language interpretation layer.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy async, asyncmy, redis.asyncio, MySQL, Redis, httpx, pymilvus, OpenAI-compatible LLM/embedding clients, pytest, ruff.

---

## Product Boundary

This plan implements the next mainline objective after the completed scaffold.

```text
Milestone 0: Runnable scaffold
  Status: complete
  Evidence: 36 tests passed, 2 skipped; ruff clean

Milestone 1: Independent backend backbone
  Status: this plan
  Goal: durable Agent state, auth boundary, readiness, and persistence contracts

Later: AptGuide main-system integration
  Goal: rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat
```

The final production entry remains the AptGuide main-system chain:

```text
rentHouseH5
  -> lease web-app POST /app/ai/chat
      -> AptGuide 3.0 POST /api/chat
          -> AptGuide 3.0 DB / Redis for Agent state
          -> lease internal tools for business facts and writes
          -> Milvus for retrieval
          -> LLM for understanding and response generation
```

## Non-Goals

- Do not copy AptGuide 2.0 keyword routing, risk-aware query routing, or RAG v2 runtime.
- Do not make AptGuide 3.0 the source of truth for rooms, appointments, leases, users, contracts, or sensitive customer data.
- Do not let frontend call lease, Milvus, MySQL, Redis, or LLM providers directly.
- Do not expand business procedures beyond repository contract integration in this phase.
- Do not claim production readiness without real MySQL/Redis/lease/Milvus/LLM verification.

## Acceptance Gates

- `backend/src/aptguide3/database/schema.sql` defines all required Agent-state tables.
- SQLAlchemy models match the schema and compile in tests.
- Repository contracts exist for sessions, messages, pending actions, memories, handoff, traces, procedure runs, and audit events.
- In-memory implementations continue to support current tests.
- MySQL-backed repository implementations exist behind the same contracts.
- Redis hot-state store supports session and pending-action TTL.
- `ChatService` persists inbound/outbound messages and procedure-run records.
- Trace sink can write durable trace events through a repository.
- `/ready` reports MySQL, Redis, lease, vector, embedding, and LLM readiness without crashing when optional services are unavailable.
- API auth boundary supports local dev mode and integrated internal-header mode.
- Existing tests still pass.
- New unit tests for schema, repositories, auth, readiness, and chat persistence pass.
- Ruff passes.

## File Map

### Create

- `backend/src/aptguide3/api/auth.py` - AuthContext and resolver for dev mode and integrated internal-header mode.
- `backend/src/aptguide3/api/readiness.py` - readiness report construction.
- `backend/src/aptguide3/database/__init__.py` - database package marker.
- `backend/src/aptguide3/database/database.py` - async SQLAlchemy engine/session factory.
- `backend/src/aptguide3/database/models.py` - SQLAlchemy models for Agent-state tables.
- `backend/src/aptguide3/database/schema.sql` - MySQL schema for local/staging setup.
- `backend/src/aptguide3/persistence/contracts.py` - typed repository protocols and state dataclasses.
- `backend/src/aptguide3/persistence/mysql_repos.py` - MySQL repository implementations.
- `backend/src/aptguide3/persistence/redis_store.py` - Redis hot session and pending-action TTL store.
- `backend/src/aptguide3/observability/repository_sink.py` - trace sink that writes trace events to persistence.
- `backend/tests/unit/api/test_auth.py` - auth resolver tests.
- `backend/tests/unit/api/test_readiness.py` - readiness report tests.
- `backend/tests/unit/database/test_models.py` - SQLAlchemy model/schema tests.
- `backend/tests/unit/persistence/test_redis_store.py` - Redis store tests with fake Redis.
- `backend/tests/unit/persistence/test_mysql_repos.py` - repository behavior tests with fake async session or isolated model assertions.
- `backend/tests/unit/application/test_chat_persistence.py` - ChatService persistence tests.
- `docs/system/main-system-integration-boundary.md` - AptGuide 3.0 integration boundary with AptGuide/lease/rentHouseH5.

### Modify

- `backend/pyproject.toml` - add `sqlalchemy`, `asyncmy`, and `redis`.
- `backend/.env.example` - document auth, MySQL, Redis, readiness, internal token, and CORS settings.
- `backend/src/aptguide3/config.py` - add persistence/auth/readiness settings.
- `backend/src/aptguide3/api/app.py` - add `/api/chat` alias if needed, `/ready`, CORS, auth wiring.
- `backend/src/aptguide3/api/deps.py` - add database, Redis, auth, repository, and trace sink factories.
- `backend/src/aptguide3/api/schemas.py` - ensure response includes `session_id`, `request_id`, and trace metadata.
- `backend/src/aptguide3/application/chat_service.py` - persist messages, pending actions, procedure runs, and trace metadata.
- `backend/src/aptguide3/observability/sink.py` - keep console/null sinks and add repository sink compatibility.
- `backend/src/aptguide3/procedures/*` - inject repository contracts only where required; do not invent private state stores.
- `docs/plans/current-plan.md` - make this plan active.
- `docs/plans/handoff.md` - hand next execution to persistence backbone work.
- `docs/plans/sprint-plan.md` - record Milestone 1 sprint scope.
- `docs/plans/next-steps.md` - align with independent-backbone sequence.
- `docs/plans/known-issues.md` - record real current blockers.
- `docs/plans/README.md` - add this plan.
- `progress/current-plan.md` - sync active objective.
- `progress/known-issues.md` - replace stale scaffold-era issues.
- `progress/next-steps.md` - sync next work.
- `reports/evaluation-report.md` - record current verification and unverified live dependencies.
- `project/feature-list.json` - sync feature statuses.
- `project/sprint-plan.json` - sync sprint objective.

## Data Model

The MySQL schema should use `aptguide3_` prefixes so it can share a database with existing projects.

```sql
CREATE TABLE IF NOT EXISTS aptguide3_users (
  user_id VARCHAR(64) PRIMARY KEY,
  source VARCHAR(32) NOT NULL DEFAULT 'lease',
  display_name VARCHAR(128) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_sessions (
  session_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  active_task VARCHAR(64) NULL,
  rolling_summary TEXT NOT NULL,
  context JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_sessions_user_id (user_id),
  INDEX idx_aptguide3_sessions_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_messages (
  message_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  request_id VARCHAR(80) NOT NULL,
  role VARCHAR(32) NOT NULL,
  content TEXT NOT NULL,
  metadata JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_messages_session_id (session_id),
  INDEX idx_aptguide3_messages_user_id (user_id),
  INDEX idx_aptguide3_messages_request_id (request_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_pending_actions (
  pending_action_id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  action_type VARCHAR(80) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  payload JSON NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_pending_actions_session_id (session_id),
  INDEX idx_aptguide3_pending_actions_user_id (user_id),
  INDEX idx_aptguide3_pending_actions_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_memories (
  memory_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  kind VARCHAR(64) NOT NULL,
  key_name VARCHAR(128) NOT NULL,
  value_json JSON NOT NULL,
  source_session_id VARCHAR(64) NOT NULL DEFAULT '',
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_memories_user_id (user_id),
  INDEX idx_aptguide3_memories_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_memory_candidates (
  candidate_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  session_id VARCHAR(64) NOT NULL,
  kind VARCHAR(64) NOT NULL,
  payload JSON NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_memory_candidates_user_id (user_id),
  INDEX idx_aptguide3_memory_candidates_session_id (session_id),
  INDEX idx_aptguide3_memory_candidates_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_handoff_tickets (
  ticket_id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'open',
  trigger_type VARCHAR(64) NOT NULL,
  summary JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_handoff_tickets_session_id (session_id),
  INDEX idx_aptguide3_handoff_tickets_user_id (user_id),
  INDEX idx_aptguide3_handoff_tickets_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_operator_messages (
  message_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  ticket_id VARCHAR(64) NOT NULL,
  sender VARCHAR(32) NOT NULL,
  content TEXT NOT NULL,
  metadata JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_operator_messages_ticket_id (ticket_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_trace_events (
  event_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  trace_id VARCHAR(80) NOT NULL,
  request_id VARCHAR(80) NOT NULL DEFAULT '',
  session_id VARCHAR(64) NOT NULL DEFAULT '',
  event_name VARCHAR(128) NOT NULL,
  payload JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_trace_events_trace_id (trace_id),
  INDEX idx_aptguide3_trace_events_session_id (session_id),
  INDEX idx_aptguide3_trace_events_request_id (request_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_procedure_runs (
  run_id VARCHAR(80) PRIMARY KEY,
  request_id VARCHAR(80) NOT NULL,
  session_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  procedure_name VARCHAR(80) NOT NULL,
  route VARCHAR(64) NOT NULL,
  task VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  metadata JSON NOT NULL,
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME NULL,
  INDEX idx_aptguide3_procedure_runs_session_id (session_id),
  INDEX idx_aptguide3_procedure_runs_request_id (request_id),
  INDEX idx_aptguide3_procedure_runs_status (status)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aptguide3_audit_log (
  audit_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL DEFAULT '',
  session_id VARCHAR(64) NOT NULL DEFAULT '',
  event_type VARCHAR(128) NOT NULL,
  payload JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aptguide3_audit_log_user_id (user_id),
  INDEX idx_aptguide3_audit_log_event_type (event_type)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Task 1: Sync Documentation And Harness State

**Files:**
- Modify: `docs/plans/current-plan.md`
- Modify: `docs/plans/handoff.md`
- Modify: `docs/plans/sprint-plan.md`
- Modify: `docs/plans/next-steps.md`
- Modify: `docs/plans/known-issues.md`
- Modify: `docs/plans/README.md`
- Modify: `progress/current-plan.md`
- Modify: `progress/known-issues.md`
- Modify: `progress/next-steps.md`
- Modify: `reports/evaluation-report.md`
- Modify: `project/feature-list.json`
- Modify: `project/sprint-plan.json`

- [ ] **Step 1: Mark scaffold as complete and this plan as active**

Set current-plan files to:

```markdown
# Current Plan

## Active Objective

AptGuide 3.0 Milestone 1: Independent Backend Backbone.

## Current State

- Milestone 0 runnable scaffold: COMPLETE.
- Backend: 36 tests passed, 2 skipped; ruff clean.
- Procedures, integrations, in-memory persistence, observability, and validation frontend exist.
- Production-grade Agent-state persistence does not exist yet.

## Active Plan

`docs/plans/2026-05-15-aptguide3-independent-backend-backbone-plan.md`

## Guardrails

- AptGuide 3.0 is an AptGuide main-system upgrade, not a disconnected product.
- Final integration path is `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`.
- No keyword fallback in natural-language understanding.
- lease remains the source of truth for users, rooms, appointments, leases, contracts, and sensitive data.
```

- [ ] **Step 2: Replace stale known issues**

Use:

```markdown
# Known Issues

- `progress/known-issues.md` and `reports/evaluation-report.md` were stale before this plan; keep them synchronized after each checkpoint.
- Persistence is currently in-memory and cannot survive process restart.
- No MySQL schema, migration script, or SQLAlchemy models exist yet.
- Redis is configured but not wired as hot session or pending-action TTL storage.
- Trace events currently write to console only.
- Procedure runs are not durably recorded.
- Auth boundary does not yet match final `lease -> AptGuide 3.0` internal-header integration.
- Real MySQL, Redis, lease, Milvus, embedding, and LLM dependency verification has not run.
```

- [ ] **Step 3: Update evaluation report**

Record:

```markdown
# Evaluation Report

## 2026-05-15 - Runnable Scaffold

- `uv run pytest -q`: 36 passed, 2 skipped
- `uv run ruff check src tests`: All checks passed
- Real LLM eval: skipped without API key
- Real MySQL/Redis/lease/Milvus eval: not run

## Current Assessment

Milestone 0 is complete as a runnable scaffold. Milestone 1 must add durable Agent-state persistence and integration-ready auth/readiness before production or main-system integration claims.
```

- [ ] **Step 4: Commit documentation state**

Run:

```bash
git add docs progress reports project README.md
git commit -m "docs: align AptGuide 3.0 independent backend plan"
```

Expected: commit succeeds after user approval to commit.

## Task 2: Add Settings And Dependencies

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/.env.example`
- Modify: `backend/src/aptguide3/config.py`
- Test: `backend/tests/unit/test_config.py` if present, otherwise create `backend/tests/unit/test_config.py`

- [ ] **Step 1: Write failing config test**

Create or update:

```python
from aptguide3.config import Settings


def test_independent_backend_settings_defaults():
    settings = Settings()
    assert settings.auth_mode == "dev"
    assert settings.redis_key_prefix == "aptguide3"
    assert settings.session_ttl_seconds == 86400
    assert settings.pending_action_ttl_seconds == 300
    assert settings.mysql_dsn.startswith("mysql+asyncmy://")
    assert settings.internal_token_required is False
```

- [ ] **Step 2: Run failing test**

Run:

```bash
cd backend && uv run pytest tests/unit/test_config.py::test_independent_backend_settings_defaults -q
```

Expected: FAIL because the new settings are missing.

- [ ] **Step 3: Add dependencies**

In `backend/pyproject.toml`, add:

```toml
"asyncmy>=0.2.10",
"redis>=5.0.0",
"sqlalchemy>=2.0.0",
```

- [ ] **Step 4: Add settings**

Add to `Settings`:

```python
auth_mode: str = "dev"  # dev | internal_header
dev_user_id: str = "dev-user-001"
dev_user_name: str = "本地测试用户"
internal_token: SecretStr = SecretStr("")
internal_token_required: bool = False
cors_allow_origins: str = "http://localhost:5173"
mysql_dsn: str = "mysql+asyncmy://root:change-me@localhost:3306/aptguide3"
redis_url: str = "redis://localhost:6379/3"
redis_key_prefix: str = "aptguide3"
session_ttl_seconds: int = 86400
pending_action_ttl_seconds: int = 300
readiness_timeout_seconds: float = 2.0
```

Add:

```python
@property
def parsed_cors_origins(self) -> list[str]:
    return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]
```

- [ ] **Step 5: Run test**

Run:

```bash
cd backend && uv run pytest tests/unit/test_config.py::test_independent_backend_settings_defaults -q
```

Expected: PASS.

## Task 3: Add Auth Boundary

**Files:**
- Create: `backend/src/aptguide3/api/auth.py`
- Create: `backend/tests/unit/api/test_auth.py`
- Modify: `backend/src/aptguide3/api/app.py`
- Modify: `backend/src/aptguide3/api/deps.py`

- [ ] **Step 1: Write auth tests**

```python
import pytest

from aptguide3.api.auth import AuthResolver
from aptguide3.config import Settings


@pytest.mark.asyncio
async def test_dev_auth_uses_requested_user_when_allowed():
    settings = Settings(auth_mode="dev", dev_user_id="dev-user-001")
    auth = await AuthResolver(settings).resolve(
        authorization=None,
        x_user_id=None,
        x_internal_token=None,
        requested_user_id="demo-user",
    )
    assert auth.user_id == "demo-user"
    assert auth.auth_mode == "dev"


@pytest.mark.asyncio
async def test_internal_header_auth_ignores_requested_user():
    settings = Settings(
        auth_mode="internal_header",
        internal_token="secret",
        internal_token_required=True,
    )
    auth = await AuthResolver(settings).resolve(
        authorization=None,
        x_user_id="lease-user-1",
        x_internal_token="secret",
        requested_user_id="spoofed-user",
    )
    assert auth.user_id == "lease-user-1"
    assert auth.auth_mode == "internal_header"


@pytest.mark.asyncio
async def test_internal_header_auth_rejects_bad_token():
    settings = Settings(
        auth_mode="internal_header",
        internal_token="secret",
        internal_token_required=True,
    )
    with pytest.raises(PermissionError):
        await AuthResolver(settings).resolve(
            authorization=None,
            x_user_id="lease-user-1",
            x_internal_token="wrong",
            requested_user_id=None,
        )
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
cd backend && uv run pytest tests/unit/api/test_auth.py -q
```

Expected: FAIL because `aptguide3.api.auth` does not exist.

- [ ] **Step 3: Implement auth resolver**

```python
from __future__ import annotations

from dataclasses import dataclass

from aptguide3.config import Settings


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    display_name: str = ""
    auth_mode: str = "dev"


class AuthResolver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def resolve(
        self,
        *,
        authorization: str | None,
        x_user_id: str | None,
        x_internal_token: str | None,
        requested_user_id: str | None,
    ) -> AuthContext:
        if self.settings.auth_mode == "dev":
            return AuthContext(
                user_id=requested_user_id or self.settings.dev_user_id,
                display_name=self.settings.dev_user_name,
                auth_mode="dev",
            )
        if self.settings.auth_mode != "internal_header":
            raise PermissionError(f"unsupported auth mode: {self.settings.auth_mode}")
        expected = self.settings.internal_token.get_secret_value()
        if self.settings.internal_token_required and x_internal_token != expected:
            raise PermissionError("invalid internal token")
        if not x_user_id:
            raise PermissionError("missing X-User-Id")
        return AuthContext(user_id=x_user_id, auth_mode="internal_header")
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd backend && uv run pytest tests/unit/api/test_auth.py -q
```

Expected: PASS.

## Task 4: Add Database Schema And Models

**Files:**
- Create: `backend/src/aptguide3/database/__init__.py`
- Create: `backend/src/aptguide3/database/schema.sql`
- Create: `backend/src/aptguide3/database/models.py`
- Create: `backend/src/aptguide3/database/database.py`
- Create: `backend/tests/unit/database/test_models.py`

- [ ] **Step 1: Write model test**

```python
from aptguide3.database.models import (
    AuditLogRecord,
    Base,
    HandoffTicketRecord,
    MemoryRecord,
    MessageRecord,
    PendingActionRecord,
    ProcedureRunRecord,
    SessionRecord,
    TraceEventRecord,
)


def test_required_tables_are_declared():
    assert {
        "aptguide3_users",
        "aptguide3_sessions",
        "aptguide3_messages",
        "aptguide3_pending_actions",
        "aptguide3_memories",
        "aptguide3_memory_candidates",
        "aptguide3_handoff_tickets",
        "aptguide3_operator_messages",
        "aptguide3_trace_events",
        "aptguide3_procedure_runs",
        "aptguide3_audit_log",
    }.issubset(Base.metadata.tables.keys())


def test_core_model_table_names():
    assert SessionRecord.__tablename__ == "aptguide3_sessions"
    assert MessageRecord.__tablename__ == "aptguide3_messages"
    assert PendingActionRecord.__tablename__ == "aptguide3_pending_actions"
    assert MemoryRecord.__tablename__ == "aptguide3_memories"
    assert HandoffTicketRecord.__tablename__ == "aptguide3_handoff_tickets"
    assert TraceEventRecord.__tablename__ == "aptguide3_trace_events"
    assert ProcedureRunRecord.__tablename__ == "aptguide3_procedure_runs"
    assert AuditLogRecord.__tablename__ == "aptguide3_audit_log"
```

- [ ] **Step 2: Run failing test**

Run:

```bash
cd backend && uv run pytest tests/unit/database/test_models.py -q
```

Expected: FAIL because database models do not exist.

- [ ] **Step 3: Implement SQLAlchemy models**

Use the Data Model section above. Map JSON columns with `sqlalchemy.JSON`, timestamps with `DateTime`, primary IDs with `String` or `Integer`, and indexes matching `schema.sql`.

- [ ] **Step 4: Implement database factory**

```python
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def build_engine(mysql_dsn: str):
    return create_async_engine(mysql_dsn, pool_pre_ping=True)


def build_sessionmaker(mysql_dsn: str) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(build_engine(mysql_dsn), expire_on_commit=False)


async def iter_session(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        yield session
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd backend && uv run pytest tests/unit/database/test_models.py -q
```

Expected: PASS.

## Task 5: Add Repository Contracts

**Files:**
- Create: `backend/src/aptguide3/persistence/contracts.py`
- Modify: `backend/src/aptguide3/persistence/session_repo.py`
- Modify: `backend/src/aptguide3/persistence/memory_repo.py`
- Modify: `backend/src/aptguide3/persistence/handoff_repo.py`
- Create: `backend/tests/unit/persistence/test_contracts.py`

- [ ] **Step 1: Write contract import test**

```python
from aptguide3.persistence.contracts import (
    AuditRepository,
    HandoffRepository,
    MemoryRepository,
    MessageRepository,
    PendingActionRepository,
    ProcedureRunRepository,
    SessionRepository,
    TraceRepository,
)


def test_repository_protocols_import():
    assert SessionRepository
    assert MessageRepository
    assert PendingActionRepository
    assert MemoryRepository
    assert HandoffRepository
    assert TraceRepository
    assert ProcedureRunRepository
    assert AuditRepository
```

- [ ] **Step 2: Run failing test**

Run:

```bash
cd backend && uv run pytest tests/unit/persistence/test_contracts.py -q
```

Expected: FAIL because `contracts.py` does not exist.

- [ ] **Step 3: Define contracts**

Define protocol methods:

```python
class SessionRepository(Protocol):
    async def upsert_session(self, session_id: str, user_id: str, context: dict) -> None: ...
    async def load_session(self, session_id: str) -> dict | None: ...

class MessageRepository(Protocol):
    async def append_message(
        self, session_id: str, user_id: str, request_id: str, role: str, content: str, metadata: dict
    ) -> None: ...

class PendingActionRepository(Protocol):
    async def save_pending_action(
        self, pending_action_id: str, session_id: str, user_id: str, action_type: str, payload: dict, expires_at
    ) -> None: ...
    async def load_pending_action(self, pending_action_id: str) -> dict | None: ...
    async def mark_completed(self, pending_action_id: str) -> None: ...

class MemoryRepository(Protocol):
    async def list_memories(self, user_id: str) -> list[dict]: ...
    async def upsert_memory(self, memory_id: str, user_id: str, kind: str, key_name: str, value_json: dict) -> None: ...

class HandoffRepository(Protocol):
    async def create_ticket(self, ticket_id: str, session_id: str, user_id: str, trigger_type: str, summary: dict) -> None: ...
    async def list_tickets(self, status: str = "open") -> list[dict]: ...

class TraceRepository(Protocol):
    async def append_trace_event(self, trace_id: str, request_id: str, session_id: str, event_name: str, payload: dict) -> None: ...

class ProcedureRunRepository(Protocol):
    async def start_run(self, run_id: str, request_id: str, session_id: str, user_id: str, procedure_name: str, route: str, task: str, metadata: dict) -> None: ...
    async def complete_run(self, run_id: str, status: str, metadata: dict) -> None: ...

class AuditRepository(Protocol):
    async def append_audit_event(self, user_id: str, session_id: str, event_type: str, payload: dict) -> None: ...
```

- [ ] **Step 4: Keep compatibility**

Keep existing `InMemorySessionRepo`, `InMemoryMemoryRepo`, and `InMemoryHandoffRepo` usable for current tests. If their method names differ, add adapter methods without deleting old ones.

- [ ] **Step 5: Run tests**

Run:

```bash
cd backend && uv run pytest tests/unit/persistence/test_contracts.py -q
```

Expected: PASS.

## Task 6: Add Redis Hot-State Store

**Files:**
- Create: `backend/src/aptguide3/persistence/redis_store.py`
- Create: `backend/tests/unit/persistence/test_redis_store.py`

- [ ] **Step 1: Write fake Redis tests**

```python
from aptguide3.persistence.redis_store import RedisStateStore


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.ttls = {}

    async def set(self, key, value, ex=None):
        self.values[key] = value
        self.ttls[key] = ex

    async def get(self, key):
        return self.values.get(key)

    async def delete(self, key):
        self.values.pop(key, None)


async def test_session_state_uses_prefix_and_ttl():
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="aptguide3", session_ttl_seconds=10, pending_ttl_seconds=3)
    await store.save_session("s1", {"hello": "world"})
    assert await store.load_session("s1") == {"hello": "world"}
    assert redis.ttls["aptguide3:session:s1"] == 10


async def test_pending_action_uses_pending_ttl():
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="aptguide3", session_ttl_seconds=10, pending_ttl_seconds=3)
    await store.save_pending_action("p1", {"type": "confirm"})
    assert await store.load_pending_action("p1") == {"type": "confirm"}
    assert redis.ttls["aptguide3:pending:p1"] == 3
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
cd backend && uv run pytest tests/unit/persistence/test_redis_store.py -q
```

Expected: FAIL because RedisStateStore does not exist.

- [ ] **Step 3: Implement RedisStateStore**

Use JSON serialization with `ensure_ascii=False`. Key format:

```text
{prefix}:session:{session_id}
{prefix}:pending:{pending_action_id}
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd backend && uv run pytest tests/unit/persistence/test_redis_store.py -q
```

Expected: PASS.

## Task 7: Add MySQL Repository Implementations

**Files:**
- Create: `backend/src/aptguide3/persistence/mysql_repos.py`
- Create: `backend/tests/unit/persistence/test_mysql_repos.py`

- [ ] **Step 1: Write repository construction test**

```python
from aptguide3.persistence.mysql_repos import (
    MySqlAuditRepository,
    MySqlMessageRepository,
    MySqlProcedureRunRepository,
    MySqlSessionRepository,
    MySqlTraceRepository,
)


def test_mysql_repositories_accept_sessionmaker():
    sessionmaker = object()
    assert MySqlSessionRepository(sessionmaker)
    assert MySqlMessageRepository(sessionmaker)
    assert MySqlTraceRepository(sessionmaker)
    assert MySqlProcedureRunRepository(sessionmaker)
    assert MySqlAuditRepository(sessionmaker)
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
cd backend && uv run pytest tests/unit/persistence/test_mysql_repos.py -q
```

Expected: FAIL because MySQL repositories do not exist.

- [ ] **Step 3: Implement repositories**

Implement each repository with an injected async sessionmaker. Each method should:

1. open `async with self.sessionmaker() as session`;
2. add or update the matching SQLAlchemy record;
3. `await session.commit()`.

Do not catch and hide database errors. Let callers/readiness surface them.

- [ ] **Step 4: Run tests**

Run:

```bash
cd backend && uv run pytest tests/unit/persistence/test_mysql_repos.py -q
```

Expected: PASS.

## Task 8: Wire Persistence Into ChatService

**Files:**
- Modify: `backend/src/aptguide3/application/chat_service.py`
- Modify: `backend/src/aptguide3/api/deps.py`
- Create: `backend/tests/unit/application/test_chat_persistence.py`

- [ ] **Step 1: Write chat persistence test**

```python
from aptguide3.application.chat_service import ChatService
from aptguide3.application.procedure_runtime import ProcedureRuntime
from aptguide3.application.safety_boundary import SafetyBoundary
from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult


class StubUnderstanding:
    def understand(self, message):
        from aptguide3.domain.understanding import UnderstandingResult
        return UnderstandingResult(route="procedure", task="clarify", confidence=0.99, slots={}, raw={})


class StubProcedure:
    name = "clarify"

    def run(self, frame, understanding):
        return ProcedureResult(message="ok", phase="clarify", metadata={"ok": True})


class RecordingMessages:
    def __init__(self):
        self.messages = []

    async def append_message(self, session_id, user_id, request_id, role, content, metadata):
        self.messages.append((role, content, metadata))


def test_chat_service_persists_user_and_assistant_messages():
    runtime = ProcedureRuntime()
    runtime.register(StubProcedure())
    messages = RecordingMessages()
    service = ChatService(
        SafetyBoundary(),
        StubUnderstanding(),
        runtime,
        message_repo=messages,
    )
    response = service.run(ConversationFrame(session_id="s1", user_id="u1", message="hi"))
    assert response.message == "ok"
    assert [message[0] for message in messages.messages] == ["user", "assistant"]
```

- [ ] **Step 2: Run failing test**

Run:

```bash
cd backend && uv run pytest tests/unit/application/test_chat_persistence.py -q
```

Expected: FAIL because `ChatService` does not accept `message_repo`.

- [ ] **Step 3: Add optional repositories to ChatService**

Add optional constructor dependencies:

```python
message_repo=None
pending_action_repo=None
procedure_run_repo=None
audit_repo=None
```

Persist:

- inbound user message before safety;
- assistant message after response composition;
- procedure run start and completion around runtime dispatch;
- pending action if response includes one.

If no repository is provided, preserve current in-memory behavior.

- [ ] **Step 4: Run tests**

Run:

```bash
cd backend && uv run pytest tests/unit/application/test_chat_persistence.py -q
```

Expected: PASS.

## Task 9: Add Durable Trace Sink

**Files:**
- Create: `backend/src/aptguide3/observability/repository_sink.py`
- Create: `backend/tests/unit/observability/test_repository_sink.py`
- Modify: `backend/src/aptguide3/api/deps.py`

- [ ] **Step 1: Write sink test**

```python
from aptguide3.observability.events import TraceEvent
from aptguide3.observability.repository_sink import RepositoryTraceSink


class RecordingTraceRepo:
    def __init__(self):
        self.events = []

    async def append_trace_event(self, trace_id, request_id, session_id, event_name, payload):
        self.events.append((trace_id, request_id, session_id, event_name, payload))


def test_repository_trace_sink_records_event():
    repo = RecordingTraceRepo()
    sink = RepositoryTraceSink(repo)
    sink.write(TraceEvent(trace_id="t1", event_name="chat_started", payload={"session_id": "s1"}))
    assert repo.events[0][0] == "t1"
    assert repo.events[0][3] == "chat_started"
```

- [ ] **Step 2: Run failing test**

Run:

```bash
cd backend && uv run pytest tests/unit/observability/test_repository_sink.py -q
```

Expected: FAIL because repository sink does not exist.

- [ ] **Step 3: Implement sink**

Implement a sync `write()` method that bridges to the async repository using `asyncio.run()` only when no loop is running. In a running loop, schedule a task. Keep `ConsoleTraceSink` available for local debugging.

- [ ] **Step 4: Run tests**

Run:

```bash
cd backend && uv run pytest tests/unit/observability/test_repository_sink.py -q
```

Expected: PASS.

## Task 10: Add Readiness Endpoint

**Files:**
- Create: `backend/src/aptguide3/api/readiness.py`
- Modify: `backend/src/aptguide3/api/app.py`
- Create: `backend/tests/unit/api/test_readiness.py`

- [ ] **Step 1: Write readiness tests**

```python
from aptguide3.api.readiness import build_readiness_report
from aptguide3.config import Settings


def test_readiness_reports_missing_live_credentials_without_crashing():
    report = build_readiness_report(Settings(llm_api_key="", embedding_api_key=""))
    names = {check["name"] for check in report["checks"]}
    assert {"mysql_config", "redis_config", "lease_config", "llm_config", "embedding_config"}.issubset(names)
    assert isinstance(report["ready"], bool)
```

- [ ] **Step 2: Run failing test**

Run:

```bash
cd backend && uv run pytest tests/unit/api/test_readiness.py -q
```

Expected: FAIL because readiness module does not exist.

- [ ] **Step 3: Implement readiness report**

Return:

```python
{
    "ready": bool,
    "checks": [
        {"name": "mysql_config", "ok": bool(settings.mysql_dsn), "required": True},
        {"name": "redis_config", "ok": bool(settings.redis_url), "required": True},
        {"name": "lease_config", "ok": bool(settings.lease_base_url), "required": True},
        {"name": "vector_config", "ok": bool(settings.vector_uri), "required": True},
        {"name": "llm_config", "ok": bool(settings.llm_api_key.get_secret_value()), "required": False},
        {"name": "embedding_config", "ok": bool(settings.embedding_api_key.get_secret_value()), "required": False},
    ],
}
```

- [ ] **Step 4: Add `/ready` route**

Register:

```python
@app.get("/ready")
def ready():
    return build_readiness_report(get_settings())
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd backend && uv run pytest tests/unit/api/test_readiness.py -q
```

Expected: PASS.

## Task 11: Run Full Verification

**Files:**
- Modify: `docs/tests/verification-log.md`
- Modify: `reports/evaluation-report.md`

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd backend && uv run pytest -q
```

Expected: all non-live tests pass. Live LLM tests may skip without API key.

- [ ] **Step 2: Run ruff**

Run:

```bash
cd backend && uv run ruff check src tests
```

Expected: `All checks passed!`

- [ ] **Step 3: Record verification**

Append exact command results to:

- `docs/tests/verification-log.md`
- `reports/evaluation-report.md`

If live dependency checks were not run, explicitly write `not_run`.

## Execution Notes

- Prefer implementing this plan before expanding appointment, memory, handoff, or operator business behavior.
- Keep in-memory implementations for fast tests, but dependency wiring should be ready for MySQL/Redis.
- Do not claim main-system integration until `lease /app/ai/chat -> AptGuide 3.0 /api/chat` is tested.
- Do not claim production readiness until real MySQL, Redis, lease, Milvus, embedding, and LLM checks are run and recorded.

## Self-Review

- Spec coverage: covers independent backend state, AptGuide main-system integration boundary, persistence, auth, readiness, verification, and documentation synchronization.
- Placeholder scan: no `TBD`, `TODO`, or vague implementation steps remain.
- Type consistency: repository names, schema table names, and task file paths use consistent `aptguide3_` naming and AptGuide 3.0 package paths.
