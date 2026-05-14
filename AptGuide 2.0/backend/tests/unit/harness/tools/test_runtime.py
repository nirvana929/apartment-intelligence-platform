
from aptguide2.harness.tools.contracts import ToolCallRequest, ToolCallResult, ToolDefinition
from aptguide2.harness.tools.errors import ToolTimeoutError
from aptguide2.harness.tools.registry import ToolRegistry
from aptguide2.harness.tools.runtime import ToolRuntime


def _registry_with(tool_name: str, **def_kwargs) -> ToolRegistry:
    registry = ToolRegistry()
    defaults = dict(
        name=tool_name,
        backend="lease",
        permission="public",
        input_schema="Input",
        output_schema="Output",
    )
    defaults.update(def_kwargs)
    registry.register(ToolDefinition(**defaults))
    return registry


def _request(tool: str = "room.search", **kwargs) -> ToolCallRequest:
    defaults = dict(tool=tool, request_id="r-1", payload={})
    defaults.update(kwargs)
    return ToolCallRequest(**defaults)


class FakeExecutor:
    def __init__(self, result: ToolCallResult | None = None, exc: Exception | None = None):
        self._result = result
        self._exc = exc
        self.last_request: ToolCallRequest | None = None

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        self.last_request = request
        if self._exc:
            raise self._exc
        return self._result or ToolCallResult.ok_result(
            tool=request.tool, data={"ok": True}, backend="lease"
        )


def test_public_tool_executes_without_user():
    registry = _registry_with("room.search")
    runtime = ToolRuntime(registry)
    executor = FakeExecutor(ToolCallResult.ok_result("room.search", {"rooms": []}, "lease"))
    runtime.register_executor("room.search", executor)
    result = runtime.execute(_request())
    assert result.ok is True


def test_user_tool_without_user_id_returns_error():
    registry = _registry_with("lease.list_mine", permission="user", requires_user=True)
    runtime = ToolRuntime(registry)
    runtime.register_executor("lease.list_mine", FakeExecutor())
    result = runtime.execute(_request("lease.list_mine"))
    assert result.ok is False
    assert result.error.code == "MISSING_USER_ID"


def test_confirmation_required_without_confirmation_id():
    registry = _registry_with("appointment.create", requires_confirmation=True, requires_user=True)
    runtime = ToolRuntime(registry)
    runtime.register_executor("appointment.create", FakeExecutor())
    result = runtime.execute(_request("appointment.create", user_id="u-1"))
    assert result.ok is False
    assert result.error.code == "CONFIRMATION_REQUIRED"


def test_missing_executor_returns_not_implemented():
    registry = _registry_with("room.search")
    runtime = ToolRuntime(registry)
    result = runtime.execute(_request())
    assert result.ok is False
    assert result.error.code == "TOOL_NOT_IMPLEMENTED"


def test_executor_exception_maps_to_unknown_error():
    registry = _registry_with("room.search")
    runtime = ToolRuntime(registry)
    runtime.register_executor("room.search", FakeExecutor(exc=ValueError("bad input")))
    result = runtime.execute(_request())
    assert result.ok is False
    assert result.error.code == "UNKNOWN_TOOL_ERROR"
    assert "ValueError" in result.error.message


def test_timeout_error_maps_to_tool_timeout():
    registry = _registry_with("room.search")
    runtime = ToolRuntime(registry)
    runtime.register_executor("room.search", FakeExecutor(exc=ToolTimeoutError("timed out")))
    result = runtime.execute(_request())
    assert result.ok is False
    assert result.error.code == "TOOL_TIMEOUT"
    assert result.error.recoverable is True


def test_builtin_timeout_error_maps_to_tool_timeout():
    registry = _registry_with("room.search")
    runtime = ToolRuntime(registry)
    runtime.register_executor("room.search", FakeExecutor(exc=TimeoutError()))
    result = runtime.execute(_request())
    assert result.ok is False
    assert result.error.code == "TOOL_TIMEOUT"


def test_result_includes_trace_id():
    registry = _registry_with("room.search")
    runtime = ToolRuntime(registry)
    runtime.register_executor("room.search", FakeExecutor(ToolCallResult.ok_result("room.search", {}, "lease")))
    result = runtime.execute(_request(trace_id="t-1"))
    assert result.metadata.get("trace_id") == "t-1"


def test_result_includes_backend_and_latency():
    registry = _registry_with("room.search")
    runtime = ToolRuntime(registry)
    runtime.register_executor("room.search", FakeExecutor(ToolCallResult.ok_result("room.search", {}, "lease")))
    result = runtime.execute(_request())
    assert result.metadata["backend"] == "lease"
    assert result.metadata["latency_ms"] >= 0


def test_user_tool_with_user_id_executes():
    registry = _registry_with("lease.list_mine", permission="user", requires_user=True)
    runtime = ToolRuntime(registry)
    executor = FakeExecutor(ToolCallResult.ok_result("lease.list_mine", {"leases": []}, "lease"))
    runtime.register_executor("lease.list_mine", executor)
    result = runtime.execute(_request("lease.list_mine", user_id="u-1"))
    assert result.ok is True


def test_confirmed_tool_with_confirmation_executes():
    registry = _registry_with("appointment.create", requires_confirmation=True, requires_user=True)
    runtime = ToolRuntime(registry)
    executor = FakeExecutor(ToolCallResult.ok_result("appointment.create", {"id": "a-1"}, "lease"))
    runtime.register_executor("appointment.create", executor)
    result = runtime.execute(_request("appointment.create", user_id="u-1", confirmation_id="c-1"))
    assert result.ok is True


# ---------------------------------------------------------------------------
# Task 8: Trace recording integration tests
# ---------------------------------------------------------------------------

from aptguide2.harness.trace import TraceRecorder


def test_recorder_records_successful_tool_trace():
    registry = _registry_with("room.search")
    recorder = TraceRecorder(trace_id="t-test", request_id="r-test")
    runtime = ToolRuntime(registry, recorder=recorder)
    executor = FakeExecutor(ToolCallResult.ok_result("room.search", {"rooms": []}, "lease"))
    runtime.register_executor("room.search", executor)

    result = runtime.execute(_request(payload={"district": "Chaoyang"}))
    assert result.ok is True

    trace = recorder.to_trace()
    assert len(trace.stages) == 1
    stage = trace.stages[0]
    assert stage.stage == "tool.room.search"
    assert stage.strategy == "lease"
    assert stage.input_summary["tool"] == "room.search"
    assert "payload_keys" in stage.input_summary
    assert stage.output_summary["ok"] is True
    assert stage.latency_ms >= 0
    assert stage.errors == []


def test_recorder_records_error_tool_trace():
    registry = _registry_with("room.search")
    recorder = TraceRecorder()
    runtime = ToolRuntime(registry, recorder=recorder)
    runtime.register_executor("room.search", FakeExecutor(exc=ValueError("bad")))

    result = runtime.execute(_request())
    assert result.ok is False

    trace = recorder.to_trace()
    assert len(trace.stages) == 1
    stage = trace.stages[0]
    assert stage.stage == "tool.room.search"
    assert stage.output_summary["ok"] is False
    assert stage.output_summary["error_code"] == "UNKNOWN_TOOL_ERROR"
    assert len(stage.errors) == 1


def test_recorder_records_permission_error_trace():
    registry = _registry_with("lease.list_mine", permission="user", requires_user=True)
    recorder = TraceRecorder()
    runtime = ToolRuntime(registry, recorder=recorder)

    result = runtime.execute(_request("lease.list_mine"))
    assert result.ok is False

    trace = recorder.to_trace()
    assert len(trace.stages) == 1
    stage = trace.stages[0]
    assert stage.stage == "tool.lease.list_mine"
    assert stage.output_summary["error_code"] == "MISSING_USER_ID"


def test_no_recorder_no_trace():
    registry = _registry_with("room.search")
    runtime = ToolRuntime(registry)
    runtime.register_executor("room.search", FakeExecutor())

    result = runtime.execute(_request())
    assert result.ok is True
    # No recorder, so no trace to verify — just ensure no crash


def test_trace_input_summary_has_no_pii():
    registry = _registry_with("room.search")
    recorder = TraceRecorder()
    runtime = ToolRuntime(registry, recorder=recorder)
    runtime.register_executor("room.search", FakeExecutor())

    result = runtime.execute(_request(payload={"phone": "13800138000", "district": "Chaoyang"}))
    assert result.ok is True

    trace = recorder.to_trace()
    stage = trace.stages[0]
    # The input_summary should contain payload_keys but the actual payload values
    # are not stored — only keys are recorded after PII redaction
    assert "payload_keys" in stage.input_summary
    assert stage.input_summary["payload_keys"] == sorted(["phone", "district"])
