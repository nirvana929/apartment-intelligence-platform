# Known Issues

## Active Issues

- T1 KB QA `expected_doc_ids` are inferred from KB doc ID patterns — need live discovery run to verify accuracy. (live eval running)
- No automatic retry on LLM or lease client transient failures — user-visible errors during brief outages.
- No request-level idempotency key at the API boundary — duplicate frontend retries create duplicate message/procedure records.
- No MySQL data retention policy or cleanup job — tables grow indefinitely.
- No alerting, Prometheus metrics, or structured logging — production incidents invisible without external monitoring.
- No rate limiting at the API layer.
- Room search lacks a confirmed `wechat_room_id -> lease_room_id` validation path.
- ChatService persistence uses sync bridge (`asyncio.run`) — should review for fully async production design.

## Resolved Issues (Eval System Overhaul 2026-05-16)

- ~~T1 KB QA: 26/30 cases have empty `expected_doc_ids`~~ RESOLVED: 60 cases, all with expected_doc_ids (inferred, TODO: live verification).
- ~~T1 Room Search: Hit@5 exact-match is wrong methodology~~ RESOLVED: criteria-based evaluation (response_not_empty, district_match, price_in_range, amenity_match, latency_ok).
- ~~T2 Understanding: 10 risk cases missing expected_risk_level; 2 free-text assertions~~ RESOLVED: all 55 cases structured, risk_level + entity resolution fields.
- ~~T3 Procedures: 9 free-text assertions; multi-turn broken; user_id ignored~~ RESOLVED: all 55 cases structured, multi-turn session reuse, user_id passthrough.
- Total: 200 cases, 64 unit tests pass, ruff clean.

## Resolved Issues

- ~~Persistence is currently in-memory and cannot survive process restart.~~ RESOLVED: MySQL schema, models, and repository implementations exist.
- ~~No MySQL schema, migration script, or SQLAlchemy models exist yet.~~ RESOLVED: 11 models + schema.sql created.
- ~~Redis is configured but not wired as hot session or pending-action TTL storage.~~ RESOLVED: RedisStateStore exists with TTL support.
- ~~Trace events currently write to console only.~~ RESOLVED: RepositoryTraceSink exists.
- ~~Procedure runs are not durably recorded.~~ RESOLVED: MySqlProcedureRunRepository exists.
- ~~Auth boundary does not yet match final `lease -> AptGuide 3.0` internal-header integration.~~ RESOLVED: AuthResolver supports internal_header mode.
- ~~deps.py still uses InMemorySessionRepo — needs Redis/MySQL wiring when live services are available.~~ RESOLVED: `_build_repos()` supports memory/mysql/hybrid modes for session, message, and procedure-run repositories.
- ChatService persistence uses sync bridge (`asyncio.run`) — live MySQL persistence now works with SQLAlchemy `NullPool`, but the API/application path should still be reviewed for a fully async production design.
- ~~Real MySQL, Redis, lease, Milvus, embedding, and LLM dependency verification has not run.~~ RESOLVED LOCALLY: live MySQL, Redis, lease health, Milvus, embedding, LLM, and chat persistence tests passed on 2026-05-15.
- No automatic retry on LLM or lease client transient failures — user-visible errors during brief outages.
- No request-level idempotency key at the API boundary — duplicate frontend retries create duplicate message/procedure records.
- No MySQL data retention policy or cleanup job — tables grow indefinitely.
- aptguide3_audit_log table exists in schema but no application code writes to it — critical security events are not audited.
- No alerting, Prometheus metrics, or structured logging — production incidents invisible without external monitoring.
- No secret rotation mechanism — compromised secrets require manual env update and restart.
- No rate limiting at the API layer.
- Room search lacks a confirmed `wechat_room_id -> lease_room_id` validation path. The `room_retrieval.py` pipeline queries `wechat_room_index` (string IDs), generates a synthetic integer via `abs(hash(wechat_id)) % 1000000 + 900000`, and passes these into `ValidatedRoom` without calling the lease API. There is no code path that resolves wechat IDs to lease-system room IDs. See `docs/system/data-inventory/room-id-alignment.md` for the full field inventory. This blocks Plan 2 (room-lease-id-alignment) and any claim of `lease_validated` evidence level for room cards.
- KB QA returns source cards, but final user-facing answer text is not yet generated from evidence with citations.
- Plan 4 LangSmith final-output tracing is complete; future LangSmith gaps should be tracked as verification issues, not as missing implementation.
- Full RAG eval is not production-grade until room identity mapping, room lease validation, and grounded risk answers are implemented.
- ~~Room search Hit@5 评测方法不适用于语义搜索~~ RESOLVED: 改用 criteria-based 评测 (response_not_empty, district_match, price_in_range, amenity_match, understanding_correct, latency_ok)。
- /ready endpoint checks config presence only, not live service connectivity — a "config green but service down" scenario is possible.
- ~~deps.py `_build_mysql_repos()` / `_build_hybrid_repos()` only return 3 of 8 repository types.~~ RESOLVED: `RepoBundle` dataclass wires all 8 repo types in all persistence modes.
- ~~deps.py `build_runtime()` passes no dependencies to procedures.~~ RESOLVED: `build_runtime(settings, bundle)` passes repos and lease_client to all procedures.
- ~~memory_repo.py InMemoryMemoryRepo uses sync protocol.~~ RESOLVED: async `list_memories()` and `upsert_memory()` methods added.
- ~~handoff_repo.py InMemoryHandoffRepo uses sync protocol.~~ RESOLVED: async `create_ticket()` and `list_tickets()` methods added.
- ~~No `InMemoryPendingActionRepo` exists.~~ RESOLVED: `InMemoryPendingActionRepo` created in `persistence/pending_action_repo.py`.
- ~~LeaseClient has no methods for appointment/lease.~~ RESOLVED: `create_appointment()`, `list_appointments()`, `list_leases()` added.
- ~~Procedure execution is synchronous but MySQL repos are async.~~ RESOLVED: `_run_async` bridge pattern in each procedure.
- ~~No application code writes to aptguide3_audit_log.~~ RESOLVED: audit writes in appointment, lease, and handoff procedures.
- ~~`/ready` endpoint checks config presence only.~~ RESOLVED: async live connectivity probes (MySQL SELECT 1, Redis PING, lease health, Milvus list_collections) added with `?live=true` query param.
