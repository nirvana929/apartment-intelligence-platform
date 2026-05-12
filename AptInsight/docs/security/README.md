# 安全文档

> 权威来源：[`AptInsight文档/03-技术架构与模块设计.md`](../../AptInsight文档/03-技术架构与模块设计.md) 第 10 节

## 安全机制概览

AptInsight 采用三层安全防护：

1. **SQL 守卫** — 基于 sqlglot AST 解析，只允许 SELECT，表/列白名单，敏感字段拦截，多语句拒绝
2. **数据脱敏** — 手机号 `138****5678`，姓名 `张*`（2字）/ `张**`（3字）
3. **只读账号** — MySQL 账号仅授予 SELECT 权限

## SQL 守卫检查项

| 检查项 | 说明 |
|--------|------|
| 语句类型 | 只允许 SELECT |
| 表白名单 | 只允许访问预定义的业务表 |
| 列白名单 | 拒绝 password、identification_number 等 |
| 多语句 | 拒绝 `SELECT ...; DELETE ...` |
| 子查询 | 递归检查子查询安全性 |

白名单定义在 `src/aptinsight/security/table_policy.py`。

## 测试覆盖

- **安全评测用例**：6 个（DELETE/UPDATE/敏感字段/DROP/EXEC），通过率 100%
- **SQL Guard 单元测试**：20 个（全部单元测试共 22 个），通过率 100%

```bash
# 运行安全测试
uv run pytest tests/unit/test_sql_guard.py -v
uv run python -m evals.runners.text_to_sql
```

完整的安全设计、白名单配置、脱敏规则详见架构设计文档第 10 节。
