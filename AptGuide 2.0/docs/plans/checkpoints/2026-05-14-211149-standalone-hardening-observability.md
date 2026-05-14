# Checkpoint: standalone-hardening-observability

## Metadata

- Created at: 2026-05-14T21:11:49+08:00
- Task: standalone-hardening-observability
- Status: completed
- Test status: passed

## Goal

Turn the standalone AptGuide 2.0 MVP into a staging-ready independent product with stronger runtime stability, security boundaries, frontend operational UX, and production-grade troubleshooting signals.

## Context

Plan: `docs/plans/2026-05-14-aptguide2-standalone-hardening-observability-agent-plan.md`
Previous state: 376 backend tests + 2 frontend tests (RAG v2 full replacement complete)

## Completed Work

- Task 1: Deployment config (environment, cors_allow_origins, log_level) + .env.example reorganization + deployment runbook
- Task 2: DependencyCheck category field, 7 readiness checks, /ready endpoint, ReadinessResponse schema
- Task 3: Auth httpx error normalization, operator default token rejection in staging/prod, disabled console returns 403
- Task 4: observability/events.py emit_event(), chat.received/chat.completed/harness.completed events, trace_id bug fix
- Task 5: Chat store error/retry/duplicate-send state, ChatShell error banner, TracePanel trace_id display
- Task 6: Operator status filter, error state, loading/empty/error UI, reply box loading guard

## Files Changed

**Backend (modified):**
- `backend/src/aptguide2/core/config.py` — deployment + observability settings, parsed_cors_origins
- `backend/src/aptguide2/api/app.py` — /ready endpoint, CORS, emit_event calls
- `backend/src/aptguide2/api/schemas.py` — ReadinessResponse
- `backend/src/aptguide2/api/auth.py` — httpx error normalization
- `backend/src/aptguide2/api/operator.py` — default token guard, 403 for disabled
- `backend/src/aptguide2/system/readiness.py` — category field, 7 checks
- `backend/src/aptguide2/harness/orchestrator.py` — harness.completed event
- `backend/.env.example` — reorganized with staging example

**Backend (created):**
- `backend/src/aptguide2/observability/__init__.py`
- `backend/src/aptguide2/observability/events.py`
- `backend/tests/unit/observability/__init__.py`
- `backend/tests/unit/observability/test_events.py`

**Backend (tests modified):**
- `backend/tests/unit/system/test_readiness.py`
- `backend/tests/e2e/test_system_mainline.py`
- `backend/tests/unit/api/test_auth.py`
- `backend/tests/unit/api/test_operator_api.py`

**Frontend (modified):**
- `frontend/src/stores/chat.ts` — error/lastDraft/lastAction, retryLast()
- `frontend/src/components/chat/ChatShell.vue` — error banner
- `frontend/src/components/chat/TracePanel.vue` — trace_id display
- `frontend/src/stores/operator.ts` — statusFilter, error, setStatusFilter()
- `frontend/src/components/operator/OperatorConsole.vue` — loading/error/empty
- `frontend/src/components/operator/TicketList.vue` — filter buttons
- `frontend/src/components/operator/OperatorReplyBox.vue` — loading guard
- `frontend/src/types/operator.ts` — created_at field
- `frontend/src/api/operator.ts` — status filtering
- `frontend/tests/chat-contract.test.ts`
- `frontend/tests/operator-contract.test.ts`

**Docs (created):**
- `docs/system/standalone-deployment-runbook.md`

## Errors And Failures

| Time | Symptom | Root Cause | Fix / Decision | Status |
| --- | --- | --- | --- | --- |
| — | trace_id empty in chat response | `_build_response_from_harness` read trace_id from metadata dict, but composer puts it on AptGuideResponse.trace_id directly | Task 4 agent fixed to use result.trace_id | resolved |

## Verification

| Command | Result | Evidence |
| --- | --- | --- |
| `cd backend && uv run pytest tests/ -q` | 386 passed, 3 warnings | All tests green |
| `cd frontend && npm run test && npm run build` | 5 tests passed, build succeeded | vitest + vite build output |

## Known Issues

- 3 pre-existing RuntimeWarning about unawaited coroutines in lease_tools.py (not introduced by this work)
- 15 pre-existing E402 lint issues (not introduced by this work)

## Next Steps

- Staging deployment execution: deploy Redis + MySQL schema, configure lease_token auth, build frontend for production, e2e integration test

## Outcome Notes

- 7 tasks completed in parallel using 5 background agents + 1 sequential task
- Total test count: 386 backend + 5 frontend = 391 tests
- Structured observability events now cover full chat lifecycle
- Security boundaries enforce non-default tokens in staging/prod
