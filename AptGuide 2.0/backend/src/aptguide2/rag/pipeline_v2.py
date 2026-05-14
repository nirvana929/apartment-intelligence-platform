"""RAG v2 orchestration behind feature flag."""

from __future__ import annotations

from aptguide2.rag.confidence import get_fallback_message
from aptguide2.rag.kb_retrieval import retrieve_kb
from aptguide2.rag.planning import build_retrieval_plan
from aptguide2.rag.query_understanding import understand_query
from aptguide2.rag.ranking import rank_rooms
from aptguide2.rag.room_retrieval import retrieve_rooms
from aptguide2.rag.schemas import PipelineResult
from aptguide2.rag.validation import validate_room_candidates


def run_pipeline_v2(
    message: str,
    vector_adapter,
    embed_fn,
    lease_validator=None,
    top_n_rooms: int = 5,
    trace_recorder=None,
) -> PipelineResult:
    qr = understand_query(message)
    plan = build_retrieval_plan(qr)

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
        sources, is_confident = retrieve_kb(qr, vector_adapter, embed_fn)
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

    candidates = retrieve_rooms(qr, vector_adapter, embed_fn)
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
            "candidate_count": len(candidates),
            "validated_count": 0,
            "fallback_reason": "lease_validator_missing",
        })
        return result
    validated = validate_room_candidates(candidates, plan.hard_filters, lease_validator)
    if not validated:
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
            "candidate_count": len(candidates),
            "validated_count": 0,
            "fallback_reason": "lease_validation_empty",
        })
        return result
    ranked = rank_rooms(validated, qr, top_n=top_n_rooms)
    _record_trace(trace_recorder, {
        "task": plan.task,
        "rewrite_count": len(plan.semantic_queries),
        "collections": ["apt_room_vector"],
        "filters": plan.hard_filters,
        "candidate_count": len(candidates),
        "validated_count": len(validated),
        "fallback_reason": "",
    })
    return PipelineResult(task="room_search", rooms=ranked, query_understanding=qr)


def _record_trace(trace_recorder, payload: dict) -> None:
    if trace_recorder is not None:
        trace_recorder.record("retrieval_finished", payload)
