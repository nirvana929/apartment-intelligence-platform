from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.rag.pipeline import run_pipeline


class RagBaselineProcedure:
    """Adapter that mounts the current MVP RAG pipeline into the harness."""

    def __init__(
        self,
        vector_adapter: Any,
        embed_fn: Callable[[str], list[float]],
        run_pipeline_fn: Callable[..., Any] = run_pipeline,
    ) -> None:
        self.vector_adapter = vector_adapter
        self.embed_fn = embed_fn
        self.run_pipeline_fn = run_pipeline_fn

    def run(self, frame: ConversationFrame, decision: RouteDecision, tool_runtime: Any | None = None) -> ProcedureResult:
        previous_state = dict(frame.task_slots)
        result = self.run_pipeline_fn(
            message=frame.message,
            vector_adapter=self.vector_adapter,
            embed_fn=self.embed_fn,
            previous_state=previous_state,
        )
        if result.task == "room_search":
            return self._room_result(result)
        if result.task == "kb_qa":
            return self._kb_result(result)
        return ProcedureResult(
            task="fallback",
            phase="boundary_declined",
            reply=result.message,
            fallback_reason=getattr(result, "fallback_reason", "rag_fallback"),
        )

    def _room_result(self, result: Any) -> ProcedureResult:
        cards = []
        for room in result.rooms:
            cards.append(
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
            )
        if cards:
            reply = "为您找到以下房源推荐。"
            phase = "showing_room_results"
        else:
            reply = result.message or "抱歉，没有找到符合条件的房源。"
            phase = "search_failed"
        return ProcedureResult(
            task="room_search",
            phase=phase,
            reply=reply,
            cards=cards,
            metadata={"source": "rag_mvp_baseline", "room_count": len(cards)},
        )

    def _kb_result(self, result: Any) -> ProcedureResult:
        sources = []
        for source in result.kb_sources[:3]:
            sources.append(
                {
                    "title": source.title,
                    "content": source.content,
                    "module": source.module,
                    "score": round(source.score, 3),
                }
            )
        return ProcedureResult(
            task="kb_qa",
            phase="answering_knowledge",
            reply=result.message or "我找到了相关知识来源，但需要进一步生成答案。",
            sources=sources,
            metadata={
                "source": "rag_mvp_baseline",
                "is_confident": result.is_confident,
                "source_count": len(sources),
            },
            fallback_reason="" if result.is_confident else "kb_low_confidence",
        )
