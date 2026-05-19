# Next Steps

## Immediate

1. Analyze live eval results (running now)
2. Verify KB QA `expected_doc_ids` accuracy from live eval output
3. Verify criteria-based room search from live eval output

## Deferred

1. Replace local eval seed mappings with reviewed real wechat→lease mappings before production claims.
2. Enable LangSmith tracing or implement local trace recording (P2 trace_visibility).
3. Triage the pre-existing full-suite asyncio runner failures.
4. Production hardening: retry, idempotency, rate limiting, metrics, alerting, data retention, secret rotation.
5. Fully async ChatService.
