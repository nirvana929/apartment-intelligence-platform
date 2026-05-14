"""Harness procedure adapter for RAG v2 pipeline."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.rag.pipeline_v2 import run_pipeline_v2
from aptguide2.rag.tool_validation import ToolRuntimeRoomValidator


class RagV2Procedure:
    """Harness procedure that mounts RAG v2 as the system retrieval module."""

    def __init__(
        self,
        vector_adapter: Any,
        embed_fn: Callable[[str], list[float]],
        run_pipeline_v2_fn: Callable[..., Any] = run_pipeline_v2,
    ) -> None:
        self.vector_adapter = vector_adapter
        self.embed_fn = embed_fn
        self.run_pipeline_v2_fn = run_pipeline_v2_fn

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        lease_validator = ToolRuntimeRoomValidator(tool_runtime) if tool_runtime is not None else None

        # Extract InteractionIntent from decision metadata if available
        intent_payload = decision.metadata.get("intent") if decision.metadata else None
        interaction_intent = None
        if intent_payload:
            from aptguide2.interaction.contracts import InteractionIntent
            interaction_intent = InteractionIntent.model_validate(intent_payload)

        result = self.run_pipeline_v2_fn(
            message=frame.message,
            vector_adapter=self.vector_adapter,
            embed_fn=self.embed_fn,
            lease_validator=lease_validator,
            interaction_intent=interaction_intent,
        )
        if result.task == "room_search":
            return self._room_result(result)
        if result.task == "kb_qa":
            return self._kb_result(result)
        return ProcedureResult(
            task="fallback",
            phase="boundary_declined",
            reply=result.message,
            fallback_reason=getattr(result, "fallback_reason", "rag_v2_fallback"),
            metadata={"source": "rag_v2"},
        )

    def _room_result(self, result: Any) -> ProcedureResult:
        cards = [
            {
                "type": "room",
                "room_id": room.room_id,
                "apartment_name": room.apartment_name,
                "room_number": room.room_number,
                "rent": room.rent,
                "district": getattr(room, "district_name", ""),
                "tags": room.tags,
                "facilities": room.facilities,
                "recommendation_reason": room.recommendation_reason,
            }
            for room in result.rooms
        ]
        return ProcedureResult(
            task="room_search",
            phase="showing_room_results" if cards else "search_failed",
            reply="为您找到以下房源推荐。" if cards else (result.message or "抱歉，没有找到符合条件的房源。"),
            cards=cards,
            metadata={"source": "rag_v2", "room_count": len(cards)},
            fallback_reason="" if cards else getattr(result, "fallback_reason", "room_search_empty"),
        )

    def _kb_result(self, result: Any) -> ProcedureResult:
        sources = [
            {
                "title": source.title,
                "content": source.content,
                "module": source.module,
                "score": round(source.score, 3),
            }
            for source in result.kb_sources[:3]
        ]
        return ProcedureResult(
            task="kb_qa",
            phase="answering_knowledge" if result.is_confident else "knowledge_low_confidence",
            reply=result.message or "我找到了相关知识来源，但需要进一步生成答案。",
            sources=sources,
            metadata={
                "source": "rag_v2",
                "is_confident": result.is_confident,
                "source_count": len(sources),
                "risk_level": result.query_understanding.risk_level if result.query_understanding else "low",
                "response_mode": result.query_understanding.response_mode if result.query_understanding else "normal_answer",
                "risk_profile": (
                    result.query_understanding.risk_profile.model_dump()
                    if result.query_understanding else {}
                ),
            },
            fallback_reason="" if result.is_confident else "kb_low_confidence",
        )
