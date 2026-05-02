"""
SQL 查询执行器 —— 安全地执行只读 SQL。

这个文件的作用：
  提供一个统一的函数来执行 SQL 查询，并返回结构化的结果。
  它是整个项目中"唯一"执行 SQL 的地方（守门员角色）。

为什么需要这个"中间层"？
  直接用 SQLAlchemy 执行 SQL 也行，但我们需要统一做这些事：
    1. 设置查询超时 —— 防止一条慢查询拖垮整个服务
    2. 限制返回行数 —— 防止 LLM 生成 `SELECT *` 返回百万行
    3. 记录查询日志 —— 每条 SQL 执行了多久、返回多少行
    4. 测量耗时   —— 用于监控和性能分析

安全流程（后续会在 sql_guard.py 中实现）：
  LLM 生成 SQL → SQL 守卫校验 → 这个执行器执行 → 返回结果
  任何 SQL 在到达这里之前，必须先通过守卫校验。

实际使用场景：
  # 在 Agent 节点中这样用：
  from aptinsight.db.executor import execute_query

  rows, columns = await execute_query("SELECT name FROM apartment_info WHERE is_deleted = 0")
  print(columns)     # ["name"]
  print(rows)        # [["尚庭公寓"], ["阳光花园"]]
"""

import time
from dataclasses import dataclass

from sqlalchemy import text

from aptinsight.core.config import settings
from aptinsight.core.logging import get_logger
from aptinsight.db.engine import async_session_factory

logger = get_logger(__name__)


# [框架] @dataclass 自动生成 __init__、__repr__ 等方法
# 比手写 class 简洁，适合用来"打包"一组数据
@dataclass
class QueryResult:
    """
    SQL 查询结果的结构化表示。

    属性：
      columns: 列名列表，如 ["apartment_name", "appointment_count"]
      rows:    数据行列表，每行是一个列表，如 [["尚庭公寓", 42], ["阳光花园", 38]]
      row_count: 实际返回的行数（可能小于实际匹配数，因为有 max_rows 限制）
      duration_ms: 查询耗时（毫秒）
    """
    columns: list[str]    # 列名
    rows: list[list]      # 数据行
    row_count: int        # 行数
    duration_ms: float    # 耗时（毫秒）


# ============================================================================
# 核心执行函数
# ============================================================================

# [设计] 这是整个项目唯一执行 SQL 的地方
# 所有 SQL 必须先通过 sql_guard 校验才能到达这里
# 这个函数只做"执行 + 记录"，不做安全检查（安全检查在上游）
async def execute_query(sql: str, max_rows: int | None = None) -> tuple[list, list[str]]:
    """
    执行一条只读 SQL 查询，返回 (rows, columns) 元组。

    执行流程：
      1. 记录开始时间
      2. 从连接池获取一个数据库会话
      3. 执行 SQL（带超时限制）
      4. 获取列名和数据行（限制最大行数）
      5. 计算耗时，记录日志
      6. 返回 (rows, columns) 元组

    参数：
      sql: 要执行的 SQL 字符串，如 "SELECT name FROM apartment_info"
           注意：这里传入的 SQL 应该已经通过了 sql_guard 的校验！
      max_rows: 最大返回行数，默认使用配置中的 mysql_max_rows

    返回：
      (rows, columns) 元组：
        - rows: 数据行列表，每行是一个字典列表
        - columns: 列名列表

    异常：
      如果 SQL 语法错误或执行超时，会抛出异常。
      调用方需要 try/except 处理。
    """
    start = time.monotonic()
    limit = max_rows if max_rows is not None else settings.mysql_max_rows

    # [框架] SQLAlchemy 的事务管理：
    # session.begin() 开启事务 → session.execute() 执行 SQL → with 块结束自动提交/回滚
    # 即使只读查询，SQLAlchemy 默认也会开事务
    async with async_session_factory() as session:
        async with session.begin():
            # [框架] text() 把 SQL 字符串转成可执行对象
            # execution_options(timeout=...) 是 MySQL 级别的超时，不是 Python 级别
            stmt = text(sql).execution_options(timeout=settings.mysql_query_timeout_seconds)
            result = await session.execute(stmt)

            if result.returns_rows:
                columns = list(result.keys())
                # [框架] fetchmany(limit) 只取前 N 行，防止大查询拖垮内存
                raw_rows = result.fetchmany(limit)
                rows = [list(row) for row in raw_rows]
            else:
                columns = []
                rows = []

    # 计算查询耗时（毫秒）
    duration_ms = (time.monotonic() - start) * 1000

    # 记录查询日志
    # sql[:500] 截断 SQL，防止超长 SQL 撑爆日志
    logger.info(
        "query_executed",
        extra={
            "sql": sql[:500],
            "row_count": len(rows),
            "duration_ms": round(duration_ms, 2),
        },
    )

    # 返回 (rows, columns) 元组
    return rows, columns
