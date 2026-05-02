# AGENTS.md

本文件面向在 AptGuide 仓库中工作的编码 Agent。

## 项目标识

AptGuide 是尚庭公寓管理系统中面向 **租客用户** 的智能找房助手。第一阶段是独立的 Python FastAPI Agent 服务，通过 Milvus 完成房源语义召回与租房知识库 RAG，通过调用 `lease`（Spring Boot）后端封装的工具接口获取真实业务数据，最终回答用户的找房、预约、租约、规则类问题。

此目录即为 AptGuide 项目根目录。除非明确要求，不要创建另一个嵌套的项目根目录。

**与 `AptInsight/` 的区别**：AptInsight 服务运营人员，使用 Text-to-SQL 直查 MySQL；AptGuide 服务租客，**不直接访问 MySQL**，全部通过 Java 工具接口。两个服务独立部署、独立依赖、独立鉴权。

## 交流语言

与用户聊天时，默认使用中文。用户是中国人，期望解释、进度更新、问题和最终总结使用中文。

仅在代码、命令输出、依赖名称、文件名、API 名称、错误信息中使用英文，或用户明确要求英文时使用英文。

## 事实来源

在进行架构或行为变更前，请阅读以下文档：

1. `AptGuide文档/01-助手总体设计.md`
2. `AptGuide文档/02-产品需求文档.md`
3. `AptGuide文档/03-技术架构与模块设计.md`
4. `AptGuide文档/04-Agent设计与提示词规范.md`
5. `AptGuide文档/05-Java工具接口契约.md`
6. `AptGuide文档/06-Milvus知识库设计.md`
7. `AptGuide文档/07-测试验收方案.md`

如果代码与文档冲突，暂停并将实现与文档化的 MVP 范围对齐，除非用户明确要求更新文档。

## 当前架构

```text
src/aptguide/
  api/          FastAPI 路由和依赖注入
  agent/        LangGraph 状态、图、节点、提示词
  tools/        调用 Java 后端工具接口的 HTTP 客户端（房源、预约、租约、浏览历史）
  vector/       Milvus 客户端、房源语义索引、租房知识库 RAG
  core/         配置、日志、共享错误
  llm/          OpenAI 兼容模型客户端和结构化 schema
  knowledge/    意图清单、待向量化的 FAQ/规则原文
  schemas/      Pydantic 请求/响应/工具入参出参模型
  security/     身份透传、敏感字段过滤
scripts/        离线脚本（房源向量同步、知识库初始化）
evals/          Agent 评测数据集、运行器、报告
tests/          单元测试和契约测试
docs/           工程文档
AptGuide文档/   产品和架构文档
```

## 工程规则

- 优先做小而专注的变更，匹配现有目录结构。
- 保持 MVP 范围紧凑：FastAPI、Pydantic v2、LangGraph、httpx、pymilvus、pytest、Ruff、mypy 和 Agent 评测系统。
- **不要把 AptGuide 代码混入 `lease`（Java）、`rentHouseH5`（Vue）、`AptInsight`（运营端 Python）任一项目。**
- 使用 `uv` 进行依赖管理。
- 行为变更时添加或更新测试。
- 将密钥排除在仓库之外。本地使用 `.env`，占位符使用 `.env.example`。
- 除非要求，不要添加大型生成产物。`AptGuide文档/` 中的 PDF 是文档交付物。

## 关键约束（与 AptInsight 不同）

- **不要引入** SQLAlchemy / asyncmy / sqlglot 等数据库直连依赖。
- **不要实现** SQL 守卫、表白名单——这些与本项目无关。
- **不要直接查询 MySQL**。所有业务数据访问通过 `src/aptguide/tools/` 调用 Java 接口。
- **不要相信前端传入的 userId**。用户身份由 `lease` 在调用 `/api/chat` 时通过内部 header 透传。
- **不要让 Milvus 返回的房源直接呈现给用户**。Milvus 仅做语义召回，最终房源数据必须由 Java 后端按 `room_id` 回查并校验状态。

## 写操作的安全模式

涉及创建/修改的工具调用（如创建预约、取消预约）必须遵循"先确认、后执行"：

1. Agent 抽取参数并组织成可读的意图摘要（房间、时间、人数）。
2. 把摘要返回给用户，请求显式确认。
3. 用户确认后，下一轮才调用 Java 写接口。

不要在用户首次表达模糊意图时就直接写入。
