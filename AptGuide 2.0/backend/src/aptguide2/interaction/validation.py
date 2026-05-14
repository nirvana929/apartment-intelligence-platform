from __future__ import annotations

from typing import Any

from aptguide2.interaction.contracts import InteractionIntent


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


def validate_or_clarify_intent(intent: InteractionIntent, min_confidence: float) -> InteractionIntent:
    if intent.confidence < min_confidence:
        return build_clarification_intent(intent.raw_message, "low_confidence")

    if intent.clarification_needed or intent.response_mode == "ask_clarification" or intent.action == "clarify":
        return build_clarification_intent(
            intent.raw_message,
            intent.reason or "model_requested_clarification",
            question=intent.clarification_question,
        )

    if not _route_shape_is_valid(intent):
        return build_clarification_intent(intent.raw_message, "invalid_route_shape")

    if not _hard_filters_are_valid(intent.hard_filters):
        return build_clarification_intent(intent.raw_message, "invalid_hard_filters")

    return intent


def build_clarification_intent(raw_message: str, reason: str, question: str = "") -> InteractionIntent:
    return InteractionIntent(
        raw_message=raw_message,
        route="fallback",
        rag_task="none",
        domain="unknown",
        action="clarify",
        confidence=0.0,
        response_mode="ask_clarification",
        clarification_needed=True,
        clarification_question=question or "请补充一下：您是想找房、咨询租房规则，还是处理预约/租约相关事项？",
        reason=reason,
    )


def _route_shape_is_valid(intent: InteractionIntent) -> bool:
    if intent.route == "rag":
        return intent.rag_task in {"kb_qa", "room_search"}
    if intent.route != "rag":
        return intent.rag_task == "none"
    return True


def _hard_filters_are_valid(filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        if key not in ALLOWED_HARD_FILTER_KEYS:
            return False
        if key in {"max_rent", "min_rent", "district_id", "apartment_id"}:
            if value is not None and not isinstance(value, int):
                return False
        if key == "payment_type" and value is not None and value not in ALLOWED_PAYMENT_TYPES:
            return False
        if key == "room_type" and value is not None and value not in ALLOWED_ROOM_TYPES:
            return False
        if key in {"district_name", "area_text"} and value is not None and not isinstance(value, str):
            return False
    return True
