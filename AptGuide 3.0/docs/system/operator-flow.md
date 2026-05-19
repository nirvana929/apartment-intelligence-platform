# Operator Workflow

This document defines the minimum operator workflow for starting, verifying, and testing AptGuide 3.0.

---

## 1. Start the Service (Dev Mode)

Dev mode uses in-memory persistence, a fake user identity, and no external dependencies beyond the LLM API.

```bash
cd "AptGuide 3.0/backend"

# Copy env template and fill in at minimum the LLM API key
cp .env.example .env

# Start with uvicorn
uv run uvicorn aptguide3.api.app:app --reload --host 0.0.0.0 --port 8000
```

Minimum `.env` for dev mode:

```
APTGUIDE3_ENVIRONMENT=local
APTGUIDE3_AUTH_MODE=dev
APTGUIDE3_LLM_API_KEY=<your-dashscope-key>
```

The service starts on `http://localhost:8000`. The `/health` endpoint returns immediately. The `/ready` endpoint checks configuration completeness.

---

## 2. Start with Live MySQL/Redis

### 2a. Start local infrastructure

```bash
cd "AptGuide 3.0/backend"
docker compose -f docker-compose.local.yml up -d
```

This starts MySQL 8.0 on port 3306 and Redis 7 on port 6379.

### 2b. Apply the database schema

The schema file is at `backend/src/aptguide3/database/schema.sql`. Apply it to the running MySQL instance:

```bash
mysql -h 127.0.0.1 -u root -pchange-me aptguide3 < src/aptguide3/database/schema.sql
```

Or if using the Docker MySQL container:

```bash
docker exec -i aptguide3-mysql mysql -uroot -pchange-me aptguide3 < src/aptguide3/database/schema.sql
```

### 2c. Configure for live services

Update `.env`:

```
APTGUIDE3_MYSQL_DSN=mysql+asyncmy://root:change-me@127.0.0.1:3306/aptguide3
APTGUIDE3_REDIS_URL=redis://127.0.0.1:6379/3
APTGUIDE3_LEASE_BASE_URL=http://localhost:8081
APTGUIDE3_VECTOR_URI=http://localhost:19530
```

### 2d. Start the service

```bash
uv run uvicorn aptguide3.api.app:app --reload --host 0.0.0.0 --port 8000
```

---

## 3. Verify Readiness

```bash
curl -s http://localhost:8000/ready | python -m json.tool
```

Expected response when all config is present:

```json
{
  "ready": true,
  "checks": [
    {"name": "mysql_config", "ok": true, "required": true},
    {"name": "redis_config", "ok": true, "required": true},
    {"name": "lease_config", "ok": true, "required": true},
    {"name": "vector_config", "ok": true, "required": true},
    {"name": "llm_config", "ok": true, "required": false},
    {"name": "embedding_config", "ok": true, "required": false}
  ]
}
```

`ready: true` means all **required** checks pass. LLM and embedding are optional -- the service degrades to clarification-only if they are absent.

---

## 4. Test the Chat Endpoint

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "hello",
    "session_id": "test-session-001",
    "user_id": "test-user-001"
  }' | python -m json.tool
```

Expected response shape:

```json
{
  "message": "...",
  "phase": "...",
  "cards": [],
  "actions": [],
  "pending_action": null,
  "metadata": {}
}
```

---

## 5. Verify Auth Modes

### Dev mode (default)

`APTGUIDE3_AUTH_MODE=dev` -- any request is accepted. `user_id` from the body is used, falling back to `APTGUIDE3_DEV_USER_ID`.

### Internal header mode (production)

`APTGUIDE3_AUTH_MODE=internal_header` -- requires these headers from the lease gateway:

| Header | Required | Description |
|--------|----------|-------------|
| `X-Internal-Token` | Yes, if `APTGUIDE3_INTERNAL_TOKEN_REQUIRED=true` | Shared secret from lease |
| `X-User-Id` | Yes | User identity from lease's auth system |
| `X-Request-Id` | No | Correlation ID for tracing |

Test rejection without headers:

```bash
# Should fail with 403
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test","session_id":"s1"}'
```

Test with valid headers:

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Internal-Token: <your-token>" \
  -H "X-User-Id: real-user-123" \
  -H "X-Request-Id: req-abc-001" \
  -d '{"message":"test","session_id":"s1"}'
```

---

## 6. Minimum Env Vars for Production

| Variable | Required | Description |
|----------|----------|-------------|
| `APTGUIDE3_ENVIRONMENT` | Yes | Set to `production` |
| `APTGUIDE3_AUTH_MODE` | Yes | Set to `internal_header` |
| `APTGUIDE3_INTERNAL_TOKEN` | Yes | Shared secret for lease gateway |
| `APTGUIDE3_INTERNAL_TOKEN_REQUIRED` | Yes | Set to `true` |
| `APTGUIDE3_MYSQL_DSN` | Yes | MySQL connection string |
| `APTGUIDE3_REDIS_URL` | Yes | Redis connection string |
| `APTGUIDE3_LEASE_BASE_URL` | Yes | Lease service base URL |
| `APTGUIDE3_VECTOR_URI` | Yes | Milvus/vector DB URI |
| `APTGUIDE3_LLM_BASE_URL` | Yes | LLM API base URL |
| `APTGUIDE3_LLM_API_KEY` | Yes | LLM API key |
| `APTGUIDE3_LLM_MODEL` | No | Defaults to `qwen-turbo-latest` |
| `APTGUIDE3_EMBEDDING_BASE_URL` | Yes | Embedding API base URL |
| `APTGUIDE3_EMBEDDING_API_KEY` | Yes | Embedding API key |
| `APTGUIDE3_EMBEDDING_MODEL` | No | Defaults to `text-embedding-3-small` |
| `APTGUIDE3_CORS_ALLOW_ORIGINS` | Yes | Comma-separated allowed origins |

---

## 7. Teardown

```bash
# Stop the service (Ctrl+C or kill the process)

# Stop local infrastructure
cd "AptGuide 3.0/backend"
docker compose -f docker-compose.local.yml down

# Remove volumes to wipe data
docker compose -f docker-compose.local.yml down -v
```
