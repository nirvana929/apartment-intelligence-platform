# Known Issues

## Active

- ChatService persistence uses sync-to-async bridge pattern — live MySQL works with NullPool, but should be reviewed for fully async production design.
- No automatic retry on LLM or lease client transient failures — user-visible errors during brief outages.
- No request-level idempotency key at the API boundary — duplicate frontend retries create duplicate message/procedure records.
- No MySQL data retention policy or cleanup job — tables grow indefinitely.
- No alerting, Prometheus metrics, or structured logging — production incidents invisible without external monitoring.
- No secret rotation mechanism — compromised secrets require manual env update and restart.
- No rate limiting at the API layer.
- 35 full-suite asyncio runner failures — pre-existing, not regressions. Need triage.
- Room search local live gate is green with `local_eval_seed` identity mappings, but these mappings are not production identity proof. Production still needs reviewed `wechat_room_id -> lease_room_id` mappings or a lease-native vector source rebuilt from current lease DB.
- KB QA returns source cards, but final user-facing answer text is not yet generated from evidence with citations.
- LangSmith traces wrapped model calls, but final `ChatResponse` output/cards/metadata are not yet recorded as application-level run output.
- Full RAG eval is not production-grade until room lease validation, grounded risk answers, and final-output trace visibility are implemented.

## Resolved

- ~~Persistence is currently in-memory and cannot survive process restart.~~ MySQL schema, models, and repository implementations exist. (M1)
- ~~No MySQL schema, migration script, or SQLAlchemy models exist yet.~~ 11 models + schema.sql created. (M1)
- ~~Redis is configured but not wired as hot session or pending-action TTL storage.~~ RedisStateStore exists with TTL support. (M1)
- ~~Trace events currently write to console only.~~ RepositoryTraceSink exists. (M1)
- ~~Procedure runs are not durably recorded.~~ MySqlProcedureRunRepository exists. (M1)
- ~~Auth boundary does not yet match final lease -> AptGuide 3.0 internal-header integration.~~ AuthResolver supports internal_header mode. (M1)
- ~~deps.py still uses InMemorySessionRepo.~~ _build_repos dispatcher supports memory/mysql/hybrid modes. (M1)
- ~~Real MySQL, Redis, lease, Milvus, embedding, and LLM dependency verification has not run.~~ All live-verified on 2026-05-15. (M2/M5)
- ~~deps.py mysql/hybrid modes only wire 3 of 8 repos.~~ RepoBundle wires all 8. (M3)
- ~~InMemoryMemoryRepo and InMemoryHandoffRepo use sync protocol.~~ Async methods added. (M1)
- ~~No InMemoryPendingActionRepo exists.~~ Created. (M3)
- ~~LeaseClient lacks methods for appointment, lease info, lease listing.~~ create_appointment, list_appointments, list_leases added. (M3)
- ~~No application code writes to aptguide3_audit_log.~~ Audit writes in appointment, lease, and handoff procedures. (M3)
- ~~/ready endpoint checks config presence only.~~ Async live connectivity probes added with ?live=true. (M3)
- ~~Procedure execution is synchronous but MySQL repos are async.~~ _run_async bridge pattern in each procedure. (M3)
- ~~Milvus collection data missing — room vectors and KB vectors need syncing before RAG eval can pass.~~ Later checkpoints show wechat room recall and KB source recall can pass live eval; remaining issue is production evidence/ID alignment, not basic recall availability.
- ~~Lease validation never triggered for room search.~~ Fixed LeaseClient response parsing, imported 44 local eval mappings, and live RAG gate reached 9/9 pass with unvalidated room count 0. (2026-05-16)
- ~~Wechat synthetic room IDs were generated with process-random Python `hash()`.~~ Replaced with deterministic SHA-256-derived synthetic IDs and updated eval expected IDs. (2026-05-16)
