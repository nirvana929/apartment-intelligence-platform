from __future__ import annotations

from aptguide3.rag.confidence import check_confidence, fallback_message
from aptguide3.rag.schemas import KBSource


def _source(chunk_id: str = "c1", module: str = "lease", score: float = 0.8, risk_level: str = "low") -> KBSource:
    return KBSource(
        chunk_id=chunk_id,
        doc_id="d1",
        title="title",
        module=module,
        content="content",
        score=score,
        risk_level=risk_level,
    )


def test_empty_sources_returns_false():
    assert check_confidence([], "low") is False


def test_low_risk_passes_with_any_good_score():
    sources = [_source(score=0.5)]
    assert check_confidence(sources, "low") is True


def test_low_risk_fails_below_threshold():
    sources = [_source(score=0.3)]
    assert check_confidence(sources, "low") is False


def test_high_risk_requires_high_risk_lease_source():
    sources = [_source(module="lease", risk_level="high", score=0.8)]
    assert check_confidence(sources, "high") is True


def test_high_risk_rejects_low_risk_source_even_with_good_score():
    sources = [_source(module="lease", risk_level="low", score=0.9)]
    assert check_confidence(sources, "high") is False


def test_high_risk_rejects_non_high_risk_modules():
    sources = [_source(module="life", risk_level="high", score=0.8)]
    assert check_confidence(sources, "high") is False


def test_medium_risk_needs_high_risk_module_in_top3():
    sources = [_source(module="life", score=0.7), _source(chunk_id="c2", module="payment", score=0.6)]
    assert check_confidence(sources, "medium") is True


def test_medium_risk_fails_without_high_risk_module():
    sources = [_source(module="life", score=0.7), _source(chunk_id="c2", module="appointment", score=0.6)]
    assert check_confidence(sources, "medium") is False


def test_fallback_message_high():
    msg = fallback_message("high")
    assert "合同" in msg or "人工客服" in msg


def test_fallback_message_medium():
    msg = fallback_message("medium")
    assert "核实" in msg


def test_fallback_message_low():
    msg = fallback_message("low")
    assert "换个问法" in msg
