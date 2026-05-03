"""
失败原因归类模块

用规则判断"为什么不能答"，不依赖 LLM。
LLM 只负责后续的润色，不决定安全边界。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .state import AgentState


class FailureReason(str, Enum):
    """失败原因枚举，按归类优先级排列"""

    PRIVACY_QUERY = "privacy_query"
    WRITE_OPERATION = "write_operation"
    SCHEMA_UNSUPPORTED = "schema_unsupported"
    SQL_GUARD_FAILED = "sql_guard_failed"
    SQL_GENERATION_FAILED = "sql_generation_failed"
    DATABASE_ERROR = "database_error"
    EMPTY_RESULT = "empty_result"
    INTENT_FAILED = "intent_failed"
    OUT_OF_SCOPE = "out_of_scope"
    UNKNOWN = "unknown"


@dataclass
class FailureContext:
    """失败上下文，包含原因、用户可读解释和改问建议"""

    reason: FailureReason
    user_reason: str
    suggestions: list[str] = field(default_factory=list)


# ============================================================================
# 关键词规则表（优先级从高到低）
# ============================================================================

_PRIVACY_KEYWORDS = ["张三", "李四", "手机号", "身份证", "身份证号", "租客记录", "个人记录", "入住的租客", "租客信息"]

_WRITE_KEYWORDS = ["删除", "修改", "更新", "改成", "下架", "新增", "添加", "创建", "插入", "改一下"]

_PAYMENT_KEYWORDS = ["收款", "实收", "流水", "付款", "支付", "到账", "回款"]

_ROOM_APPOINTMENT_KEYWORDS_PAIRS = [
    (["房间"], ["预约"]),
]


def classify_failure(state: AgentState) -> FailureContext:
    """
    根据 state 中的 question / intent / error / rows 等信息，
    用规则判断失败原因，返回 FailureContext。

    不调用 LLM，纯规则，稳定可控。
    """
    question = state.get("question", "")
    error = state.get("error") or ""
    rows = state.get("rows", [])
    intent = state.get("intent", "")

    # --- 1. 隐私查询（最高优先级）---
    if any(kw in question for kw in _PRIVACY_KEYWORDS):
        return FailureContext(
            reason=FailureReason.PRIVACY_QUERY,
            user_reason="这个问题涉及租客个人信息，系统默认不支持按个人身份查询明细。",
            suggestions=["5月新增租约有多少", "各公寓新签租约数量排名"],
        )

    # --- 2. 写操作 ---
    if any(kw in question for kw in _WRITE_KEYWORDS):
        return FailureContext(
            reason=FailureReason.WRITE_OPERATION,
            user_reason="系统只支持查看和分析数据，不能修改、删除或新增业务数据。",
            suggestions=["当前已发布房间有多少", "各公寓空置房间数量排名"],
        )

    # --- 3. 支付流水缺失 ---
    if any(kw in question for kw in _PAYMENT_KEYWORDS):
        return FailureContext(
            reason=FailureReason.SCHEMA_UNSUPPORTED,
            user_reason="当前数据中没有支付流水记录，不能统计实际收款金额。",
            suggestions=["本月有效租约的合同月租金规模", "当前有效租约数量"],
        )

    # --- 4. 房间级预约缺失 ---
    for required, trigger in _ROOM_APPOINTMENT_KEYWORDS_PAIRS:
        if all(kw in question for kw in required) and all(kw in question for kw in trigger):
            return FailureContext(
                reason=FailureReason.SCHEMA_UNSUPPORTED,
                user_reason="预约数据目前只记录到公寓维度，没有细分到具体房间。",
                suggestions=["本月各公寓预约量排名", "最近30天浏览量最高的公寓"],
            )

    # --- 5. SQL 守卫失败 ---
    if error and "SQL 安全检查失败" in error:
        return FailureContext(
            reason=FailureReason.SQL_GUARD_FAILED,
            user_reason="这个查询涉及不允许访问的数据范围，系统做了安全拦截。",
            suggestions=["换成聚合统计类问题", "避免查询个人身份、手机号等敏感字段"],
        )

    # --- 6. SQL 生成失败 ---
    if error and ("SQL 生成失败" in error or "生成的 SQL 无效" in error):
        return FailureContext(
            reason=FailureReason.SQL_GENERATION_FAILED,
            user_reason="系统没能稳定理解这个问题，可能是表述不够明确或超出了当前数据范围。",
            suggestions=["请明确时间范围和统计对象", "例如：5月各公寓新增租约数量"],
        )

    # --- 7. 数据库错误 ---
    if error and "SQL 执行失败" in error:
        return FailureContext(
            reason=FailureReason.DATABASE_ERROR,
            user_reason="查询数据时遇到了问题，请稍后再试。",
            suggestions=["换个时间范围试试", "用更简单的条件重新提问"],
        )

    # --- 8. 意图识别失败 ---
    if error and "意图识别失败" in error:
        return FailureContext(
            reason=FailureReason.INTENT_FAILED,
            user_reason="系统没能理解这个问题，请稍后重试或换个方式描述。",
            suggestions=["用一句完整的话描述你的需求", "例如：本月各公寓预约量排名"],
        )

    # --- 9. 空结果 ---
    if not rows and not error and intent == "analysis":
        return FailureContext(
            reason=FailureReason.EMPTY_RESULT,
            user_reason="没有查到符合条件的数据，可能是时间范围内确实没有记录，也可能是筛选条件太窄。",
            suggestions=["放宽时间范围", "换成按公寓或月份的汇总统计"],
        )

    # --- 10. 超出范围 ---
    if intent == "out_of_scope":
        return FailureContext(
            reason=FailureReason.OUT_OF_SCOPE,
            user_reason="这个问题不在公寓运营分析范围内。",
            suggestions=["本月各公寓预约量排名", "当前有效租约数量"],
        )

    # --- 11. 兜底 ---
    return FailureContext(
        reason=FailureReason.UNKNOWN,
        user_reason="系统暂时无法稳定回答这个问题。",
        suggestions=["请换成预约量、签约情况、租金、空置率等运营统计问题"],
    )


def generate_static_fallback(ctx: FailureContext) -> str:
    """
    纯静态兜底回复，不调 LLM。
    当 LLM 润色失败时使用。
    """
    parts = [ctx.user_reason]
    if ctx.suggestions:
        suggestions_text = "、".join(f"“{s}”" for s in ctx.suggestions[:2])
        parts.append(f"你可以试试这样问：{suggestions_text}。")
    return "".join(parts)
