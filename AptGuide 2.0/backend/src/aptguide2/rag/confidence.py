"""Confidence gate for KB retrieval results.

这是知识库 RAG 的安全阀：不是所有召回结果都应该被拿去生成答案。
当问题涉及押金、合同、违约金等高风险事项时，系统需要更高分数和更可靠来源。
"""

from __future__ import annotations

from aptguide2.rag.schemas import KBSource

# 风险越高，最低相似度阈值越高。
# 这些值是 MVP 人工阈值，应结合 eval 报告继续校准。
THRESHOLDS = {
    "low": 0.45,
    "medium": 0.55,
    "high": 0.65,
}

# High-risk modules that require source-level risk matching
HIGH_RISK_MODULES = {"lease", "payment"}


def check_confidence(sources: list[KBSource], risk_level: str) -> bool:
    """Check if retrieval results meet confidence threshold.

    Rules:
    - low: top score >= low threshold
    - medium: top score >= medium threshold AND module match
    - high: top score >= high threshold AND source has risk_level=high

    Args:
        sources: Ranked list of KB sources (best first).
        risk_level: Risk level of the query.

    Returns:
        True if confident enough to answer.
    """
    if not sources:
        return False

    threshold = THRESHOLDS.get(risk_level, THRESHOLDS["low"])
    top = sources[0]

    # 先做基础分数检查：最高分过低说明召回证据本身不够相关。
    if top.score < threshold:
        return False

    if risk_level == "medium":
        # 中风险问题不能只看分数，还要看前几个来源是否来自关键业务模块。
        return any(s.module in HIGH_RISK_MODULES for s in sources[:3])

    if risk_level == "high":
        # 高风险问题要求前几个来源里存在 risk_level=high 的租赁/支付来源。
        # 这能降低“低风险泛文档误答高风险问题”的概率。
        return any(
            s.risk_level == "high" and s.module in HIGH_RISK_MODULES
            for s in sources[:3]
        )

    return True


def get_fallback_message(risk_level: str) -> str:
    """Get user-facing fallback message when confidence is low."""
    if risk_level == "high":
        return (
            "关于押金、违约金等重要事项，建议您直接联系门店或查看租房合同条款，"
            "以获取最准确的信息。"
        )
    if risk_level == "medium":
        return (
            "这个问题我暂时无法给出确定的答案，建议您联系门店客服确认。"
        )
    return "抱歉，我暂时找不到相关信息，请稍后再试或联系门店。"
