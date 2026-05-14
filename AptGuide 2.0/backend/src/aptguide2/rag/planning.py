"""Retrieval planning for RAG v2.

This module separates deterministic control-plane parsing from semantic
retrieval planning. Character matching may seed hard filters and policy, but
semantic relevance must be handled downstream by hybrid retrieval and rerank.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from aptguide2.rag.schemas import QueryUnderstandingResult

TaskName = Literal["room_search", "kb_qa", "fallback"]
ValidationMode = Literal["none", "lease_required", "source_required"]
SourcePolicy = Literal["none", "source_required", "high_risk_source_required"]


class RetrievalPlan(BaseModel):
    task: TaskName
    raw_message: str
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    semantic_queries: list[str] = Field(default_factory=list)
    sparse_queries: list[str] = Field(default_factory=list)
    recall_channels: list[str] = Field(default_factory=list)
    module_intent: str | None = None
    risk_level: Literal["low", "medium", "high"] = "low"
    validation_mode: ValidationMode = "none"
    source_policy: SourcePolicy = "none"


def build_retrieval_plan(qr: QueryUnderstandingResult) -> RetrievalPlan:
    if qr.task == "fallback":
        return RetrievalPlan(
            task="fallback",
            raw_message=qr.raw_message,
            risk_level=qr.risk_level,
        )

    if qr.task == "room_search":
        semantic_queries = _dedupe([qr.raw_message, *qr.retrieval_queries])
        return RetrievalPlan(
            task="room_search",
            raw_message=qr.raw_message,
            hard_filters=dict(qr.hard_filters),
            soft_preferences=list(qr.soft_preferences),
            semantic_queries=semantic_queries,
            sparse_queries=_build_sparse_queries(qr),
            recall_channels=["dense", "sparse", "metadata"],
            risk_level=qr.risk_level,
            validation_mode="lease_required",
            source_policy="none",
        )

    module_intent = _infer_kb_module_intent(qr.raw_message)
    semantic_queries = _dedupe([qr.raw_message, *_build_kb_rewrite_queries(qr, module_intent)])
    recall_channels = ["dense", "sparse"]
    if qr.risk_level in ("medium", "high"):
        recall_channels.append("step_back")

    return RetrievalPlan(
        task="kb_qa",
        raw_message=qr.raw_message,
        hard_filters=dict(qr.hard_filters),
        soft_preferences=list(qr.soft_preferences),
        semantic_queries=semantic_queries,
        sparse_queries=_build_sparse_queries(qr),
        recall_channels=recall_channels,
        module_intent=module_intent,
        risk_level=qr.risk_level,
        validation_mode="source_required",
        source_policy="high_risk_source_required" if qr.risk_level == "high" else "source_required",
    )


def _build_sparse_queries(qr: QueryUnderstandingResult) -> list[str]:
    terms = [qr.raw_message, *qr.soft_preferences]
    area = qr.hard_filters.get("area_text")
    if area:
        terms.append(str(area))
    return _dedupe([t for t in terms if t])


def _build_kb_rewrite_queries(qr: QueryUnderstandingResult, module_intent: str | None) -> list[str]:
    queries: list[str] = []
    if module_intent:
        queries.append(f"{module_intent} {qr.raw_message}")
    if qr.risk_level in ("medium", "high"):
        queries.append(_step_back_query(qr.raw_message, module_intent))
    return [q for q in queries if q]


def _infer_kb_module_intent(message: str) -> str | None:
    # Enterprise boundary: this is a coarse policy hint, not final relevance ranking.
    module_terms = {
        "lease": ("合同", "租约", "签约", "退租", "押金", "续租", "违约", "转租"),
        "payment": ("支付", "租金", "水电", "退款", "发票", "逾期", "花呗"),
        "appointment": ("预约", "看房", "取消", "改期", "迟到"),
        "life": ("报修", "维修", "噪音", "宠物", "电器", "卫生", "快递"),
        "account": ("注册", "密码", "实名", "隐私", "注销", "账号"),
        "policy": ("优惠", "投诉", "换锁", "安全", "同住", "节假日"),
    }
    for module, terms in module_terms.items():
        if any(term in message for term in terms):
            return module
    return None


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
