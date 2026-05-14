# AptGuide 2.0 Standalone Productization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn AptGuide 2.0 into an independently runnable rental Agent application with its own frontend, `/chat` backend, real lease backend access, Redis + MySQL memory, and a local operator console for human handoff.

**Architecture:** The product runtime remains `POST /chat -> AptGuideHarness -> procedures -> ToolRuntime -> real lease/Milvus/LLM dependencies`. The standalone frontend calls AptGuide 2.0 directly instead of going through the platform H5 or `lease /app/ai/chat`; later platform integration becomes a separate phase. Redis owns hot conversation state and pending-action TTLs, MySQL owns durable sessions, memory profile, memory candidates, handoff tickets, operator messages, and audit logs.

**Tech Stack:** Python 3.12/3.13, FastAPI, Pydantic v2, pytest, ruff, httpx, OpenAI-compatible embeddings/LLM, Milvus, real lease Java backend, Redis, MySQL, SQLAlchemy async, asyncmy, Vue 3, Vite, TypeScript, Vant, Pinia.

---

## Phase Decision

This plan intentionally does **not** optimize RAG retrieval hit rate. RAG v2 remains the active retrieval module, but live eval gaps such as KB hit@3 and Room hit@5 are deferred.

This plan also does **not** integrate AptGuide 2.0 back into the full apartment platform. The target is a standalone AptGuide 2.0 app:

```text
AptGuide 2.0 frontend
  -> POST /chat
  -> AptGuide 2.0 backend
  -> AptGuideHarness
  -> Redis + MySQL memory/handoff state
  -> real lease backend internal tools
  -> Milvus + embeddings + LLM
```

Legacy RAG MVP code may stay in the repository as reference, but no product task in this plan should reconnect it to API, harness procedures, e2e acceptance, frontend, memory, or handoff.

## Current Baseline

- `/chat` already exists in `backend/src/aptguide2/api/app.py`.
- `/chat` already enters `AptGuideHarness`.
- RAG v2 is already mounted as a harness procedure.
- Appointment create/cancel already use two-turn confirmation.
- Lease list and appointment list exist as governed tool flows.
- Current context store is `InMemoryContextStore`, explicitly marked development-only.
- Current handoff writes state into `ConversationFrame` only; there is no durable ticket, operator API, or operator UI.
- `docs/system/feature-list.md` and `docs/plans/sprint-plan.md` are not synchronized with actual completion state.

## Non-Goals

- Do not improve RAG eval thresholds in this plan.
- Do not modify `rentHouseH5`, `rentHouseAdmin`, or `lease /app/ai/chat` for platform integration.
- Do not delete legacy `aptguide2.rag.pipeline`.
- Do not add a production-grade enterprise customer-service integration.
- Do not trust frontend-provided `user_id` in formal auth mode.

## Acceptance Gates

The phase is complete only when all gates below pass:

- Standalone frontend starts locally and can call `POST /chat` directly.
- Frontend renders text, room cards, lease cards, appointment cards, confirmation cards, memory cards, handoff cards, actions, pending actions, and trace metadata.
- Backend supports development auth with a test-user selector.
- Backend supports formal auth mode where `Authorization: Bearer <lease_token>` is resolved into `user_id`.
- In formal auth mode, frontend-provided `user_id` is ignored.
- Redis-backed context store persists active session and pending action TTL.
- MySQL-backed repositories persist sessions, recent messages, memory profile, memory candidates, handoff tickets, operator messages, and audit logs.
- Memory can remember confirmed preferences, show current preferences, delete preferences, and survive backend restart.
- Appointment create/cancel pending actions survive backend restart until TTL expiry.
- Handoff creates durable tickets and pauses AI auto-replies for that session.
- Operator console can list tickets, inspect conversation summary, reply, close ticket, and resume AI.
- `/health/deps` or equivalent readiness endpoint reports Redis, MySQL, lease, Milvus, embedding, and pipeline readiness.
- Existing backend tests still pass.
- New frontend checks pass.
- Harness docs and state files identify Standalone Productization as the active objective.

## File Map

### Backend Create

- `backend/src/aptguide2/api/auth.py` - auth resolver for dev mode and lease-token mode.
- `backend/src/aptguide2/api/operator.py` - local operator console API routes.
- `backend/src/aptguide2/api/deps_persistence.py` - Redis/MySQL dependency factories.
- `backend/src/aptguide2/persistence/__init__.py` - persistence package marker.
- `backend/src/aptguide2/persistence/database.py` - SQLAlchemy async engine/session setup.
- `backend/src/aptguide2/persistence/models.py` - MySQL durable table models.
- `backend/src/aptguide2/persistence/schema.sql` - explicit MySQL schema for local setup.
- `backend/src/aptguide2/persistence/redis_store.py` - Redis key helpers and TTL state operations.
- `backend/src/aptguide2/harness/context_persistent.py` - Redis + MySQL `ContextStore`.
- `backend/src/aptguide2/harness/memory_repository.py` - durable memory profile/candidate/audit repository.
- `backend/src/aptguide2/harness/modules/memory.py` - memory procedure for profile show/update/delete flows.
- `backend/src/aptguide2/harness/handoff_repository.py` - durable handoff ticket/message repository.
- `backend/src/aptguide2/harness/operator_service.py` - operator workflow service.
- `backend/tests/unit/api/test_auth.py` - auth resolver tests.
- `backend/tests/unit/api/test_operator_api.py` - operator API tests.
- `backend/tests/unit/persistence/test_redis_store.py` - Redis state tests using a fake Redis client.
- `backend/tests/unit/persistence/test_database_models.py` - model/schema tests.
- `backend/tests/unit/harness/test_persistent_context.py` - context persistence tests.
- `backend/tests/unit/harness/test_memory_repository.py` - memory repository tests.
- `backend/tests/unit/harness/modules/test_memory.py` - memory procedure tests.
- `backend/tests/unit/harness/test_handoff_repository.py` - handoff repository tests.
- `backend/tests/e2e/test_standalone_product.py` - standalone `/chat` product acceptance tests.
- `backend/tests/e2e/test_handoff_operator_flow.py` - handoff + operator acceptance tests.

### Backend Modify

- `backend/pyproject.toml` - add Redis/MySQL/SQLAlchemy dependencies.
- `backend/.env.example` - document Redis, MySQL, auth, CORS, and operator settings.
- `backend/src/aptguide2/core/config.py` - add standalone product settings.
- `backend/src/aptguide2/api/app.py` - add auth resolution, CORS, `/health/deps`, and operator router.
- `backend/src/aptguide2/api/schemas.py` - add response `session_id`, `request_id`, `trace_id`, and typed action/card aliases if needed.
- `backend/src/aptguide2/api/deps.py` - switch from `InMemoryContextStore` to configurable persistent context store.
- `backend/src/aptguide2/harness/contracts.py` - add auth context, paused handoff state, and memory fields if needed.
- `backend/src/aptguide2/harness/orchestrator.py` - respect paused handoff sessions before normal routing.
- `backend/src/aptguide2/harness/routing.py` - add memory-intent routing and handoff paused follow-up behavior.
- `backend/src/aptguide2/harness/memory.py` - delegate durable operations to repository while keeping in-frame short-term helpers.
- `backend/src/aptguide2/harness/modules/handoff.py` - create durable handoff tickets instead of only frame state.
- `backend/src/aptguide2/system/readiness.py` - include Redis/MySQL/auth/handoff readiness.
- `backend/tests/unit/system/test_readiness.py` - verify readiness report.
- `backend/tests/e2e/test_system_mainline.py` - assert new response identity/session fields.

### Frontend Create

- `frontend/package.json` - Vite app scripts and dependencies.
- `frontend/index.html` - standalone app entry HTML.
- `frontend/vite.config.ts` - Vite config with backend proxy.
- `frontend/tsconfig.json` - TypeScript config.
- `frontend/src/main.ts` - Vue app bootstrap.
- `frontend/src/App.vue` - shell with chat and operator routes.
- `frontend/src/router.ts` - `chat` and `operator` routes.
- `frontend/src/api/client.ts` - typed HTTP client.
- `frontend/src/api/chat.ts` - `/chat` client.
- `frontend/src/api/operator.ts` - operator API client.
- `frontend/src/stores/auth.ts` - dev user / token auth store.
- `frontend/src/stores/chat.ts` - session, messages, actions, pending state.
- `frontend/src/stores/operator.ts` - ticket list/detail state.
- `frontend/src/types/chat.ts` - response/card/action/pending types.
- `frontend/src/types/operator.ts` - handoff ticket/message types.
- `frontend/src/components/chat/ChatShell.vue` - main chat layout.
- `frontend/src/components/chat/MessageList.vue` - message stream.
- `frontend/src/components/chat/MessageComposer.vue` - input and send controls.
- `frontend/src/components/chat/CardRenderer.vue` - dispatches card type renderers.
- `frontend/src/components/chat/cards/RoomCard.vue` - room card.
- `frontend/src/components/chat/cards/LeaseCard.vue` - lease card.
- `frontend/src/components/chat/cards/AppointmentCard.vue` - appointment card.
- `frontend/src/components/chat/cards/ConfirmationCard.vue` - confirmation card.
- `frontend/src/components/chat/cards/MemoryCard.vue` - memory card.
- `frontend/src/components/chat/cards/HandoffCard.vue` - handoff card.
- `frontend/src/components/chat/ActionBar.vue` - response action buttons.
- `frontend/src/components/chat/PendingActionBanner.vue` - current pending action state.
- `frontend/src/components/chat/TracePanel.vue` - developer trace metadata.
- `frontend/src/components/auth/DevUserSelector.vue` - development user selector.
- `frontend/src/components/operator/OperatorConsole.vue` - operator layout.
- `frontend/src/components/operator/TicketList.vue` - handoff ticket queue.
- `frontend/src/components/operator/TicketDetail.vue` - ticket summary/messages.
- `frontend/src/components/operator/OperatorReplyBox.vue` - operator reply form.
- `frontend/src/styles.css` - app styles.
- `frontend/tests/chat-contract.test.ts` - response contract tests.
- `frontend/tests/operator-contract.test.ts` - operator contract tests.

### Docs Modify

- `docs/plans/current-plan.md` - make this plan the active objective.
- `docs/plans/sprint-plan.md` - define the standalone productization sprint scope.
- `docs/plans/handoff.md` - hand execution agent this plan.
- `docs/plans/next-steps.md` - replace immediate RAG tuning with standalone productization.
- `docs/plans/README.md` - add this plan.
- `docs/system/feature-list.md` - replace empty table with real feature status.
- `docs/27-current-implementation-guide.md` - remove outdated “RAG pipeline is current workflow” language after implementation.
- `docs/README.md` - update current project status.
- `.agent-state/handoff.json` - machine-readable handoff.

---

## Task 1: Sync Harness State To The New Objective

**Files:**
- Modify: `docs/plans/current-plan.md`
- Modify: `docs/plans/sprint-plan.md`
- Modify: `docs/plans/next-steps.md`
- Modify: `docs/plans/README.md`
- Modify: `docs/system/feature-list.md`
- Modify: `.agent-state/handoff.json`

- [ ] **Step 1: Update `docs/plans/current-plan.md`**

Replace the current RAG-quality next step with:

```markdown
# Current Plan

## Goal

AptGuide 2.0 Standalone Productization: build AptGuide 2.0 as an independently runnable product app with its own frontend, `/chat` backend, Redis + MySQL memory, real lease backend access, and local operator console.

## Context

System feature completion and mainline integration is complete. `/chat` enters `AptGuideHarness` by default, legacy RAG is disconnected from public runtime paths, RAG v2 is an internal harness module, and 323 tests passed.

The next phase intentionally defers RAG hit-rate optimization. The active objective is productization around the harness runtime.

## Active Plan

`docs/plans/2026-05-14-aptguide2-standalone-productization-agent-plan.md`

## Scope

1. Standalone AptGuide 2.0 frontend.
2. Direct frontend-to-`POST /chat` product flow.
3. Development auth with test user selector.
4. Formal auth mode using lease token resolution.
5. Redis + MySQL persistent context and memory.
6. Durable pending actions.
7. Durable human handoff tickets.
8. Local operator console.
9. Readiness checks for Redis, MySQL, lease, Milvus, embedding, and pipeline.
10. Harness documentation synchronization.

## Non-Goals

- Do not tune RAG retrieval quality in this phase.
- Do not integrate through `rentHouseH5` or `lease /app/ai/chat` in this phase.
- Do not reconnect legacy RAG MVP to any product runtime path.
```

- [ ] **Step 2: Update `docs/plans/sprint-plan.md`**

Use this sprint scope:

```markdown
# Sprint Plan

## Scope

Standalone AptGuide 2.0 productization.

## Commitments

- AptGuide 2.0 owns its standalone frontend and direct `/chat` flow.
- Auth supports development test users and formal lease-token mode.
- Redis + MySQL replace development-only in-memory conversation state.
- Memory profile and memory candidates are durable and user-scoped.
- Human handoff creates durable tickets and supports a local operator console.
- Readiness and docs reflect the standalone product state.

## Explicitly Deferred

- RAG retrieval hit-rate optimization.
- Full apartment platform integration.
- Production customer-service integration.
```

- [ ] **Step 3: Update `docs/system/feature-list.md`**

Use concrete statuses instead of the empty placeholder:

```markdown
# Feature List

| Feature | Status | Notes |
| --- | --- | --- |
| Harness mainline `/chat` runtime | completed | `/chat` enters `AptGuideHarness`; legacy RAG disconnected. |
| RAG v2 harness module | completed | Internal module for room search and KB QA; quality tuning deferred. |
| Real lease backend tool access | completed | Lease adapter and governed tool runtime exist; readiness must remain green. |
| Appointment create confirmation | completed | Two-turn confirmation with `confirmation_id`. |
| Appointment cancel confirmation | completed | Two-turn confirmation with `confirmation_id`. |
| Appointment list | completed | User-scoped governed tool flow. |
| Lease list | completed | User-scoped governed tool flow. |
| Standalone frontend | planned | New `frontend/` app. |
| Development auth | planned | Test user selector for local product testing. |
| Formal lease-token auth | planned | Resolve `user_id` from token; ignore frontend `user_id`. |
| Redis + MySQL context store | planned | Replace development-only `InMemoryContextStore`. |
| Durable memory profile | planned | Confirmed preferences survive restart. |
| Memory candidates | planned | Candidate extraction requires confirmation before profile writes. |
| Durable handoff tickets | planned | Handoff state leaves `ConversationFrame` and enters MySQL. |
| Local operator console | planned | Ticket list/detail/reply/close/resume AI. |
| Production platform integration | deferred | Later phase after standalone app works. |
| RAG retrieval-quality optimization | deferred | KB hit@3 and Room hit@5 gates remain known quality work. |
```

- [ ] **Step 4: Verify the doc-state update**

Run:

```bash
rg -n "Standalone Productization|RAG retrieval quality improvement|No sprint scope recorded|No features recorded" docs/plans docs/system .agent-state
```

Expected:

- `Standalone Productization` appears in current plan, sprint plan, and handoff.
- `No sprint scope recorded` has no output.
- `No features recorded` has no output.
- `RAG retrieval quality improvement` may still appear in historical checkpoints or reports, but not as the immediate active objective.

---

## Task 2: Add Backend Dependencies And Product Configuration

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/.env.example`
- Modify: `backend/src/aptguide2/core/config.py`
- Test: `backend/tests/unit/system/test_readiness.py`

- [ ] **Step 1: Add dependencies**

Modify `backend/pyproject.toml` dependencies:

```toml
dependencies = [
    "pydantic>=2.9",
    "pydantic-settings>=2.5",
    "httpx>=0.27",
    "openai>=1.50",
    "pymilvus>=2.4",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
    "tenacity>=9.0",
    "fastapi>=0.115",
    "uvicorn>=0.34",
    "redis>=5.2",
    "sqlalchemy[asyncio]>=2.0",
    "asyncmy>=0.2",
]
```

- [ ] **Step 2: Add settings**

Extend `backend/src/aptguide2/core/config.py`:

```python
    # Standalone product
    app_mode: str = "standalone"
    frontend_origin: str = "http://localhost:5173"

    # Auth
    auth_mode: str = "dev"  # dev | lease_token
    dev_user_id: str = "dev-user-001"
    dev_user_name: str = "本地测试用户"
    lease_userinfo_path: str = "/app/info"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "aptguide2"
    session_ttl_seconds: int = 86400
    pending_action_ttl_seconds: int = 300

    # MySQL
    mysql_dsn: str = "mysql+asyncmy://root:change-me@localhost:3306/aptguide2"

    # Operator console
    operator_console_enabled: bool = True
    operator_dev_token: str = "operator-dev-token"
```

- [ ] **Step 3: Update `.env.example`**

Append:

```dotenv
# Standalone product
APTGUIDE_APP_MODE=standalone
APTGUIDE_FRONTEND_ORIGIN=http://localhost:5173

# Auth: dev | lease_token
APTGUIDE_AUTH_MODE=dev
APTGUIDE_DEV_USER_ID=dev-user-001
APTGUIDE_DEV_USER_NAME=本地测试用户
APTGUIDE_LEASE_USERINFO_PATH=/app/info

# Redis
APTGUIDE_REDIS_URL=redis://localhost:6379/0
APTGUIDE_REDIS_KEY_PREFIX=aptguide2
APTGUIDE_SESSION_TTL_SECONDS=86400
APTGUIDE_PENDING_ACTION_TTL_SECONDS=300

# MySQL
APTGUIDE_MYSQL_DSN=mysql+asyncmy://root:change-me@localhost:3306/aptguide2

# Operator console
APTGUIDE_OPERATOR_CONSOLE_ENABLED=true
APTGUIDE_OPERATOR_DEV_TOKEN=operator-dev-token
```

- [ ] **Step 4: Verify settings load**

Run:

```bash
cd backend
uv run python - <<'PY'
from aptguide2.core.config import Settings
s = Settings()
assert s.app_mode == "standalone"
assert s.auth_mode in {"dev", "lease_token"}
assert s.redis_url.startswith("redis://")
assert "mysql" in s.mysql_dsn
print("settings ok")
PY
```

Expected:

```text
settings ok
```

---

## Task 3: Add Auth Resolver For Dev And Lease-Token Modes

**Files:**
- Create: `backend/src/aptguide2/api/auth.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Modify: `backend/src/aptguide2/api/schemas.py`
- Test: `backend/tests/unit/api/test_auth.py`
- Test: `backend/tests/e2e/test_standalone_product.py`

- [ ] **Step 1: Write auth resolver tests**

Create `backend/tests/unit/api/test_auth.py`:

```python
import pytest
import respx
from httpx import Response

from aptguide2.api.auth import AuthContext, AuthResolver
from aptguide2.core.config import Settings


def test_dev_auth_uses_configured_dev_user_and_allows_display_name() -> None:
    settings = Settings(auth_mode="dev", dev_user_id="u-dev", dev_user_name="测试用户")
    resolver = AuthResolver(settings)

    ctx = resolver.resolve_sync(authorization=None, requested_user_id="forged-user")

    assert ctx == AuthContext(user_id="u-dev", display_name="测试用户", auth_mode="dev")


@respx.mock
@pytest.mark.asyncio
async def test_lease_token_auth_resolves_user_from_lease_backend() -> None:
    settings = Settings(
        auth_mode="lease_token",
        lease_base_url="http://lease.test",
        lease_userinfo_path="/app/info",
    )
    respx.get("http://lease.test/app/info").mock(
        return_value=Response(200, json={"code": 200, "data": {"id": 42, "nickname": "张三"}})
    )

    ctx = await AuthResolver(settings).resolve("Bearer token-abc", requested_user_id="999")

    assert ctx.user_id == "42"
    assert ctx.display_name == "张三"
    assert ctx.auth_mode == "lease_token"


@pytest.mark.asyncio
async def test_lease_token_auth_rejects_missing_token() -> None:
    settings = Settings(auth_mode="lease_token")

    with pytest.raises(PermissionError, match="missing bearer token"):
        await AuthResolver(settings).resolve(None, requested_user_id=None)
```

- [ ] **Step 2: Implement auth resolver**

Create `backend/src/aptguide2/api/auth.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

import httpx

from aptguide2.core.config import Settings


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    display_name: str = ""
    auth_mode: str = "dev"


class AuthResolver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def resolve_sync(self, authorization: str | None, requested_user_id: str | None) -> AuthContext:
        if self.settings.auth_mode == "dev":
            return AuthContext(
                user_id=self.settings.dev_user_id or requested_user_id or "dev-user-001",
                display_name=self.settings.dev_user_name,
                auth_mode="dev",
            )
        raise RuntimeError("lease_token auth requires async resolution")

    async def resolve(self, authorization: str | None, requested_user_id: str | None) -> AuthContext:
        if self.settings.auth_mode == "dev":
            return self.resolve_sync(authorization, requested_user_id)
        if self.settings.auth_mode != "lease_token":
            raise PermissionError(f"unsupported auth mode: {self.settings.auth_mode}")
        if not authorization or not authorization.lower().startswith("bearer "):
            raise PermissionError("missing bearer token")

        token = authorization.split(" ", 1)[1].strip()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(
            base_url=self.settings.lease_base_url.rstrip("/"),
            timeout=self.settings.lease_timeout_seconds,
            headers=headers,
        ) as client:
            response = await client.get(self.settings.lease_userinfo_path)
            response.raise_for_status()
            payload = response.json()

        data = payload.get("data", payload)
        user_id = data.get("id") or data.get("user_id") or data.get("userId")
        if user_id is None:
            raise PermissionError("lease token did not resolve user")
        return AuthContext(
            user_id=str(user_id),
            display_name=str(data.get("nickname") or data.get("name") or ""),
            auth_mode="lease_token",
        )
```

- [ ] **Step 3: Pass resolved user into `/chat`**

Modify `backend/src/aptguide2/api/app.py`:

```python
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from aptguide2.api.auth import AuthResolver
from aptguide2.api.deps import get_aptguide_harness, get_settings, get_vector_adapter
```

Add CORS after `app = FastAPI(...)`:

```python
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Change `chat()` to async and resolve identity:

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
    settings = get_settings()
    try:
        auth = await AuthResolver(settings).resolve(authorization, requested_user_id=req.user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    harness = get_aptguide_harness()
    request_id = f"r-{uuid4().hex}"
    result = harness.run(
        AptGuideRequest(
            request_id=request_id,
            session_id=req.session_id,
            user_id=auth.user_id,
            message=req.message,
            action=req.action,
            client_context={**req.client_context, "auth_mode": auth.auth_mode, "display_name": auth.display_name},
        )
    )
    return _build_response_from_harness(result)
```

- [ ] **Step 4: Add identity fields to response**

Modify `backend/src/aptguide2/api/schemas.py`:

```python
class ChatResponse(BaseModel):
    session_id: str | None = None
    request_id: str = ""
    trace_id: str = ""
    task: str
    message: str = ""
    phase: str = ""
    cards: list[dict] = Field(default_factory=list)
    rooms: list[RoomResponse] = Field(default_factory=list)
    kb_sources: list[KBSourceResponse] = Field(default_factory=list)
    is_confident: bool = False
    actions: list[dict] = Field(default_factory=list)
    pending_action: dict | None = None
    metadata: dict = Field(default_factory=dict)
```

Modify `_build_response_from_harness()` to populate:

```python
        session_id=result.session_id,
        request_id=result.request_id,
        trace_id=result.trace_id,
```

- [ ] **Step 5: Verify auth**

Run:

```bash
cd backend
uv run pytest tests/unit/api/test_auth.py -q
uv run pytest tests/e2e/test_system_mainline.py -q
```

Expected: all tests pass.

---

## Task 4: Create MySQL Schema And Persistence Models

**Files:**
- Create: `backend/src/aptguide2/persistence/database.py`
- Create: `backend/src/aptguide2/persistence/models.py`
- Create: `backend/src/aptguide2/persistence/schema.sql`
- Create: `backend/src/aptguide2/persistence/__init__.py`
- Test: `backend/tests/unit/persistence/test_database_models.py`

- [ ] **Step 1: Add model test**

Create `backend/tests/unit/persistence/test_database_models.py`:

```python
from aptguide2.persistence.models import Base


def test_required_tables_are_declared() -> None:
    assert {
        "aptguide_sessions",
        "aptguide_recent_messages",
        "aptguide_pending_actions",
        "aptguide_user_profiles",
        "aptguide_memory_candidates",
        "aptguide_handoff_tickets",
        "aptguide_operator_messages",
        "aptguide_audit_log",
    }.issubset(Base.metadata.tables.keys())
```

- [ ] **Step 2: Implement models**

Create `backend/src/aptguide2/persistence/models.py`:

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SessionRecord(Base):
    __tablename__ = "aptguide_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    phase: Mapped[str] = mapped_column(String(64), default="idle")
    active_task: Mapped[str | None] = mapped_column(String(64), nullable=True)
    task_slots: Mapped[dict] = mapped_column(JSON, default=dict)
    rolling_summary: Mapped[str] = mapped_column(Text, default="")
    long_term_profile_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    handoff_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class RecentMessageRecord(Base):
    __tablename__ = "aptguide_recent_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    request_id: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PendingActionRecord(Base):
    __tablename__ = "aptguide_pending_actions"

    confirmation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    action_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class UserProfileRecord(Base):
    __tablename__ = "aptguide_user_profiles"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class MemoryCandidateRecord(Base):
    __tablename__ = "aptguide_memory_candidates"

    candidate_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class HandoffTicketRecord(Base):
    __tablename__ = "aptguide_handoff_tickets"

    ticket_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="open")
    trigger: Mapped[str] = mapped_column(String(64))
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class OperatorMessageRecord(Base):
    __tablename__ = "aptguide_operator_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(64), index=True)
    sender: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AuditLogRecord(Base):
    __tablename__ = "aptguide_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    session_id: Mapped[str] = mapped_column(String(64), default="")
    event_type: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 3: Implement database factory**

Create `backend/src/aptguide2/persistence/database.py`:

```python
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def create_engine(mysql_dsn: str) -> AsyncEngine:
    return create_async_engine(mysql_dsn, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def session_scope(factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        async with session.begin():
            yield session
```

- [ ] **Step 4: Create explicit schema SQL**

Create `backend/src/aptguide2/persistence/schema.sql` with MySQL DDL matching the model table names. Use `JSON` columns for `task_slots`, `profile`, `payload`, and `summary`; use `utf8mb4`.

The first table must be:

```sql
CREATE TABLE IF NOT EXISTS aptguide_sessions (
  session_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  phase VARCHAR(64) NOT NULL DEFAULT 'idle',
  active_task VARCHAR(64) NULL,
  task_slots JSON NOT NULL,
  rolling_summary TEXT NOT NULL,
  long_term_profile_snapshot JSON NOT NULL,
  handoff_state JSON NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_aptguide_sessions_user_id (user_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Add the seven remaining tables using the model fields from Step 2.

- [ ] **Step 5: Verify model declarations**

Run:

```bash
cd backend
uv run pytest tests/unit/persistence/test_database_models.py -q
```

Expected: test passes.

---

## Task 5: Add Redis State Store

**Files:**
- Create: `backend/src/aptguide2/persistence/redis_store.py`
- Test: `backend/tests/unit/persistence/test_redis_store.py`

- [ ] **Step 1: Write fake Redis tests**

Create `backend/tests/unit/persistence/test_redis_store.py`:

```python
import json

from aptguide2.persistence.redis_store import RedisStateStore


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}
        self.ttls = {}

    async def set(self, key, value, ex=None):
        self.values[key] = value
        self.ttls[key] = ex

    async def get(self, key):
        return self.values.get(key)

    async def delete(self, key):
        self.values.pop(key, None)


async def test_session_round_trip() -> None:
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="test", session_ttl_seconds=60, pending_ttl_seconds=30)

    await store.save_session("s1", {"user_id": "u1", "phase": "idle"})
    loaded = await store.load_session("s1")

    assert loaded == {"user_id": "u1", "phase": "idle"}
    assert redis.ttls["test:session:s1"] == 60


async def test_pending_action_round_trip() -> None:
    redis = FakeRedis()
    store = RedisStateStore(redis, prefix="test", session_ttl_seconds=60, pending_ttl_seconds=30)

    await store.save_pending_action("c1", {"type": "appointment.create"})
    loaded = await store.load_pending_action("c1")

    assert loaded == {"type": "appointment.create"}
    assert json.loads(redis.values["test:pending:c1"])["type"] == "appointment.create"
```

- [ ] **Step 2: Implement Redis store**

Create `backend/src/aptguide2/persistence/redis_store.py`:

```python
from __future__ import annotations

import json
from typing import Any


class RedisStateStore:
    def __init__(
        self,
        redis_client: Any,
        prefix: str,
        session_ttl_seconds: int,
        pending_ttl_seconds: int,
    ) -> None:
        self.redis = redis_client
        self.prefix = prefix.rstrip(":")
        self.session_ttl_seconds = session_ttl_seconds
        self.pending_ttl_seconds = pending_ttl_seconds

    def session_key(self, session_id: str) -> str:
        return f"{self.prefix}:session:{session_id}"

    def pending_key(self, confirmation_id: str) -> str:
        return f"{self.prefix}:pending:{confirmation_id}"

    async def save_session(self, session_id: str, payload: dict[str, Any]) -> None:
        await self.redis.set(
            self.session_key(session_id),
            json.dumps(payload, ensure_ascii=False),
            ex=self.session_ttl_seconds,
        )

    async def load_session(self, session_id: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self.session_key(session_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    async def save_pending_action(self, confirmation_id: str, payload: dict[str, Any]) -> None:
        await self.redis.set(
            self.pending_key(confirmation_id),
            json.dumps(payload, ensure_ascii=False),
            ex=self.pending_ttl_seconds,
        )

    async def load_pending_action(self, confirmation_id: str) -> dict[str, Any] | None:
        raw = await self.redis.get(self.pending_key(confirmation_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    async def delete_pending_action(self, confirmation_id: str) -> None:
        await self.redis.delete(self.pending_key(confirmation_id))
```

- [ ] **Step 3: Verify Redis store**

Run:

```bash
cd backend
uv run pytest tests/unit/persistence/test_redis_store.py -q
```

Expected: tests pass.

---

## Task 6: Replace Development Context With Redis + MySQL Context Store

**Files:**
- Create: `backend/src/aptguide2/harness/context_persistent.py`
- Modify: `backend/src/aptguide2/api/deps.py`
- Modify: `backend/src/aptguide2/api/deps_persistence.py`
- Test: `backend/tests/unit/harness/test_persistent_context.py`

- [ ] **Step 1: Define context store behavior in tests**

Create `backend/tests/unit/harness/test_persistent_context.py`:

```python
from aptguide2.harness.context_persistent import PersistentContextStore
from aptguide2.harness.contracts import AptGuideRequest, ConversationFrame


class FakeRedisStore:
    def __init__(self) -> None:
        self.sessions = {}

    async def load_session(self, session_id):
        return self.sessions.get(session_id)

    async def save_session(self, session_id, payload):
        self.sessions[session_id] = payload


class FakeSessionRepository:
    def __init__(self) -> None:
        self.frames = {}

    async def load_frame(self, session_id):
        return self.frames.get(session_id)

    async def save_frame(self, frame):
        self.frames[frame.session_id] = frame.model_dump()


def test_new_request_creates_frame_when_no_session_exists() -> None:
    store = PersistentContextStore(redis_store=FakeRedisStore(), session_repository=FakeSessionRepository())

    frame = store.load(AptGuideRequest(request_id="r1", session_id="s1", user_id="u1", message="找房"))

    assert frame.session_id == "s1"
    assert frame.user_id == "u1"
    assert frame.message == "找房"


def test_save_and_load_round_trip() -> None:
    store = PersistentContextStore(redis_store=FakeRedisStore(), session_repository=FakeSessionRepository())
    frame = ConversationFrame(session_id="s1", request_id="r1", user_id="u1", message="找房", phase="idle")

    store.save(frame)
    loaded = store.load(AptGuideRequest(request_id="r2", session_id="s1", user_id="u1", message="我的预约"))

    assert loaded.request_id == "r2"
    assert loaded.message == "我的预约"
    assert loaded.user_id == "u1"
```

- [ ] **Step 2: Implement sync-compatible persistent context wrapper**

Create `backend/src/aptguide2/harness/context_persistent.py`.

Because `AptGuideHarness.run()` is currently synchronous, use `asyncio.run()` internally for repository calls in this task. Keep this wrapper small so a later async harness refactor is possible:

```python
from __future__ import annotations

import asyncio
from typing import Any

from aptguide2.harness.contracts import AptGuideRequest, ConversationFrame


class PersistentContextStore:
    def __init__(self, redis_store: Any, session_repository: Any) -> None:
        self.redis_store = redis_store
        self.session_repository = session_repository

    def load(self, request: AptGuideRequest) -> ConversationFrame:
        if not request.session_id:
            return ConversationFrame(
                session_id=request.session_id,
                request_id=request.request_id,
                user_id=request.user_id,
                message=request.message,
                action=request.action,
            )

        payload = asyncio.run(self.redis_store.load_session(request.session_id))
        if payload is None:
            payload = asyncio.run(self.session_repository.load_frame(request.session_id))

        if payload:
            frame = ConversationFrame.model_validate(payload)
            frame.request_id = request.request_id
            frame.user_id = request.user_id
            frame.message = request.message
            frame.action = request.action
            return frame

        return ConversationFrame(
            session_id=request.session_id,
            request_id=request.request_id,
            user_id=request.user_id,
            message=request.message,
            action=request.action,
        )

    def save(self, frame: ConversationFrame) -> None:
        if not frame.session_id:
            return
        payload = frame.model_dump(mode="json")
        asyncio.run(self.redis_store.save_session(frame.session_id, payload))
        asyncio.run(self.session_repository.save_frame(frame))
```

- [ ] **Step 3: Register persistent dependencies**

Create `backend/src/aptguide2/api/deps_persistence.py`:

```python
from __future__ import annotations

from functools import lru_cache

import redis.asyncio as redis

from aptguide2.api.deps import get_settings
from aptguide2.persistence.redis_store import RedisStateStore


@lru_cache
def get_redis_client():
    return redis.from_url(get_settings().redis_url, decode_responses=True)


@lru_cache
def get_redis_state_store() -> RedisStateStore:
    s = get_settings()
    return RedisStateStore(
        redis_client=get_redis_client(),
        prefix=s.redis_key_prefix,
        session_ttl_seconds=s.session_ttl_seconds,
        pending_ttl_seconds=s.pending_action_ttl_seconds,
    )
```

Add the MySQL session repository after Task 7, then wire `get_context_store()` to `PersistentContextStore`.

- [ ] **Step 4: Verify focused tests**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/test_persistent_context.py -q
```

Expected: tests pass.

---

## Task 7: Implement Durable Session And Memory Repositories

**Files:**
- Create: `backend/src/aptguide2/harness/memory_repository.py`
- Modify: `backend/src/aptguide2/api/deps_persistence.py`
- Test: `backend/tests/unit/harness/test_memory_repository.py`

- [ ] **Step 1: Write repository tests**

Create `backend/tests/unit/harness/test_memory_repository.py` using a fake in-memory repository if a real database is not available in unit tests:

```python
from aptguide2.harness.memory_repository import MemoryCandidate, MemoryRepository


class FakeMemoryRepository(MemoryRepository):
    def __init__(self) -> None:
        self.profiles = {}
        self.candidates = {}
        self.audit = []


async def test_profile_update_and_delete_contract() -> None:
    repo = FakeMemoryRepository()

    await repo.upsert_profile("u1", {"budget_max": 2500, "preferences": ["安静"]})
    assert await repo.get_profile("u1") == {"budget_max": 2500, "preferences": ["安静"]}

    await repo.delete_profile_key("u1", "budget_max", session_id="s1")
    assert await repo.get_profile("u1") == {"preferences": ["安静"]}
    assert repo.audit[-1]["event_type"] == "memory.profile_delete"


async def test_candidate_confirmation_contract() -> None:
    repo = FakeMemoryRepository()
    candidate = await repo.create_candidate(
        user_id="u1",
        session_id="s1",
        kind="preference",
        payload={"preferences": ["近地铁"]},
    )

    assert isinstance(candidate, MemoryCandidate)
    assert candidate.status == "pending"

    await repo.confirm_candidate(candidate.candidate_id)
    assert repo.candidates[candidate.candidate_id]["status"] == "confirmed"
```

- [ ] **Step 2: Implement repository protocol and fake-friendly base**

Create `backend/src/aptguide2/harness/memory_repository.py`:

```python
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MemoryCandidate:
    candidate_id: str
    user_id: str
    session_id: str
    kind: str
    payload: dict[str, Any]
    status: str = "pending"


class MemoryRepository:
    def __init__(self) -> None:
        self.profiles: dict[str, dict[str, Any]] = {}
        self.candidates: dict[str, dict[str, Any]] = {}
        self.audit: list[dict[str, Any]] = []

    async def get_profile(self, user_id: str) -> dict[str, Any]:
        return dict(self.profiles.get(user_id, {}))

    async def upsert_profile(self, user_id: str, patch: dict[str, Any], session_id: str = "") -> dict[str, Any]:
        current = dict(self.profiles.get(user_id, {}))
        current.update(patch)
        self.profiles[user_id] = current
        self.audit.append({"user_id": user_id, "session_id": session_id, "event_type": "memory.profile_update", "payload": patch})
        return current

    async def delete_profile_key(self, user_id: str, key: str, session_id: str = "") -> dict[str, Any]:
        current = dict(self.profiles.get(user_id, {}))
        current.pop(key, None)
        self.profiles[user_id] = current
        self.audit.append({"user_id": user_id, "session_id": session_id, "event_type": "memory.profile_delete", "payload": {"key": key}})
        return current

    async def create_candidate(self, user_id: str, session_id: str, kind: str, payload: dict[str, Any]) -> MemoryCandidate:
        candidate_id = f"mem-{uuid.uuid4().hex[:12]}"
        record = {
            "candidate_id": candidate_id,
            "user_id": user_id,
            "session_id": session_id,
            "kind": kind,
            "payload": payload,
            "status": "pending",
        }
        self.candidates[candidate_id] = record
        return MemoryCandidate(**record)

    async def confirm_candidate(self, candidate_id: str) -> MemoryCandidate | None:
        record = self.candidates.get(candidate_id)
        if record is None:
            return None
        record["status"] = "confirmed"
        return MemoryCandidate(**record)
```

- [ ] **Step 3: Replace in-memory implementation with SQLAlchemy-backed methods**

After the base contract passes, add a concrete `SqlMemoryRepository` in the same file that uses `AsyncSession` and the models from `persistence.models`. Keep the in-memory base for tests.

Required methods:

```python
class SqlMemoryRepository(MemoryRepository):
    async def get_profile(self, user_id: str) -> dict[str, Any]: ...
    async def upsert_profile(self, user_id: str, patch: dict[str, Any], session_id: str = "") -> dict[str, Any]: ...
    async def delete_profile_key(self, user_id: str, key: str, session_id: str = "") -> dict[str, Any]: ...
    async def create_candidate(self, user_id: str, session_id: str, kind: str, payload: dict[str, Any]) -> MemoryCandidate: ...
    async def confirm_candidate(self, candidate_id: str) -> MemoryCandidate | None: ...
```

- [ ] **Step 4: Verify repository contract**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/test_memory_repository.py -q
```

Expected: tests pass.

---

## Task 8: Add Memory Procedure And Routing

**Files:**
- Create: `backend/src/aptguide2/harness/modules/memory.py`
- Modify: `backend/src/aptguide2/harness/routing.py`
- Modify: `backend/src/aptguide2/api/deps.py`
- Test: `backend/tests/unit/harness/modules/test_memory.py`
- Test: `backend/tests/unit/harness/test_routing.py`

- [ ] **Step 1: Write memory procedure tests**

Create `backend/tests/unit/harness/modules/test_memory.py`:

```python
from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.memory_repository import MemoryRepository
from aptguide2.harness.modules.memory import MemoryProcedure


def decision() -> RouteDecision:
    return RouteDecision(task="memory", procedure="memory.profile", confidence=0.9)


async def test_show_profile_requires_user() -> None:
    proc = MemoryProcedure(MemoryRepository())
    frame = ConversationFrame(request_id="r1", session_id="s1", message="我的偏好")

    result = await proc.run_async(frame, decision())

    assert result.phase == "memory_auth_required"


async def test_remember_preference_creates_confirmation_card() -> None:
    repo = MemoryRepository()
    proc = MemoryProcedure(repo)
    frame = ConversationFrame(request_id="r1", session_id="s1", user_id="u1", message="记住我喜欢安静近地铁")

    result = await proc.run_async(frame, decision())

    assert result.phase == "memory_confirmation_required"
    assert result.pending_action["type"] == "memory.profile_update"
    assert result.cards[0]["type"] == "memory_confirmation"
```

- [ ] **Step 2: Implement memory procedure**

Create `backend/src/aptguide2/harness/modules/memory.py`:

```python
from __future__ import annotations

from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.memory import MemoryManager
from aptguide2.harness.memory_repository import MemoryRepository


class MemoryProcedure:
    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository
        self.memory = MemoryManager()

    async def run_async(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        if not frame.user_id:
            return ProcedureResult(task="memory", phase="memory_auth_required", reply="请先登录后再管理偏好。")

        message = frame.message or ""
        if "我的偏好" in message or "记住了什么" in message:
            profile = await self.repository.get_profile(frame.user_id)
            return ProcedureResult(
                task="memory",
                phase="memory_profile",
                reply="这是我目前记住的找房偏好。" if profile else "我还没有记住您的长期找房偏好。",
                cards=[{"type": "memory_profile", "profile": profile}],
                metadata={"profile_keys": list(profile.keys())},
            )

        if "删除" in message or "忘记" in message:
            key = "preferences"
            profile = await self.repository.delete_profile_key(frame.user_id, key, session_id=frame.session_id or "")
            return ProcedureResult(
                task="memory",
                phase="memory_deleted",
                reply="已删除相关长期偏好。",
                cards=[{"type": "memory_profile", "profile": profile}],
            )

        patch = self._extract_memory_patch(message)
        candidate = await self.repository.create_candidate(
            user_id=frame.user_id,
            session_id=frame.session_id or "",
            kind="preference",
            payload=patch,
        )
        pending = self.memory.create_pending_action(
            frame,
            action_type="memory.profile_update",
            payload={"candidate_id": candidate.candidate_id, "patch": patch},
        )
        return ProcedureResult(
            task="memory",
            phase="memory_confirmation_required",
            reply="我可以把这个作为长期找房偏好记住，请确认。",
            cards=[{"type": "memory_confirmation", "candidate_id": candidate.candidate_id, "patch": patch}],
            actions=[
                {"type": "confirm", "confirmation_id": pending["confirmation_id"], "label": "确认记住"},
                {"type": "cancel", "confirmation_id": pending["confirmation_id"], "label": "不记住"},
            ],
            pending_action=pending,
        )

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        import asyncio

        return asyncio.run(self.run_async(frame, decision, tool_runtime))

    def _extract_memory_patch(self, message: str) -> dict[str, Any]:
        preferences = []
        for term in ("安静", "近地铁", "采光好", "独卫", "通勤方便"):
            if term in message:
                preferences.append(term)
        return {"preferences": preferences or [message.replace("记住", "").strip()]}
```

- [ ] **Step 3: Route memory intents**

Modify `backend/src/aptguide2/harness/routing.py`:

```python
    memory_terms = ("记住", "我的偏好", "忘记", "删除偏好", "别再记")
```

Add before KB/room routing:

```python
        if any(term in message for term in self.memory_terms):
            return RouteDecision(
                task="memory",
                procedure="memory.profile",
                confidence=0.9,
                domain_category="in_domain_task",
                reason="memory management request",
            )
```

- [ ] **Step 4: Register procedure**

Modify `backend/src/aptguide2/api/deps.py`:

```python
from aptguide2.harness.modules.memory import MemoryProcedure
```

Register:

```python
runtime.register("memory.profile", MemoryProcedure(get_memory_repository()))
```

- [ ] **Step 5: Verify memory routing**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/modules/test_memory.py tests/unit/harness/test_routing.py -q
```

Expected: tests pass.

---

## Task 9: Make Pending Actions Durable

**Files:**
- Modify: `backend/src/aptguide2/harness/memory.py`
- Modify: `backend/src/aptguide2/harness/context_persistent.py`
- Modify: `backend/src/aptguide2/persistence/redis_store.py`
- Test: `backend/tests/unit/harness/test_memory.py`
- Test: `backend/tests/e2e/test_standalone_product.py`

- [ ] **Step 1: Add acceptance test for restart-safe pending action**

Add to `backend/tests/e2e/test_standalone_product.py`:

```python
def test_pending_action_survives_context_reload(client):
    response = client.post("/chat", json={"session_id": "s-pending", "message": "帮我预约第一套房"})
    data = response.json()
    assert data["pending_action"]["confirmation_id"]

    confirmation_id = data["pending_action"]["confirmation_id"]
    response = client.post(
        "/chat",
        json={"session_id": "s-pending", "message": "确认", "action": {"type": "confirm", "confirmation_id": confirmation_id}},
    )

    assert response.status_code == 200
```

- [ ] **Step 2: Persist pending action when saving frame**

Modify `PersistentContextStore.save()` so that when `frame.pending_action` exists it also calls:

```python
confirmation_id = frame.pending_action.get("confirmation_id")
if confirmation_id:
    asyncio.run(self.redis_store.save_pending_action(confirmation_id, frame.pending_action))
```

- [ ] **Step 3: Rehydrate pending action when loading session**

When loading a frame from Redis/MySQL, keep `frame.pending_action` intact. If a confirm action arrives and frame does not contain pending action, load by `confirmation_id`:

```python
confirmation_id = (request.action or {}).get("confirmation_id")
if confirmation_id and frame.pending_action is None:
    pending = asyncio.run(self.redis_store.load_pending_action(confirmation_id))
    if pending:
        frame.pending_action = pending
```

- [ ] **Step 4: Verify pending action**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/test_memory.py tests/e2e/test_standalone_product.py -q
```

Expected: tests pass.

---

## Task 10: Implement Durable Handoff Tickets

**Files:**
- Create: `backend/src/aptguide2/harness/handoff_repository.py`
- Modify: `backend/src/aptguide2/harness/modules/handoff.py`
- Modify: `backend/src/aptguide2/harness/orchestrator.py`
- Test: `backend/tests/unit/harness/test_handoff_repository.py`
- Test: `backend/tests/unit/harness/test_orchestrator.py`

- [ ] **Step 1: Write repository tests**

Create `backend/tests/unit/harness/test_handoff_repository.py`:

```python
from aptguide2.harness.handoff_repository import HandoffRepository


async def test_create_ticket_and_reply() -> None:
    repo = HandoffRepository()

    ticket = await repo.create_ticket(
        user_id="u1",
        session_id="s1",
        trigger="user_initiated",
        summary={"current_message": "转人工"},
    )
    await repo.add_message(ticket.ticket_id, sender="operator", content="您好，我来帮您。")

    detail = await repo.get_ticket(ticket.ticket_id)
    assert detail.ticket_id == ticket.ticket_id
    assert detail.status == "open"
    assert detail.messages[-1]["content"] == "您好，我来帮您。"


async def test_close_ticket_marks_closed() -> None:
    repo = HandoffRepository()
    ticket = await repo.create_ticket("u1", "s1", "user_initiated", {})

    await repo.close_ticket(ticket.ticket_id)

    assert (await repo.get_ticket(ticket.ticket_id)).status == "closed"
```

- [ ] **Step 2: Implement repository**

Create `backend/src/aptguide2/harness/handoff_repository.py`:

```python
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HandoffTicket:
    ticket_id: str
    user_id: str
    session_id: str
    trigger: str
    summary: dict[str, Any]
    status: str = "open"
    messages: list[dict[str, Any]] = field(default_factory=list)


class HandoffRepository:
    def __init__(self) -> None:
        self.tickets: dict[str, HandoffTicket] = {}

    async def create_ticket(self, user_id: str, session_id: str, trigger: str, summary: dict[str, Any]) -> HandoffTicket:
        ticket = HandoffTicket(
            ticket_id=f"hof-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            session_id=session_id,
            trigger=trigger,
            summary=summary,
        )
        self.tickets[ticket.ticket_id] = ticket
        return ticket

    async def list_tickets(self, status: str = "open") -> list[HandoffTicket]:
        return [ticket for ticket in self.tickets.values() if ticket.status == status]

    async def get_ticket(self, ticket_id: str) -> HandoffTicket:
        return self.tickets[ticket_id]

    async def add_message(self, ticket_id: str, sender: str, content: str) -> None:
        self.tickets[ticket_id].messages.append({"sender": sender, "content": content})

    async def close_ticket(self, ticket_id: str) -> None:
        self.tickets[ticket_id].status = "closed"
```

Add SQL-backed implementation after the in-memory contract passes.

- [ ] **Step 3: Modify handoff procedure**

Inject repository into `HandoffProcedure` and create a ticket:

```python
class HandoffProcedure:
    def __init__(self, repository: HandoffRepository | None = None) -> None:
        self.repository = repository or HandoffRepository()
```

When handoff is requested:

```python
ticket = asyncio.run(self.repository.create_ticket(
    user_id=frame.user_id or "",
    session_id=frame.session_id or "",
    trigger="user_initiated",
    summary=summary,
))
frame.handoff = {
    "status": "paused",
    "ticket_id": ticket.ticket_id,
    "trigger": "user_initiated",
    "summary": summary,
}
```

Return a handoff card:

```python
cards=[{"type": "handoff", "ticket_id": ticket.ticket_id, "status": "paused", "summary": summary}]
```

- [ ] **Step 4: Make orchestrator respect paused handoff**

At the start of `AptGuideHarness.run()` after context load:

```python
if frame.handoff and frame.handoff.get("status") == "paused":
    result = ProcedureResult(
        task="handoff",
        phase="handoff_paused",
        reply="当前会话已转接人工客服，AI 暂停自动回复。",
        cards=[{"type": "handoff", **frame.handoff}],
        metadata={"handoff_paused": True},
    )
    trace = recorder.to_trace()
    return self.composer.compose(frame, RouteDecision(task="handoff", procedure="handoff.paused", confidence=1.0), result, trace)
```

- [ ] **Step 5: Verify handoff**

Run:

```bash
cd backend
uv run pytest tests/unit/harness/test_handoff_repository.py tests/unit/harness/test_orchestrator.py -q
```

Expected: tests pass.

---

## Task 11: Add Operator API

**Files:**
- Create: `backend/src/aptguide2/api/operator.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Create: `backend/tests/unit/api/test_operator_api.py`

- [ ] **Step 1: Write API tests**

Create `backend/tests/unit/api/test_operator_api.py`:

```python
def test_operator_requires_token(client):
    response = client.get("/operator/tickets")
    assert response.status_code == 401


def test_operator_can_list_tickets(client):
    response = client.get("/operator/tickets", headers={"X-Operator-Token": "operator-dev-token"})
    assert response.status_code == 200
    assert "tickets" in response.json()
```

- [ ] **Step 2: Implement operator router**

Create `backend/src/aptguide2/api/operator.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from aptguide2.api.deps import get_settings
from aptguide2.api.deps_persistence import get_handoff_repository

router = APIRouter(prefix="/operator", tags=["operator"])


class OperatorReplyRequest(BaseModel):
    content: str


def require_operator(token: str | None) -> None:
    settings = get_settings()
    if not settings.operator_console_enabled:
        raise HTTPException(status_code=404, detail="operator console disabled")
    if token != settings.operator_dev_token:
        raise HTTPException(status_code=401, detail="invalid operator token")


@router.get("/tickets")
async def list_tickets(x_operator_token: str | None = Header(default=None), status: str = "open"):
    require_operator(x_operator_token)
    repo = get_handoff_repository()
    tickets = await repo.list_tickets(status=status)
    return {"tickets": [ticket.__dict__ for ticket in tickets]}


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, x_operator_token: str | None = Header(default=None)):
    require_operator(x_operator_token)
    ticket = await get_handoff_repository().get_ticket(ticket_id)
    return ticket.__dict__


@router.post("/tickets/{ticket_id}/reply")
async def reply(ticket_id: str, req: OperatorReplyRequest, x_operator_token: str | None = Header(default=None)):
    require_operator(x_operator_token)
    await get_handoff_repository().add_message(ticket_id, sender="operator", content=req.content)
    return {"ok": True}


@router.post("/tickets/{ticket_id}/close")
async def close(ticket_id: str, x_operator_token: str | None = Header(default=None)):
    require_operator(x_operator_token)
    await get_handoff_repository().close_ticket(ticket_id)
    return {"ok": True}
```

- [ ] **Step 3: Include router**

Modify `backend/src/aptguide2/api/app.py`:

```python
from aptguide2.api.operator import router as operator_router

app.include_router(operator_router)
```

- [ ] **Step 4: Verify operator API**

Run:

```bash
cd backend
uv run pytest tests/unit/api/test_operator_api.py -q
```

Expected: tests pass.

---

## Task 12: Add Standalone Frontend Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router.ts`
- Create: `frontend/src/styles.css`

- [ ] **Step 1: Create package file**

Create `frontend/package.json`:

```json
{
  "name": "aptguide2-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-vue": "^5.2.0",
    "axios": "^1.7.9",
    "pinia": "^2.3.0",
    "vant": "^4.9.14",
    "vue": "^3.5.13",
    "vue-router": "^4.5.0"
  },
  "devDependencies": {
    "typescript": "^5.7.2",
    "vite": "^6.0.3",
    "vitest": "^2.1.8",
    "vue-tsc": "^2.1.10"
  }
}
```

- [ ] **Step 2: Create Vite config**

Create `frontend/vite.config.ts`:

```ts
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/chat": "http://localhost:8100",
      "/health": "http://localhost:8100",
      "/operator": "http://localhost:8100"
    }
  }
});
```

- [ ] **Step 3: Create app shell**

Create `frontend/src/App.vue`:

```vue
<template>
  <router-view />
</template>
```

Create `frontend/src/main.ts`:

```ts
import "vant/lib/index.css";
import "./styles.css";

import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";

createApp(App).use(createPinia()).use(router).mount("#app");
```

Create `frontend/src/router.ts`:

```ts
import { createRouter, createWebHistory } from "vue-router";

import ChatShell from "./components/chat/ChatShell.vue";
import OperatorConsole from "./components/operator/OperatorConsole.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: ChatShell },
    { path: "/operator", component: OperatorConsole }
  ]
});
```

- [ ] **Step 4: Verify frontend scaffold**

Run:

```bash
cd frontend
npm install
npm run build
```

Expected: build succeeds.

---

## Task 13: Implement Frontend Chat Contract And Stores

**Files:**
- Create: `frontend/src/types/chat.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/chat.ts`
- Create: `frontend/src/stores/auth.ts`
- Create: `frontend/src/stores/chat.ts`
- Create: `frontend/tests/chat-contract.test.ts`

- [ ] **Step 1: Define chat types**

Create `frontend/src/types/chat.ts`:

```ts
export type ChatAction = {
  type: string;
  label?: string;
  confirmation_id?: string;
  payload?: Record<string, unknown>;
};

export type PendingAction = {
  type: string;
  confirmation_id: string;
  status: string;
  payload: Record<string, unknown>;
  expires_at?: number;
};

export type ChatCard = {
  type: string;
  [key: string]: unknown;
};

export type ChatResponse = {
  session_id: string | null;
  request_id: string;
  trace_id: string;
  task: string;
  message: string;
  phase: string;
  cards: ChatCard[];
  rooms: unknown[];
  kb_sources: unknown[];
  is_confident: boolean;
  actions: ChatAction[];
  pending_action: PendingAction | null;
  metadata: Record<string, unknown>;
};

export type ChatRequest = {
  message: string;
  session_id?: string;
  user_id?: string;
  action?: Record<string, unknown>;
  client_context?: Record<string, unknown>;
};
```

- [ ] **Step 2: Implement client**

Create `frontend/src/api/client.ts`:

```ts
import axios from "axios";

export const http = axios.create({
  baseURL: import.meta.env.VITE_APTGUIDE_API_BASE || "",
  timeout: 30000
});

export function setBearerToken(token: string | null) {
  if (token) {
    http.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete http.defaults.headers.common.Authorization;
  }
}
```

Create `frontend/src/api/chat.ts`:

```ts
import { http } from "./client";
import type { ChatRequest, ChatResponse } from "../types/chat";

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await http.post<ChatResponse>("/chat", request);
  return response.data;
}
```

- [ ] **Step 3: Implement stores**

Create `frontend/src/stores/auth.ts`:

```ts
import { defineStore } from "pinia";
import { setBearerToken } from "../api/client";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    mode: "dev" as "dev" | "lease_token",
    devUserId: "dev-user-001",
    token: ""
  }),
  actions: {
    setDevUser(userId: string) {
      this.mode = "dev";
      this.devUserId = userId;
      setBearerToken(null);
    },
    setToken(token: string) {
      this.mode = "lease_token";
      this.token = token;
      setBearerToken(token);
    }
  }
});
```

Create `frontend/src/stores/chat.ts`:

```ts
import { defineStore } from "pinia";
import { sendChat } from "../api/chat";
import { useAuthStore } from "./auth";
import type { ChatAction, ChatCard, ChatResponse, PendingAction } from "../types/chat";

type Message = {
  role: "user" | "assistant";
  content: string;
  cards?: ChatCard[];
  actions?: ChatAction[];
};

export const useChatStore = defineStore("chat", {
  state: () => ({
    sessionId: undefined as string | undefined,
    messages: [] as Message[],
    pendingAction: null as PendingAction | null,
    latestResponse: null as ChatResponse | null,
    loading: false
  }),
  actions: {
    async send(message: string, action?: Record<string, unknown>) {
      const auth = useAuthStore();
      this.loading = true;
      this.messages.push({ role: "user", content: message });
      try {
        const response = await sendChat({
          message,
          session_id: this.sessionId,
          user_id: auth.mode === "dev" ? auth.devUserId : undefined,
          action,
          client_context: { frontend: "standalone" }
        });
        this.sessionId = response.session_id || this.sessionId;
        this.pendingAction = response.pending_action;
        this.latestResponse = response;
        this.messages.push({
          role: "assistant",
          content: response.message,
          cards: response.cards,
          actions: response.actions
        });
      } finally {
        this.loading = false;
      }
    }
  }
});
```

- [ ] **Step 4: Add contract test**

Create `frontend/tests/chat-contract.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import type { ChatResponse } from "../src/types/chat";

describe("ChatResponse contract", () => {
  it("supports cards, actions, pending action, and trace ids", () => {
    const response: ChatResponse = {
      session_id: "s1",
      request_id: "r1",
      trace_id: "t1",
      task: "appointment",
      message: "请确认预约",
      phase: "confirmation_required",
      cards: [{ type: "confirmation", confirmation_id: "c1" }],
      rooms: [],
      kb_sources: [],
      is_confident: true,
      actions: [{ type: "confirm", confirmation_id: "c1" }],
      pending_action: { type: "appointment.create", confirmation_id: "c1", status: "pending", payload: {} },
      metadata: {}
    };

    expect(response.cards[0].type).toBe("confirmation");
    expect(response.actions[0].confirmation_id).toBe("c1");
  });
});
```

- [ ] **Step 5: Verify frontend contract**

Run:

```bash
cd frontend
npm run test
```

Expected: tests pass.

---

## Task 14: Build Standalone Chat UI

**Files:**
- Create: `frontend/src/components/auth/DevUserSelector.vue`
- Create: `frontend/src/components/chat/ChatShell.vue`
- Create: `frontend/src/components/chat/MessageList.vue`
- Create: `frontend/src/components/chat/MessageComposer.vue`
- Create: `frontend/src/components/chat/CardRenderer.vue`
- Create: `frontend/src/components/chat/ActionBar.vue`
- Create: `frontend/src/components/chat/PendingActionBanner.vue`
- Create: `frontend/src/components/chat/TracePanel.vue`
- Create: `frontend/src/components/chat/cards/RoomCard.vue`
- Create: `frontend/src/components/chat/cards/LeaseCard.vue`
- Create: `frontend/src/components/chat/cards/AppointmentCard.vue`
- Create: `frontend/src/components/chat/cards/ConfirmationCard.vue`
- Create: `frontend/src/components/chat/cards/MemoryCard.vue`
- Create: `frontend/src/components/chat/cards/HandoffCard.vue`

- [ ] **Step 1: Implement development user selector**

Create `frontend/src/components/auth/DevUserSelector.vue`:

```vue
<script setup lang="ts">
import { useAuthStore } from "../../stores/auth";

const auth = useAuthStore();
const users = [
  { id: "dev-user-001", name: "测试用户 1" },
  { id: "dev-user-002", name: "测试用户 2" }
];
</script>

<template>
  <select :value="auth.devUserId" @change="auth.setDevUser(($event.target as HTMLSelectElement).value)">
    <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
  </select>
</template>
```

- [ ] **Step 2: Implement chat shell**

Create `frontend/src/components/chat/ChatShell.vue`:

```vue
<script setup lang="ts">
import DevUserSelector from "../auth/DevUserSelector.vue";
import MessageComposer from "./MessageComposer.vue";
import MessageList from "./MessageList.vue";
import PendingActionBanner from "./PendingActionBanner.vue";
import TracePanel from "./TracePanel.vue";
</script>

<template>
  <main class="app-shell">
    <header class="topbar">
      <div>
        <h1>AptGuide 2.0</h1>
        <p>独立租房 Agent 应用</p>
      </div>
      <DevUserSelector />
    </header>
    <section class="chat-layout">
      <div class="chat-main">
        <PendingActionBanner />
        <MessageList />
        <MessageComposer />
      </div>
      <TracePanel />
    </section>
  </main>
</template>
```

- [ ] **Step 3: Implement card renderer**

Create `frontend/src/components/chat/CardRenderer.vue`:

```vue
<script setup lang="ts">
import AppointmentCard from "./cards/AppointmentCard.vue";
import ConfirmationCard from "./cards/ConfirmationCard.vue";
import HandoffCard from "./cards/HandoffCard.vue";
import LeaseCard from "./cards/LeaseCard.vue";
import MemoryCard from "./cards/MemoryCard.vue";
import RoomCard from "./cards/RoomCard.vue";

defineProps<{ card: Record<string, unknown> }>();
</script>

<template>
  <RoomCard v-if="card.type === 'room'" :card="card" />
  <LeaseCard v-else-if="card.type === 'lease_record'" :card="card" />
  <AppointmentCard v-else-if="card.type === 'appointment_record'" :card="card" />
  <ConfirmationCard v-else-if="String(card.type).includes('confirmation')" :card="card" />
  <MemoryCard v-else-if="String(card.type).startsWith('memory')" :card="card" />
  <HandoffCard v-else-if="card.type === 'handoff'" :card="card" />
  <pre v-else class="raw-card">{{ card }}</pre>
</template>
```

- [ ] **Step 4: Implement action handling**

Create `frontend/src/components/chat/ActionBar.vue`:

```vue
<script setup lang="ts">
import { useChatStore } from "../../stores/chat";
import type { ChatAction } from "../../types/chat";

defineProps<{ actions: ChatAction[] }>();
const chat = useChatStore();

function run(action: ChatAction) {
  const label = action.type === "cancel" ? "取消" : "确认";
  chat.send(label, {
    type: action.type,
    confirmation_id: action.confirmation_id,
    payload: action.payload || {}
  });
}
</script>

<template>
  <div class="action-bar">
    <button v-for="action in actions" :key="`${action.type}-${action.confirmation_id}`" @click="run(action)">
      {{ action.label || action.type }}
    </button>
  </div>
</template>
```

- [ ] **Step 5: Verify frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: build succeeds and no TypeScript errors.

---

## Task 15: Build Local Operator Console UI

**Files:**
- Create: `frontend/src/types/operator.ts`
- Create: `frontend/src/api/operator.ts`
- Create: `frontend/src/stores/operator.ts`
- Create: `frontend/src/components/operator/OperatorConsole.vue`
- Create: `frontend/src/components/operator/TicketList.vue`
- Create: `frontend/src/components/operator/TicketDetail.vue`
- Create: `frontend/src/components/operator/OperatorReplyBox.vue`
- Create: `frontend/tests/operator-contract.test.ts`

- [ ] **Step 1: Define operator types**

Create `frontend/src/types/operator.ts`:

```ts
export type HandoffTicket = {
  ticket_id: string;
  user_id: string;
  session_id: string;
  status: string;
  trigger: string;
  summary: Record<string, unknown>;
  messages: Array<{ sender: string; content: string; created_at?: string }>;
};
```

- [ ] **Step 2: Implement operator API client**

Create `frontend/src/api/operator.ts`:

```ts
import { http } from "./client";
import type { HandoffTicket } from "../types/operator";

const headers = { "X-Operator-Token": import.meta.env.VITE_OPERATOR_DEV_TOKEN || "operator-dev-token" };

export async function listTickets(): Promise<HandoffTicket[]> {
  const response = await http.get<{ tickets: HandoffTicket[] }>("/operator/tickets", { headers });
  return response.data.tickets;
}

export async function getTicket(ticketId: string): Promise<HandoffTicket> {
  const response = await http.get<HandoffTicket>(`/operator/tickets/${ticketId}`, { headers });
  return response.data;
}

export async function replyTicket(ticketId: string, content: string): Promise<void> {
  await http.post(`/operator/tickets/${ticketId}/reply`, { content }, { headers });
}

export async function closeTicket(ticketId: string): Promise<void> {
  await http.post(`/operator/tickets/${ticketId}/close`, {}, { headers });
}
```

- [ ] **Step 3: Implement operator console**

Create `frontend/src/components/operator/OperatorConsole.vue`:

```vue
<script setup lang="ts">
import { onMounted } from "vue";
import { useOperatorStore } from "../../stores/operator";
import TicketDetail from "./TicketDetail.vue";
import TicketList from "./TicketList.vue";

const store = useOperatorStore();
onMounted(() => store.refresh());
</script>

<template>
  <main class="operator-layout">
    <TicketList />
    <TicketDetail v-if="store.selectedTicket" />
  </main>
</template>
```

- [ ] **Step 4: Verify operator frontend**

Run:

```bash
cd frontend
npm run test
npm run build
```

Expected: tests and build pass.

---

## Task 16: Add Dependency Readiness For Standalone Product

**Files:**
- Modify: `backend/src/aptguide2/system/readiness.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Modify: `backend/tests/unit/system/test_readiness.py`

- [ ] **Step 1: Extend readiness contract**

Add checks for:

```text
redis
mysql
auth
operator_console
milvus
embedding
lease
pipeline
```

Each check must include:

```python
DependencyCheck(name="redis", required=True, ready=True | False, detail="...")
```

- [ ] **Step 2: Add endpoint**

Add to `backend/src/aptguide2/api/app.py`:

```python
@app.get("/health/deps")
async def health_deps():
    from aptguide2.system.readiness import build_readiness_report

    return build_readiness_report(settings=get_settings()).model_dump()
```

- [ ] **Step 3: Verify readiness**

Run:

```bash
cd backend
uv run pytest tests/unit/system/test_readiness.py -q
```

Expected: readiness tests pass.

---

## Task 17: End-To-End Standalone Product Smoke

**Files:**
- Create: `backend/tests/e2e/test_standalone_product.py`
- Create: `backend/tests/e2e/test_handoff_operator_flow.py`
- Modify: `docs/tests/verification-log.md`

- [ ] **Step 1: Add backend smoke cases**

Create cases covering:

```python
def test_chat_capability_direct(client): ...
def test_room_search_returns_cards(client): ...
def test_lease_requires_auth_or_resolved_user(client): ...
def test_memory_confirm_then_show_profile(client): ...
def test_appointment_confirmation_flow(client): ...
def test_handoff_creates_ticket_and_pauses_ai(client): ...
def test_operator_reply_and_close(client): ...
```

Each case should call `POST /chat` directly, not `lease /app/ai/chat`.

- [ ] **Step 2: Run backend smoke**

Run:

```bash
cd backend
uv run pytest tests/e2e/test_standalone_product.py tests/e2e/test_handoff_operator_flow.py -q
```

Expected: all new e2e tests pass.

- [ ] **Step 3: Run full backend verification**

Run:

```bash
cd backend
uv run pytest tests/ -q
uv run ruff check src/ tests/
```

Expected:

```text
all tests passed
All checks passed!
```

- [ ] **Step 4: Run frontend verification**

Run:

```bash
cd frontend
npm run test
npm run build
```

Expected: tests and build pass.

---

## Task 18: Final Documentation Sync And Checkpoint

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/27-current-implementation-guide.md`
- Modify: `docs/plans/current-plan.md`
- Modify: `docs/plans/execution-log.md`
- Modify: `docs/plans/next-steps.md`
- Modify: `docs/tests/verification-log.md`
- Modify: `docs/system/feature-list.md`
- Modify: `.agent-state/last-checkpoint.json`

- [ ] **Step 1: Update implementation guide**

In `docs/27-current-implementation-guide.md`, ensure the first “current implementation” section says:

```text
当前 AptGuide 2.0 是独立可运行的租房 Agent 应用：standalone frontend 直接调用 backend `/chat`，backend 使用 AptGuideHarness、RAG v2、Redis + MySQL memory、真实 lease backend、Milvus 和 LLM。
```

Remove or rewrite any later section that says `backend/src/aptguide2/rag/pipeline.py` is the current main workflow. It may remain only as:

```text
Legacy RAG MVP reference, not product runtime.
```

- [ ] **Step 2: Update verification log**

Append:

```markdown
## 2026-05-14 — Standalone Productization

**Backend:** `cd backend && uv run pytest tests/ -q`
**Lint:** `cd backend && uv run ruff check src/ tests/`
**Frontend:** `cd frontend && npm run test && npm run build`

### Coverage

- Direct `/chat` standalone product flow
- Development auth and lease-token auth resolver
- Redis + MySQL persistent context and memory
- Durable pending actions
- Durable handoff tickets
- Local operator console API
- Frontend chat cards/actions/pending state
- Frontend operator console
```

- [ ] **Step 3: Create harness checkpoint**

Run:

```bash
python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py checkpoint --project "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0" --task "standalone-productization"
```

Expected: a checkpoint file appears under `docs/plans/checkpoints/`.

- [ ] **Step 4: Fill checkpoint with real evidence**

The checkpoint must include:

- backend test command and result
- frontend test command and result
- readiness status
- files changed
- known gaps
- explicit statement that RAG quality optimization remains deferred

---

## Recommended Execution Order

1. Task 1: Docs/harness state sync.
2. Task 2: Config and dependencies.
3. Task 3: Auth resolver.
4. Tasks 4-7: MySQL/Redis persistence and memory repository.
5. Tasks 8-9: Memory procedure and durable pending actions.
6. Tasks 10-11: Durable handoff and operator API.
7. Tasks 12-15: Standalone frontend and operator UI.
8. Tasks 16-17: Readiness and e2e smoke.
9. Task 18: Docs/checkpoint.

## Risk Register

| Risk | Mitigation |
| --- | --- |
| Sync harness calls async persistence through `asyncio.run()` | Keep wrapper isolated; later refactor harness to async if needed. |
| Lease token user-info endpoint differs from assumed `/app/info` response | Make path configurable and cover expected response variants `id`, `user_id`, `userId`. |
| MySQL is not available in unit tests | Unit tests use fake repositories; e2e/live readiness validates real MySQL. |
| Redis outage breaks pending action confirmation | Readiness should fail; user-facing response should say context service unavailable instead of silently losing state. |
| Operator console becomes a second product surface | Keep it local and minimal: list, inspect, reply, close, resume AI. |
| Frontend contract drifts from backend response | Keep `frontend/tests/chat-contract.test.ts` and backend e2e schema assertions. |

## Handoff Summary

Execution agent should start with Task 1 and avoid touching RAG retrieval quality. The first implementation milestone is not “all productization complete”; it is a clean state sync plus backend config/auth foundation. Commit or checkpoint after each task group so the project can resume safely.
