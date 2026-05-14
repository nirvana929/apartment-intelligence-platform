# Handoff

## Status: COMPLETED (Standalone Hardening) — Next: Staging Deployment

Standalone hardening and observability is complete: 386 backend tests + 5 frontend tests passed, build succeeded. See verification log: `docs/tests/verification-log.md`

## Goal (Achieved)

The standalone AptGuide 2.0 is staging-ready:

- `backend/.env.example` separates local and staging/prod settings
- `/ready` returns structured dependency report (pipeline, auth, mysql, redis, lease, milvus, embedding)
- Auth failures normalized; operator console rejects default token in staging/prod
- Backend emits structured events (chat.received, chat.completed, harness.completed)
- Chat UI has error/retry/trace states
- Operator UI has loading/error/empty/filter states

## Next Execution Goal

Staging deployment execution:

- Deploy Redis + MySQL schema (`persistence/schema.sql`) to staging
- Configure `AUTH_MODE=lease_token`
- Build frontend for production (`npm run build` + nginx)
- End-to-end integration test with live lease backend

## Verification Commands

```bash
cd "AptGuide 2.0/backend" && uv run pytest tests/ -q
cd "AptGuide 2.0/frontend" && npm run test && npm run build
curl http://localhost:8000/health
curl http://localhost:8000/ready
```
