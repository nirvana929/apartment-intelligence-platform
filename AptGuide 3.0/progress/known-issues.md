# Known Issues

- Milestone 0 is a runnable scaffold, not a production-ready independent backend.
- Persistence is currently in-memory and cannot survive process restart.
- No MySQL schema, migration script, or SQLAlchemy models exist yet.
- Redis is configured but not wired as hot session or pending-action TTL storage.
- Trace events currently write to console only.
- Procedure runs are not durably recorded.
- Auth boundary does not yet match final `lease -> AptGuide 3.0` internal-header integration.
- Real MySQL, Redis, lease, Milvus, embedding, and LLM dependency verification has not run.
