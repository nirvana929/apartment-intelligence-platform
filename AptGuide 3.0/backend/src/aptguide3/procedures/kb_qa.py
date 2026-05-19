from __future__ import annotations

from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.rag.grounded_answer import (
    Citation,
    GroundedAnswer,
    build_conservative_grounded_fallback,
    build_grounded_prompt,
)
from aptguide3.rag.planning import build_retrieval_plan

SNIPPET_MAX_LEN = 200


class KbQaProcedure:
    name = "kb_qa"

    def __init__(
        self,
        vector_client: Any = None,
        embedding_client: Any = None,
        answer_client: Any = None,
        answer_model: str = "",
    ) -> None:
        self._vector = vector_client
        self._embedding = embedding_client
        self._answer_client = answer_client
        self._answer_model = answer_model

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        if self._vector is None or self._embedding is None:
            return self._conservative_fallback(understanding)

        plan = build_retrieval_plan(understanding)

        from aptguide3.rag.confidence import check_confidence, fallback_message
        from aptguide3.rag.diagnostics import KbRecDiagnostic
        from aptguide3.rag.kb_retrieval import retrieve_kb_sources

        diagnostic = KbRecDiagnostic(raw_message=understanding.raw_message)
        sources = retrieve_kb_sources(plan, self._vector, self._embedding, top_k=10, diagnostic=diagnostic)

        if not sources:
            diagnostic.failure_stage = diagnostic.failure_stage or "kb_vector_recall_empty"
            return ProcedureResult(
                message="已理解您的租房规则问题。知识库检索将在接入 retrieval 后返回带来源的回答。",
                phase="kb_qa",
                metadata={
                    "route": understanding.route,
                    "task": understanding.task,
                    "domain": understanding.domain,
                    "rec_diagnostic": diagnostic.to_report_dict(),
                },
            )

        if not check_confidence(sources, plan.risk_level):
            diagnostic.confidence_passed = False
            diagnostic.confidence_failure_reason = (
                f"source_count={len(sources)}, risk_level={plan.risk_level}"
            )
            return ProcedureResult(
                message=fallback_message(plan.risk_level),
                phase="kb_qa",
                metadata={
                    "confidence_passed": False,
                    "risk_level": plan.risk_level,
                    "source_count": len(sources),
                    "rec_diagnostic": diagnostic.to_report_dict(),
                },
            )

        diagnostic.confidence_passed = True
        cards = [_source_card(s) for s in sources[:5]]

        # --- Grounded answer generation ---
        grounded = self._generate_grounded_answer(
            understanding.raw_message, sources, plan.risk_level,
        )

        return ProcedureResult(
            message=grounded.answer,
            phase="kb_qa",
            cards=cards,
            metadata={
                "route": understanding.route,
                "task": understanding.task,
                "domain": understanding.domain,
                "risk_level": plan.risk_level,
                "source_count": len(sources),
                "confidence_passed": True,
                "grounded_answer": grounded.grounded,
                "citations": [c.model_dump() for c in grounded.citations],
                "evidence_count": len(grounded.citations),
                "fallback_reason": grounded.fallback_reason,
                "rec_diagnostic": diagnostic.to_report_dict(),
            },
        )

    # ------------------------------------------------------------------
    # Grounded answer generation
    # ------------------------------------------------------------------

    def _generate_grounded_answer(
        self,
        query: str,
        sources: list,
        risk_level: str,
    ) -> GroundedAnswer:
        """Call the answer LLM with an evidence-only prompt.

        Falls back deterministically if no answer client is configured or
        if the LLM call fails.
        """
        if self._answer_client is None:
            return build_conservative_grounded_fallback(
                query, risk_level, "no_answer_client",
            )

        source_dicts: list[dict[str, Any]] = []
        for s in sources[:5]:
            if hasattr(s, "model_dump"):
                source_dicts.append(s.model_dump())
            elif isinstance(s, dict):
                source_dicts.append(s)
            else:
                source_dicts.append({})

        prompt = build_grounded_prompt(query, source_dicts)

        try:
            response = self._answer_client.chat.completions.create(
                model=self._answer_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=512,
            )
            answer_text = (response.choices[0].message.content or "").strip()
        except Exception:
            return build_conservative_grounded_fallback(
                query, risk_level, "llm_call_failed",
            )

        if not answer_text:
            return build_conservative_grounded_fallback(
                query, risk_level, "empty_llm_response",
            )

        citations = [
            Citation(
                chunk_id=getattr(s, "chunk_id", "") or (s.get("chunk_id", "") if isinstance(s, dict) else ""),
                doc_id=getattr(s, "doc_id", "") or (s.get("doc_id", "") if isinstance(s, dict) else ""),
                title=getattr(s, "title", "") or (s.get("title", "") if isinstance(s, dict) else ""),
            )
            for s in sources[:5]
        ]

        return GroundedAnswer(
            answer=answer_text,
            citations=citations,
            grounded=True,
            fallback_reason="",
        )

    def _conservative_fallback(self, understanding: UnderstandingResult) -> ProcedureResult:
        return ProcedureResult(
            message="已理解您的租房规则问题。知识库检索将在接入 retrieval 后返回带来源的回答。",
            phase="kb_qa",
            metadata={"route": understanding.route, "task": understanding.task, "domain": understanding.domain},
        )


def _source_card(source: Any) -> dict[str, Any]:
    if hasattr(source, "model_dump"):
        data = source.model_dump()
    elif isinstance(source, dict):
        data = source
    else:
        data = {}
    content = data.get("content", "")
    snippet = content[:SNIPPET_MAX_LEN] + ("..." if len(content) > SNIPPET_MAX_LEN else "")
    return {
        "type": "kb_source",
        "chunk_id": data.get("chunk_id", ""),
        "doc_id": data.get("doc_id", ""),
        "title": data.get("title", ""),
        "module": data.get("module", ""),
        "content_snippet": snippet,
        "score": data.get("score", 0.0),
        "risk_level": data.get("risk_level", "low"),
    }
