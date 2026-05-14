"""Tests for RagV2Procedure harness adapter."""

from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.rag.v2 import RagV2Procedure
from aptguide2.rag.schemas import KBSource, PipelineResult, RankedRoom


def _frame(message: str = "番禺1500以内找房") -> ConversationFrame:
    return ConversationFrame(
        request_id="req-1",
        session_id="s-1",
        user_id="u-1",
        message=message,
    )


def _decision(task: str) -> RouteDecision:
    return RouteDecision(
        task=task,
        procedure=f"rag.{task}",
        confidence=0.9,
        domain_category="in_domain_task",
        reason="test",
    )


def test_rag_v2_room_result_maps_cards() -> None:
    def fake_pipeline(**kwargs):
        return PipelineResult(
            task="room_search",
            rooms=[
                RankedRoom(
                    room_id=200013,
                    apartment_id=1,
                    apartment_name="南亭公寓",
                    room_number="A101",
                    district_name="番禺区",
                    rent=1450,
                    tags=["安静"],
                    facilities=["空调"],
                    recommendation_reason="预算和区域匹配",
                    final_score=0.91,
                )
            ],
        )

    proc = RagV2Procedure(vector_adapter=object(), embed_fn=lambda text: [], run_pipeline_v2_fn=fake_pipeline)
    result = proc.run(_frame(), _decision("room_search"), tool_runtime=object())

    assert result.task == "room_search"
    assert result.phase == "showing_room_results"
    assert result.cards[0]["room_id"] == 200013
    assert result.metadata["source"] == "rag_v2"


def test_rag_v2_kb_result_maps_sources() -> None:
    def fake_pipeline(**kwargs):
        return PipelineResult(
            task="kb_qa",
            message="押金按合同规则处理。",
            is_confident=True,
            kb_sources=[
                KBSource(
                    chunk_id="c1",
                    doc_id="KB-LEASE-001",
                    title="押金规则",
                    module="lease",
                    content="押金退还以合同和账单为准。",
                    score=0.8,
                    risk_level="high",
                )
            ],
        )

    proc = RagV2Procedure(vector_adapter=object(), embed_fn=lambda text: [], run_pipeline_v2_fn=fake_pipeline)
    result = proc.run(_frame("押金怎么退"), _decision("kb_qa"), tool_runtime=object())

    assert result.task == "kb_qa"
    assert result.phase == "answering_knowledge"
    assert result.sources[0]["title"] == "押金规则"
    assert result.metadata["is_confident"] is True


def test_rag_v2_passes_tool_runtime_as_lease_validator() -> None:
    captured = {}

    def fake_pipeline(**kwargs):
        captured.update(kwargs)
        return PipelineResult(task="fallback", message="fallback")

    tool_runtime = object()
    proc = RagV2Procedure(vector_adapter=object(), embed_fn=lambda text: [], run_pipeline_v2_fn=fake_pipeline)
    proc.run(_frame(), _decision("room_search"), tool_runtime=tool_runtime)

    assert captured["lease_validator"] is not None


def test_rag_v2_no_tool_runtime_passes_none_lease_validator() -> None:
    captured = {}

    def fake_pipeline(**kwargs):
        captured.update(kwargs)
        return PipelineResult(task="fallback", message="fallback")

    proc = RagV2Procedure(vector_adapter=object(), embed_fn=lambda text: [], run_pipeline_v2_fn=fake_pipeline)
    proc.run(_frame(), _decision("room_search"), tool_runtime=None)

    assert captured["lease_validator"] is None


def test_rag_v2_fallback_result() -> None:
    def fake_pipeline(**kwargs):
        return PipelineResult(task="fallback", message="超出范围", fallback_reason="out_of_scope")

    proc = RagV2Procedure(vector_adapter=object(), embed_fn=lambda text: [], run_pipeline_v2_fn=fake_pipeline)
    result = proc.run(_frame("今天天气怎么样"), _decision("fallback"), tool_runtime=None)

    assert result.task == "fallback"
    assert result.phase == "boundary_declined"
    assert result.metadata["source"] == "rag_v2"


def test_rag_v2_empty_room_result() -> None:
    def fake_pipeline(**kwargs):
        return PipelineResult(task="room_search", message="没有找到房源", rooms=[], fallback_reason="no_results")

    proc = RagV2Procedure(vector_adapter=object(), embed_fn=lambda text: [], run_pipeline_v2_fn=fake_pipeline)
    result = proc.run(_frame(), _decision("room_search"), tool_runtime=object())

    assert result.task == "room_search"
    assert result.phase == "search_failed"
    assert result.cards == []
