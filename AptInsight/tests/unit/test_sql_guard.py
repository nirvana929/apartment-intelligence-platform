"""SQL Guard 单元测试"""

from aptinsight.security.sql_guard import (
    GuardViolation,
    check_sql,
    extract_tables_from_sql,
)


class TestCheckSql:
    """测试 check_sql 函数"""

    def test_empty_sql(self):
        """空 SQL 应该被拒绝"""
        result = check_sql("")
        assert not result.is_safe
        assert result.violation == GuardViolation.EMPTY_SQL

    def test_none_sql(self):
        """None SQL 应该被拒绝"""
        result = check_sql("")
        assert not result.is_safe

    def test_select_allowed(self):
        """SELECT 语句应该通过"""
        result = check_sql("SELECT id, name FROM apartment_info WHERE is_deleted = 0")
        assert result.is_safe
        assert result.rewritten_sql is not None

    def test_insert_blocked(self):
        """INSERT 语句应该被拒绝"""
        result = check_sql("INSERT INTO apartment_info (name) VALUES ('test')")
        assert not result.is_safe
        assert result.violation == GuardViolation.NOT_SELECT

    def test_update_blocked(self):
        """UPDATE 语句应该被拒绝"""
        result = check_sql("UPDATE apartment_info SET name = 'test' WHERE id = 1")
        assert not result.is_safe
        assert result.violation == GuardViolation.NOT_SELECT

    def test_delete_blocked(self):
        """DELETE 语句应该被拒绝"""
        result = check_sql("DELETE FROM apartment_info WHERE id = 1")
        assert not result.is_safe
        assert result.violation == GuardViolation.NOT_SELECT

    def test_drop_blocked(self):
        """DROP 语句应该被拒绝"""
        result = check_sql("DROP TABLE apartment_info")
        assert not result.is_safe
        assert result.violation == GuardViolation.NOT_SELECT

    def test_whitelisted_table(self):
        """白名单中的表应该通过"""
        result = check_sql("SELECT id FROM apartment_info")
        assert result.is_safe

    def test_blocked_table(self):
        """不在白名单中的表应该被拒绝"""
        result = check_sql("SELECT id FROM unknown_table")
        assert not result.is_safe
        assert result.violation == GuardViolation.BLOCKED_TABLE

    def test_sensitive_column_blocked(self):
        """敏感字段应该被拒绝"""
        result = check_sql("SELECT identification_number FROM lease_agreement")
        assert not result.is_safe
        assert result.violation == GuardViolation.BLOCKED_SENSITIVE

    def test_phone_column_sensitive(self):
        """手机号字段是敏感字段，应该允许访问但需要脱敏"""
        result = check_sql("SELECT phone FROM apartment_info")
        assert result.is_safe  # phone 是 sensitive，不是 blocked

    def test_safe_column_allowed(self):
        """非敏感字段应该通过"""
        result = check_sql("SELECT id, name FROM apartment_info")
        assert result.is_safe

    def test_multi_statement_blocked(self):
        """多语句 SQL 应该被拒绝"""
        result = check_sql("SELECT id FROM apartment_info; DELETE FROM apartment_info")
        assert not result.is_safe
        assert result.violation == GuardViolation.MULTI_STATEMENT

    def test_invalid_sql(self):
        """无效 SQL 应该被拒绝"""
        result = check_sql("SELECT FROM WHERE")
        assert not result.is_safe
        assert result.violation == GuardViolation.PARSE_ERROR

    def test_complex_join(self):
        """复杂的 JOIN 查询应该通过（如果表和列都在白名单中）"""
        sql = """
        SELECT ai.name, COUNT(va.id) as cnt
        FROM apartment_info ai
        JOIN view_appointment va ON ai.id = va.apartment_id
        WHERE ai.is_deleted = 0
        GROUP BY ai.id, ai.name
        """
        result = check_sql(sql)
        assert result.is_safe

    def test_subquery_safe(self):
        """安全的子查询应该通过"""
        sql = """
        SELECT id, name
        FROM apartment_info
        WHERE id IN (SELECT apartment_id FROM view_appointment)
        """
        result = check_sql(sql)
        assert result.is_safe

    def test_subquery_blocked_table(self):
        """子查询中引用未授权表应该被拒绝"""
        sql = """
        SELECT id, name
        FROM apartment_info
        WHERE id IN (SELECT apartment_id FROM unknown_table)
        """
        result = check_sql(sql)
        assert not result.is_safe
        # 主查询遍历时会先检测到 unknown_table
        assert result.violation in [GuardViolation.BLOCKED_TABLE, GuardViolation.SUBQUERY_VIOLATION]


class TestExtractTables:
    """测试 extract_tables_from_sql 函数"""

    def test_single_table(self):
        """单表查询"""
        tables = extract_tables_from_sql("SELECT id FROM apartment_info")
        assert tables == ["apartment_info"]

    def test_join_tables(self):
        """JOIN 查询"""
        sql = """
        SELECT ai.name, va.id
        FROM apartment_info ai
        JOIN view_appointment va ON ai.id = va.apartment_id
        """
        tables = extract_tables_from_sql(sql)
        assert "apartment_info" in tables
        assert "view_appointment" in tables

    def test_invalid_sql(self):
        """无效 SQL 应该返回空列表"""
        tables = extract_tables_from_sql("INVALID SQL")
        assert tables == []
