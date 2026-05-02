"""
SQL 守卫节点模块

本模块负责对 LLM 生成的 SQL 进行安全检查，确保 SQL 符合安全策略。
这是安全架构的第一道防线，在 SQL 执行前进行检查。

学习要点：
1. 安全守卫模式 - 在执行前检查安全性
2. SQL AST 解析 - 使用 sqlglot 进行语法分析
3. 白名单机制 - 只允许访问预定义的表和列
4. 错误处理 - 如何优雅地处理安全违规

安全检查项：
1. 只允许 SELECT 语句
2. 拒绝多语句 SQL
3. 检查表是否在白名单中
4. 检查列是否在白名单中
5. 拦截敏感字段（如身份证号）

工作流程：
SQL → 安全检查 → 通过/拒绝 → 更新状态
"""

from __future__ import annotations

from ...core.logging import get_logger
from ...security.sql_guard import GuardResult, GuardViolation, check_sql
from ..state import AgentState

# 获取日志记录器
logger = get_logger(__name__)


# ============================================================================
# SQL 守卫节点函数
# ============================================================================

async def guard_sql(state: AgentState) -> AgentState:
    """
    SQL 守卫节点

    这个节点负责：
    1. 读取生成的 SQL
    2. 调用 SQL 守卫进行安全检查
    3. 根据检查结果更新状态
    4. 如果检查通过，保存重写后的 SQL

    Args:
        state: 当前状态

    Returns:
        更新后的状态

    学习要点：
    - 安全检查：在执行前验证 SQL 的安全性
    - 状态更新：根据检查结果更新状态
    - 错误传播：将安全违规信息传递给后续节点
    """
    generated_sql = state.get("generated_sql")

    # 如果没有生成的 SQL，跳过检查
    if not generated_sql:
        logger.warning("没有生成的 SQL，跳过安全检查")
        return {
            **state,
            "sql_guard_result": {
                "passed": False,
                "message": "没有生成的 SQL",
                "violation": "no_sql",
            },
            "error": "没有生成的 SQL",
        }

    logger.info(f"开始 SQL 安全检查，SQL: {generated_sql[:100]}")

    try:
        # 调用 SQL 守卫进行安全检查
        # 学习要点：使用之前实现的安全模块
        result: GuardResult = check_sql(generated_sql)

        # 构造检查结果
        guard_result = {
            "passed": result.is_safe,
            "message": result.message,
            "violation": result.violation.value if result.violation else None,
            "rewritten_sql": result.rewritten_sql,
        }

        if result.is_safe:
            # 检查通过
            logger.info(f"SQL 安全检查通过，重写后: {result.rewritten_sql[:100]}")

            return {
                **state,
                "safe_sql": result.rewritten_sql,
                "sql_guard_result": guard_result,
            }
        else:
            # 检查失败
            violation = result.violation.value if result.violation else "unknown"
            logger.warning(f"SQL 安全检查失败，违规: {violation}，原因: {result.message}")

            return {
                **state,
                "sql_guard_result": guard_result,
                "error": f"SQL 安全检查失败: {result.message}",
            }

    except Exception as e:
        # 异常处理
        logger.error(f"SQL 守卫检查异常，错误: {e}")

        return {
            **state,
            "sql_guard_result": {
                "passed": False,
                "message": f"SQL 守卫检查异常: {str(e)}",
                "violation": "guard_error",
            },
            "error": f"SQL 守卫检查异常: {str(e)}",
        }


# ============================================================================
# 辅助函数
# ============================================================================

def get_violation_message(violation: GuardViolation) -> str:
    """
    获取违规类型的用户友好消息

    Args:
        violation: 违规类型枚举

    Returns:
        用户友好的错误消息

    学习要点：
    - 错误消息本地化：将技术错误转换为用户友好的消息
    - 枚举处理：处理不同的违规类型
    """
    messages = {
        GuardViolation.NOT_SELECT: "只允许查询操作，不支持修改数据",
        GuardViolation.MULTI_STATEMENT: "不支持一次执行多条 SQL 语句",
        GuardViolation.BLOCKED_TABLE: "查询的表不在允许范围内",
        GuardViolation.BLOCKED_COLUMN: "查询的字段不在允许范围内",
        GuardViolation.BLOCKED_SENSITIVE: "查询包含敏感字段，已被拦截",
        GuardViolation.PARSE_ERROR: "SQL 语法错误，无法解析",
        GuardViolation.EMPTY_SQL: "SQL 语句为空",
        GuardViolation.SUBQUERY_VIOLATION: "子查询包含不允许的操作",
    }

    return messages.get(violation, "SQL 安全检查未通过")


def suggest_fix(violation: GuardViolation, message: str) -> str:
    """
    根据违规类型提供修复建议

    Args:
        violation: 违规类型
        message: 错误消息

    Returns:
        修复建议

    学习要点：
    - 用户体验：提供有用的修复建议
    - 引导用户：帮助用户理解如何修正问题
    """
    suggestions = {
        GuardViolation.NOT_SELECT: "请确保问题只需要查询数据，不需要修改",
        GuardViolation.MULTI_STATEMENT: "请将问题拆分为多个独立的查询",
        GuardViolation.BLOCKED_TABLE: "请检查问题是否涉及系统支持的业务表",
        GuardViolation.BLOCKED_COLUMN: "请检查问题是否需要查询系统允许的字段",
        GuardViolation.BLOCKED_SENSITIVE: "该字段涉及隐私，系统不允许查询",
        GuardViolation.PARSE_ERROR: "请尝试用更简单的方式描述您的问题",
        GuardViolation.EMPTY_SQL: "请重新描述您的问题",
        GuardViolation.SUBQUERY_VIOLATION: "请简化查询逻辑",
    }

    return suggestions.get(violation, "请尝试重新描述您的问题")


def is_recoverable_error(violation: GuardViolation) -> bool:
    """
    判断错误是否可恢复

    Args:
        violation: 违规类型

    Returns:
        True 如果错误可恢复（可以重试），否则 False

    学习要点：
    - 错误分类：区分可恢复和不可恢复的错误
    - 重试策略：决定是否需要重试
    """
    # 语法错误和解析错误通常可以通过重新生成 SQL 来修复
    recoverable_violations = {
        GuardViolation.PARSE_ERROR,
        GuardViolation.EMPTY_SQL,
    }

    return violation in recoverable_violations


# ============================================================================
# SQL 重写建议
# ============================================================================

def get_rewrite_suggestion(state: AgentState) -> str | None:
    """
    获取 SQL 重写建议

    如果 SQL 守卫检查失败，尝试提供建议的修改。

    Args:
        state: 当前状态

    Returns:
        重写建议，如果没有则返回 None

    学习要点：
    - 智能建议：根据错误类型提供具体的修改建议
    - 用户引导：帮助用户理解如何改进查询
    """
    guard_result = state.get("sql_guard_result", {})
    violation = guard_result.get("violation")

    if not violation:
        return None

    # 根据违规类型提供建议
    if violation == "blocked_table":
        return "请检查问题是否涉及系统支持的业务表，如 apartment_info, room_info, lease_agreement 等"
    elif violation == "blocked_column":
        return "请检查问题是否需要查询系统允许的字段，避免查询敏感信息"
    elif violation == "blocked_sensitive":
        return "该字段涉及隐私（如手机号、身份证号），系统不允许直接查询"
    elif violation == "not_select":
        return "系统只支持查询操作，请确保问题只需要读取数据"
    else:
        return None
