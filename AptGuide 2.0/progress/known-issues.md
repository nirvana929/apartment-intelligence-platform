# Known Issues

## Non-Blocking

- `appointment.create`, `appointment.list_mine`, `lease.list_mine` executors return TOOL_NOT_IMPLEMENTED when LeaseAdapter lacks the method. This is by design — appointment workflow not yet implemented.
- `trace.record` has no executor registered in ToolRuntime. Trace recording is handled by the harness TraceRecorder directly. This is by design.
- LeaseAdapter async methods bridged via `_run_awaitable()` in executors. If an event loop is already running, returns TOOL_NOT_IMPLEMENTED instead of blocking.

## Resolved

- Module name collision between `tests/unit/harness/` and `tests/unit/harness/tools/` — resolved by adding `__init__.py` to test directories.
- Harness implementation pending — resolved, all 24 features completed with test evidence.
