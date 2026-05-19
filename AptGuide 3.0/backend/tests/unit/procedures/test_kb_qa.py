from __future__ import annotations

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import RiskDecision, UnderstandingResult
from aptguide3.procedures.kb_qa import KbQaProcedure

FRAME = ConversationFrame(message="押金怎么算", session_id="s-1")
UNDERSTANDING = UnderstandingResult(
    raw_message="押金怎么算",
    route="rag",
    task="kb_qa",
    domain="payment",
    action="ask_policy",
    confidence=0.9,
    retrieval_queries=["押金规则"],
    risk=RiskDecision(level="low", response_mode="kb_grounded_answer"),
)

FALLBACK_MESSAGE = "已理解您的租房规则问题。知识库检索将在接入 retrieval 后返回带来源的回答。"

SAMPLE_HITS = [
    {
        "chunk_id": "c1",
        "doc_id": "d1",
        "title": "押金收取标准",
        "module": "payment",
        "content": "押金为一个月租金，退房时扣除损坏费用后退还。",
        "distance": 0.12,
        "risk_level": "low",
    },
    {
        "chunk_id": "c2",
        "doc_id": "d1",
        "title": "押金退还流程",
        "module": "payment",
        "content": "退房后15个工作日内完成押金退还。",
        "distance": 0.25,
        "risk_level": "low",
    },
]


_DEFAULT_VEC = [0.1, 0.2, 0.3]


class StubEmbedding:
    def __init__(self, vector: list[float] | None = None) -> None:
        self._vector = vector if vector is not None else _DEFAULT_VEC

    def embed(self, text: str) -> list[float]:
        return self._vector


class StubVector:
    def __init__(self, hits: list[dict] | None = None) -> None:
        self._hits = hits if hits is not None else SAMPLE_HITS

    def search_kb(self, vector: list[float], top_k: int = 10) -> list[dict]:
        return self._hits


def test_conservative_fallback_when_no_deps():
    proc = KbQaProcedure()
    result = proc.run(FRAME, UNDERSTANDING)
    assert result.message == FALLBACK_MESSAGE
    assert result.cards == []


def test_conservative_fallback_when_empty_hits():
    proc = KbQaProcedure(vector_client=StubVector(hits=[]), embedding_client=StubEmbedding())
    result = proc.run(FRAME, UNDERSTANDING)
    assert result.message == FALLBACK_MESSAGE


def test_confidence_gate_blocks_low_confidence_sources():
    high_risk_understanding = UnderstandingResult(
        raw_message="押金怎么算",
        route="rag",
        task="kb_qa",
        domain="payment",
        action="ask_policy",
        confidence=0.9,
        retrieval_queries=["押金规则"],
        risk=RiskDecision(level="high", response_mode="kb_grounded_answer"),
    )
    low_risk_hits = [
        {
            "chunk_id": "c1",
            "doc_id": "d1",
            "title": "押金收取标准",
            "module": "payment",
            "content": "押金为一个月租金。",
            "distance": 0.12,
            "risk_level": "low",
        },
    ]
    proc = KbQaProcedure(vector_client=StubVector(hits=low_risk_hits), embedding_client=StubEmbedding())
    result = proc.run(FRAME, high_risk_understanding)
    assert result.metadata.get("confidence_passed") is False
    assert result.cards == []


def test_success_returns_source_cards():
    proc = KbQaProcedure(vector_client=StubVector(), embedding_client=StubEmbedding())
    result = proc.run(FRAME, UNDERSTANDING)
    assert result.phase == "kb_qa"
    assert len(result.cards) > 0
    assert result.cards[0]["type"] == "kb_source"
    assert result.cards[0]["title"] == "押金收取标准"
    assert result.metadata.get("confidence_passed") is True


def test_success_cards_have_required_fields():
    proc = KbQaProcedure(vector_client=StubVector(), embedding_client=StubEmbedding())
    result = proc.run(FRAME, UNDERSTANDING)
    card = result.cards[0]
    assert "chunk_id" in card
    assert "doc_id" in card
    assert "title" in card
    assert "module" in card
    assert "content_snippet" in card
    assert "score" in card
    assert "risk_level" in card


def test_grounded_answer_metadata_present():
    proc = KbQaProcedure(vector_client=StubVector(), embedding_client=StubEmbedding())
    result = proc.run(FRAME, UNDERSTANDING)
    assert "grounded_answer" in result.metadata
    assert "citations" in result.metadata
    assert "evidence_count" in result.metadata
    assert "fallback_reason" in result.metadata
    # Without answer_client, grounded_answer should be False (fallback)
    assert result.metadata["grounded_answer"] is False
    assert result.metadata["fallback_reason"] == "no_answer_client"


def test_grounded_answer_fallback_reason_is_no_answer_client():
    proc = KbQaProcedure(vector_client=StubVector(), embedding_client=StubEmbedding())
    result = proc.run(FRAME, UNDERSTANDING)
    assert "无法基于现有资料" in result.message or "没有找到" in result.message
