from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.rag.baseline import RagBaselineProcedure


class FakePipelineResult:
    def __init__(self, task, message="", rooms=None, kb_sources=None, is_confident=False):
        self.task = task
        self.message = message
        self.rooms = rooms or []
        self.kb_sources = kb_sources or []
        self.is_confident = is_confident


class FakeRoom:
    room_id = 1
    apartment_name = "测试公寓"
    room_number = "101"
    rent = 1500
    district_name = "番禺区"
    tags = ["安静"]
    facilities = ["空调"]
    recommendation_reason = "符合安静偏好"


class FakeSource:
    title = "押金规则"
    content = "押金按合同约定退还。"
    module = "lease"
    score = 0.8


def test_rag_baseline_maps_room_result_to_procedure_result():
    procedure = RagBaselineProcedure(
        run_pipeline_fn=lambda **kwargs: FakePipelineResult(task="room_search", rooms=[FakeRoom()]),
        vector_adapter=object(),
        embed_fn=lambda text: [0.0],
    )
    frame = ConversationFrame(request_id="r-1", message="番禺安静房子")
    decision = RouteDecision(task="room_search", procedure="rag.room_search", confidence=0.8)
    result = procedure.run(frame, decision)
    assert result.task == "room_search"
    assert result.cards[0]["room_id"] == 1
    assert result.phase == "showing_room_results"


def test_rag_baseline_maps_kb_result_to_sources():
    procedure = RagBaselineProcedure(
        run_pipeline_fn=lambda **kwargs: FakePipelineResult(
            task="kb_qa",
            message="押金按合同约定退还。",
            kb_sources=[FakeSource()],
            is_confident=True,
        ),
        vector_adapter=object(),
        embed_fn=lambda text: [0.0],
    )
    frame = ConversationFrame(request_id="r-1", message="押金怎么退")
    decision = RouteDecision(task="kb_qa", procedure="rag.kb_qa", confidence=0.8)
    result = procedure.run(frame, decision)
    assert result.task == "kb_qa"
    assert result.sources[0]["title"] == "押金规则"
    assert result.metadata["is_confident"] is True
