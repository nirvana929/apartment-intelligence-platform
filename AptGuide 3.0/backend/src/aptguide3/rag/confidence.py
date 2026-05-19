from __future__ import annotations

from aptguide3.rag.schemas import KBSource

THRESHOLDS = {"low": 0.40, "medium": 0.45, "high": 0.40}
HIGH_RISK_MODULES = {"lease", "payment", "account"}


def check_confidence(sources: list[KBSource], risk_level: str) -> bool:
    if not sources:
        return False
    top = sources[0]
    if top.score < THRESHOLDS.get(risk_level, THRESHOLDS["low"]):
        return False
    if risk_level == "medium":
        return any(source.module in HIGH_RISK_MODULES for source in sources[:3])
    if risk_level == "high":
        return any(
            source.risk_level == "high" and source.module in HIGH_RISK_MODULES
            for source in sources[:3]
        )
    return True


def fallback_message(risk_level: str) -> str:
    if risk_level == "high":
        return "这个问题涉及合同、押金、退款或账户安全，我暂时没有足够可靠的规则来源，建议联系门店或人工客服确认。"
    if risk_level == "medium":
        return "这个问题需要进一步确认，我暂时无法给出确定答复，建议联系门店客服核实。"
    return "我暂时没有找到足够相关的规则来源，请换个问法或联系人工客服。"
