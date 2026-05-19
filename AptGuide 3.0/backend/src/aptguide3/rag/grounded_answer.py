from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: str = ""
    doc_id: str = ""
    title: str = ""


class GroundedAnswer(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    grounded: bool = False
    fallback_reason: str = ""


# ---------------------------------------------------------------------------
# Evidence-only prompt builder (Task 2)
# ---------------------------------------------------------------------------

_SYSTEM_INSTRUCTIONS = (
    "你只能使用下面提供的资料来回答用户问题。\n"
    "每条事实或政策声明必须标注来源 chunk_id 和 doc_id。\n"
    "如果资料不足以回答，返回保守的兜底说明。\n"
    "不要承诺退款、房源可租、预约成功、合同变更或运营人员操作。\n"
)


def build_grounded_prompt(
    query: str,
    sources: list[dict[str, Any]],
    max_sources: int = 5,
) -> str:
    """Build a prompt that restricts the LLM to *only* use provided sources.

    Parameters
    ----------
    query:
        The user's original question.
    sources:
        Each dict must contain at least ``chunk_id``, ``doc_id``, ``title``,
        and ``content``.  Additional keys are ignored.
    max_sources:
        Cap on how many sources to include in the prompt.
    """
    source_blocks: list[str] = []
    for i, src in enumerate(sources[:max_sources], 1):
        chunk_id = src.get("chunk_id", "")
        doc_id = src.get("doc_id", "")
        title = src.get("title", "")
        content = src.get("content", "")
        source_blocks.append(
            f"[资料{i}] chunk_id={chunk_id}, doc_id={doc_id}, title={title}\n{content}"
        )

    sources_text = "\n\n".join(source_blocks) if source_blocks else "(无可用资料)"

    return (
        f"{_SYSTEM_INSTRUCTIONS}\n\n"
        f"---\n用户问题: {query}\n\n"
        f"可用资料:\n{sources_text}\n\n"
        f"---\n请基于以上资料回答，并在每条声明后标注 [chunk_id]。"
    )


# ---------------------------------------------------------------------------
# Deterministic conservative fallback (Task 3)
# ---------------------------------------------------------------------------

_HIGH_RISK_FALLBACK = (
    "您的问题涉及合同、押金、退款或账户安全等重要内容，我暂时无法基于现有资料给出确定回答。"
    "为保障您的权益，建议通过官方客服或门店工作人员进行确认。"
)

_MEDIUM_RISK_FALLBACK = (
    "您的问题需要进一步确认，我暂时无法基于现有资料给出确定回答。"
    "建议联系门店客服核实相关信息。"
)

_LOW_RISK_FALLBACK = (
    "我暂时没有找到足够相关的资料来回答您的问题，建议换个问法或联系人工客服。"
)


def build_conservative_grounded_fallback(
    query: str,
    risk_level: str,
    reason: str,
) -> GroundedAnswer:
    """Return a deterministic ``GroundedAnswer`` with no citations.

    For high-risk queries the message explicitly directs the user to a
    verified channel or human follow-up.
    """
    if risk_level == "high":
        answer = _HIGH_RISK_FALLBACK
    elif risk_level == "medium":
        answer = _MEDIUM_RISK_FALLBACK
    else:
        answer = _LOW_RISK_FALLBACK

    return GroundedAnswer(
        answer=answer,
        citations=[],
        grounded=False,
        fallback_reason=reason,
    )


# ---------------------------------------------------------------------------
# Room result message builder (Task 5 helper)
# ---------------------------------------------------------------------------

def build_room_result_message(
    cards: list[dict[str, Any]],
    risk_level: str = "low",
) -> str:
    """Build a user-facing message for room search results.

    If ``risk_level`` is medium/high and no cards carry
    ``lease_validation_status == "passed"``, the message uses conservative
    language that avoids claiming confirmed availability.
    """
    if not cards:
        return "暂未找到符合条件的房源，请调整筛选条件后重试。"

    has_lease_validated = any(
        c.get("lease_validation_status") == "passed"
        or c.get("evidence_level") in ("lease_validated", "lease_validated_with_freshness")
        for c in cards
    )

    count = len(cards)

    if risk_level in ("medium", "high") and not has_lease_validated:
        return (
            f"找到 {count} 间可能符合条件的房源（尚未通过租赁系统验证），"
            "请在看房前联系门店确认实际可租状态。"
        )

    return f"找到 {count} 间符合条件的房源"
