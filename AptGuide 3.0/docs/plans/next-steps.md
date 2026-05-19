# Next Steps

## Immediate

1. ~~Execute `docs/plans/2026-05-16-aptguide3-eval-system-overhaul-plan.md`.~~ DONE (2026-05-16)
2. Live discovery run to verify KB QA `expected_doc_ids`.
3. Live eval run to verify criteria-based room search end-to-end.

## Deferred

1. Enable LangSmith tracing or implement local trace recording (P2 trace_visibility).
2. Triaging the pre-existing full-suite asyncio runner failures.
3. Production hardening: retry, idempotency, rate limiting, metrics, alerting, data retention, secret rotation.
4. Fully async ChatService.
5. Room identity mapping + lease validation (需要 wechat→lease ID 数据源).
6. Main-chain integration: `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`.
