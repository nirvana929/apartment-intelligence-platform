from __future__ import annotations

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.kb_qa import PLACEHOLDER_MESSAGE, KbQaProcedure

FRAME = ConversationFrame(message="押金怎么算", session_id="s-1")
UNDERSTANDING = UnderstandingResult(
    raw_message="押金怎么算",
    route="rag",
    task="kb_qa",
    domain="payment",
    action="ask_policy",
    confidence=0.9,
    retrieval_queries=["押金规则"],
)

SAMPLE_HITS = [
    {
        "chunk_id": "c1",
        "doc_id": "d1",
        "title": "押金收取标准",
        "module": "payment",
        "content": "押金为一个月租金，退房时扣除损坏费用后退还。",
        "distance": 0.12,
        "risk_level": "medium",
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
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return self._vector


class StubVector:
    def __init__(self, hits: list[dict] | None = None) -> None:
        self._hits = hits if hits is not None else SAMPLE_HITS
        self.last_top_k: int | None = None

    def search_kb(self, vector: list[float], top_k: int = 10) -> list[dict]:
        self.last_top_k = top_k
        return self._hits


def test_with_results_returns_source_cards():
    proc = KbQaProcedure(vector_client=StubVector(), embedding_client=StubEmbedding())

    result = proc.run(FRAME, UNDERSTANDING)

    assert result.phase == "kb_qa"
    assert len(result.cards) == 2
    assert result.cards[0]["title"] == "押金收取标准"
    assert result.cards[0]["risk_level"] == "medium"
    assert result.cards[0]["score"] == 0.12
    assert "content_snippet" in result.cards[0]
    assert result.metadata["source_count"] == 2
    assert result.metadata["risk_level"] == "medium"


def test_with_results_uses_retrieval_query_for_embedding():
    emb = StubEmbedding()
    proc = KbQaProcedure(vector_client=StubVector(), embedding_client=emb)

    proc.run(FRAME, UNDERSTANDING)

    assert emb.calls == ["押金规则"]


def test_with_results_falls_back_to_message_when_no_retrieval_query():
    emb = StubEmbedding()
    no_query = UnderstandingResult(
        raw_message="押金怎么算", route="rag", task="kb_qa", domain="payment", action="ask_policy", confidence=0.9,
    )
    proc = KbQaProcedure(vector_client=StubVector(), embedding_client=emb)

    proc.run(FRAME, no_query)

    assert emb.calls == ["押金怎么算"]


def test_empty_hits_returns_placeholder():
    proc = KbQaProcedure(vector_client=StubVector(hits=[]), embedding_client=StubEmbedding())

    result = proc.run(FRAME, UNDERSTANDING)

    assert result.message == PLACEHOLDER_MESSAGE
    assert result.cards == []


def test_empty_embedding_returns_placeholder():
    proc = KbQaProcedure(vector_client=StubVector(), embedding_client=StubEmbedding(vector=[]))

    result = proc.run(FRAME, UNDERSTANDING)

    assert result.message == PLACEHOLDER_MESSAGE


def test_no_clients_returns_placeholder():
    proc = KbQaProcedure()

    result = proc.run(FRAME, UNDERSTANDING)

    assert result.message == PLACEHOLDER_MESSAGE
    assert result.cards == []


def test_risk_level_high_wins():
    high_risk_hits = [
        {**SAMPLE_HITS[0], "risk_level": "high"},
        {**SAMPLE_HITS[1], "risk_level": "low"},
    ]
    proc = KbQaProcedure(vector_client=StubVector(hits=high_risk_hits), embedding_client=StubEmbedding())

    result = proc.run(FRAME, UNDERSTANDING)

    assert result.metadata["risk_level"] == "high"


def test_long_content_is_truncated():
    long_content = "a" * 300
    long_hit = {**SAMPLE_HITS[0], "content": long_content}
    proc = KbQaProcedure(vector_client=StubVector(hits=[long_hit]), embedding_client=StubEmbedding())

    result = proc.run(FRAME, UNDERSTANDING)

    assert len(result.cards[0]["content_snippet"]) == 203  # 200 + "..."
    assert result.cards[0]["content_snippet"].endswith("...")
