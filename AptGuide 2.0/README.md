# AptGuide 2.0

> 面向租客的独立 Agentic 租房助手应用。

`AptGuide 2.0` 不是在旧版 AptGuide 上继续增加节点或修补 fallback，而是重新设计一个可以独立运行、带前端交互、直接调用现有租赁系统真实接口的租房领域 Agent 应用框架。

## 当前实现状态

当前代码已经落地到 **FastAPI + RAG 检索 MVP**：

- Web 入口：[backend/src/aptguide2/api/app.py](backend/src/aptguide2/api/app.py)
- 当前 API：`GET /health`、`POST /chat`
- RAG 主流程：[backend/src/aptguide2/rag/pipeline.py](backend/src/aptguide2/rag/pipeline.py)
- 当前实现导览：[docs/27-current-implementation-guide.md](docs/27-current-implementation-guide.md)
- **成果报告**：[docs/28-rag-mvp-achievement-report.md](docs/28-rag-mvp-achievement-report.md)

**数据规模**：126 间房源 + 70 条 KB 规则 | **测试**：149/149 通过

一次 `/chat` 请求的当前工作流：

```text
POST /chat
  -> run_pipeline()
  -> understand_query()
  -> room_search / kb_qa / fallback
  -> Milvus retrieval
  -> ranking 或 confidence gate
  -> ChatResponse
```

已经实现：

- 确定性 query understanding；
- 房源向量召回和多维重排；
- KB 多路召回、source rerank、confidence gate；
- KB 置信后基于来源内容调用 LLM 生成回答；
- Milvus 向量库适配器；
- lease Java 后端适配器；
- KB 和房源向量同步脚本；
- mock 房源 seed 脚本；
- RAG eval runner；
- 单元测试和 `/chat` e2e 测试。

尚未完整实现：

- 独立前端聊天应用；
- 多轮会话记忆和长期偏好画像；
- Agent planner / specialist agents；
- 预约、签约、取消等写操作 workflow；
- 结构化确认卡片和 action 执行；
- 人工接管、权限认证、Trace 持久化和 MCP 封装。

它的目标是把旧版固定 workflow 聊天机器人升级为：

- 有明确领域边界的租房助手，而不是通用大模型入口；
- 有短期记忆和任务阶段的多轮对话系统；
- 有任务规划、工具调用、检索恢复和失败解释能力的 Agentic Workflow；
- 有结构化前端协议的交互产品，而不是只返回文本；
- 可作为独立前后端应用运行，但业务数据直接来自现有 `lease`、Milvus 和业务工具接口。

## 为什么重构

旧版 AptGuide 的主要问题不是单个节点实现不完善，而是整体范式偏硬：

```text
intent -> slot -> search/tool/confirm -> reply
```

这个流程适合确定性任务，但不适合真实租房对话中的模糊区域、预算变化、空结果恢复、用户记忆、过期确认、工具失败和领域边界判断。

`AptGuide 2.0` 的核心变化是把系统重构为：

```text
User Message
  -> Conversation Manager
  -> Domain Boundary Router
  -> Task Planner
  -> Specialist Agent / Deterministic Workflow
  -> Tool & Retrieval Layer
  -> Recovery / Reflection
  -> Response Composer
  -> Frontend Interaction Protocol
```

## 独立运行方式

当前后端可以作为独立 FastAPI 服务运行：

```bash
cd "AptGuide 2.0/backend"
uv sync
cp .env.example .env
uv run uvicorn aptguide2.api.app:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

聊天接口：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"番禺区1500以内安静一点的房子"}'
```

本地运行前需要准备：

- Milvus；
- OpenAI-compatible embedding API；
- OpenAI-compatible LLM API；
- 如果要从真实系统同步房源，需要启动 `lease` Java 后端。

完整产品形态仍然计划作为一个独立项目运行，包含：

- 后端 Agent 服务；
- 独立前端聊天应用；
- 真实工具后端适配器；
- 对现有 `lease` 后端、Milvus 和知识库服务的依赖配置。

第一阶段就直接依赖真实项目后端。启动 `AptGuide 2.0` 前，需要启动现有 `lease/web-app` 以及必要的 MySQL、Redis、Milvus 等依赖，由 `AptGuide 2.0` 通过受控接口调用：

```text
AptGuide 2.0 Frontend
  -> AptGuide 2.0 API
  -> Tool Adapter
      -> lease internal tools
      -> vector / KB service
```

## 产品技术评审结论

结论：当前方案方向合理，适合作为 `apartment-intelligence-platform` 里新的租客侧智能应用，而不是旧版 AptGuide 的补丁式升级。

设计合理的关键原因：

- 产品边界清楚：只做找房、租房规则、预约、我的预约/租约和人工接管，不做通用大模型入口；
- 技术边界清楚：房源、预约、租约和规则答案来自真实 `lease`、Milvus / KB 或受控工具，不让模型编造业务事实；
- 风险控制路径正确：写操作走确定性 workflow，确认 action 结构化，个人数据走后端身份，不信任前端 `user_id`；
- 架构可演进：用 Conversation Manager、Hybrid Router、Procedure、Tool Registry、Trace/Eval 分层，比旧版 intent/slot/reply 图更适合复杂对话；
- 实施路线可拆：可以先做最小演示闭环，再扩展长期记忆、人工接管、运营看板和高级 eval。

需要重点控制的风险：

- 第一版范围偏大，必须把“最小可演示闭环”和“完整产品能力”拆开；
- `lease` 真实工具接口需要和 AptGuide 2.0 schema 对齐，包括字段命名、错误码、预约校验、房源检索能力；
- 长期记忆、人工接管和 trace 涉及隐私与运营责任，必须从第一版就预留审计和删除能力；
- 评测用例需要尽快从文档样例固化为可运行 YAML / pytest 回归。

完整评审见 [13-product-technical-review.md](docs/13-product-technical-review.md)。

## Claude 检索入口

如果用 Claude / Codex 继续编写或实现，建议先给模型读取本 README。下面的链接把文档按产品、架构、契约、运行时、评测和实施串起来，模型可以沿链接按需读取，不必一次塞入全部文档。

### 接手最短路径

如果目标是让 Claude 快速接手项目，按下面顺序读取即可：

```text
1. README.md
2. docs/00-start-here.md
3. docs/27-current-implementation-guide.md
4. docs/01-product-requirements.md
5. docs/02-agent-framework-architecture.md
6. docs/04-tool-and-integration-contract.md
7. docs/12-implementation-task-plan.md
8. 按任务读取下方表格中的专项文档
```

如果这次重点是 RAG、向量库、RAGAS、MCP 或知识库持续更新，直接读取：

```text
docs/21-rag-final-implementation-scheme.md
docs/22-rag-mvp-data-and-implementation-plan.md
docs/23-rag-data-supplement-agent-plan.md
docs/24-rag-implementation-agent-plan.md
docs/20-rag-retrieval-vector-mcp-evaluation-upgrade.md
docs/10-trace-eval-and-observability.md
docs/19-anthropic-agent-eval-methodology.md
docs/15-tool-registry-and-error-codes.md
```

| 你要处理的问题 | 优先阅读 |
| --- | --- |
| 理解当前已经实现的系统 | [27-current-implementation-guide.md](docs/27-current-implementation-guide.md)、[api/app.py](backend/src/aptguide2/api/app.py)、[rag/pipeline.py](backend/src/aptguide2/rag/pipeline.py) |
| 快速理解项目目标和边界 | [00-start-here.md](docs/00-start-here.md)、[01-product-requirements.md](docs/01-product-requirements.md)、[13-product-technical-review.md](docs/13-product-technical-review.md) |
| 判断产品范围、拒答策略、人工接管 | [01-product-requirements.md](docs/01-product-requirements.md)、[03-domain-boundary-and-interaction-policy.md](docs/03-domain-boundary-and-interaction-policy.md)、[09-human-handoff-and-operations.md](docs/09-human-handoff-and-operations.md) |
| 设计后端 Agent 架构 | [02-agent-framework-architecture.md](docs/02-agent-framework-architecture.md)、[08-procedure-driven-agent-runtime.md](docs/08-procedure-driven-agent-runtime.md)、[07-memory-and-context-architecture.md](docs/07-memory-and-context-architecture.md) |
| 固定 API、工具和状态契约 | [14-api-and-schema-contract.md](docs/14-api-and-schema-contract.md)、[15-tool-registry-and-error-codes.md](docs/15-tool-registry-and-error-codes.md)、[16-memory-state-schema.md](docs/16-memory-state-schema.md) |
| 对接真实业务系统 | [04-tool-and-integration-contract.md](docs/04-tool-and-integration-contract.md)、[05-frontend-interaction-protocol.md](docs/05-frontend-interaction-protocol.md)、[10-trace-eval-and-observability.md](docs/10-trace-eval-and-observability.md) |
| 设计 RAG、向量库、MCP 和检索评估 | [21-rag-final-implementation-scheme.md](docs/21-rag-final-implementation-scheme.md)、[22-rag-mvp-data-and-implementation-plan.md](docs/22-rag-mvp-data-and-implementation-plan.md)、[23-rag-data-supplement-agent-plan.md](docs/23-rag-data-supplement-agent-plan.md)、[24-rag-implementation-agent-plan.md](docs/24-rag-implementation-agent-plan.md)、[20-rag-retrieval-vector-mcp-evaluation-upgrade.md](docs/20-rag-retrieval-vector-mcp-evaluation-upgrade.md)、[10-trace-eval-and-observability.md](docs/10-trace-eval-and-observability.md)、[19-anthropic-agent-eval-methodology.md](docs/19-anthropic-agent-eval-methodology.md) |
| 准备开发任务和验收 | [11-feasibility-and-development-plan.md](docs/11-feasibility-and-development-plan.md)、[12-implementation-task-plan.md](docs/12-implementation-task-plan.md)、[17-prompt-and-eval-contract.md](docs/17-prompt-and-eval-contract.md)、[18-implementation-readiness-checklist.md](docs/18-implementation-readiness-checklist.md)、[19-anthropic-agent-eval-methodology.md](docs/19-anthropic-agent-eval-methodology.md) |

## 完整文档目录

### 入口和产品边界

- [00-start-here.md](docs/00-start-here.md)：阅读顺序和项目边界。
- [27-current-implementation-guide.md](docs/27-current-implementation-guide.md)：当前已经实现的 API、RAG 主流程、入库脚本、测试和阅读路线。
- [01-product-requirements.md](docs/01-product-requirements.md)：产品定位、用户场景、能力边界。
- [03-domain-boundary-and-interaction-policy.md](docs/03-domain-boundary-and-interaction-policy.md)：领域边界、防白嫖和交互话术策略。
- [13-product-technical-review.md](docs/13-product-technical-review.md)：从产品和技术角度评审方案合理性、风险和补文档建议。

### Agent 架构和运行时

- [02-agent-framework-architecture.md](docs/02-agent-framework-architecture.md)：AptGuide 2.0 Agent 框架设计。
- [07-memory-and-context-architecture.md](docs/07-memory-and-context-architecture.md)：长期记忆、短期上下文、上下文压缩和记忆治理。
- [08-procedure-driven-agent-runtime.md](docs/08-procedure-driven-agent-runtime.md)：任务流程驱动、多专家模块、混合路由和运行时状态。
- [09-human-handoff-and-operations.md](docs/09-human-handoff-and-operations.md)：人工接管、运营后台、客服协同和业务闭环。

### 工具、接口和前端协议

- [04-tool-and-integration-contract.md](docs/04-tool-and-integration-contract.md)：工具注册表、真实接口和旧项目集成方式。
- [05-frontend-interaction-protocol.md](docs/05-frontend-interaction-protocol.md)：前端交互、确认卡片、结构化 action 和 SSE 事件。
- [14-api-and-schema-contract.md](docs/14-api-and-schema-contract.md)：后端 API、Chat Response、Card、Action、SSE 和错误响应契约。
- [15-tool-registry-and-error-codes.md](docs/15-tool-registry-and-error-codes.md)：工具注册表、字段映射、权限、错误码和 trace 要求。
- [16-memory-state-schema.md](docs/16-memory-state-schema.md)：ConversationFrame、ActiveTaskState、PendingAction、长期画像和 audit log schema。

### 评测、RAG 和可观测性

- [06-evaluation-roadmap-and-upgrade-assessment.md](docs/06-evaluation-roadmap-and-upgrade-assessment.md)：评测方案、重构路线和对旧升级文档的修正建议。
- [10-trace-eval-and-observability.md](docs/10-trace-eval-and-observability.md)：Trace、审计、评测集、指标和可观测性。
- [17-prompt-and-eval-contract.md](docs/17-prompt-and-eval-contract.md)：Prompt 输出结构、eval case schema 和各阶段回归门槛。
- [19-anthropic-agent-eval-methodology.md](docs/19-anthropic-agent-eval-methodology.md)：基于 Anthropic Agent eval 方法的 AptGuide 2.0 专属评估与测试报告方案。
- [20-rag-retrieval-vector-mcp-evaluation-upgrade.md](docs/20-rag-retrieval-vector-mcp-evaluation-upgrade.md)：RAG 范式、Query Rewrite、chunking、多路召回、粗排精排、Milvus 算法选型、RAGAS、动态知识库和 MCP 封装方案。
- [21-rag-final-implementation-scheme.md](docs/21-rag-final-implementation-scheme.md)：RAG、向量库、知识库生命周期、benchmark、业务 grader 和 MCP 的最终实施方案。
- [22-rag-mvp-data-and-implementation-plan.md](docs/22-rag-mvp-data-and-implementation-plan.md)：RAG 初版实现、数据库数据是否足够、造数边界和 seed/eval 数据计划。
- [23-rag-data-supplement-agent-plan.md](docs/23-rag-data-supplement-agent-plan.md)：交给数据补充 Agent 执行的数据库审计、lease seed、KB 规则和 eval 数据计划。
- [24-rag-implementation-agent-plan.md](docs/24-rag-implementation-agent-plan.md)：交给 RAG 实现 Agent 执行的 schema、Milvus、检索、校验、trace 和 eval runner 计划。

### 实施计划和验收

- [11-feasibility-and-development-plan.md](docs/11-feasibility-and-development-plan.md)：可行性判断、风险控制和分阶段开发计划。
- [12-implementation-task-plan.md](docs/12-implementation-task-plan.md)：建议代码结构、开发任务拆解和验收命令。
- [18-implementation-readiness-checklist.md](docs/18-implementation-readiness-checklist.md)：进入编码和每个 Phase 退出前的硬检查清单。

## 设计原则

1. 租房域内尽量智能，租房域外清晰拒绝。
2. 写操作必须确定性 workflow，不交给自由 Agent 执行。
3. 房源、价格、合同、个人数据必须来自工具或知识库，不允许模型编造。
4. 找房和问答允许 ReAct 式观察和恢复，但必须受工具白名单约束。
5. 前端发送结构化 action，不用纯文本模拟按钮点击。
6. 每一次失败都要能解释原因，并给出下一步可操作建议。
7. 长期记忆只保存用户可解释、可撤销、低敏的偏好事实，不保存完整隐私历史。
8. 对外产品叙述采用“任务流程驱动的租房客服 Agent”，内部实现可混合使用 Planner、ReAct、RAG 和确定性 Workflow。
