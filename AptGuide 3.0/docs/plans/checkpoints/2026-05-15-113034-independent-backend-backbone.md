# Checkpoint: independent-backend-backbone

## Metadata

- Created at: 2026-05-15T11:30:34+08:00
- Task: independent-backend-backbone
- Status: complete
- Test status: 55 passed, 2 skipped

## Goal

Milestone 1: Independent Backend Backbone — turn the runnable AptGuide 3.0 scaffold into an independently verifiable backend service with durable Agent-state persistence, auth boundary, and readiness checks.

## Context

Plan: `docs/plans/2026-05-15-aptguide3-independent-backend-backbone-plan.md`
Baseline: 36 tests (Milestone 0 scaffold)
Final: 55 tests (+19 new)

## Completed Work

- Task 1: Documentation sync — known-issues, eval-report, execution-log, feature-list, sprint-plan updated
- Task 2: Settings and dependencies — sqlalchemy, asyncmy, redis added; 11 new config fields
- Task 3: Auth boundary — AuthContext + AuthResolver (dev + internal_header modes), 3 tests
- Task 4: Database schema and models — 11 SQLAlchemy models, schema.sql, database.py factory, 2 tests
- Task 5: Repository contracts — 8 Protocol classes (session, message, pending_action, memory, handoff, trace, procedure_run, audit), 1 test
- Task 6: Redis hot-state store — RedisStateStore with session/pending TTL, 4 tests
- Task 7: MySQL repository implementations — 8 MySQL repo classes, 1 test
- Task 8: ChatService persistence — optional message_repo/procedure_run_repo wiring, 2 tests
- Task 9: Durable trace sink — RepositoryTraceSink adapting TraceEvent to TraceRepository, 2 tests
- Task 10: Readiness endpoint — build_readiness_report + /ready route, 3 tests
- Task 11: Full verification — pytest + ruff pass

## Files Changed

### Created (18 files)
- `backend/src/aptguide3/api/auth.py`
- `backend/src/aptguide3/api/readiness.py`
- `backend/src/aptguide3/database/__init__.py`
- `backend/src/aptguide3/database/schema.sql`
- `backend/src/aptguide3/database/models.py`
- `backend/src/aptguide3/database/database.py`
- `backend/src/aptguide3/persistence/contracts.py`
- `backend/src/aptguide3/persistence/redis_store.py`
- `backend/src/aptguide3/persistence/mysql_repos.py`
- `backend/src/aptguide3/observability/repository_sink.py`
- `backend/tests/unit/api/__init__.py`
- `backend/tests/unit/api/test_auth.py`
- `backend/tests/unit/api/test_readiness.py`
- `backend/tests/unit/database/__init__.py`
- `backend/tests/unit/database/test_models.py`
- `backend/tests/unit/persistence/test_contracts.py`
- `backend/tests/unit/persistence/test_redis_store.py`
- `backend/tests/unit/persistence/test_mysql_repos.py`
- `backend/tests/unit/application/test_chat_persistence.py`
- `backend/tests/unit/observability/__init__.py`
- `backend/tests/unit/observability/test_repository_sink.py`

### Modified (5 files)
- `backend/pyproject.toml` — added asyncmy, redis, sqlalchemy, pytest-asyncio
- `backend/.env.example` — added auth, mysql, redis, cors, readiness docs
- `backend/src/aptguide3/config.py` — 11 new settings fields + parsed_cors_origins property
- `backend/src/aptguide3/api/app.py` — CORS from settings, /ready route
- `backend/src/aptguide3/api/deps.py` — message_repo/procedure_run_repo params
- `backend/src/aptguide3/application/chat_service.py` — optional message persistence

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| _No errors._ | All tasks completed cleanly. | | | |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `uv run pytest -q` | 55 passed, 2 skipped | test_real_llm.py skipped (no API key) |
| `uv run ruff check src tests` | All checks passed | |

## Known Issues

- Real MySQL/Redis/lease/Milvus/LLM dependency verification has not run.
- Auth boundary is wired but not integration-tested with lease internal headers.
- ChatService persistence uses sync bridge (asyncio.get_running_loop) — works but should be reviewed for production.

## Next Steps

1. Wire Redis for session persistence (replace InMemorySessionRepo in deps.py when Redis is available)
2. Wire MySQL for durable state (replace in-memory repos when MySQL is available)
3. Integration test with real MySQL + Redis
4. Integration through `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`
5. Production operator flow and deployment hardening

## Outcome Notes

Milestone 1 completed with 55 tests (+19 from baseline) in a single parallel execution session. All 11 tasks executed across 5 parallel waves. The backend now has independently verifiable persistence contracts, auth boundary, and readiness checks — ready for live dependency integration.
