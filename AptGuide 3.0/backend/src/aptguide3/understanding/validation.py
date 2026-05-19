from __future__ import annotations

from typing import Any

from aptguide3.domain.understanding import Clarification, RiskDecision, UnderstandingResult

ALLOWED_HARD_FILTER_KEYS = {
    "max_rent",
    "min_rent",
    "district_id",
    "district_name",
    "area_text",
    "payment_type",
    "room_type",
    "apartment_id",
}
ALLOWED_PAYMENT_TYPES = {"MONTHLY", "QUARTERLY", "SEMI_ANNUAL", "ANNUAL"}
ALLOWED_ROOM_TYPES = {"STUDIO", "ONE_BEDROOM", "TWO_BEDROOM", "SHARED", "WHOLE_RENT", "UNKNOWN"}


def validation_failure_reason(result: UnderstandingResult, min_confidence: float) -> str:
    if result.confidence < min_confidence:
        return "low_confidence"
    if result.clarification.needed or result.risk.response_mode == "ask_clarification":
        return result.reason or "model_requested_clarification"
    if not _shape_is_valid(result):
        return "invalid_route_task_shape"
    if not _hard_filters_are_valid(result.hard_filters):
        return "invalid_hard_filters"
    return ""


def validate_or_clarify(result: UnderstandingResult, min_confidence: float) -> UnderstandingResult:
    reason = validation_failure_reason(result, min_confidence)
    if not reason:
        return result
    if reason == (result.reason or "model_requested_clarification"):
        return clarification_result(result.raw_message, reason, result.clarification.question)
    return clarification_result(result.raw_message, reason)


def clarification_result(raw_message: str, reason: str, question: str = "") -> UnderstandingResult:
    return UnderstandingResult(
        raw_message=raw_message,
        route="clarify",
        task="clarify",
        domain="unknown",
        action="ask_clarification",
        confidence=0.0,
        risk=RiskDecision(level="low", response_mode="ask_clarification"),
        clarification=Clarification(
            needed=True,
            question=question or "请补充一下：您是想找房、咨询租房规则，还是处理预约/租约相关事项？",
        ),
        reason=reason,
    )


def _shape_is_valid(result: UnderstandingResult) -> bool:
    if result.route == "rag":
        return result.task in {"room_search", "kb_qa"}
    if result.route == "clarify":
        return result.task == "clarify" and result.action == "ask_clarification"
    if result.route == "fallback":
        return result.task == "fallback"
    return result.task == result.route


def _hard_filters_are_valid(filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        if key not in ALLOWED_HARD_FILTER_KEYS:
            return False
        if key in {"max_rent", "min_rent", "district_id", "apartment_id"}:
            if value is not None and not isinstance(value, int):
                return False
        if key in {"district_name", "area_text"}:
            if value is not None and not isinstance(value, str):
                return False
        if key == "payment_type" and value is not None and value not in ALLOWED_PAYMENT_TYPES:
            return False
        if key == "room_type" and value is not None and value not in ALLOWED_ROOM_TYPES:
            return False
    return True
