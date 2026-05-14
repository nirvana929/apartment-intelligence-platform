from aptguide2.harness.trace import TraceRecorder


def test_trace_recorder_records_stage():
    recorder = TraceRecorder(trace_id="t-1", request_id="r-1", session_id="s-1")
    token = recorder.start_stage("routing", "rule_v1", {"message_len": 4})
    recorder.finish_stage(token, {"task": "room_search"})
    trace = recorder.to_trace()

    assert trace.trace_id == "t-1"
    assert trace.request_id == "r-1"
    assert trace.stages[0].stage == "routing"
    assert trace.stages[0].output_summary == {"task": "room_search"}
    assert trace.stages[0].latency_ms >= 0


def test_trace_recorder_records_errors():
    recorder = TraceRecorder(trace_id="t-1", request_id="r-1")
    token = recorder.start_stage("tool", "room.search", {})
    recorder.finish_stage(token, {}, errors=["TOOL_TIMEOUT"])
    trace = recorder.to_trace()
    assert trace.stages[0].errors == ["TOOL_TIMEOUT"]
