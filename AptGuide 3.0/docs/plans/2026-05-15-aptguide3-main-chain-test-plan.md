# AptGuide 3.0 Main-System Chain Test Plan

**Goal:** Verify the full request chain `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat` works end-to-end with internal-header auth and MySQL/Redis persistence.

---

## Prerequisites

- MySQL running on `127.0.0.1:3306` with database `least` and the AptGuide 3.0 schema applied.
- Redis running on `127.0.0.1:6379`.
- A shared internal token agreed between lease-web-app and AptGuide 3.0 (referred to as `<shared-token>` below).
- A test user exists in the lease database with a known user ID (e.g. `1`) and a valid JWT.

---

## Step 1: Start AptGuide 3.0

From `AptGuide 3.0/backend`:

```bash
APTGUIDE3_AUTH_MODE=internal_header \
APTGUIDE3_INTERNAL_TOKEN=<shared-token> \
APTGUIDE3_INTERNAL_TOKEN_REQUIRED=true \
APTGUIDE3_PERSISTENCE_MODE=mysql \
APTGUIDE3_MYSQL_DSN=mysql+asyncmy://chove:123456@127.0.0.1:3306/least \
APTGUIDE3_REDIS_URL=redis://127.0.0.1:6379/3 \
uv run uvicorn aptguide3.api.app:app --host 0.0.0.0 --port 8100
```

Verify it is up:

```bash
curl http://127.0.0.1:8100/ready
```

Expected: HTTP 200 with all checks green (MySQL, Redis, auth mode = internal_header).

---

## Step 2: Start lease-web-app

Configure lease-web-app environment:

```bash
APTGUIDE_URL=http://host.docker.internal:8100
```

`host.docker.internal` resolves to the host machine from inside Docker. If lease runs natively, use `http://127.0.0.1:8100` instead.

---

## Step 3: Expected Request Flow

```
rentHouseH5 (browser)
    |
    | POST /app/ai/chat  { message, session_id }  + JWT cookie/header
    v
lease-web-app  (/app/ai/chat)
    |
    | 1. Validate JWT, extract user_id
    | 2. POST /api/chat to AptGuide 3.0
    |    Headers:
    |      X-Internal-Token: <shared-token>
    |      X-User-Id: <from JWT>
    |      X-Request-Id: <uuid>
    |    Body: { "message": "...", "session_id": "..." }
    v
AptGuide 3.0  (/api/chat)
    |
    | 1. Validate X-Internal-Token
    | 2. Extract X-User-Id (trusted from lease, not body)
    | 3. Run Agent: understand -> route -> procedure -> respond
    | 4. Persist messages + session to MySQL, session state to Redis
    | 5. Return { message, phase, cards, actions, metadata }
    v
lease-web-app
    |
    | Forward response to rentHouseH5
    v
rentHouseH5 (browser)
```

---

## Step 4: Manual Smoke Test

### 4a. Direct AptGuide 3.0 call (skip lease, verify AptGuide alone)

```bash
curl -X POST http://127.0.0.1:8100/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Internal-Token: <shared-token>" \
  -H "X-User-Id: 1" \
  -H "X-Request-Id: smoke-req-001" \
  -d '{"message": "你好", "session_id": "smoke-session-001"}'
```

Expected: HTTP 200, body contains `message`, `phase`, `cards`, `actions`, `metadata`.

### 4b. Full chain via lease (requires JWT)

```bash
# Acquire JWT from lease auth endpoint first
TOKEN=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' | jq -r '.token')

# Send chat through lease
curl -X POST http://localhost:8080/app/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "你好", "session_id": "chain-session-001"}'
```

Expected: HTTP 200, same response shape as 4a.

---

## Blockers

### Blocker 1: lease JWT Test User Setup

The full chain (4b) requires a valid JWT from lease. If the lease test database does not contain a test user, or the auth endpoint is not available, this step cannot run.

**Workaround:** Run 4a (direct AptGuide call) to verify AptGuide 3.0 independently. The skip-safe smoke test (`test_lease_gateway_chain.py`) covers exactly this path.

### Blocker 2: lease-web-app Configuration

lease-web-app must be configured to forward to AptGuide 3.0 at the correct URL and include the internal headers. If lease does not yet have this wiring, the full chain cannot be tested.

**Workaround:** Verify AptGuide 3.0 independently via 4a and the automated smoke test.

---

## Automated Smoke Test

A skip-safe pytest is provided at:

```
backend/tests/integration/test_lease_gateway_chain.py
```

It is skipped unless `APTGUIDE3_GATEWAY_TEST=1` is set. When enabled, it sends a direct POST to `http://127.0.0.1:8100/api/chat` with internal headers and verifies a 200 response with the expected `message` field.

Run:

```bash
APTGUIDE3_GATEWAY_TEST=1 \
APTGUIDE3_INTERNAL_TOKEN=<shared-token> \
uv run pytest tests/integration/test_lease_gateway_chain.py -v
```

---

## Verification Checklist

- [ ] AptGuide 3.0 starts on port 8100 with internal-header auth.
- [ ] `/ready` returns 200 with MySQL and Redis green.
- [ ] Direct POST to `/api/chat` with internal headers returns 200.
- [ ] Response contains `message`, `phase`, `cards`, `actions`, `metadata`.
- [ ] Messages are persisted in `aptguide3_messages` table.
- [ ] Session is persisted in `aptguide3_sessions` table.
- [ ] lease-web-app forwards requests with correct headers (if lease is available).
- [ ] Full chain from lease to AptGuide returns 200 (if JWT setup is available).
- [ ] `uv run ruff check tests/integration/test_lease_gateway_chain.py` passes.
