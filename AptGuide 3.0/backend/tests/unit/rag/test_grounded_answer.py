from __future__ import annotations

from aptguide3.rag.grounded_answer import (
    Citation,
    GroundedAnswer,
    build_conservative_grounded_fallback,
    build_grounded_prompt,
    build_room_result_message,
)

# ---------------------------------------------------------------------------
# Task 1 / Task 6: Data type and citation tests
# ---------------------------------------------------------------------------


def test_high_risk_kb_answer_contains_citations_when_sources_pass():
    answer = GroundedAnswer(
        answer="押金处理需以合同和平台规则为准。[KB-LS-011]",
        citations=[Citation(chunk_id="KB-LS-011", doc_id="KB-LS-011", title="签约后可以反悔吗")],
        grounded=True,
    )
    assert answer.grounded is True
    assert answer.citations[0].doc_id == "KB-LS-011"
    assert answer.citations[0].chunk_id == "KB-LS-011"
    assert answer.fallback_reason == ""


def test_high_risk_kb_answer_falls_back_when_no_citations():
    answer = build_conservative_grounded_fallback("押金不退怎么办", "high", "no_citations")
    assert answer.grounded is False
    assert answer.fallback_reason == "no_citations"
    assert "无法基于现有资料给出确定回答" in answer.answer


def test_medium_risk_fallback_uses_medium_message():
    answer = build_conservative_grounded_fallback("预约流程", "medium", "no_citations")
    assert answer.grounded is False
    assert answer.fallback_reason == "no_citations"
    assert "进一步确认" in answer.answer


def test_low_risk_fallback_uses_low_message():
    answer = build_conservative_grounded_fallback("附近超市", "low", "no_sources")
    assert answer.grounded is False
    assert answer.fallback_reason == "no_sources"
    assert "换个问法" in answer.answer


def test_room_search_does_not_claim_availability_without_lease_validation():
    card = {"evidence_level": "vector_only", "lease_validation_status": "not_checked"}
    message = build_room_result_message([card], risk_level="medium")
    assert "确认可租" not in message
    assert "确认可预约" not in message
    assert "尚未通过租赁系统验证" in message


def test_room_search_with_lease_validated_claims_normally():
    card = {"evidence_level": "lease_validated", "lease_validation_status": "passed"}
    message = build_room_result_message([card], risk_level="medium")
    assert "找到 1 间符合条件的房源" in message
    assert "尚未通过" not in message


def test_room_search_low_risk_no_disclaimer():
    card = {"evidence_level": "vector_only", "lease_validation_status": "not_checked"}
    message = build_room_result_message([card], risk_level="low")
    assert "找到 1 间符合条件的房源" in message
    assert "尚未通过" not in message


def test_room_search_empty_cards():
    message = build_room_result_message([], risk_level="medium")
    assert "暂未找到" in message


def test_build_grounded_prompt_includes_sources():
    sources = [
        {"chunk_id": "c1", "doc_id": "d1", "title": "押金规则", "content": "押金一个月"},
        {"chunk_id": "c2", "doc_id": "d2", "title": "退房流程", "content": "提前30天通知"},
    ]
    prompt = build_grounded_prompt("押金怎么算", sources)
    assert "押金怎么算" in prompt
    assert "chunk_id=c1" in prompt
    assert "chunk_id=c2" in prompt
    assert "不要承诺退款" in prompt


def test_build_grounded_prompt_caps_sources():
    sources = [
        {"chunk_id": f"c{i}", "doc_id": f"d{i}", "title": f"t{i}", "content": f"content{i}"}
        for i in range(10)
    ]
    prompt = build_grounded_prompt("test", sources, max_sources=3)
    assert "chunk_id=c0" in prompt
    assert "chunk_id=c2" in prompt
    assert "chunk_id=c3" not in prompt


def test_grounded_answer_model_defaults():
    answer = GroundedAnswer(answer="test")
    assert answer.citations == []
    assert answer.grounded is False
    assert answer.fallback_reason == ""


def test_citation_model_defaults():
    citation = Citation()
    assert citation.chunk_id == ""
    assert citation.doc_id == ""
    assert citation.title == ""


def test_high_risk_room_search_with_mixed_evidence():
    cards = [
        {"evidence_level": "lease_validated", "lease_validation_status": "passed"},
        {"evidence_level": "vector_only", "lease_validation_status": "not_checked"},
    ]
    message = build_room_result_message(cards, risk_level="high")
    # Has at least one lease-validated card, so no disclaimer
    assert "找到 2 间符合条件的房源" in message
    assert "尚未通过" not in message


def test_high_risk_room_search_all_vector_only():
    cards = [
        {"evidence_level": "vector_only", "lease_validation_status": "not_checked"},
        {"evidence_level": "vector_only", "lease_validation_status": "not_checked"},
    ]
    message = build_room_result_message(cards, risk_level="high")
    assert "尚未通过租赁系统验证" in message
    assert "联系门店确认" in message
