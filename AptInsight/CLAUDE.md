# CLAUDE.md

本文件为 Claude Code 提供 AptInsight 项目指引。

## 角色

你正在协助构建 AptInsight——尚庭公寓系统的智能运营分析助手。

MVP 是一个独立的 Python FastAPI Agent 服务。它接收中文自然语言运营问题，生成安全的只读 SQL，查询现有 MySQL 业务数据库，并返回表格、ECharts 兼容的图表选项和简洁的业务总结。

## 仓库边界

当前目录是 AptInsight 项目根目录。保持此项目独立于现有的 `least` Spring Boot/Vue 代码库。Java 后端和 Vue 前端是第二阶段的集成目标，不是放置 Python Agent 代码的地方。

## 交流语言

与用户交流时，默认使用中文。进度更新、澄清问题、技术解释和最终回复都应使用中文。

仅在以下情况使用英文：代码、命令、日志、标识符、依赖名称、文件名、API 名称、精确错误信息，或用户明确要求英文。

## 必读文档

使用以下文档作为项目事实来源：

- `AptInsight文档/01-助手总体设计.md` — 项目定位、阶段规划
- `AptInsight文档/03-技术架构与模块设计.md` — 架构、部署、配置
- `AptInsight文档/04-Agent设计与提示词规范.md` — Agent 工作流、提示词
- `AptInsight文档/05-数据库字典与指标口径.md` — 表结构、指标定义
- `AptInsight文档/06-接口契约与集成方案.md` — API 契约、Spring Boot 集成
- `AptInsight文档/07-测试验收方案.md` — 测试策略
- `AptInsight文档/08-企业工程规范与Harness.md` — Harness 定义
- `docs/aptinsight-system-failure-investigation-guide.md` — 系统失败定位指南
- `docs/aptinsight-system-failure-root-cause-report.md` — 系统失败根因报告

如果代码与文档冲突，暂停并将实现与文档化的 MVP 范围对齐，除非用户明确要求更新文档。

## 预期技术栈

- Python 3.12
- `uv`
- FastAPI
- Pydantic v2
- LangGraph
- OpenAI 兼容 LLM 客户端
- SQLAlchemy 2.x async
- asyncmy
- sqlglot
- pandas
- cryptography（MySQL 认证）
- redis
- langsmith（LLM 调用追踪）
- pytest
- Ruff

没有明确理由不要引入更重的技术栈。

## 目录指引

```text
src/aptinsight/api/        HTTP API 路由
src/aptinsight/agent/      LangGraph 工作流、状态、节点、提示词
src/aptinsight/core/       配置、日志、错误处理
src/aptinsight/db/         数据库引擎和查询执行器
src/aptinsight/llm/        模型客户端和结构化 schema
src/aptinsight/security/   SQL 守卫、脱敏、表白策略
src/aptinsight/knowledge/  数据库 schema、指标、few-shot 示例
src/aptinsight/schemas/    Pydantic 请求/响应模型
evals/                    Agent 评测系统
tests/                    测试
docs/                     工程文档
AptInsight文档/           产品和架构文档
```

## 不可协商的安全规则

- SQL 守卫未批准前，绝不执行生成的 SQL。
- 只允许 `SELECT`。
- 拒绝写操作和 DDL。
- 拒绝多语句 SQL。
- 使用表和列白名单。
- 保护敏感字段和凭据。
- 仅使用只读 MySQL 账号。
- 不要编造字段、表、指标、收入或业务原因。
- 如果数据库 DDL 无法支持某个问题，说明限制。

## 编码风格

- 保持路由处理函数简洁。
- 将提示词放在 `src/aptinsight/agent/prompts/` 下的 Markdown 文件中。
- 将业务 schema 知识放在 `src/aptinsight/knowledge/` 中。
- 对外部契约使用 Pydantic 模型。
- 对有意义的行为变更添加测试。
- 优先使用清晰的模块边界，而非大型单体文件。
- 保持注释有用且精简。
- 优先使用异步数据库访问。
- 使用结构化错误和 trace_id 进行请求级诊断。

## 常用命令

```bash
uv sync
uv run uvicorn aptinsight.main:app --reload
uv run pytest
uv run ruff check src tests
uv run ruff format src tests
make run
make test
make lint
make eval
```

## 开发顺序

建议的下一步实现顺序：

1. 完成配置和 JSON 日志。
2. 实现表白名单和基于 `sqlglot` 的 SQL 守卫。
3. 实现 async MySQL 引擎和只读执行器。
4. 实现 LLM 客户端和结构化输出 schema。
5. 实现 LangGraph 节点。
6. 将 `/api/chat` 接入工作流。
7. 扩展 `evals/datasets/text_to_sql_cases.yaml`。
8. Agent 行为稳定后再接入 Spring Boot 和 Vue 集成。

## 审查清单

完成变更前，验证：

- 变更符合文档化的 MVP。
- 未引入密钥。
- 生成的 SQL 无法绕过守卫。
- 不支持的 schema 问题被拒绝或加了警告。
- API 响应仍匹配 Pydantic schema。
- 在适当时测试或评测覆盖了行为。

## 回复前的最终检查

确认变更内容，提及运行的测试或检查，并清楚说明任何限制。
