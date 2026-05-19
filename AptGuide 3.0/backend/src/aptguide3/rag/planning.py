from __future__ import annotations

from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.rag.schemas import RetrievalPlan
from aptguide3.understanding.entity_resolution import resolve_entities


def build_retrieval_plan(understanding: UnderstandingResult) -> RetrievalPlan:
    if understanding.route != "rag":
        return RetrievalPlan(
            task="fallback",
            raw_message=understanding.raw_message,
            risk_level=understanding.risk.level,
        )

    # Resolve entities to canonical forms before building the plan
    resolution = resolve_entities(understanding.hard_filters)
    resolved_filters = resolution.resolved_filters

    if understanding.task == "room_search":
        semantic_queries = _dedupe([understanding.raw_message, *understanding.retrieval_queries])
        return RetrievalPlan(
            task="room_search",
            raw_message=understanding.raw_message,
            hard_filters=resolved_filters,
            soft_preferences=list(understanding.soft_preferences),
            semantic_queries=semantic_queries,
            sparse_queries=_build_sparse_queries(understanding, resolved_filters),
            risk_level=understanding.risk.level,
            validation_mode="lease_required",
            source_policy="none",
        )

    if understanding.task == "kb_qa":
        module_intent = (
            understanding.domain
            if understanding.domain in {"payment", "lease", "life", "appointment", "account", "policy"}
            else None
        )
        semantic_queries = _dedupe([
            understanding.raw_message,
            *understanding.retrieval_queries,
            _step_back_query(understanding.raw_message, module_intent),
        ])
        return RetrievalPlan(
            task="kb_qa",
            raw_message=understanding.raw_message,
            hard_filters=resolved_filters,
            soft_preferences=list(understanding.soft_preferences),
            semantic_queries=semantic_queries,
            sparse_queries=_build_sparse_queries(understanding, resolved_filters),
            module_intent=module_intent,
            risk_level=understanding.risk.level,
            validation_mode="source_required",
            source_policy="high_risk_source_required"
            if understanding.risk.level == "high"
            else "source_required",
        )

    return RetrievalPlan(
        task="fallback",
        raw_message=understanding.raw_message,
        risk_level=understanding.risk.level,
    )


def _build_sparse_queries(understanding: UnderstandingResult, resolved_filters: dict | None = None) -> list[str]:
    values = [understanding.raw_message, *understanding.soft_preferences]
    filters = resolved_filters or understanding.hard_filters
    area = filters.get("area_text") or filters.get("district_name")
    if area:
        values.append(str(area))
    return _dedupe(values)


def _step_back_query(message: str, module_intent: str | None) -> str:
    if module_intent == "lease":
        return f"租赁合同 押金 退租 违约 规则 {message}"
    if module_intent == "payment":
        return f"租金 支付 费用 退款 规则 {message}"
    if module_intent == "appointment":
        return f"看房预约 取消 改期 流程 {message}"
    return f"租房规则 流程 风险说明 {message}"


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result[:4]
