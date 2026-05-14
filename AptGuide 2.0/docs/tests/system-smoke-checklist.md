# System Smoke Checklist

> 状态：active

## Purpose

Verify AptGuide 2.0 harness mainline against real or locally configured services.

## Preflight

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/unit/evals tests/unit/system tests/e2e -q
uv run python scripts/check_live_dependencies.py --report ../reports/live-dependency-readiness-report.md
```

## RAG v2 Live Eval

```bash
cd "AptGuide 2.0/backend"
uv run python evals/runners/run_rag_v2.py \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

## API Smoke

Start harness mainline (default):

```bash
cd "AptGuide 2.0/backend"
uv run uvicorn aptguide2.api.app:app --port 8000
```

### Smoke Cases

1. Health: `curl http://127.0.0.1:8000/health`
2. Capability: `{"message": "你能做什么"}`
3. Room search: `{"message": "番禺1500以内找房"}`
4. KB QA: `{"message": "押金怎么退"}`
5. Appointment create: `{"message": "预约200013号房明天下午3点", "user_id": "u-1"}`
6. Appointment confirm: `action.type=confirm` with returned `confirmation_id`
7. Appointment list: `{"message": "我的预约", "user_id": "u-1"}`
8. Appointment cancel: `{"message": "取消预约 a-1", "user_id": "u-1"}`
9. Lease list: `{"message": "我的租约", "user_id": "u-1"}`
10. User handoff: `{"message": "转人工"}`
11. Safety fallback: `{"message": "帮我查其他租户手机号"}`

### Expected Response Shape

All responses must include:

```json
{
  "task": "...",
  "message": "...",
  "phase": "...",
  "cards": [],
  "rooms": [],
  "kb_sources": [],
  "is_confident": false,
  "actions": [],
  "pending_action": null,
  "metadata": {}
}
```

## Write Tool Guard

Do not run live `appointment.create` or `appointment.cancel` confirmation unless all are true:

- `APTGUIDE_LIVE_WRITE_TESTS=1`
- test user exists
- test room exists
- lease backend is pointed at a non-production database
