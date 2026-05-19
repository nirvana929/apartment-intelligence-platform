# AptGuide 3.0 Frontend E2E and Live RAG Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify AptGuide 3.0 as an independent product loop through its own frontend, run live dependency checks and live RAG evaluation, then fix only non-RAG chain defects discovered during verification.

**Architecture:** The execution path is `AptGuide 3.0 frontend -> AptGuide 3.0 /chat -> ChatService -> procedures -> MySQL/Redis/Milvus/Embedding/LLM/lease tools`. The final platform chain `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0` is intentionally out of scope for this plan. RAG quality defects are reported with evidence but not optimized in this phase.

**Tech Stack:** FastAPI, static Vue 3 frontend, Python Playwright, pytest, MySQL, Redis, Milvus, OpenAI-compatible LLM/embedding APIs, lease internal tool API.

---

## Scope Boundary

In scope:

- AptGuide 3.0 built-in frontend: `frontend/index.html`, `frontend/app.js`, `frontend/style.css`.
- AptGuide 3.0 backend: `/health`, `/ready`, `/chat`.
- Browser-level testing with Playwright against the real page, not only curl.
- Live dependency verification.
- Live RAG evaluation reporting.
- Fixes for frontend/backend chain blockers that prevent verification.
- Harness documentation updates under `AptGuide 3.0`.

Out of scope:

- `rentHouseH5`.
- `lease /app/ai/chat` gateway chain.
- RAG ranking, prompt, retrieval, chunking, or dataset optimization.
- Production hardening items such as retry, idempotency, rate limiting, metrics, alerting, secret rotation, and data retention jobs.

## Files and Responsibilities

- `frontend/index.html`: Real browser test target; add stable attributes only if selectors are fragile.
- `frontend/app.js`: Chat UI request/response handling; fix only defects that block frontend E2E.
- `frontend/style.css`: Fix only layout defects found during browser verification.
- `backend/tests/e2e/test_frontend_chat_flow.py`: Playwright E2E tests for the real frontend page.
- `backend/tests/integration/test_*_live.py`: Existing live dependency checks.
- `backend/evals/datasets/rag_retrieval_cases.yaml`: Seed RAG eval dataset. Expand only if needed to make reporting meaningful; do not tune RAG behavior.
- `backend/evals/runners/run_rag_eval.py`: Eval runner. Upgrade from smoke-only to live-capable reporting if live retrieval results are available.
- `backend/evals/reports/rag-evaluation-report.md`: Generated RAG evaluation report.
- `docs/tests/verification-log.md`: Append exact verification commands and results.
- `docs/tests/evaluation-report.md`: Summarize frontend E2E and live RAG results.
- `docs/plans/current-plan.md`: Current plan pointer and active scope.
- `progress/current-plan.md`: Harness-facing active plan summary.
- `progress/known-issues.md`: Non-RAG chain defects to fix and RAG findings to report separately.
- `progress/next-steps.md`: Follow-up work after this plan.
- `reports/evaluation-report.md`: Harness-facing evaluation summary.

## Play 1: Harness and Runtime Baseline

**Purpose:** Ensure the default project is AptGuide 3.0 and the backend can be started in an independently testable mode.

- [ ] **Step 1: Confirm project harness default**

Run from repo root:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py status
```

Expected: `default_project_path` is `/home/chove/桌面/apartment-intelligence-platform/AptGuide 3.0`.

- [ ] **Step 2: Start or verify local infrastructure**

Run from `AptGuide 3.0/backend`:

```bash
docker compose -f docker-compose.local.yml up -d
```

Expected: MySQL, Redis, Milvus support services are running or already healthy.

- [ ] **Step 3: Apply schema when using local MySQL**

Run from `AptGuide 3.0/backend`:

```bash
APTGUIDE3_MYSQL_DSN=mysql+asyncmy://chove:123456@127.0.0.1:3306/least \
uv run python scripts/apply_schema.py
```

Expected: schema application completes without SQL errors.

- [ ] **Step 4: Start AptGuide 3.0 backend**

Run from `AptGuide 3.0/backend`:

```bash
APTGUIDE3_AUTH_MODE=dev \
APTGUIDE3_DEV_USER_ID=dev-user-001 \
APTGUIDE3_PERSISTENCE_MODE=hybrid \
APTGUIDE3_MYSQL_DSN=mysql+asyncmy://chove:123456@127.0.0.1:3306/least \
APTGUIDE3_REDIS_URL=redis://127.0.0.1:6379/3 \
uv run uvicorn aptguide3.api.app:app --host 127.0.0.1 --port 8100
```

Expected: backend serves `http://127.0.0.1:8100/`.

- [ ] **Step 5: Verify health and readiness**

Run:

```bash
curl -s http://127.0.0.1:8100/health
curl -s 'http://127.0.0.1:8100/ready?live=true'
```

Expected: `/health` returns `status: ok`; `/ready?live=true` reports live dependency status with clear pass/fail details.

## Play 2: Real Frontend Playwright E2E

**Purpose:** Test the real built-in frontend through Chromium. Curl is allowed only for diagnosis, not final frontend verification.

- [ ] **Step 1: Install Playwright dependency if missing**

Run from `AptGuide 3.0/backend`:

```bash
uv add --dev playwright
uv run playwright install chromium
```

Expected: `playwright` is added to the dev dependency group and Chromium is installed.

- [ ] **Step 2: Create the E2E test directory**

Create:

```text
backend/tests/e2e/test_frontend_chat_flow.py
```

- [ ] **Step 3: Add a page-load test**

Test behavior:

```python
def test_frontend_loads_without_console_errors(page):
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto("http://127.0.0.1:8100/")
    page.wait_for_load_state("networkidle")
    assert page.locator("text=AptGuide").first.is_visible()
    assert page.locator("input[placeholder='输入你的租房需求...']").is_visible()
    assert page.locator("button[type='submit']").is_visible()
    assert errors == []
```

Expected: page loads, chat input is visible, no browser console errors.

- [ ] **Step 4: Add a happy-path chat test**

Test behavior:

```python
def test_frontend_sends_message_and_renders_reply(page):
    page.goto("http://127.0.0.1:8100/")
    page.wait_for_load_state("networkidle")
    page.fill("input[placeholder='输入你的租房需求...']", "你好")
    page.click("button[type='submit']")
    page.wait_for_selector(".message.user .bubble")
    page.wait_for_selector(".message.assistant .bubble:not(.typing)", timeout=30000)
    assert page.locator(".message.user .bubble").last.inner_text()
    assert page.locator(".message.assistant .bubble:not(.typing)").last.inner_text()
```

Expected: user message and assistant message both render in the page.

- [ ] **Step 5: Add a network assertion test**

Test behavior:

```python
def test_frontend_posts_to_chat_endpoint(page):
    requests = []
    page.on("request", lambda req: requests.append(req.url) if req.method == "POST" else None)
    page.goto("http://127.0.0.1:8100/")
    page.fill("input[placeholder='输入你的租房需求...']", "找番禺1500以内安静一点的房子")
    page.click("button[type='submit']")
    page.wait_for_selector(".message.assistant .bubble:not(.typing)", timeout=45000)
    assert any(url.endswith("/chat") for url in requests)
```

Expected: the frontend performs a real POST to `/chat`.

- [ ] **Step 6: Add screenshot artifact capture on failure**

Use pytest failure handling or explicit debug output to write screenshots to:

```text
backend/evals/reports/frontend-e2e/
```

Expected: failed browser tests leave a screenshot and console/network notes.

- [ ] **Step 7: Run the E2E suite**

Run from `AptGuide 3.0/backend` while the backend is running:

```bash
uv run pytest tests/e2e/test_frontend_chat_flow.py -v
```

Expected: tests pass or fail with actionable browser evidence.

## Play 3: Live Dependency Verification

**Purpose:** Confirm the real services needed by the agent are available before business E2E and RAG eval.

- [ ] **Step 1: Run MySQL and Redis live tests**

Run from `AptGuide 3.0/backend`:

```bash
APTGUIDE3_MYSQL_DSN=mysql+asyncmy://chove:123456@127.0.0.1:3306/least \
APTGUIDE3_REDIS_URL=redis://127.0.0.1:6379/3 \
uv run pytest tests/integration/test_mysql_schema.py tests/integration/test_mysql_repos_live.py tests/integration/test_redis_state_store_live.py -q
```

Expected: live persistence tests pass, or failures identify schema/connection defects.

- [ ] **Step 2: Run LLM and embedding live tests**

Run from `AptGuide 3.0/backend` with real keys exported:

```bash
APTGUIDE3_LIVE_TESTS=1 \
APTGUIDE3_LLM_API_KEY="$APTGUIDE3_LLM_API_KEY" \
APTGUIDE3_EMBEDDING_API_KEY="$APTGUIDE3_EMBEDDING_API_KEY" \
uv run pytest tests/integration/test_llm_live.py tests/integration/test_embedding_live.py -q
```

Expected: LLM and embedding tests pass, or the report records missing credentials/upstream failures.

- [ ] **Step 3: Run Milvus/vector live tests**

Run:

```bash
APTGUIDE3_LIVE_TESTS=1 \
APTGUIDE3_VECTOR_URI=http://127.0.0.1:19530 \
APTGUIDE3_EMBEDDING_API_KEY="$APTGUIDE3_EMBEDDING_API_KEY" \
uv run pytest tests/integration/test_vector_live.py -q
```

Expected: vector tests pass or clearly identify Milvus collection/config issues.

- [ ] **Step 4: Run readiness and audit live tests**

Run:

```bash
APTGUIDE3_LIVE_TESTS=1 \
APTGUIDE3_MYSQL_DSN=mysql+asyncmy://chove:123456@127.0.0.1:3306/least \
APTGUIDE3_REDIS_URL=redis://127.0.0.1:6379/3 \
uv run pytest tests/integration/test_readiness_live.py tests/integration/test_trace_audit_live.py -q
```

Expected: `/ready` and trace/audit behavior match the current implementation. If not, fix chain truthfulness issues in Play 6.

## Play 4: Frontend Business Scenario E2E

**Purpose:** Use the built-in frontend to exercise user-visible business behavior.

- [ ] **Step 1: Run baseline chat scenario**

Input in the browser:

```text
你好
```

Expected: page shows a natural assistant reply and loading state clears.

- [ ] **Step 2: Run room-search scenario**

Input:

```text
找番禺1500以内安静一点的房子
```

Expected: page shows either validated room cards or a conservative fallback/clarification. It must not show raw unvalidated vector records.

- [ ] **Step 3: Run second room-search scenario**

Input:

```text
天河区近地铁2000以内的房子
```

Expected: page shows validated room cards or a clear fallback/clarification.

- [ ] **Step 4: Run KB high-risk scenario**

Input:

```text
押金不退怎么办
```

Expected: page does not make an unverified commitment. If source cards are available, they render as source cards, not raw JSON.

- [ ] **Step 5: Run KB medium-risk scenario**

Input:

```text
租金可以退款吗
```

Expected: page gives a conservative answer and cites source cards when retrieval confidence is sufficient.

- [ ] **Step 6: Run multi-turn slot-filling scenario**

Inputs in the same session:

```text
我想找房
预算1500以内
番禺，安静一点
```

Expected: the assistant preserves context and does not restart the conversation each turn.

- [ ] **Step 7: Run appointment confirmation scenario if lease tools are live**

Inputs:

```text
我想预约看这套房
确认预约
```

Expected: the first turn creates a pending action; the second turn executes only after confirmation. If lease tools are unavailable, record this scenario as blocked by live dependency status.

## Play 5: Live RAG Evaluation Report Only

**Purpose:** Run and report RAG quality. Do not optimize RAG behavior in this plan.

- [ ] **Step 1: Review seed dataset**

Open:

```text
backend/evals/datasets/rag_retrieval_cases.yaml
```

Expected: cases include room-search and KB QA examples with expected room/doc IDs or explicit safety expectations.

- [ ] **Step 2: Run current eval runner in smoke mode**

Run from `AptGuide 3.0/backend`:

```bash
uv run python evals/runners/run_rag_eval.py
```

Expected: report is generated and clearly says smoke metrics are N/A when live retrieval is not used.

- [ ] **Step 3: Run live RAG integration tests**

Run:

```bash
APTGUIDE3_LIVE_TESTS=1 \
APTGUIDE3_LLM_API_KEY="$APTGUIDE3_LLM_API_KEY" \
APTGUIDE3_EMBEDDING_API_KEY="$APTGUIDE3_EMBEDDING_API_KEY" \
APTGUIDE3_VECTOR_URI=http://127.0.0.1:19530 \
APTGUIDE3_LEASE_BASE_URL=http://127.0.0.1:8081 \
uv run pytest tests/integration/test_rag_live.py -v
```

Expected: live RAG smoke tests pass or produce concrete failures.

- [ ] **Step 4: If the runner is still smoke-only, add live-result reporting without tuning**

Acceptable implementation:

- The runner can call the existing ChatService or retrieval modules for each eval case.
- The runner records returned card IDs, source IDs, latency, and pass/fail.
- The runner computes available Hit@K/MRR/nDCG only when expected IDs exist.
- The runner records `N/A` when expected IDs are missing.
- The runner does not change retrieval, ranking, prompt, confidence gate, or chunking code.

Expected: `backend/evals/reports/rag-evaluation-report.md` distinguishes:

- live retrieval failures
- missing data/config failures
- low-quality retrieval findings
- dataset limitations

- [ ] **Step 5: Report RAG findings as findings, not fixes**

Record examples under:

```text
docs/tests/evaluation-report.md
reports/evaluation-report.md
progress/known-issues.md
```

Expected: RAG findings are clearly labeled `RAG evaluation finding - optimization deferred`.

## Play 6: Fix Non-RAG Chain Defects and Checkpoint

**Purpose:** Repair defects that block the frontend, live dependency, persistence, readiness, or reporting chain. Do not tune RAG behavior.

- [ ] **Step 1: Triage failures by category**

Use these categories:

```text
frontend-ui
frontend-network
backend-chat-contract
live-config
persistence
readiness
trace-audit
rag-eval-report-only
out-of-scope-rag-optimization
```

Expected: only the first seven categories are eligible for fixes in this plan.

- [ ] **Step 2: Fix frontend UI defects if found**

Allowed files:

```text
frontend/index.html
frontend/app.js
frontend/style.css
backend/tests/e2e/test_frontend_chat_flow.py
```

Expected: Playwright E2E passes after each fix.

- [ ] **Step 3: Fix backend chat contract defects if found**

Allowed files:

```text
backend/src/aptguide3/api/app.py
backend/src/aptguide3/api/schemas.py
backend/src/aptguide3/application/chat_service.py
backend/tests/unit/
backend/tests/integration/
```

Expected: `/chat` returns a stable shape consumed by the frontend.

- [ ] **Step 4: Fix live config/readiness/persistence/audit defects if found**

Allowed files:

```text
backend/src/aptguide3/config.py
backend/src/aptguide3/api/readiness.py
backend/src/aptguide3/persistence/
backend/src/aptguide3/observability/
backend/tests/integration/
```

Expected: live tests and `/ready?live=true` reflect the true runtime state.

- [ ] **Step 5: Run final verification batch**

Run from `AptGuide 3.0/backend`:

```bash
uv run pytest -q
uv run ruff check src tests
uv run pytest tests/e2e/test_frontend_chat_flow.py -v
```

Expected: unit/integration suite passes or skip reasons are explicit; frontend E2E passes against the running backend.

- [ ] **Step 6: Update harness documents**

Update:

```text
progress/current-plan.md
progress/known-issues.md
progress/next-steps.md
reports/evaluation-report.md
docs/tests/verification-log.md
docs/tests/evaluation-report.md
```

Expected: verification status never claims pass without command evidence.

- [ ] **Step 7: Create checkpoint**

Run from `AptGuide 3.0`:

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Expected: snapshot shows AptGuide 3.0 as the project and lists the final changed files.

## Exit Criteria

- AptGuide 3.0 default harness project is active.
- Built-in frontend opens in Chromium and sends real `/chat` requests.
- Frontend E2E covers page load, basic chat, network call, and at least one business scenario.
- Live dependency status is recorded with exact commands.
- Live RAG evaluation report exists; RAG quality issues are reported but not optimized.
- Non-RAG chain defects found during verification are fixed or documented as blockers.
- `docs/tests/verification-log.md`, `docs/tests/evaluation-report.md`, and `reports/evaluation-report.md` reflect the final evidence.
