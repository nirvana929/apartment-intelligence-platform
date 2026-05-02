# CLAUDE.md

本文件为 Claude Code 提供 AptGuide 项目指引。

## 角色

你正在协助构建 **AptGuide**——尚庭公寓管理系统中面向 **租客用户** 的智能找房助手。

MVP 是一个独立的 Python FastAPI Agent 服务。它接收用户自然语言（找房需求、看房预约、租约咨询、租房规则问答），通过 **Milvus 向量检索** 完成语义召回与 RAG，通过 **调用 Java 后端工具接口** 获取真实业务数据，最终返回房源卡片、推荐理由和可执行操作。

**AptGuide 不直接访问 MySQL。** 所有业务数据访问通过 `lease`（Spring Boot）后端封装的内部工具接口。这是与同仓库 `AptInsight`（运营端、Text-to-SQL）的关键区别。

## 交流语言

与用户交流时，默认使用中文。用户是中国人，进度更新、澄清问题、技术解释和最终回复都应使用中文。

仅在以下情况使用英文：代码、命令、日志、标识符、依赖名称、文件名、API 名称、精确错误信息，或用户明确要求英文。

## 仓库边界

当前目录是 AptGuide 项目根目录。保持此项目独立于：

- 同级 `AptInsight/`（运营端 Python 服务，技术栈相似但独立部署）
- 同级 `lease/`（Spring Boot 后端，AptGuide 通过 HTTP 调用它）
- 同级 `rentHouseH5/`、`rentHouseAdmin/`（前端项目）

不要把 Python 代码放到 Java 或前端项目下，也不要把 Java/Vue 代码放到 AptGuide 下。

## 必读文档

使用以下文档作为项目事实来源：

- `AptGuide文档/01-助手总体设计.md`
- `AptGuide文档/02-产品需求文档.md`
- `AptGuide文档/03-技术架构与模块设计.md`
- `AptGuide文档/04-Agent设计与提示词规范.md`
- `AptGuide文档/05-Java工具接口契约.md`
- `AptGuide文档/06-Milvus知识库设计.md`
- `AptGuide文档/07-测试验收方案.md`

如果代码与文档冲突，暂停并把实现对齐到文档化的 MVP 范围，除非用户明确要求更新文档。

## 预期技术栈

- Python 3.12
- `uv`
- FastAPI
- Pydantic v2 + pydantic-settings
- LangGraph
- OpenAI 兼容 LLM 客户端（默认 Qwen / DashScope）
- pymilvus
- httpx（调用 Java 内部接口）
- tenacity（重试）
- pytest、respx、Ruff、mypy

没有明确理由不要引入更重的技术栈。**不要**引入 SQLAlchemy / asyncmy / sqlglot——AptGuide 不直查数据库。

## 目录指引

```text
src/aptguide/api/         HTTP API 路由（/api/chat、/health）
src/aptguide/agent/       LangGraph 工作流、状态、节点、提示词
src/aptguide/tools/       调用 Java 后端工具接口的 HTTP 客户端
src/aptguide/vector/      Milvus 客户端、房源索引、知识库 RAG
src/aptguide/core/        配置、日志、错误处理
src/aptguide/llm/         LLM 客户端和结构化 schema
src/aptguide/knowledge/   意图清单、待入库的 FAQ/规则原文
src/aptguide/schemas/     Pydantic 请求/响应/工具入参出参模型
src/aptguide/security/    身份透传、敏感字段过滤
scripts/                  离线脚本（房源向量同步、知识库初始化）
evals/                    Agent 评测系统
tests/                    单元和契约测试
docs/                     工程文档
AptGuide文档/             产品和架构文档
```

## 不可协商的安全规则

- **不直接查询 MySQL。** 所有业务数据通过 Java 工具接口获取。
- **用户数据严格按 userId 隔离。** 租约、预约、浏览历史只能由 Java 后端按当前登录用户 ID 过滤后返回；AptGuide 不接受、不伪造、不透传客户端传来的 userId。
- **Milvus 不存敏感数据。** 只存可公开的房源描述、公寓介绍、租房规则、FAQ；不存手机号、身份证、合同全文、密码、支付记录。
- **写操作必须二次确认。** 预约、取消预约、续约/退租等动作，Agent 先返回意图摘要，等待用户确认后才调用 Java 接口。
- **AptGuide ↔ lease 内部接口使用共享密钥**（请求头 `X-Internal-Token`），不对公网暴露。
- **不要编造房源、价格、规则、链接。** 信息一律来自 Milvus 召回结果或 Java 工具接口返回。
- **Milvus 召回结果必须经 Java 二次校验**（是否上架、租金、可预约等），避免推荐过期或下架房源。

## 编码风格

- 保持路由处理函数简洁，业务逻辑放在 `agent/` 与 `tools/`。
- 提示词放在 `src/aptguide/agent/prompts/` 下的 Markdown 文件中。
- 工具入参 / 出参用 Pydantic 模型在 `schemas/tools.py` 集中定义。
- 调用 Java 的 HTTP 客户端统一使用 `tools/client.py`，注入超时与重试。
- 对外部契约（API、工具接口）使用 Pydantic 模型。
- 对有意义的行为变更添加测试。
- 优先清晰的模块边界，而非大型单体文件。
- 注释保持有用且精简。

## 常用命令

```bash
uv sync
uv run uvicorn aptguide.main:app --reload --port 8100
uv run pytest
uv run ruff check src tests
uv run ruff format src tests
make dev
make test
make lint
make eval
make sync-vectors    # MySQL → Milvus 房源同步
make seed-kb         # 初始化租房知识库
```

## 开发顺序

建议的下一步实现顺序：

1. 完成配置（`core/config.py`）和 JSON 日志。
2. 实现 Java 工具 HTTP 客户端骨架（`tools/client.py`），含内部 token、超时、重试。
3. 实现 Milvus 客户端与房源/知识库两个 Collection 的读取（`vector/`）。
4. 实现 LLM 客户端与结构化输出 schema（`llm/`）。
5. 实现 LangGraph 状态、意图识别、槽位抽取、工具调度、回复生成节点。
6. 接入 `/api/chat` 路由，串通最小闭环（找房 → 推荐 → 预约确认）。
7. 扩展评测数据集（`evals/datasets/`），覆盖找房、预约、租约、FAQ 四类。
8. Agent 行为稳定后，再接入 `lease` 与 `rentHouseH5`。

## 回复前的最终检查

确认变更内容、提及运行的测试或检查、清楚说明任何限制。涉及安全规则的修改前先停下来与用户确认。
