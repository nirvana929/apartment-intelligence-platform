"""
SQL 执行节点模块

本模块负责执行经过安全检查的 SQL 查询，并返回结果。
这是数据库交互的核心节点，使用 async MySQL 引擎执行查询。

学习要点：
1. 异步数据库操作 - 使用 SQLAlchemy async 引擎
2. 只读执行 - 确保只执行 SELECT 查询
3. 结果处理 - 将数据库结果转换为字典列表
4. 性能监控 - 记录查询执行时间
5. 错误处理 - 处理数据库连接和查询错误

工作流程：
安全 SQL → 建立连接 → 执行查询 → 获取结果 → 更新状态

安全保证：
1. 只执行经过守卫检查的 SQL
2. 使用只读数据库账号
3. 设置查询超时
4. 限制返回行数
"""

from __future__ import annotations

import time
from typing import Any

from ...core.logging import get_logger
from ...db.executor import execute_query
from ...security.redaction import redact_rows
from ..state import AgentState

# 获取日志记录器
logger = get_logger(__name__)

# 默认最大返回行数
# 学习要点：限制结果集大小，防止内存溢出和前端卡顿
DEFAULT_MAX_ROWS = 100


# ============================================================================
# SQL 执行节点函数
# ============================================================================

async def execute_sql(state: AgentState) -> AgentState:
    """
    SQL 执行节点

    这个节点负责：
    1. 读取经过安全检查的 SQL
    2. 执行数据库查询
    3. 对结果进行脱敏处理
    4. 更新状态

    Args:
        state: 当前状态

    Returns:
        更新后的状态

    学习要点：
    - 异步执行：使用 await 进行异步数据库操作
    - 性能监控：记录查询执行时间
    - 数据脱敏：对敏感字段进行脱敏处理
    """
    # 只执行经过 SQL 守卫检查并重写后的 SQL。
    safe_sql = state.get("safe_sql")

    # 如果没有安全 SQL，拒绝执行，避免绕过 guard_sql 直接执行 generated_sql。
    if not safe_sql:
        logger.warning("缺少经过安全检查的 SQL，拒绝执行")
        return {
            **state,
            "error": "缺少经过安全检查的 SQL，拒绝执行",
        }

    logger.info(f"开始执行 SQL 查询，SQL: {safe_sql[:100]}")

    # 记录开始时间
    # 学习要点：使用 time.monotonic() 测量时间，比 time.time() 更精确
    start_time = time.monotonic()

    try:
        # 执行查询
        # 学习要点：使用异步上下文管理器处理数据库连接
        raw_rows, columns = await execute_query(safe_sql, max_rows=DEFAULT_MAX_ROWS)

        # 计算执行时间
        execution_time_ms = (time.monotonic() - start_time) * 1000

        logger.info(
            "SQL 执行完成",
            extra={
                "row_count": len(raw_rows),
                "column_count": len(columns),
                "execution_time_ms": round(execution_time_ms, 2),
            },
        )

        # 将 list[list] 转换为 list[dict]，方便后续处理
        rows = [dict(zip(columns, row)) for row in raw_rows]

        # 对结果进行脱敏处理
        redacted_rows = redact_rows(rows)

        # 更新状态
        return {
            **state,
            "rows": redacted_rows,
            "columns": columns,
            "execution_time_ms": round(execution_time_ms, 2),
        }

    except Exception as e:
        # 计算执行时间（即使失败也要记录）
        execution_time_ms = (time.monotonic() - start_time) * 1000

        logger.error(
            "SQL 执行失败",
            extra={"error": str(e), "execution_time_ms": round(execution_time_ms, 2)},
        )

        return {
            **state,
            "error": f"SQL 执行失败: {str(e)}",
        }


# ============================================================================
# 结果处理辅助函数
# ============================================================================

def format_rows_for_display(rows: list[dict[str, Any]], max_rows: int = 20) -> list[dict[str, Any]]:
    """
    格式化结果行用于显示

    Args:
        rows: 原始结果行
        max_rows: 最大显示行数

    Returns:
        格式化后的结果行

    学习要点：
    - 数据格式化：将数据库结果转换为显示友好的格式
    - 行数限制：防止前端显示过多数据
    """
    if not rows:
        return []

    # 限制行数
    display_rows = rows[:max_rows]

    # 格式化每个字段的值
    formatted_rows = []
    for row in display_rows:
        formatted_row = {}
        for key, value in row.items():
            # 处理 None 值
            if value is None:
                formatted_row[key] = "-"
            # 处理数字格式化
            elif isinstance(value, float):
                formatted_row[key] = round(value, 2)
            # 处理日期格式化
            elif hasattr(value, "strftime"):
                formatted_row[key] = value.strftime("%Y-%m-%d")
            else:
                formatted_row[key] = value
        formatted_rows.append(formatted_row)

    return formatted_rows


def extract_column_names(columns: list[dict[str, Any]]) -> list[str]:
    """
    从列信息中提取列名

    Args:
        columns: 列信息列表（包含列名、类型等）

    Returns:
        列名列表

    学习要点：
    - 数据提取：从复杂结构中提取简单信息
    - 兼容性处理：处理不同的列信息格式
    """
    if not columns:
        return []

    # 如果列信息是字典列表，提取列名
    if isinstance(columns[0], dict):
        return [col.get("name", "") for col in columns]

    # 如果列信息已经是字符串列表，直接返回
    if isinstance(columns[0], str):
        return columns

    return []


def calculate_summary_stats(rows: list[dict[str, Any]], columns: list[str]) -> dict[str, Any]:
    """
    计算结果的摘要统计

    Args:
        rows: 结果行
        columns: 列名列表

    Returns:
        摘要统计信息

    学习要点：
    - 数据分析：计算基本的统计信息
    - 用于生成答案摘要
    """
    if not rows or not columns:
        return {}

    stats = {
        "total_rows": len(rows),
        "total_columns": len(columns),
        "column_names": columns,
    }

    # 尝试计算数值列的统计信息
    numeric_stats = {}
    for col in columns:
        values = [row.get(col) for row in rows if row.get(col) is not None]
        if values and all(isinstance(v, (int, float)) for v in values):
            numeric_stats[col] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

    if numeric_stats:
        stats["numeric_stats"] = numeric_stats

    return stats


# ============================================================================
# 错误处理辅助函数
# ============================================================================

def get_user_friendly_error(error: str) -> str:
    """
    将数据库错误转换为用户友好的消息

    Args:
        error: 原始错误消息

    Returns:
        用户友好的错误消息

    学习要点：
    - 错误本地化：将技术错误转换为用户能理解的消息
    - 错误分类：识别不同类型的数据库错误
    """
    error_lower = error.lower()

    # 连接错误
    if "connection" in error_lower or "connect" in error_lower:
        return "数据库连接失败，请稍后重试"

    # 语法错误
    if "syntax" in error_lower or "sql" in error_lower:
        return "查询语法错误，请尝试用更简单的方式描述您的问题"

    # 超时错误
    if "timeout" in error_lower:
        return "查询超时，请尝试缩小查询范围"

    # 权限错误
    if "permission" in error_lower or "access" in error_lower:
        return "数据库访问权限不足"

    # 表不存在
    if "table" in error_lower and "doesn't exist" in error_lower:
        return "查询的表不存在，请检查问题描述"

    # 列不存在
    if "column" in error_lower and "doesn't exist" in error_lower:
        return "查询的字段不存在，请检查问题描述"

    # 默认消息
    return "数据库查询失败，请稍后重试"
