"""
安全模块

本模块提供 AptInsight 系统的安全防护功能，包括：
1. table_policy - 表和列的白名单策略
2. sql_guard - SQL 安全检查守卫
3. redaction - 敏感字段脱敏

安全架构：
- 第一层：SQL 守卫（sql_guard）- 在 SQL 执行前检查安全性
- 第二层：结果脱敏（redaction）- 在结果返回前进行脱敏处理

使用示例：
    from aptinsight.security import check_sql, redact_rows

    # 检查 SQL 安全性
    result = check_sql("SELECT * FROM apartment_info")
    if result.is_safe:
        # 执行 SQL
        rows = execute_query(result.rewritten_sql)
        # 脱敏处理
        safe_rows = redact_rows(rows)
"""

from .sql_guard import (
    GuardResult,
    GuardViolation,
    check_sql,
    extract_columns_from_sql,
    extract_tables_from_sql,
)
from .table_policy import (
    ALLOWED_TABLES,
    ColumnPolicy,
    TablePolicy,
    get_blocked_columns,
    get_sensitive_columns,
    get_table_policy,
    is_column_allowed,
    is_column_blocked,
    is_column_sensitive,
)
from .redaction import (
    RedactionStats,
    is_id_card,
    redact_address,
    redact_name,
    redact_phone,
    redact_row,
    redact_rows,
    redact_rows_with_stats,
)

__all__ = [
    # SQL 守卫
    "check_sql",
    "GuardResult",
    "GuardViolation",
    "extract_tables_from_sql",
    "extract_columns_from_sql",

    # 表策略
    "ALLOWED_TABLES",
    "TablePolicy",
    "ColumnPolicy",
    "get_table_policy",
    "is_column_allowed",
    "is_column_sensitive",
    "is_column_blocked",
    "get_sensitive_columns",
    "get_blocked_columns",

    # 脱敏
    "redact_phone",
    "redact_name",
    "redact_address",
    "is_id_card",
    "redact_row",
    "redact_rows",
    "redact_rows_with_stats",
    "RedactionStats",
]
