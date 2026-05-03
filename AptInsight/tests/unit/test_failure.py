"""failure.py 的单元测试"""

from aptinsight.agent.failure import (
    FailureContext,
    FailureReason,
    classify_failure,
    generate_static_fallback,
)


# ============================================================================
# FailureReason 枚举测试
# ============================================================================


class TestFailureReason:
    def test_all_reasons_exist(self):
        assert FailureReason.PRIVACY_QUERY == "privacy_query"
        assert FailureReason.WRITE_OPERATION == "write_operation"
        assert FailureReason.SCHEMA_UNSUPPORTED == "schema_unsupported"
        assert FailureReason.SQL_GENERATION_FAILED == "sql_generation_failed"
        assert FailureReason.SQL_GUARD_FAILED == "sql_guard_failed"
        assert FailureReason.EMPTY_RESULT == "empty_result"
        assert FailureReason.DATABASE_ERROR == "database_error"
        assert FailureReason.INTENT_FAILED == "intent_failed"
        assert FailureReason.OUT_OF_SCOPE == "out_of_scope"
        assert FailureReason.UNKNOWN == "unknown"


# ============================================================================
# FailureContext 测试
# ============================================================================


class TestFailureContext:
    def test_has_required_fields(self):
        ctx = FailureContext(
            reason=FailureReason.UNKNOWN,
            user_reason="测试原因",
            suggestions=["建议1", "建议2"],
        )
        assert ctx.reason == FailureReason.UNKNOWN
        assert ctx.user_reason == "测试原因"
        assert ctx.suggestions == ["建议1", "建议2"]

    def test_defaults(self):
        ctx = FailureContext(
            reason=FailureReason.UNKNOWN,
            user_reason="测试",
        )
        assert ctx.suggestions == []


# ============================================================================
# classify_failure 规则归类测试
# ============================================================================


class TestClassifyFailurePrivacy:
    """隐私查询归类"""

    def test_zhangsan_record(self):
        state = {"question": "帮我查一下张三的记录", "intent": "out_of_scope"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.PRIVACY_QUERY
        assert "隐私" in ctx.user_reason or "个人" in ctx.user_reason
        assert len(ctx.suggestions) >= 1

    def test_phone_number(self):
        state = {"question": "查一下这个租客的手机号", "intent": "out_of_scope"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.PRIVACY_QUERY

    def test_id_card(self):
        state = {"question": "能查身份证号吗", "intent": "out_of_scope"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.PRIVACY_QUERY

    def test_tenant_record(self):
        state = {"question": "帮我查一下租客记录", "intent": "out_of_scope"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.PRIVACY_QUERY

    def test_may_tenants(self):
        state = {"question": "帮我查一下5月入住的租客", "intent": "out_of_scope"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.PRIVACY_QUERY


class TestClassifyFailureWriteOperation:
    """写操作归类"""

    def test_delete(self):
        state = {"question": "帮我删除这条记录", "intent": "out_of_scope"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.WRITE_OPERATION
        assert "只读" in ctx.user_reason or "不能" in ctx.user_reason or "不支持" in ctx.user_reason

    def test_modify_price(self):
        state = {"question": "帮我改一下房间价格", "intent": "out_of_scope"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.WRITE_OPERATION

    def test_update(self):
        state = {"question": "更新一下公寓信息", "intent": "out_of_scope"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.WRITE_OPERATION

    def test_add_room(self):
        state = {"question": "新增一个房间", "intent": "out_of_scope"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.WRITE_OPERATION


class TestClassifyFailureSchemaUnsupported:
    """数据结构不支持归类"""

    def test_actual_payment(self):
        state = {"question": "本月实际收款是多少", "intent": "analysis"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.SCHEMA_UNSUPPORTED
        assert "支付" in ctx.user_reason or "收款" in ctx.user_reason or "流水" in ctx.user_reason

    def test_payment_flow(self):
        state = {"question": "查一下付款流水", "intent": "analysis"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.SCHEMA_UNSUPPORTED

    def test_room_appointment(self):
        state = {"question": "预约量最高的房间有哪些", "intent": "analysis"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.SCHEMA_UNSUPPORTED
        assert "预约" in ctx.user_reason

    def test_actual_receipt(self):
        state = {"question": "这个月实收多少", "intent": "analysis"}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.SCHEMA_UNSUPPORTED


class TestClassifyFailureSqlGuardFailed:
    """SQL 守卫失败归类"""

    def test_guard_blocked_table(self):
        state = {
            "question": "查一下系统配置",
            "intent": "analysis",
            "error": "SQL 安全检查失败: 表 'sys_config' 不在允许访问的白名单中",
        }
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.SQL_GUARD_FAILED
        assert len(ctx.suggestions) >= 1

    def test_guard_blocked_sensitive(self):
        state = {
            "question": "查一下各公寓的联系人信息",
            "intent": "analysis",
            "error": "SQL 安全检查失败: 列 'info.phone' 是敏感字段，禁止访问",
        }
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.SQL_GUARD_FAILED


class TestClassifyFailureSqlGenerationFailed:
    """SQL 生成失败归类"""

    def test_generation_failed(self):
        state = {
            "question": "一些复杂问题",
            "intent": "analysis",
            "error": "SQL 生成失败: LLM 返回格式异常",
        }
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.SQL_GENERATION_FAILED

    def test_invalid_sql(self):
        state = {
            "question": "测试问题",
            "intent": "analysis",
            "error": "生成的 SQL 无效: 只允许 SELECT 语句",
        }
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.SQL_GENERATION_FAILED


class TestClassifyFailureDatabaseError:
    """数据库错误归类"""

    def test_connection_error(self):
        state = {
            "question": "本月预约量",
            "intent": "analysis",
            "error": "SQL 执行失败: Connection refused",
        }
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.DATABASE_ERROR

    def test_timeout_error(self):
        state = {
            "question": "本月预约量",
            "intent": "analysis",
            "error": "SQL 执行失败: Query timeout",
        }
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.DATABASE_ERROR


class TestClassifyFailureEmptyResult:
    """空结果归类"""

    def test_no_data_no_error(self):
        state = {
            "question": "本月预约量",
            "intent": "analysis",
            "rows": [],
            "error": None,
        }
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.EMPTY_RESULT


class TestClassifyFailureOutOfScope:
    """超出范围归类"""

    def test_stock_market(self):
        state = {"question": "最近股市怎么样", "intent": "out_of_scope", "error": None}
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.OUT_OF_SCOPE


class TestClassifyFailureIntentFailed:
    """意图识别失败归类"""

    def test_intent_error(self):
        state = {
            "question": "测试问题",
            "intent": "out_of_scope",
            "error": "意图识别失败: LLM 超时",
        }
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.INTENT_FAILED


class TestClassifyFailureUnknown:
    """未知错误归类"""

    def test_unknown_error(self):
        state = {
            "question": "测试问题",
            "intent": "analysis",
            "error": "一些奇怪的错误",
        }
        ctx = classify_failure(state)
        assert ctx.reason == FailureReason.UNKNOWN


# ============================================================================
# generate_static_fallback 测试
# ============================================================================


class TestGenerateStaticFallback:
    def test_contains_reason(self):
        ctx = FailureContext(
            reason=FailureReason.PRIVACY_QUERY,
            user_reason="系统不支持按个人身份查询",
            suggestions=["5月新增租约有多少"],
        )
        result = generate_static_fallback(ctx)
        assert "系统不支持按个人身份查询" in result

    def test_contains_suggestions(self):
        ctx = FailureContext(
            reason=FailureReason.SCHEMA_UNSUPPORTED,
            user_reason="没有支付流水数据",
            suggestions=["本月合同月租金规模", "有效租约数量"],
        )
        result = generate_static_fallback(ctx)
        assert "本月合同月租金规模" in result
        assert "有效租约数量" in result

    def test_no_suggestions(self):
        ctx = FailureContext(
            reason=FailureReason.UNKNOWN,
            user_reason="暂时无法回答",
            suggestions=[],
        )
        result = generate_static_fallback(ctx)
        assert "暂时无法回答" in result
