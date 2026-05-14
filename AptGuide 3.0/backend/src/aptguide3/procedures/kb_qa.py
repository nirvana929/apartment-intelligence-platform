from __future__ import annotations

from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.integrations.embedding_client import EmbeddingClient
from aptguide3.integrations.vector_client import VectorClient

PLACEHOLDER_MESSAGE = "已理解您的租房规则问题。知识库检索将在接入 retrieval 后返回带来源的回答。"
SNIPPET_MAX_LEN = 200


class KbQaProcedure:
    name = "kb_qa"

    def __init__(
        self, vector_client: VectorClient | None = None, embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self._vector = vector_client
        self._embedding = embedding_client

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        if self._vector is None or self._embedding is None:
            return self._placeholder(understanding)

        query = understanding.retrieval_queries[0] if understanding.retrieval_queries else frame.message
        vector = self._embedding.embed(query)
        if not vector or all(v == 0 for v in vector):
            return self._placeholder(understanding)

        hits = self._vector.search_kb(vector, top_k=5)
        if not hits:
            return self._placeholder(understanding)

        cards = [self._hit_to_card(h) for h in hits]
        top_risk = self._highest_risk(hits)
        return ProcedureResult(
            message="以下是知识库中与您问题相关的内容：",
            phase="kb_qa",
            cards=cards,
            metadata={
                "route": understanding.route,
                "task": understanding.task,
                "domain": understanding.domain,
                "risk_level": top_risk,
                "source_count": len(cards),
            },
        )

    def _placeholder(self, understanding: UnderstandingResult) -> ProcedureResult:
        return ProcedureResult(
            message=PLACEHOLDER_MESSAGE,
            phase="kb_qa",
            metadata={"route": understanding.route, "task": understanding.task, "domain": understanding.domain},
        )

    @staticmethod
    def _hit_to_card(hit: dict[str, Any]) -> dict[str, Any]:
        content = hit.get("content", "")
        snippet = content[:SNIPPET_MAX_LEN] + ("..." if len(content) > SNIPPET_MAX_LEN else "")
        return {
            "title": hit.get("title", ""),
            "content_snippet": snippet,
            "risk_level": hit.get("risk_level", "low"),
            "score": round(hit.get("distance", 0.0), 4),
        }

    @staticmethod
    def _highest_risk(hits: list[dict[str, Any]]) -> str:
        risk_order = {"high": 2, "medium": 1, "low": 0}
        best = "low"
        for h in hits:
            level = h.get("risk_level", "low")
            if risk_order.get(level, 0) > risk_order.get(best, 0):
                best = level
        return best
