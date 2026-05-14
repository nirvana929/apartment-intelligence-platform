# AptGuide 2.0 Standalone Hardening And Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the standalone AptGuide 2.0 MVP into a staging-ready independent product with stronger runtime stability, security boundaries, frontend operational UX, and production-grade troubleshooting signals.

**Architecture:** Keep AptGuide 2.0 as an independently deployable backend + Vue frontend. Harden the existing standalone runtime around configuration, dependency readiness, auth/operator security, frontend error states, and structured observability without changing the RAG retrieval strategy or integrating into the larger apartment platform.

**Tech Stack:** FastAPI, Pydantic Settings, httpx, SQLAlchemy async models, Redis, MySQL, Vue 3, Pinia, Vant, Vitest, pytest.

---

## Scope

This plan improves the existing independent system only:

- Deployment and runtime stability.
- Security and permission hardening.
- Frontend product experience for chat and operator workflows.
- Observability and diagnostics.

## Explicit Non-Goals

- Do not optimize RAG retrieval quality, ranking, reranking, chunking, embedding strategy, or eval thresholds.
- Do not integrate through `rentHouseH5`.
- Do not align or replace the platform `lease /app/ai/chat` proxy.
- Do not replace the local operator console with the future production customer-service system.
- Do not reconnect legacy RAG MVP to any public runtime path.

## File Structure

- `backend/src/aptguide2/core/config.py` controls deployment, auth, CORS, operator, and observability settings.
- `backend/.env.example` documents required staging/prod variables and unsafe defaults.
- `backend/src/aptguide2/system/readiness.py` owns dependency readiness checks.
- `backend/src/aptguide2/api/app.py` exposes health/readiness/chat endpoints and injects request IDs.
- `backend/src/aptguide2/api/auth.py` resolves dev and lease-token identity.
- `backend/src/aptguide2/api/operator.py` protects operator workflows.
- `backend/src/aptguide2/observability/` will contain request context and structured logging helpers.
- `backend/tests/unit/system/test_readiness.py` covers readiness behavior.
- `backend/tests/unit/api/test_auth.py` and `backend/tests/unit/api/test_operator_api.py` cover auth/operator boundaries.
- `backend/tests/unit/observability/test_request_logging.py` will cover structured event helpers.
- `backend/tests/e2e/test_system_mainline.py` should assert request/trace IDs are returned on `/chat`.
- `frontend/src/stores/chat.ts` and `frontend/src/stores/operator.ts` own loading/error/retry state.
- `frontend/src/components/chat/` renders chat operational states.
- `frontend/src/components/operator/` renders operator workflow states.
- `frontend/tests/chat-contract.test.ts` and `frontend/tests/operator-contract.test.ts` should expand contract coverage for new fields.
- `docs/system/standalone-deployment-runbook.md` will document staging startup, validation, restart, and rollback.
- `docs/tests/verification-log.md` must record final verification after implementation.

---

### Task 1: Deployment Configuration And Runbook

**Files:**
- Modify: `backend/src/aptguide2/core/config.py`
- Modify: `backend/.env.example`
- Create: `docs/system/standalone-deployment-runbook.md`
- Test: `backend/tests/unit/system/test_readiness.py`

- [ ] **Step 1: Add deployment safety settings**

Add these fields to `Settings` in `backend/src/aptguide2/core/config.py`:

```python
    # Deployment
    environment: str = "local"  # local | staging | production
    service_name: str = "aptguide2"
    service_version: str = "0.1.0"
    cors_allow_origins: str = "http://localhost:5173"
    require_secure_defaults: bool = False

    # Observability
    log_level: str = "INFO"
    structured_logs_enabled: bool = True
    expose_trace_to_frontend: bool = True
```

- [ ] **Step 2: Replace single-origin CORS usage with parsed origins**

In `backend/src/aptguide2/core/config.py`, add:

```python
    @property
    def parsed_cors_origins(self) -> list[str]:
        values = [origin.strip() for origin in self.cors_allow_origins.split(",")]
        return [origin for origin in values if origin]
```

In `backend/src/aptguide2/api/app.py`, change CORS setup to:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 3: Document staging/prod environment variables**

Update `backend/.env.example` with concrete variable groups:

```bash
APTGUIDE_ENVIRONMENT=staging
APTGUIDE_AUTH_MODE=lease_token
APTGUIDE_CORS_ALLOW_ORIGINS=https://aptguide-staging.example.com
APTGUIDE_LEASE_BASE_URL=http://localhost:8081
APTGUIDE_LEASE_USERINFO_PATH=/app/info
APTGUIDE_REDIS_URL=redis://localhost:6379/0
APTGUIDE_MYSQL_DSN=mysql+asyncmy://root:change-me@localhost:3306/least
APTGUIDE_OPERATOR_CONSOLE_ENABLED=true
APTGUIDE_OPERATOR_DEV_TOKEN=replace-with-staging-operator-token
APTGUIDE_STRUCTURED_LOGS_ENABLED=true
APTGUIDE_EXPOSE_TRACE_TO_FRONTEND=true
```

Keep development defaults clearly marked as local-only.

- [ ] **Step 4: Create the standalone deployment runbook**

Create `docs/system/standalone-deployment-runbook.md` with these sections:

```markdown
# AptGuide 2.0 Standalone Deployment Runbook

## Purpose

Run AptGuide 2.0 as an independent staging service before platform integration.

## Dependencies

- MySQL database with `backend/src/aptguide2/persistence/schema.sql` applied.
- Redis reachable from the backend.
- Lease backend reachable through `APTGUIDE_LEASE_BASE_URL`.
- Milvus reachable through `APTGUIDE_MILVUS_URI`.
- Embedding and LLM credentials configured.

## Startup

1. Configure backend environment variables from `backend/.env.example`.
2. Apply `backend/src/aptguide2/persistence/schema.sql` to the staging database.
3. Start Redis.
4. Start lease backend.
5. Start AptGuide backend.
6. Build and serve the frontend with the staging API base URL.

## Verification

Run:

```bash
cd backend && uv run pytest tests/ -q
cd frontend && npm run test && npm run build
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Restart Validation

1. Send a chat message that creates memory or a pending action.
2. Restart the backend.
3. Continue the same session.
4. Confirm Redis/MySQL-backed state is preserved.

## Rollback

1. Stop the new backend/frontend processes.
2. Restore the previous backend and frontend artifacts.
3. Keep MySQL tables because the schema uses the `aptguide_` prefix.
4. Disable operator access by setting `APTGUIDE_OPERATOR_CONSOLE_ENABLED=false`.
```

- [ ] **Step 5: Verify docs and config syntax**

Run:

```bash
cd backend && uv run pytest tests/unit/system/test_readiness.py -q
```

Expected: existing readiness tests still pass before deeper readiness changes.

---

### Task 2: Dependency Readiness And Runtime Stability

**Files:**
- Modify: `backend/src/aptguide2/system/readiness.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Modify: `backend/tests/unit/system/test_readiness.py`
- Modify: `backend/tests/e2e/test_system_mainline.py`

- [ ] **Step 1: Add readiness check metadata**

Extend `DependencyCheck` in `backend/src/aptguide2/system/readiness.py`:

```python
class DependencyCheck(BaseModel):
    name: str
    ok: bool
    required: bool = True
    detail: str = ""
    category: str = "runtime"
```

- [ ] **Step 2: Split readiness into required dependency checks**

Update `build_readiness_report()` so it always returns checks for:

```python
checks = [
    DependencyCheck(
        name="pipeline",
        ok=settings.pipeline_version == "harness_v1",
        detail=f"pipeline_version={settings.pipeline_version}",
        category="runtime",
    ),
    DependencyCheck(
        name="auth_mode",
        ok=settings.auth_mode in {"dev", "lease_token"},
        detail=f"auth_mode={settings.auth_mode}",
        category="security",
    ),
    DependencyCheck(
        name="mysql_config",
        ok=bool(settings.mysql_dsn),
        detail="mysql_dsn configured" if settings.mysql_dsn else "mysql_dsn missing",
        category="persistence",
    ),
    DependencyCheck(
        name="redis_config",
        ok=bool(settings.redis_url),
        detail="redis_url configured" if settings.redis_url else "redis_url missing",
        category="persistence",
    ),
    DependencyCheck(
        name="lease_config",
        ok=bool(settings.lease_base_url),
        detail=f"lease_base_url={settings.lease_base_url}",
        category="integration",
    ),
    DependencyCheck(
        name="milvus_config",
        ok=bool(settings.milvus_uri),
        detail=f"milvus_uri={settings.milvus_uri}",
        category="integration",
    ),
    DependencyCheck(
        name="embedding_config",
        ok=bool(settings.embedding_model) and settings.embedding_dim > 0,
        detail=f"embedding_model={settings.embedding_model}, dim={settings.embedding_dim}",
        category="integration",
    ),
]
```

This task should validate configuration readiness without doing expensive live network probes in unit tests.

- [ ] **Step 3: Add `/ready` endpoint**

In `backend/src/aptguide2/api/app.py`, import readiness:

```python
from aptguide2.system.readiness import ReadinessReport, build_readiness_report
```

Add:

```python
@app.get("/ready", response_model=ReadinessReport)
def ready() -> ReadinessReport:
    """Readiness check for staging deployment gates."""
    return build_readiness_report(get_settings())
```

- [ ] **Step 4: Test readiness categories and required gate**

Add to `backend/tests/unit/system/test_readiness.py`:

```python
def test_readiness_report_contains_standalone_dependencies():
    report = build_readiness_report(Settings())
    names = {check.name for check in report.checks}

    assert "pipeline" in names
    assert "auth_mode" in names
    assert "mysql_config" in names
    assert "redis_config" in names
    assert "lease_config" in names
    assert "milvus_config" in names
    assert "embedding_config" in names
    assert report.all_required_ok is True
```

- [ ] **Step 5: Test `/ready` endpoint**

Add to `backend/tests/e2e/test_system_mainline.py`:

```python
def test_ready_endpoint_returns_required_dependency_report(client):
    response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    names = {check["name"] for check in payload["checks"]}
    assert "pipeline" in names
    assert "mysql_config" in names
    assert "redis_config" in names
```

- [ ] **Step 6: Run backend verification for readiness**

Run:

```bash
cd backend && uv run pytest tests/unit/system/test_readiness.py tests/e2e/test_system_mainline.py -q
```

Expected: all selected tests pass.

---

### Task 3: Security And Permission Hardening

**Files:**
- Modify: `backend/src/aptguide2/api/auth.py`
- Modify: `backend/src/aptguide2/api/operator.py`
- Modify: `backend/src/aptguide2/core/config.py`
- Modify: `backend/tests/unit/api/test_auth.py`
- Modify: `backend/tests/unit/api/test_operator_api.py`

- [ ] **Step 1: Normalize auth failures**

In `backend/src/aptguide2/api/auth.py`, catch lease backend request failures and convert them to `PermissionError`:

```python
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.lease_base_url.rstrip("/"),
                timeout=self.settings.lease_timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.get(self.settings.lease_userinfo_path)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise PermissionError("lease token rejected") from exc
        except httpx.HTTPError as exc:
            raise PermissionError("lease auth service unavailable") from exc
```

- [ ] **Step 2: Keep formal auth user identity token-derived**

Add or keep a test in `backend/tests/unit/api/test_auth.py`:

```python
@pytest.mark.asyncio
async def test_lease_token_auth_ignores_requested_user_id(respx_mock):
    settings = Settings(auth_mode="lease_token", lease_base_url="http://lease.test")
    respx_mock.get("http://lease.test/app/info").respond(
        200,
        json={"data": {"id": 42, "nickname": "Lease User"}},
    )

    auth = await AuthResolver(settings).resolve(
        "Bearer valid-token",
        requested_user_id="frontend-spoof",
    )

    assert auth.user_id == "42"
    assert auth.display_name == "Lease User"
    assert auth.auth_mode == "lease_token"
```

- [ ] **Step 3: Require non-default operator token outside local**

In `backend/src/aptguide2/api/operator.py`, update `require_operator()`:

```python
    if settings.environment in {"staging", "production"} and settings.operator_dev_token == "operator-dev-token":
        raise HTTPException(status_code=500, detail="operator token is not configured")
```

Keep this before comparing the incoming token.

- [ ] **Step 4: Return 403 for disabled operator console**

In `backend/src/aptguide2/api/operator.py`, change disabled console behavior:

```python
    if not settings.operator_console_enabled:
        raise HTTPException(status_code=403, detail="operator console disabled")
```

- [ ] **Step 5: Test operator security boundaries**

Add to `backend/tests/unit/api/test_operator_api.py`:

```python
def test_operator_console_rejects_default_token_in_staging(monkeypatch, client):
    settings = Settings(environment="staging", operator_dev_token="operator-dev-token")
    monkeypatch.setattr("aptguide2.api.deps.get_settings", lambda: settings)

    response = client.get("/operator/tickets", headers={"X-Operator-Token": "operator-dev-token"})

    assert response.status_code == 500
    assert response.json()["detail"] == "operator token is not configured"


def test_operator_console_disabled_returns_403(monkeypatch, client):
    settings = Settings(operator_console_enabled=False)
    monkeypatch.setattr("aptguide2.api.deps.get_settings", lambda: settings)

    response = client.get("/operator/tickets", headers={"X-Operator-Token": "operator-dev-token"})

    assert response.status_code == 403
```

- [ ] **Step 6: Run auth/operator tests**

Run:

```bash
cd backend && uv run pytest tests/unit/api/test_auth.py tests/unit/api/test_operator_api.py -q
```

Expected: all selected tests pass.

---

### Task 4: Backend Observability And Error Classification

**Files:**
- Create: `backend/src/aptguide2/observability/__init__.py`
- Create: `backend/src/aptguide2/observability/events.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Modify: `backend/src/aptguide2/harness/orchestrator.py`
- Create: `backend/tests/unit/observability/test_events.py`
- Modify: `backend/tests/e2e/test_system_mainline.py`

- [ ] **Step 1: Add structured event helper**

Create `backend/src/aptguide2/observability/events.py`:

```python
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("aptguide2")


def emit_event(event: str, **fields: Any) -> dict[str, Any]:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload
```

- [ ] **Step 2: Test event helper payload**

Create `backend/tests/unit/observability/test_events.py`:

```python
from aptguide2.observability.events import emit_event


def test_emit_event_returns_structured_payload(caplog):
    payload = emit_event("chat.completed", request_id="r-1", trace_id="t-1", task="room_search")

    assert payload == {
        "event": "chat.completed",
        "request_id": "r-1",
        "trace_id": "t-1",
        "task": "room_search",
    }
    assert "chat.completed" in caplog.text
```

- [ ] **Step 3: Emit chat request lifecycle events**

In `backend/src/aptguide2/api/app.py`, import:

```python
from aptguide2.observability.events import emit_event
```

In `chat()`, emit:

```python
    emit_event(
        "chat.received",
        request_id=request_id,
        session_id=req.session_id,
        auth_mode=auth.auth_mode,
        message_len=len(req.message),
    )
```

After harness result:

```python
    emit_event(
        "chat.completed",
        request_id=request_id,
        trace_id=result.metadata.get("trace_id", ""),
        session_id=req.session_id,
        task=result.metadata.get("task", "fallback"),
        phase=result.phase,
        has_pending_action=result.pending_action is not None,
    )
```

- [ ] **Step 4: Emit harness stage summary events**

In `backend/src/aptguide2/harness/orchestrator.py`, import `emit_event` and emit after `trace = recorder.to_trace()`:

```python
        emit_event(
            "harness.completed",
            request_id=request.request_id,
            trace_id=trace.trace_id,
            session_id=request.session_id,
            task=decision.task,
            phase=result.phase,
            stage_count=len(trace.stages),
            card_count=len(result.cards),
            source_count=len(result.sources),
        )
```

- [ ] **Step 5: Assert `/chat` still returns request and trace IDs**

Add to `backend/tests/e2e/test_system_mainline.py`:

```python
def test_chat_response_includes_request_and_trace_ids(client):
    response = client.post("/chat", json={"message": "我想找一套一居室"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"].startswith("r-")
    assert payload["trace_id"].startswith("t-")
```

- [ ] **Step 6: Run observability verification**

Run:

```bash
cd backend && uv run pytest tests/unit/observability/test_events.py tests/e2e/test_system_mainline.py -q
```

Expected: selected tests pass and no response contract regression appears.

---

### Task 5: Frontend Chat UX Hardening

**Files:**
- Modify: `frontend/src/stores/chat.ts`
- Modify: `frontend/src/components/chat/ChatShell.vue`
- Modify: `frontend/src/components/chat/MessageComposer.vue`
- Modify: `frontend/src/components/chat/TracePanel.vue`
- Modify: `frontend/tests/chat-contract.test.ts`

- [ ] **Step 1: Add explicit error and retry state**

Extend state in `frontend/src/stores/chat.ts`:

```ts
error: null as string | null,
lastDraft: "" as string,
lastAction: undefined as Record<string, unknown> | undefined,
```

At the start of `send()`:

```ts
this.error = null;
this.lastDraft = message;
this.lastAction = action;
```

In the catch block:

```ts
} catch (error) {
  this.error = error instanceof Error ? error.message : "请求失败，请稍后重试";
  throw error;
} finally {
  this.loading = false;
}
```

Add:

```ts
async retryLast() {
  if (!this.lastDraft) return;
  await this.send(this.lastDraft, this.lastAction);
}
```

- [ ] **Step 2: Prevent duplicate sends while loading**

At the top of `send()`:

```ts
if (this.loading) return;
```

- [ ] **Step 3: Render chat error and retry controls**

In `frontend/src/components/chat/ChatShell.vue`, import the store:

```ts
import { useChatStore } from "../../stores/chat";

const chat = useChatStore();
```

Render inside `.chat-main` above `MessageComposer`:

```vue
<div v-if="chat.error" class="inline-error">
  <span>{{ chat.error }}</span>
  <button type="button" @click="chat.retryLast">重试</button>
</div>
```

- [ ] **Step 4: Keep trace panel user-facing but compact**

In `frontend/src/components/chat/TracePanel.vue`, ensure it shows `request_id`, `trace_id`, `task`, and `phase` from `latestResponse` when available. Keep full chain-of-thought absent; only show execution metadata.

- [ ] **Step 5: Expand chat contract test**

In `frontend/tests/chat-contract.test.ts`, assert the contract includes:

```ts
expect(response.request_id).toMatch(/^r-/);
expect(response.trace_id).toMatch(/^t-/);
expect(response.task).toBeTruthy();
expect(response.phase).toBeTruthy();
```

- [ ] **Step 6: Run frontend chat verification**

Run:

```bash
cd frontend && npm run test && npm run build
```

Expected: tests pass and production build succeeds.

---

### Task 6: Operator Console UX Hardening

**Files:**
- Modify: `frontend/src/api/operator.ts`
- Modify: `frontend/src/stores/operator.ts`
- Modify: `frontend/src/components/operator/OperatorConsole.vue`
- Modify: `frontend/src/components/operator/TicketList.vue`
- Modify: `frontend/src/components/operator/TicketDetail.vue`
- Modify: `frontend/src/components/operator/OperatorReplyBox.vue`
- Modify: `frontend/tests/operator-contract.test.ts`

- [ ] **Step 1: Allow operator ticket API filtering**

Update `frontend/src/api/operator.ts`:

```ts
export async function listTickets(status = "open"): Promise<HandoffTicket[]> {
  const response = await http.get<{ tickets: HandoffTicket[] }>("/operator/tickets", {
    headers,
    params: status === "all" ? {} : { status }
  });
  return response.data.tickets;
}
```

- [ ] **Step 2: Add operator error and status filter state**

Extend state in `frontend/src/stores/operator.ts`:

```ts
statusFilter: "open" as "open" | "closed" | "all",
error: null as string | null,
```

Update `refresh()`:

```ts
async refresh() {
  this.loading = true;
  this.error = null;
  try {
    this.tickets = await listTickets(this.statusFilter);
  } catch (error) {
    this.error = error instanceof Error ? error.message : "工单加载失败";
    throw error;
  } finally {
    this.loading = false;
  }
}
```

- [ ] **Step 2: Add filter action**

Add:

```ts
async setStatusFilter(status: "open" | "closed" | "all") {
  this.statusFilter = status;
  await this.refresh();
}
```

- [ ] **Step 4: Render operator loading/error/empty states**

In `frontend/src/components/operator/OperatorConsole.vue`, render:

```vue
<div v-if="store.error" class="inline-error">
  <span>{{ store.error }}</span>
  <button type="button" @click="store.refresh">重试</button>
</div>
<div v-else-if="store.loading" class="inline-status">正在加载工单...</div>
<div v-else-if="store.tickets.length === 0" class="inline-status">暂无工单</div>
```

- [ ] **Step 5: Add status filter controls**

In `frontend/src/components/operator/TicketList.vue`, add three controls:

```vue
<button type="button" @click="store.setStatusFilter('open')">未处理</button>
<button type="button" @click="store.setStatusFilter('closed')">已关闭</button>
<button type="button" @click="store.setStatusFilter('all')">全部</button>
```

- [ ] **Step 6: Harden reply box**

In `frontend/src/components/operator/OperatorReplyBox.vue`, disable submit when content is blank or the store is loading:

```vue
<button type="submit" :disabled="!content.trim() || store.loading">发送</button>
```

- [ ] **Step 7: Expand operator contract test**

In `frontend/tests/operator-contract.test.ts`, assert ticket fields used by the console:

```ts
expect(ticket.ticket_id).toBeTruthy();
expect(ticket.status).toMatch(/open|closed/);
expect(Array.isArray(ticket.messages)).toBe(true);
expect(ticket.created_at).toBeTruthy();
```

- [ ] **Step 8: Run frontend operator verification**

Run:

```bash
cd frontend && npm run test && npm run build
```

Expected: tests pass and production build succeeds.

---

### Task 7: Final Verification And Harness Documentation Sync

**Files:**
- Modify: `docs/tests/verification-log.md`
- Modify: `docs/plans/execution-log.md`
- Modify: `docs/plans/next-steps.md`
- Modify: `docs/system/feature-list.md`
- Modify: `.agent-state/last-checkpoint.json` through harness checkpoint command

- [ ] **Step 1: Run full backend test suite**

Run:

```bash
cd backend && uv run pytest tests/ -q
```

Expected: all backend tests pass. If pre-existing lint issues remain, record them separately and do not treat them as introduced by this plan unless touched files caused new lint failures.

- [ ] **Step 2: Run full frontend verification**

Run:

```bash
cd frontend && npm run test && npm run build
```

Expected: contract tests pass and production build succeeds.

- [ ] **Step 3: Run manual staging-readiness smoke checks**

Run with backend started:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Expected:

- `/health` returns `status=ok`.
- `/ready` includes `pipeline`, `auth_mode`, `mysql_config`, `redis_config`, `lease_config`, `milvus_config`, and `embedding_config`.

- [ ] **Step 4: Update verification log**

Append a new section to `docs/tests/verification-log.md`:

```markdown
## 2026-05-14 — Standalone Hardening And Observability

**Backend:** `cd backend && uv run pytest tests/ -q`
**Result:** record actual result

**Frontend:** `cd frontend && npm run test && npm run build`
**Result:** record actual result

**Smoke:** `/health`, `/ready`
**Result:** record actual result
```

- [ ] **Step 5: Update next steps**

Update `docs/plans/next-steps.md` so the immediate next item after this plan is staging deployment execution, not more standalone hardening.

- [ ] **Step 6: Create harness checkpoint**

Run:

```bash
python3 /home/chove/.codex/skills/agent-project-harness/scripts/project_harness.py checkpoint --project "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0" --task "standalone-hardening-observability"
```

Expected: new checkpoint appears under `docs/plans/checkpoints/` and `.agent-state/checkpoints/`.

---

## Acceptance Criteria

- `backend/.env.example` clearly separates local and staging/prod settings.
- `docs/system/standalone-deployment-runbook.md` exists and explains startup, verification, restart validation, and rollback.
- `/ready` returns a structured readiness report covering pipeline, auth, MySQL, Redis, lease, Milvus, and embedding configuration.
- Formal `lease_token` auth still ignores frontend-supplied `user_id`.
- Lease auth errors are normalized into controlled unauthorized responses.
- Operator console cannot run in staging/production with the default development token.
- Chat responses continue to include `request_id` and `trace_id`.
- Backend emits structured events for chat and harness completion.
- Chat UI has loading, error, retry, and trace metadata states.
- Operator UI has loading, error, empty, status-filter, reply, close, and refresh states.
- Backend test suite passes.
- Frontend contract tests and production build pass.
- Harness docs and state reflect this plan's completion after execution.

## Rollback Notes

- Runtime config changes can be rolled back by restoring previous `APTGUIDE_*` environment values.
- `/ready` is additive; removing it should not affect `/chat`.
- Structured logs are additive and can be disabled through `APTGUIDE_STRUCTURED_LOGS_ENABLED=false` if needed.
- Frontend UX hardening is client-side only; backend contracts remain backward compatible.
- This plan does not modify RAG quality logic or platform integration paths, so rollback should not affect RAG v2 internals or `rentHouseH5`.

## Self-Review

- Spec coverage: covers deployment/runtime stability, security/permissions, frontend UX, and observability.
- Explicit exclusions: RAG quality optimization and full platform integration are listed as non-goals.
- Placeholder scan: no implementation step depends on unspecified work.
- Type consistency: fields and paths match current backend/frontend structure.
