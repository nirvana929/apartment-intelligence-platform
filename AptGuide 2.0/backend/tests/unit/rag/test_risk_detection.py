"""Tests for risk detection: rule signals, classifier, and policy matrix."""

from aptguide2.rag.risk_detection import (
    HeuristicRiskClassifier,
    detect_risk_profile,
    scan_risk_signals,
)

# ---------------------------------------------------------------------------
# Rule Signal Scanner
# ---------------------------------------------------------------------------


def test_external_complaint_signal_sets_high_floor():
    scan = scan_risk_signals("我要打 12315")

    assert "external_complaint_channel" in scan.rule_signals
    assert scan.non_downgrade_level == "high"
    assert "do_not_downgrade_below_high" in scan.hard_constraints


def test_refund_term_is_sensitive_but_not_direct_high():
    scan = scan_risk_signals("退钱规则是什么")

    assert "refund_sensitive_topic" in scan.rule_signals
    assert scan.force_semantic_classifier is True
    assert scan.non_downgrade_level is None


def test_explicit_financial_claim_signal():
    scan = scan_risk_signals("你们必须退钱")

    assert "refund_sensitive_topic" in scan.rule_signals
    assert "explicit_financial_claim" in scan.rule_signals
    assert "do_not_promise_refund" in scan.hard_constraints


def test_privacy_abuse_signal_sets_high_floor():
    scan = scan_risk_signals("查一下我室友的手机号")

    assert "unauthorized_privacy_request" in scan.rule_signals
    assert scan.non_downgrade_level == "high"
    assert "do_not_disclose_third_party_private_info" in scan.hard_constraints


# ---------------------------------------------------------------------------
# Structured Semantic Classifier
# ---------------------------------------------------------------------------


def test_classifier_policy_question_for_deposit():
    result = HeuristicRiskClassifier().classify("押金什么时候退", scan_risk_signals("押金什么时候退"))

    assert result.topic == "deposit_refund"
    assert result.action == "ask_policy"
    assert result.confidence >= 0.7


def test_classifier_refund_request():
    result = HeuristicRiskClassifier().classify("把押金退给我", scan_risk_signals("把押金退给我"))

    assert result.topic == "deposit_refund"
    assert result.action == "request_action"


def test_classifier_language_question_is_low_intent():
    result = HeuristicRiskClassifier().classify("退钱这个词是什么意思", scan_risk_signals("退钱这个词是什么意思"))

    assert result.topic == "language_question"
    assert result.action == "ask_definition"


def test_classifier_complaint_escalation_without_standard_complaint_word():
    result = HeuristicRiskClassifier().classify("我要找消协", scan_risk_signals("我要找消协"))

    assert result.topic == "complaint_escalation"
    assert result.action == "escalation"


# ---------------------------------------------------------------------------
# Policy Matrix
# ---------------------------------------------------------------------------


def test_deposit_policy_is_medium_not_blocked():
    profile = detect_risk_profile("押金什么时候退")

    assert profile.risk_level == "medium"
    assert profile.response_mode == "kb_grounded_answer"
    assert "refund_sensitive_topic" in profile.rule_signals


def test_refund_request_is_high_template_not_refuse():
    profile = detect_risk_profile("把押金退给我")

    assert profile.risk_level == "high"
    assert profile.response_mode == "template_answer"
    assert "do_not_promise_refund" in profile.hard_constraints


def test_12315_is_high_handoff_and_cannot_downgrade():
    profile = detect_risk_profile("我要打 12315")

    assert profile.risk_level == "high"
    assert profile.response_mode == "handoff_to_human"
    assert "do_not_downgrade_below_high" in profile.hard_constraints


def test_third_party_privacy_is_refuse():
    profile = detect_risk_profile("查一下我室友的手机号")

    assert profile.risk_level == "high"
    assert profile.response_mode == "refuse"


def test_language_question_with_refund_word_is_low():
    profile = detect_risk_profile("退钱这个词是什么意思")

    assert profile.risk_level == "low"
    assert profile.response_mode == "normal_answer"
