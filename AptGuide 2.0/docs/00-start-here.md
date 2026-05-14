# 00 · Start Here

本文档是 `AptGuide 2.0` 的原始阅读入口。新的分类索引入口是 [docs/README.md](README.md)，用于按 `system`、`plans`、`tests`、`outcomes` 四类阅读文档。

> 相关入口：[README](../README.md)、[文档中心](README.md)、[当前实现导览](27-current-implementation-guide.md)、[产品需求](01-product-requirements.md)、[Agent 架构](02-agent-framework-architecture.md)、[工具契约](04-tool-and-integration-contract.md)、[实施计划](12-implementation-task-plan.md)、[RAG/向量/MCP 升级](20-rag-retrieval-vector-mcp-evaluation-upgrade.md)、[实施准备清单](18-implementation-readiness-checklist.md)。

## 项目一句话

`AptGuide 2.0` 是一个独立运行的租房领域 Agent 应用。它有自己的前端和后端，但业务数据直接来自现有 `apartment-intelligence-platform` 的真实接口，包括房源、预约、租约和租房规则知识库。

当前长期目标不是只做一个 RAG 应用，而是建设一个企业级租房 Agent harness：

```text
AptGuide 2.0 Enterprise Harness
  -> conversation / context
  -> domain boundary / safety
  -> procedure runtime
  -> tool registry
  -> RAG module
  -> appointment workflow
  -> memory / user data / handoff
  -> trace / replay / observability
```

RAG 是这个 harness 里的核心模块之一，不是整个系统的唯一主语。后续应先搭好 AptGuide 2.0 系统 harness，再在其中把 RAG 优化到高质量。

## 当前代码状态

当前代码已经实现到 **Harness + RAG v2 + System Integration + System Feature Completion/Mainline Integration** 阶段。

已经落地的主入口：

```text
backend/src/aptguide2/api/app.py
```

当前 API：

```text
GET  /health
POST /chat  (支持 user_id, action, cards, pending_action, actions, metadata)
```

当前核心工作流：

```text
/chat
  -> AptGuideHarness.run()
  -> routing
  -> procedures
     -> RAG v2 internal module
     -> appointment / lease workflows
     -> handoff / fallback
  -> tool governance
  -> response composer
```

旧 RAG MVP 已从公共 API、harness procedure 和 system e2e acceptance 中断开，仅保留为 legacy reference。Live 验证：Milvus + embedding + lease 全部就绪，readiness 含 pipeline 版本检查。RAG v2 live eval 55 cases 真实运行，当前 blocker 是检索质量：KB hit@3=48.6%，Room hit@5=40%。

想理解”现在代码实际实现了什么”，先读 [27-current-implementation-guide.md](27-current-implementation-guide.md)。后续编号较早的文档里有很多产品规划和架构设计，不都代表当前已经完成。

## 与旧版 AptGuide 的关系

旧版 AptGuide 是一个固定 LangGraph workflow：

```text
intent -> slot -> room_search/kb/tool/confirm -> reply
```

`AptGuide 2.0` 不以“补丁式升级”为目标，而是作为新框架重新设计：

```text
Conversation Manager
  -> Domain Boundary Router
  -> Task Planner
  -> Specialist Agents / Workflows
  -> Tool Registry
  -> Recovery
  -> Response Composer
```

旧项目可以复用的内容：

- 租房业务领域知识；
- `lease` 内部工具接口契约；
- Milvus / KB 数据设计思路；
- 旧评测中暴露的失败案例；
- H5 集成链路经验。

旧项目不建议直接继承的内容：

- 过薄的 `AgentState`；
- 单一 `reply_node` fallback；
- 纯文本确认按钮协议；
- hard filter 优先的房源检索方式；
- 只做 intent/slot 的 Agent 入口；
- 把所有非命中问题都归为 `other` 的意图体系。

## 推荐阅读顺序

Claude / Codex 接手时不需要一次读取全部文档。先读 1-5 建立项目地图，再按任务选择专项文档。

1. [27-current-implementation-guide.md](27-current-implementation-guide.md)：先理解当前代码实际实现了什么。
2. [01-product-requirements.md](01-product-requirements.md)：再理解产品目标。
3. [03-domain-boundary-and-interaction-policy.md](03-domain-boundary-and-interaction-policy.md)：确定什么能答、什么不能答。
4. [02-agent-framework-architecture.md](02-agent-framework-architecture.md)：再看后端 Agent 框架规划。
5. [system/enterprise-harness-architecture.md](system/enterprise-harness-architecture.md)：理解企业级 harness 主线，避免把 RAG 当成整个系统。
6. [system/harness-method-selection.md](system/harness-method-selection.md)：理解本项目采用的 Procedure-driven Product Harness + Eval-first Engineering Harness 方法。
7. [04-tool-and-integration-contract.md](04-tool-and-integration-contract.md)：理解工具和旧项目接口如何接入。
8. [05-frontend-interaction-protocol.md](05-frontend-interaction-protocol.md)：理解前端如何和 Agent 交互。
9. [06-evaluation-roadmap-and-upgrade-assessment.md](06-evaluation-roadmap-and-upgrade-assessment.md)：看评测、路线和旧文档升级建议。
10. [07-memory-and-context-architecture.md](07-memory-and-context-architecture.md)：理解长期记忆、短期上下文和压缩策略。
11. [08-procedure-driven-agent-runtime.md](08-procedure-driven-agent-runtime.md)：理解任务流程驱动的多专家运行时。
12. [09-human-handoff-and-operations.md](09-human-handoff-and-operations.md)：理解人工接管和运营闭环。
13. [10-trace-eval-and-observability.md](10-trace-eval-and-observability.md)：理解 trace、审计和评测体系。
14. [11-feasibility-and-development-plan.md](11-feasibility-and-development-plan.md)：理解可行性判断和开发计划。
15. [12-implementation-task-plan.md](12-implementation-task-plan.md)：理解具体开发任务和验收顺序。
16. [13-product-technical-review.md](13-product-technical-review.md)：在动手实现前复查产品技术合理性和风险。
17. [14-api-and-schema-contract.md](14-api-and-schema-contract.md)：固定 API、cards、actions、SSE 和错误响应。
18. [15-tool-registry-and-error-codes.md](15-tool-registry-and-error-codes.md)：固定工具 schema、字段映射、错误码。
19. [16-memory-state-schema.md](16-memory-state-schema.md)：固定会话状态、任务状态、pending action 和长期记忆。
20. [17-prompt-and-eval-contract.md](17-prompt-and-eval-contract.md)：固定 prompt 输出和 eval 回归门槛。
21. [18-implementation-readiness-checklist.md](18-implementation-readiness-checklist.md)：进入编码前和每个阶段退出前做硬检查。
22. [19-anthropic-agent-eval-methodology.md](19-anthropic-agent-eval-methodology.md)：理解 eval-first 的 Agent 评估方法。
23. [20-rag-retrieval-vector-mcp-evaluation-upgrade.md](20-rag-retrieval-vector-mcp-evaluation-upgrade.md)：理解 RAG、向量库、Query Rewrite、RAGAS、动态知识库和 MCP 封装升级。

## Claude 接手路径

如果只给 Claude 一个入口，让它先读：

```text
README.md
docs/00-start-here.md
docs/27-current-implementation-guide.md
docs/01-product-requirements.md
docs/02-agent-framework-architecture.md
docs/system/enterprise-harness-architecture.md
docs/04-tool-and-integration-contract.md
docs/12-implementation-task-plan.md
```

然后按任务补读：

| 当前任务 | 补读文档 |
| --- | --- |
| 理解当前已实现代码 | [27-current-implementation-guide.md](27-current-implementation-guide.md)、`backend/src/aptguide2/api/app.py`、`backend/src/aptguide2/rag/pipeline.py` |
| 实现 Agent 主流程 | [02-agent-framework-architecture.md](02-agent-framework-architecture.md)、[08-procedure-driven-agent-runtime.md](08-procedure-driven-agent-runtime.md)、[17-prompt-and-eval-contract.md](17-prompt-and-eval-contract.md) |
| 接真实 lease 工具 | [04-tool-and-integration-contract.md](04-tool-and-integration-contract.md)、[15-tool-registry-and-error-codes.md](15-tool-registry-and-error-codes.md)、[14-api-and-schema-contract.md](14-api-and-schema-contract.md) |
| 做前端交互 | [05-frontend-interaction-protocol.md](05-frontend-interaction-protocol.md)、[14-api-and-schema-contract.md](14-api-and-schema-contract.md)、[16-memory-state-schema.md](16-memory-state-schema.md) |
| 搭企业级 AptGuide harness | [system/enterprise-harness-architecture.md](system/enterprise-harness-architecture.md)、[02-agent-framework-architecture.md](02-agent-framework-architecture.md)、[08-procedure-driven-agent-runtime.md](08-procedure-driven-agent-runtime.md)、[plans/2026-05-12-enterprise-aptguide-harness-plan.md](plans/2026-05-12-enterprise-aptguide-harness-plan.md) |
| 选择 harness 方法和工程门禁 | [system/harness-method-selection.md](system/harness-method-selection.md)、[system/enterprise-harness-architecture.md](system/enterprise-harness-architecture.md)、[19-anthropic-agent-eval-methodology.md](19-anthropic-agent-eval-methodology.md)、[10-trace-eval-and-observability.md](10-trace-eval-and-observability.md) |
| 做 RAG / 向量库 / RAGAS / MCP | [20-rag-retrieval-vector-mcp-evaluation-upgrade.md](20-rag-retrieval-vector-mcp-evaluation-upgrade.md)、[21-rag-final-implementation-scheme.md](21-rag-final-implementation-scheme.md)、[10-trace-eval-and-observability.md](10-trace-eval-and-observability.md) |
| 做记忆和上下文压缩 | [07-memory-and-context-architecture.md](07-memory-and-context-architecture.md)、[16-memory-state-schema.md](16-memory-state-schema.md)、[10-trace-eval-and-observability.md](10-trace-eval-and-observability.md) |
| 做评测和验收 | [06-evaluation-roadmap-and-upgrade-assessment.md](06-evaluation-roadmap-and-upgrade-assessment.md)、[17-prompt-and-eval-contract.md](17-prompt-and-eval-contract.md)、[18-implementation-readiness-checklist.md](18-implementation-readiness-checklist.md)、[19-anthropic-agent-eval-methodology.md](19-anthropic-agent-eval-methodology.md) |

## 按任务检索

| 任务 | 相关文档 |
| --- | --- |
| 定义产品范围 | [01-product-requirements.md](01-product-requirements.md)、[03-domain-boundary-and-interaction-policy.md](03-domain-boundary-and-interaction-policy.md) |
| 设计 Agent 编排 | [02-agent-framework-architecture.md](02-agent-framework-architecture.md)、[08-procedure-driven-agent-runtime.md](08-procedure-driven-agent-runtime.md) |
| 设计 API、工具和前端契约 | [14-api-and-schema-contract.md](14-api-and-schema-contract.md)、[15-tool-registry-and-error-codes.md](15-tool-registry-and-error-codes.md)、[04-tool-and-integration-contract.md](04-tool-and-integration-contract.md)、[05-frontend-interaction-protocol.md](05-frontend-interaction-protocol.md) |
| 设计 RAG、向量库和检索评估 | [20-rag-retrieval-vector-mcp-evaluation-upgrade.md](20-rag-retrieval-vector-mcp-evaluation-upgrade.md)、[10-trace-eval-and-observability.md](10-trace-eval-and-observability.md)、[19-anthropic-agent-eval-methodology.md](19-anthropic-agent-eval-methodology.md) |
| 设计记忆和上下文 | [16-memory-state-schema.md](16-memory-state-schema.md)、[07-memory-and-context-architecture.md](07-memory-and-context-architecture.md)、[10-trace-eval-and-observability.md](10-trace-eval-and-observability.md) |
| 设计人工接管 | [09-human-handoff-and-operations.md](09-human-handoff-and-operations.md)、[03-domain-boundary-and-interaction-policy.md](03-domain-boundary-and-interaction-policy.md) |
| 计划开发和验收 | [11-feasibility-and-development-plan.md](11-feasibility-and-development-plan.md)、[12-implementation-task-plan.md](12-implementation-task-plan.md)、[17-prompt-and-eval-contract.md](17-prompt-and-eval-contract.md)、[18-implementation-readiness-checklist.md](18-implementation-readiness-checklist.md) |

## 当前阶段目标

第一阶段只要求文档和框架设计清晰，不要求立即实现全部能力。

第一版实现时建议先跑通最小闭环：

- 独立前端聊天界面；
- 后端 Agent API；
- 真实 `lease` 工具适配器；
- 对现有后端依赖的启动和健康检查；
- 领域边界分类；
- 短期记忆和任务阶段；
- 找房 Agent 的渐进式检索恢复；
- 结构化确认 action；
- trace 记录；
- 基础 eval 用例。

第一版需要预留但不必做完整形态：

- 长期偏好画像；
- 上下文压缩；
- 人工接管；
- 运营报表。

## 非目标

`AptGuide 2.0` 不做通用大模型产品，不回答任意代码生成、文章写作、天气、新闻、翻译等无关问题。它可以礼貌解释能力边界，但不能让用户把它当成免费通用 LLM 使用。
