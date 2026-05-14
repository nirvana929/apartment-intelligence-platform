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
