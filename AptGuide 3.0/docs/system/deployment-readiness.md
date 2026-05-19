# Deployment Readiness

This document lists deployment requirements, external dependencies, operational risks, and a pre-deployment checklist for AptGuide 3.0.

---

## Required Runtime Environment Variables

All variables use the `APTGUIDE3_` prefix. See `backend/.env.example` for the full template.

### Service Identity

| Variable | Default | Notes |
|----------|---------|-------|
| `APTGUIDE3_ENVIRONMENT` | `local` | Set to `production` |
| `APTGUIDE3_SERVICE_NAME` | `aptguide3` | Used in health response |

### Authentication

| Variable | Default | Notes |
|----------|---------|-------|
| `APTGUIDE3_AUTH_MODE` | `dev` | Must be `internal_header` in production |
| `APTGUIDE3_INTERNAL_TOKEN` | (empty) | Shared secret with lease gateway |
| `APTGUIDE3_INTERNAL_TOKEN_REQUIRED` | `false` | Must be `true` in production |

### MySQL

| Variable | Default | Notes |
|----------|---------|-------|
| `APTGUIDE3_MYSQL_DSN` | `mysql+asyncmy://root:change-me@localhost:3306/aptguide3` | Async MySQL connection |

### Redis

| Variable | Default | Notes |
|----------|---------|-------|
| `APTGUIDE3_REDIS_URL` | (empty) | `redis://host:port/db` |
| `APTGUIDE3_REDIS_KEY_PREFIX` | `aptguide3` | Namespace prefix for all keys |
| `APTGUIDE3_SESSION_TTL_SECONDS` | `86400` | 24 hours |
| `APTGUIDE3_PENDING_ACTION_TTL_SECONDS` | `300` | 5 minutes |

### Lease Gateway

| Variable | Default | Notes |
|----------|---------|-------|
| `APTGUIDE3_LEASE_BASE_URL` | `http://localhost:8081` | Lease service URL |
| `APTGUIDE3_LEASE_TIMEOUT_SECONDS` | `5.0` | HTTP timeout for lease calls |

### Vector DB

| Variable | Default | Notes |
|----------|---------|-------|
| `APTGUIDE3_VECTOR_URI` | `http://localhost:19530` | Milvus endpoint |

### LLM

| Variable | Default | Notes |
|----------|---------|-------|
| `APTGUIDE3_LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | DashScope-compatible endpoint |
| `APTGUIDE3_LLM_API_KEY` | (empty) | Required for understanding/routing |
| `APTGUIDE3_LLM_MODEL` | `qwen-turbo-latest` | Model name |

### Embedding

| Variable | Default | Notes |
|----------|---------|-------|
| `APTGUIDE3_EMBEDDING_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `APTGUIDE3_EMBEDDING_API_KEY` | (empty) | Required for KB-QA procedure |
| `APTGUIDE3_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model name |

### CORS

| Variable | Default | Notes |
|----------|---------|-------|
| `APTGUIDE3_CORS_ALLOW_ORIGINS` | `http://localhost:5173` | Comma-separated origins |

---

## External Service Dependencies

| Dependency | Health Check | Timeout | Failure Impact |
|-----------|-------------|---------|----------------|
| MySQL 8.0 | `mysqladmin ping` | 2s (readiness) | Service cannot start; no persistence |
| Redis 7+ | `redis-cli ping` | 2s (readiness) | No session cache; no pending-action TTL |
| Lease service | `GET /health` (assumed) | 5s | Room search, appointment, lease procedures fail |
| Milvus | gRPC health | 2s (readiness) | KB-QA vector search unavailable; service degrades |
| LLM API | (no active check) | Per-request | Understanding falls back to clarification-only |
| Embedding API | (no active check) | Per-request | KB-QA unavailable; other procedures unaffected |

### Health Check Endpoints

AptGuide 3.0 exposes:

- `GET /health` -- always returns `{"service": "aptguide3", "status": "ok"}` if the process is running.
- `GET /ready` -- checks configuration completeness for all required dependencies. Returns `{"ready": bool, "checks": [...]}`.

Note: `/ready` checks config presence by default. Append `?live=true` for async live connectivity probes (MySQL SELECT 1, Redis PING, lease health, Milvus list_collections).

---

## Operational Risks

### Retry Strategy

- **LLM calls**: No automatic retry in the current implementation. A single LLM failure returns a clarification prompt to the user. The caller (lease gateway / frontend) may retry.
- **Lease client calls**: No automatic retry. `httpx.TimeoutException` propagates as a procedure failure.
- **MySQL/Redis**: No automatic retry at the repository level. Connection pool handles transient failures internally via asyncmy/redis.asyncio.

**Risk**: Transient LLM or lease failures are not retried, which may cause user-visible errors during brief outages.

### Idempotency

- Chat requests are keyed by `session_id` + `message` but there is no deduplication layer. Re-submitting the same message creates a new message record.
- Pending actions use a unique `pending_action_id`; re-creating with the same ID would fail on primary key conflict.
- No request-level idempotency key is enforced at the API boundary.

**Risk**: Duplicate requests from frontend retries can create duplicate message records and duplicate procedure runs.

### Data Retention

- Session TTL in Redis: 24 hours (configurable via `APTGUIDE3_SESSION_TTL_SECONDS`).
- Pending action TTL in Redis: 5 minutes (configurable via `APTGUIDE3_PENDING_ACTION_TTL_SECONDS`).
- MySQL records (messages, sessions, trace events, audit log): no automatic expiration or cleanup job exists.
- No data retention policy is enforced. Tables will grow indefinitely.

**Risk**: Without a cleanup job, MySQL tables will grow unbounded. A retention policy and periodic purge job are needed before production scale.

### Audit Logging

- An `aptguide3_audit_log` table exists in the schema but no code currently writes to it.
- Trace events are written to `aptguide3_trace_events` via `RepositoryTraceSink` when MySQL is active.
- Procedure runs are logged to `aptguide3_procedure_runs`.

**Risk**: The audit log table is unused. Critical security events (auth failures, permission denials) are not audited.

### Alerting

- No alerting, metrics, or monitoring hooks are implemented.
- No Prometheus metrics endpoint exists.
- No structured logging format is enforced (console output only via `ConsoleTraceSink`).

**Risk**: Production incidents will be invisible without external monitoring. An operator must set up process-level monitoring (restart on crash, alert on high error rate) externally.

### Secret Handling

- All secrets are read from environment variables via pydantic-settings.
- Secrets use `SecretStr` to prevent accidental logging of API keys.
- The `.env` file is used for local development; it must not be committed to version control.
- `internal_token` is a `SecretStr` field.

**Risk**: No secret rotation mechanism exists. If a secret is compromised, it must be manually replaced in the environment and the service restarted.

### Connection Pooling

- MySQL uses asyncmy's default connection pool.
- Redis uses redis.asyncio's default connection pool.
- No explicit pool size tuning is configured.

**Risk**: Under high concurrency, default pool sizes may be insufficient. Pool exhaustion would manifest as request timeouts.

---

## Pre-Deployment Checklist

### Infrastructure

- [ ] MySQL 8.0 provisioned and accessible from the service
- [ ] Redis 7+ provisioned and accessible from the service
- [ ] Schema applied from `backend/src/aptguide3/database/schema.sql`
- [ ] Milvus instance provisioned (or vector search deliberately disabled)
- [ ] Network connectivity verified to all external services

### Configuration

- [ ] All required env vars set (see table above)
- [ ] `APTGUIDE3_AUTH_MODE=internal_header`
- [ ] `APTGUIDE3_INTERNAL_TOKEN_REQUIRED=true`
- [ ] `APTGUIDE3_INTERNAL_TOKEN` matches the value configured in the lease gateway
- [ ] `APTGUIDE3_CORS_ALLOW_ORIGINS` restricted to production frontend origins
- [ ] No `.env` file with real secrets deployed to production containers

### Verification

- [ ] `GET /health` returns 200
- [ ] `GET /ready` returns `ready: true`
- [ ] `POST /chat` succeeds with valid internal-header auth
- [ ] `POST /chat` is rejected without `X-Internal-Token` / `X-User-Id`
- [ ] Messages are persisted in `aptguide3_messages` after a chat
- [ ] Trace events are written to `aptguide3_trace_events`
- [ ] Lease gateway can successfully call AptGuide 3.0 end-to-end

### Operational

- [ ] Process supervisor or container orchestrator configured to restart on crash
- [ ] Log collection configured (stdout/stderr capture)
- [ ] External health check monitoring configured against `/health`
- [ ] MySQL backup strategy in place
- [ ] Redis persistence strategy decided (RDB, AOF, or accept ephemeral sessions)

---

## Known Limitations and Skipped Verifications

1. ~~**No live MySQL/Redis verification**~~ RESOLVED: Live MySQL schema/repos and Redis state store tests passed on 2026-05-15. Schema applied to live database.

2. ~~**No live lease gateway contract**~~ RESOLVED: Internal-header auth mode tested with 6 live integration tests on 2026-05-15.

3. ~~**No live Milvus verification**~~ RESOLVED: Milvus connectivity verified via live vector test. Collection data sync (room vectors, KB vectors) still pending.

4. ~~**No live LLM/embedding verification**~~ RESOLVED: LLM and embedding live tests passed on 2026-05-15.

5. ~~**In-memory session repo in deps.py**~~ RESOLVED: `_build_repos()` dispatcher supports memory/mysql/hybrid modes. `RepoBundle` wires all 8 repo types.

6. **Sync bridge in ChatService**: Persistence calls use sync-to-async bridge pattern. Live MySQL persistence works with SQLAlchemy `NullPool`, but should be reviewed for fully async production design.

7. ~~**No audit log writes**~~ RESOLVED: Appointment, lease, and handoff procedures write audit events.

8. **No data retention job**: No cron job or background task cleans up old records. Tables will grow indefinitely.

9. **No rate limiting**: No per-user or per-session rate limiting exists at the API layer.

10. ~~**Readiness checks are config-only**~~ RESOLVED: `GET /ready?live=true` runs async live connectivity probes (MySQL SELECT 1, Redis PING, lease health, Milvus list_collections).

11. **No retry strategy**: No automatic retry on LLM or lease client transient failures.

12. **No request-level idempotency**: Duplicate frontend retries can create duplicate message/procedure records.

13. **No alerting or metrics**: No Prometheus metrics endpoint, no structured logging, no alerting hooks.

14. **No secret rotation**: Compromised secrets require manual env update and restart.

15. **Milvus collection data missing**: Room vectors and KB vectors need to be synced via `scripts/sync_room_vectors.py` and `scripts/sync_kb_vectors.py` before RAG evaluation can pass.
