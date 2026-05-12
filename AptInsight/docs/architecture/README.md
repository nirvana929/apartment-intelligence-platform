# 架构文档

> 权威来源：[`AptInsight文档/03-技术架构与模块设计.md`](../../AptInsight文档/03-技术架构与模块设计.md)

## 系统架构概览

```text
用户问题 → FastAPI (/api/chat) → LangGraph Agent → 返回结果
```

LangGraph 工作流节点：

1. **意图识别** (intent) — 分类用户问题
2. **SQL 生成** (generate_sql) — LLM 生成 SQL
3. **SQL 安全检查** (guard_sql) — sqlglot AST 校验
4. **SQL 执行** (execute_sql) — 只读 MySQL 查询
5. **图表生成** (build_chart) — ECharts 选项
6. **答案生成** (write_answer) — 业务总结

## 核心模块

| 模块 | 路径 | 职责 |
|------|------|------|
| API 层 | `src/aptinsight/api/` | HTTP 路由 |
| Agent 层 | `src/aptinsight/agent/` | LangGraph 工作流 |
| 安全层 | `src/aptinsight/security/` | SQL 守卫、脱敏 |
| 数据层 | `src/aptinsight/db/` | 数据库引擎 |
| LLM 层 | `src/aptinsight/llm/` | 模型客户端 |
| 知识层 | `src/aptinsight/knowledge/` | Schema、指标 |

## 技术栈

Python 3.12 / FastAPI / LangGraph / SQLAlchemy 2.x async / sqlglot / Pydantic v2 / pandas

完整部署方案、配置说明、技术选型理由详见架构设计文档。
