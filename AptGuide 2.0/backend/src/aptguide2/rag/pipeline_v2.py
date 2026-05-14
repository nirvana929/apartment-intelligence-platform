"""RAG v2 orchestration behind feature flag."""

from __future__ import annotations

from typing import Any

from aptguide2.rag.confidence import get_fallback_message
from aptguide2.rag.kb_v2 import retrieve_kb_v2
from aptguide2.rag.planning import build_retrieval_plan
from aptguide2.rag.query_understanding import understand_query
from aptguide2.rag.room_v2 import retrieve_ranked_rooms_v2
from aptguide2.rag.schemas import PipelineResult


def run_pipeline_v2(
    message: str,
    vector_adapter,
    embed_fn,
    lease_validator=None,
    top_n_rooms: int = 5,
    trace_recorder=None,
    interaction_intent=None,
    diagnostics: dict[str, Any] | None = None,
) -> PipelineResult:
    qr = understand_query(message, interaction_intent=interaction_intent)
    plan = build_retrieval_plan(qr)

    if diagnostics is not None:
        diagnostics["query_understanding"] = qr.model_dump()
        diagnostics["retrieval_plan"] = plan.model_dump()

    if qr.response_mode == "refuse":
        result = PipelineResult(
            task="fallback",
            message="抱歉，我不能查询或透露他人隐私信息。您可以查看自己的账号、预约和租约信息，或联系人工客服处理。",
            fallback_reason="risk_refuse",
            query_understanding=qr,
        )
        _record_trace(trace_recorder, {
            "task": "fallback",
            "rewrite_count": 0,
            "collections": [],
            "filters": {},
            "candidate_count": 0,
            "validated_count": 0,
            "fallback_reason": "risk_refuse",
        })
        return result

    if qr.response_mode == "template_answer" and qr.risk_level == "high":
        result = PipelineResult(
            task="kb_qa",
            message=(
                "这个问题涉及退款、合同或资金处理，我不能直接承诺结果。"
                "您可以查看相关规则说明，或联系人工客服核实具体订单和合同状态。"
            ),
            is_confident=False,
            fallback_reason="risk_controlled_template",
            query_understanding=qr,
        )
        _record_trace(trace_recorder, {
            "task": "kb_qa",
            "rewrite_count": 0,
            "collections": [],
            "filters": {},
            "candidate_count": 0,
            "validated_count": 0,
            "fallback_reason": "risk_controlled_template",
        })
        return result

    if plan.task == "fallback":
        result = PipelineResult(
            task="fallback",
            message="抱歉，这个问题超出了我的服务范围。我是租房助手，可以帮您找房或回答租房相关问题。",
            fallback_reason="out_of_scope",
            query_understanding=qr,
        )
        _record_trace(trace_recorder, {
            "task": plan.task,
            "rewrite_count": 0,
            "collections": [],
            "filters": {},
            "candidate_count": 0,
            "validated_count": 0,
            "fallback_reason": "out_of_scope",
        })
        return result

    if plan.task == "kb_qa":
        sources, is_confident = retrieve_kb_v2(plan, vector_adapter, embed_fn, diagnostics=diagnostics)
        if not is_confident:
            result = PipelineResult(
                task="kb_qa",
                message=get_fallback_message(qr.risk_level),
                kb_sources=sources,
                is_confident=False,
                fallback_reason="confidence_gate_blocked",
                query_understanding=qr,
            )
            _record_trace(trace_recorder, {
                "task": plan.task,
                "rewrite_count": len(plan.semantic_queries),
                "collections": ["apt_rental_kb"],
                "filters": plan.hard_filters,
                "candidate_count": len(sources),
                "validated_count": 0,
                "fallback_reason": "confidence_gate_blocked",
            })
            return result
        result = PipelineResult(
            task="kb_qa",
            kb_sources=sources,
            is_confident=True,
            query_understanding=qr,
        )
        _record_trace(trace_recorder, {
            "task": plan.task,
            "rewrite_count": len(plan.semantic_queries),
            "collections": ["apt_rental_kb"],
            "filters": plan.hard_filters,
            "candidate_count": len(sources),
            "validated_count": len(sources),
            "fallback_reason": "",
        })
        return result

    if lease_validator is None:
        result = PipelineResult(
            task="room_search",
            message="房源需要经过业务系统校验后才能推荐，请稍后再试。",
            fallback_reason="lease_validator_missing",
            query_understanding=qr,
        )
        _record_trace(trace_recorder, {
            "task": plan.task,
            "rewrite_count": len(plan.semantic_queries),
            "collections": ["apt_room_vector"],
            "filters": plan.hard_filters,
            "candidate_count": 0,
            "validated_count": 0,
            "fallback_reason": "lease_validator_missing",
        })
        return result

    ranked = retrieve_ranked_rooms_v2(
        plan=plan,
        query_result=qr,
        vector_adapter=vector_adapter,
        embed_fn=embed_fn,
        lease_validator=lease_validator,
        top_n=top_n_rooms,
        diagnostics=diagnostics,
    )
    if not ranked:
        result = PipelineResult(
            task="room_search",
            message="抱歉，经过业务系统校验后没有找到可靠可展示的房源。您可以尝试放宽预算或区域条件。",
            fallback_reason="lease_validation_empty",
            query_understanding=qr,
        )
        _record_trace(trace_recorder, {
            "task": plan.task,
            "rewrite_count": len(plan.semantic_queries),
            "collections": ["apt_room_vector"],
            "filters": plan.hard_filters,
            "candidate_count": 0,
            "validated_count": 0,
            "fallback_reason": "lease_validation_empty",
        })
        return result
    _record_trace(trace_recorder, {
        "task": plan.task,
        "rewrite_count": len(plan.semantic_queries),
        "collections": ["apt_room_vector"],
        "filters": plan.hard_filters,
        "candidate_count": len(ranked),
        "validated_count": len(ranked),
        "fallback_reason": "",
    })
    return PipelineResult(task="room_search", rooms=ranked, query_understanding=qr)


def _record_trace(trace_recorder, payload: dict) -> None:
    if trace_recorder is not None:
        trace_recorder.record("retrieval_finished", payload)
