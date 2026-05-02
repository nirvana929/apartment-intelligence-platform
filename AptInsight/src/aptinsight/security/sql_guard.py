"""
SQL 守卫模块

本模块负责对 LLM 生成的 SQL 进行安全检查，确保：
1. 只允许 SELECT 查询（禁止 INSERT/UPDATE/DELETE/DROP 等）
2. 只访问白名单中的表和列
3. 拒绝多语句 SQL（防止 SQL 注入）
4. 拒绝子查询中的危险操作

安全策略：
- 使用 sqlglot 进行 SQL AST 解析，比正则表达式更安全可靠
- 所有检查都在 AST 层面进行，无法通过字符串混淆绕过
- 默认拒绝，只有通过所有检查的 SQL 才能执行
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from .table_policy import (
    get_table_policy,
    is_column_allowed,
    is_column_blocked,
)


class GuardViolation(Enum):
    """
    SQL 守卫违规类型枚举

    每种违规类型对应一种安全风险，用于错误提示和日志记录
    """
    NOT_SELECT = "not_select"              # 非 SELECT 语句
    MULTI_STATEMENT = "multi_statement"    # 多语句 SQL
    BLOCKED_TABLE = "blocked_table"        # 访问未授权的表
    BLOCKED_COLUMN = "blocked_column"      # 访问未授权的列
    BLOCKED_SENSITIVE = "blocked_sensitive"  # 访问被禁止的敏感字段（如身份证号）
    PARSE_ERROR = "parse_error"            # SQL 解析失败
    EMPTY_SQL = "empty_sql"                # 空 SQL
    SUBQUERY_VIOLATION = "subquery_violation"  # 子查询违规


@dataclass(frozen=True)
class GuardResult:
    """
    SQL 守卫检查结果

    Attributes:
        is_safe: SQL 是否通过所有安全检查
        violation: 违规类型（如果 is_safe=False）
        message: 详细的错误信息
        rewritten_sql: 重写后的安全 SQL（如果 is_safe=True）
    """
    is_safe: bool
    violation: Optional[GuardViolation] = None
    message: str = ""
    rewritten_sql: Optional[str] = None


def check_sql(sql: str) -> GuardResult:
    """
    检查 SQL 的安全性

    这是 SQL 守卫的主入口函数，对传入的 SQL 进行全面的安全检查。

    Args:
        sql: LLM 生成的原始 SQL 字符串

    Returns:
        GuardResult: 检查结果，包含是否安全、违规类型、错误信息等

    Example:
        >>> result = check_sql("SELECT * FROM apartment_info")
        >>> print(result.is_safe)  # True

        >>> result = check_sql("DELETE FROM apartment_info")
        >>> print(result.is_safe)  # False
        >>> print(result.violation)  # GuardViolation.NOT_SELECT
    """
    # 第一步：基础校验
    if not sql or not sql.strip():
        return GuardResult(
            is_safe=False,
            violation=GuardViolation.EMPTY_SQL,
            message="SQL 语句为空"
        )

    # 第二步：解析 SQL 为 AST
    # 使用 sqlglot 将 SQL 字符串解析为抽象语法树
    try:
        # dialect="mysql" 指定使用 MySQL 方言解析
        # 这样可以正确处理 MySQL 特有的语法
        ast = sqlglot.parse_one(sql, dialect="mysql")
    except SqlglotError as e:
        return GuardResult(
            is_safe=False,
            violation=GuardViolation.PARSE_ERROR,
            message=f"SQL 解析失败: {str(e)}"
        )

    # 第三步：检查是否为单条语句
    # sqlglot.parse_one 会抛出异常如果有多条语句
    # 但为了安全起见，我们再检查一次
    try:
        statements = sqlglot.parse(sql, dialect="mysql")
        if len(statements) > 1:
            return GuardResult(
                is_safe=False,
                violation=GuardViolation.MULTI_STATEMENT,
                message=f"检测到多条 SQL 语句（共 {len(statements)} 条），只允许单条 SELECT"
            )
    except SqlglotError:
        pass  # parse_one 已经成功，这里失败不影响

    # 第四步：检查是否为 SELECT 语句
    # 只允许 SELECT，禁止 INSERT/UPDATE/DELETE/DROP 等
    if not isinstance(ast, exp.Select):
        return GuardResult(
            is_safe=False,
            violation=GuardViolation.NOT_SELECT,
            message=f"只允许 SELECT 语句，检测到: {type(ast).__name__}"
        )

    # 第五步：检查所有涉及的表是否在白名单中
    # 使用 AST 的 find_all 方法查找所有 Table 节点
    tables_used: set[str] = set()
    for table_node in ast.find_all(exp.Table):
        table_name = table_node.name
        tables_used.add(table_name)

        # 检查表是否在白名单中
        policy = get_table_policy(table_name)
        if not policy:
            return GuardResult(
                is_safe=False,
                violation=GuardViolation.BLOCKED_TABLE,
                message=f"表 '{table_name}' 不在允许访问的白名单中"
            )

    # 第六步：检查所有涉及的列是否在白名单中
    # 先收集 SELECT 子句中定义的所有别名（如 COUNT(x) AS cnt 中的 cnt）
    # ORDER BY / GROUP BY 中引用这些别名时，sqlglot 会解析为 Column 节点，需要跳过
    alias_names: set[str] = set()
    for alias_node in ast.find_all(exp.Alias):
        alias_names.add(alias_node.alias)

    # 使用 AST 的 find_all 方法查找所有 Column 节点
    for col_node in ast.find_all(exp.Column):
        # 跳过别名定义中的列名（父节点为 Alias）
        if isinstance(col_node.parent, exp.Alias):
            continue
        # 跳过引用别名的列名（如 ORDER BY alias_name）
        if col_node.name in alias_names and not col_node.table:
            continue

        col_name = col_node.name
        # 获取列所属的表名
        # 如果列有表限定符（如 t.column），使用限定符
        # 否则需要从上下文推断（这里简化处理，检查所有使用的表）
        table_alias = col_node.table if col_node.table else None

        if table_alias:
            # 列有表限定符，直接检查
            policy = get_table_policy(table_alias)
            if policy:
                if not is_column_allowed(policy.name, col_name):
                    return GuardResult(
                        is_safe=False,
                        violation=GuardViolation.BLOCKED_COLUMN,
                        message=f"列 '{table_alias}.{col_name}' 不在允许访问的白名单中"
                    )
                if is_column_blocked(policy.name, col_name):
                    return GuardResult(
                        is_safe=False,
                        violation=GuardViolation.BLOCKED_SENSITIVE,
                        message=f"列 '{table_alias}.{col_name}' 是敏感字段，禁止访问"
                    )
        else:
            # 列没有表限定符，检查所有使用的表
            # 这种情况常见于 SELECT id FROM table
            column_allowed = False
            for table_name in tables_used:
                if is_column_allowed(table_name, col_name):
                    column_allowed = True
                    if is_column_blocked(table_name, col_name):
                        return GuardResult(
                            is_safe=False,
                            violation=GuardViolation.BLOCKED_SENSITIVE,
                            message=f"列 '{col_name}' 在表 '{table_name}' 中是敏感字段，禁止访问"
                        )
                    break

            if not column_allowed and tables_used:
                # 列在任何表中都不被允许
                return GuardResult(
                    is_safe=False,
                    violation=GuardViolation.BLOCKED_COLUMN,
                    message=f"列 '{col_name}' 不在任何允许访问的表的白名单中"
                )

    # 第七步：检查子查询的安全性
    # 递归检查所有子查询
    for subquery in ast.find_all(exp.Subquery):
        subquery_result = _check_subquery(subquery)
        if not subquery_result.is_safe:
            return subquery_result

    # 所有检查通过，返回安全结果
    # 使用 sqlglot 重新生成规范化的 SQL
    rewritten = ast.sql(dialect="mysql")

    return GuardResult(
        is_safe=True,
        rewritten_sql=rewritten,
        message="SQL 安全检查通过"
    )


def _check_subquery(subquery: exp.Subquery) -> GuardResult:
    """
    检查子查询的安全性

    递归检查子查询中的表和列是否在白名单中。

    Args:
        subquery: sqlglot 子查询节点

    Returns:
        GuardResult: 检查结果
    """
    # 获取子查询内部的 SELECT 语句
    inner_select = subquery.find(exp.Select)
    if not inner_select:
        return GuardResult(is_safe=True)

    # 检查子查询中的表
    for table_node in inner_select.find_all(exp.Table):
        table_name = table_node.name
        policy = get_table_policy(table_name)
        if not policy:
            return GuardResult(
                is_safe=False,
                violation=GuardViolation.SUBQUERY_VIOLATION,
                message=f"子查询中引用了未授权的表: {table_name}"
            )

    # 检查子查询中的列（白名单 + blocked）
    inner_tables: set[str] = set()
    for t in inner_select.find_all(exp.Table):
        inner_tables.add(t.name)

    for col_node in inner_select.find_all(exp.Column):
        col_name = col_node.name
        table_alias = col_node.table if col_node.table else None

        if table_alias:
            policy = get_table_policy(table_alias)
            if policy:
                if not is_column_allowed(policy.name, col_name):
                    return GuardResult(
                        is_safe=False,
                        violation=GuardViolation.SUBQUERY_VIOLATION,
                        message=f"子查询中引用了未授权的列: {table_alias}.{col_name}"
                    )
                if is_column_blocked(policy.name, col_name):
                    return GuardResult(
                        is_safe=False,
                        violation=GuardViolation.SUBQUERY_VIOLATION,
                        message=f"子查询中引用了敏感字段: {table_alias}.{col_name}"
                    )
        else:
            for table_name in inner_tables:
                if is_column_blocked(table_name, col_name):
                    return GuardResult(
                        is_safe=False,
                        violation=GuardViolation.SUBQUERY_VIOLATION,
                        message=f"子查询中引用了敏感字段: {col_name}"
                    )

    return GuardResult(is_safe=True)


def extract_tables_from_sql(sql: str) -> list[str]:
    """
    从 SQL 中提取所有涉及的表名

    用于日志记录和审计追踪。

    Args:
        sql: SQL 语句

    Returns:
        表名列表（去重）
    """
    try:
        ast = sqlglot.parse_one(sql, dialect="mysql")
        tables = set()
        for table_node in ast.find_all(exp.Table):
            tables.add(table_node.name)
        return list(tables)
    except SqlglotError:
        return []


def extract_columns_from_sql(sql: str) -> list[tuple[str, str]]:
    """
    从 SQL 中提取所有涉及的列名

    返回格式：[(表名/别名, 列名), ...]

    Args:
        sql: SQL 语句

    Returns:
        (表名, 列名) 元组列表
    """
    try:
        ast = sqlglot.parse_one(sql, dialect="mysql")
        columns = set()
        for col_node in ast.find_all(exp.Column):
            table = col_node.table if col_node.table else ""
            columns.add((table, col_node.name))
        return list(columns)
    except SqlglotError:
        return []
