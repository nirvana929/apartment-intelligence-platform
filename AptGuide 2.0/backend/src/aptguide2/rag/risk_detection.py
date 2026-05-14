"""Risk-aware query guardrail for AptGuide 2.0.

Architecture:
1. Rule signals scan deterministic red-line signals and sensitive-topic features.
2. A structured classifier produces topic/action/object/attitude/confidence.
3. A policy matrix decides risk_level and response_mode.
4. A non-downgrade floor prevents strong safety rules from being overridden.

Most medium/high-risk questions are routed safely, not blocked.
Only privacy abuse and unsupported dangerous requests are refused.
"""

from __future__ import annotations

import re
from typing import Protocol

from aptguide2.rag.schemas import (
    RiskClassifierResult,
    RiskProfile,
    RiskSignalScan,
)

# ---------------------------------------------------------------------------
# Rule Signal Scanner
# ---------------------------------------------------------------------------

STRONG_HIGH_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"12315|消协|消费者协会|市场监管|市监局", "external_complaint_channel"),
    (r"起诉|法院见|律师函|报警", "legal_escalation"),
    (r"曝光|找媒体|发小红书|发微博", "public_escalation"),
)

PRIVACY_PATTERNS: tuple[str, ...] = (
    r"查.*(别人|室友|其他租户).*(手机号|电话|身份证|合同|租约)",
    r"(别人|室友|其他租户).*(手机号|电话|身份证|合同|租约).*(给我|发我|查一下)",
)

SENSITIVE_TOPIC_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"押金|退款|退钱|还钱|扣钱|扣款", "refund_sensitive_topic"),
    (r"退租|退房|解约|解除合同|违约金|合同|转租", "contract_sensitive_topic"),
    (r"投诉|举报|维权|纠纷", "complaint_sensitive_topic"),
    (r"隐私|实名|身份证|手机号|电话", "privacy_sensitive_topic"),
)

EXPLICIT_FINANCIAL_CLAIM_PATTERNS: tuple[str, ...] = (
    r"(我要|给我|必须|立刻|马上).*(退钱|退款|还钱|退押金)",
    r"(退钱|退款|还钱|退押金).*(给我|必须|立刻|马上)",
    r"把.*(押金|退款|钱).*(退|还).*(给我|回来)",
    r"凭什么.*扣.*(钱|款|押金)",
    r"不(退钱|退款|还钱).*投诉",
    r"(我要|给我|必须).*(解除合同|退租|解约)",
)


def scan_risk_signals(message: str) -> RiskSignalScan:
    """Scan deterministic safety signals without making the final risk decision."""
    signals: list[str] = []
    constraints: list[str] = []
    non_downgrade_level = None
    force_semantic_classifier = False

    for pattern, signal in STRONG_HIGH_PATTERNS:
        if re.search(pattern, message):
            signals.append(signal)
            non_downgrade_level = "high"
            constraints.append("do_not_downgrade_below_high")
            force_semantic_classifier = True

    if any(re.search(pattern, message) for pattern in PRIVACY_PATTERNS):
        signals.append("unauthorized_privacy_request")
        non_downgrade_level = "high"
        constraints.extend([
            "do_not_downgrade_below_high",
            "do_not_disclose_third_party_private_info",
        ])
        force_semantic_classifier = True

    for pattern, signal in SENSITIVE_TOPIC_PATTERNS:
        if re.search(pattern, message):
            signals.append(signal)
            force_semantic_classifier = True

    if any(re.search(pattern, message) for pattern in EXPLICIT_FINANCIAL_CLAIM_PATTERNS):
        signals.append("explicit_financial_claim")
        constraints.extend([
            "do_not_promise_refund",
            "do_not_make_final_financial_decision",
        ])
        force_semantic_classifier = True

    return RiskSignalScan(
        rule_signals=_dedupe(signals),
        hard_constraints=_dedupe(constraints),
        non_downgrade_level=non_downgrade_level,
        force_semantic_classifier=force_semantic_classifier,
    )


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


# ---------------------------------------------------------------------------
# Structured Semantic Classifier
# ---------------------------------------------------------------------------


class RiskClassifier(Protocol):
    """Semantic risk classifier interface.

    A production adapter can call an LLM with structured output. Unit tests use
    HeuristicRiskClassifier so the guardrail remains deterministic.
    """

    def classify(self, message: str, scan: RiskSignalScan) -> RiskClassifierResult:
        ...


class HeuristicRiskClassifier:
    """Deterministic classifier used as local fallback and unit-test oracle."""

    def classify(self, message: str, scan: RiskSignalScan) -> RiskClassifierResult:
        if re.search(r"(这个词是什么意思|翻译|英文)", message):
            return RiskClassifierResult(
                topic="language_question",
                action="ask_definition",
                object="language",
                confidence=0.85,
                reason="语言解释问题，不是租赁业务诉求",
            )

        if "unauthorized_privacy_request" in scan.rule_signals:
            return RiskClassifierResult(
                topic="privacy_access",
                action="unauthorized_query",
                object="third_party_private_info",
                attitude="neutral",
                confidence=0.95,
                reason="用户请求第三方隐私信息",
            )

        if any(signal in scan.rule_signals for signal in (
            "external_complaint_channel",
            "legal_escalation",
            "public_escalation",
        )):
            return RiskClassifierResult(
                topic="complaint_escalation",
                action="escalation",
                object="complaint",
                attitude="angry",
                confidence=0.92,
                reason="用户表达投诉或外部升级意图",
            )

        if "explicit_financial_claim" in scan.rule_signals:
            if re.search(r"(解除合同|退租|解约)", message):
                return RiskClassifierResult(
                    topic="contract_termination",
                    action="request_action",
                    object="contract",
                    attitude="dissatisfied",
                    confidence=0.88,
                    reason="用户提出明确退租或解约诉求",
                )
            return RiskClassifierResult(
                topic="deposit_refund",
                action="request_action",
                object="money",
                attitude="dissatisfied",
                confidence=0.88,
                reason="用户提出明确退款或还款诉求",
            )

        if re.search(r"我的.*(退款|押金|退租).*(进度|到哪|处理)", message):
            return RiskClassifierResult(
                topic="deposit_refund",
                action="query_status",
                object="own_business_status",
                confidence=0.82,
                reason="用户查询自己的退款或退租状态",
            )

        if re.search(r"押金|退款|退钱|还钱|扣钱|扣款", message):
            return RiskClassifierResult(
                topic="deposit_refund",
                action="ask_policy",
                object="deposit_or_refund_policy",
                confidence=0.78,
                reason="用户询问押金或退款政策",
            )

        if re.search(r"退租|退房|解约|解除合同|违约金|合同|转租", message):
            return RiskClassifierResult(
                topic="contract_termination",
                action="ask_policy",
                object="contract_or_termination_policy",
                confidence=0.78,
                reason="用户询问合同或退租政策",
            )

        return RiskClassifierResult(
            topic="unknown",
            action="unknown",
            confidence=0.55,
            reason="未识别到明确风险语义",
        )


# ---------------------------------------------------------------------------
# Policy Matrix
# ---------------------------------------------------------------------------

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def detect_risk_profile(message: str, classifier: RiskClassifier | None = None) -> RiskProfile:
    """Detect risk profile using rule signals, semantic classification, and policy matrix."""
    scan = scan_risk_signals(message)
    classifier = classifier or HeuristicRiskClassifier()
    semantic = classifier.classify(message, scan)
    profile = _apply_policy_matrix(semantic, scan)
    return _apply_non_downgrade_floor(profile, scan)


def _apply_policy_matrix(semantic: RiskClassifierResult, scan: RiskSignalScan) -> RiskProfile:
    risk_level = "low"
    response_mode = "normal_answer"

    if semantic.topic in {"deposit_refund", "contract_termination", "normal_policy"}:
        if semantic.action == "ask_policy":
            risk_level = "medium"
            response_mode = "kb_grounded_answer"
        elif semantic.action == "query_status":
            risk_level = "medium"
            response_mode = "authenticated_tool_query"
        elif semantic.action in {"request_action", "dispute"}:
            risk_level = "high"
            response_mode = "template_answer"

    if semantic.topic == "complaint_escalation":
        risk_level = "high"
        response_mode = "handoff_to_human"

    if semantic.topic == "privacy_access":
        if semantic.action == "unauthorized_query":
            risk_level = "high"
            response_mode = "refuse"
        else:
            risk_level = "medium"
            response_mode = "authenticated_tool_query"

    if semantic.topic == "language_question":
        risk_level = "low"
        response_mode = "normal_answer"

    return RiskProfile(
        topic=semantic.topic,
        action=semantic.action,
        object=semantic.object,
        attitude=semantic.attitude,
        confidence=semantic.confidence,
        risk_level=risk_level,
        response_mode=response_mode,
        rule_signals=scan.rule_signals,
        hard_constraints=scan.hard_constraints,
        reason=semantic.reason,
    )


def _apply_non_downgrade_floor(profile: RiskProfile, scan: RiskSignalScan) -> RiskProfile:
    if scan.non_downgrade_level is None:
        return profile

    if RISK_ORDER[profile.risk_level] >= RISK_ORDER[scan.non_downgrade_level]:
        return profile

    return profile.model_copy(update={
        "risk_level": scan.non_downgrade_level,
        "response_mode": "handoff_to_human" if scan.non_downgrade_level == "high" else profile.response_mode,
        "hard_constraints": _dedupe(profile.hard_constraints + ["do_not_downgrade_below_high"]),
    })
