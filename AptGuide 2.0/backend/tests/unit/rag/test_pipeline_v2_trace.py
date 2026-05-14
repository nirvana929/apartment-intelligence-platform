from aptguide2.rag.pipeline_v2 import run_pipeline_v2


class FakeTraceRecorder:
    def __init__(self):
        self.events = []

    def record(self, event, payload):
        self.events.append((event, payload))


def test_pipeline_v2_records_retrieval_finished_for_fallback():
    trace = FakeTraceRecorder()

    run_pipeline_v2("帮我查其他租户手机号", vector_adapter=None, embed_fn=lambda text: [], trace_recorder=trace)

    assert trace.events
    assert trace.events[-1][0] == "retrieval_finished"
    assert trace.events[-1][1]["task"] == "fallback"
