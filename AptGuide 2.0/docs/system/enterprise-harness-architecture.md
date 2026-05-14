# Enterprise Harness Architecture

> 状态：active
> 范围：AptGuide 2.0 整体系统架构，不是单独 RAG 架构。

## 一句话结论

`AptGuide 2.0` 的目标不是做一个孤立的 RAG 应用，而是建设一个企业级租房 Agent harness。RAG 是其中的核心模块之一，和预约、记忆、用户数据、人工接管、工具注册、trace/replay 一起运行在同一个系统底座上。

当前项目采用的具体方法是 **Procedure-driven Product Harness + Eval-first Engineering Harness + External Progress State**。也就是：用确定性 procedure runtime 管住租房业务行为，用 eval-first 和 trace/replay 管住工程可信度，用外部 JSON/Markdown 状态文件保证长期迭代可恢复。详细选型见 [harness-method-selection.md](./harness-method-selection.md)。

## 为什么不是 RAG Harness

当前 MVP 的主要实现是 FastAPI + RAG，所以容易把升级目标误写成“RAG harness”。这是不准确的。

正确边界是：

```text
AptGuide 2.0 Enterprise Harness
  -> RAG module
  -> Appointment workflow
  -> Memory module
  -> User data module
  -> Handoff module
  -> Tool registry
  -> Trace / replay
```

如果只做 RAG harness，会导致：

- `/chat` 仍然缺少完整 Conversation Manager；
- 预约、确认、人工接管无法进入统一 runtime；
- 工具调用和错误处理分散；
- trace/replay 只能覆盖检索，不能覆盖完整用户任务；
- 后续前端 action、pending action、memory 都要重新接一次框架。

## 企业级 Harness 的定义

这里的 harness 指一个可运行、可插拔、可观测、可回放的 Agent 工程框架。

它必须具备：

- 统一请求响应契约；
- 会话上下文加载和更新；
- 领域边界和安全路由；
- 任务流程选择；
- 工具注册和权限约束；
- 模块化 procedure runtime；
- 结构化 action 和 confirmation；
- trace、replay、降级和错误分类；
- 配置化 strategy registry；
- 可逐步替换的 RAG、reranker、router、composer。

本文档中的 harness 分为两层：

```text
Product Harness
  -> 处理用户请求、业务流程、工具调用、响应生成和 trace

Engineering Harness
  -> 管理 feature、sprint、测试证据、进度、问题和评估报告
```

第一阶段优先实现 Product Harness 的最小闭环，同时补齐 Engineering Harness 的状态文件和验证门禁。

## 目标运行时

```text
ChatRequest
  -> AptGuideRequest
  -> ContextLoader
  -> EventFilter
  -> SafetyBoundary
  -> ConversationManager
  -> HybridRouter
  -> ProcedureSelector
  -> ProcedureRuntime
      -> modules.rag.room_search
      -> modules.rag.kb_qa
      -> modules.appointment.workflow
      -> modules.user_data.query
      -> modules.memory.workflow
      -> modules.handoff.workflow
      -> modules.capability.workflow
  -> ToolRegistry
  -> RecoveryPolicy
  -> ResponseComposer
  -> TraceRecorder
  -> AptGuideResponse
```

## 推荐代码边界

```text
aptguide2/harness/
  contracts.py       # 系统级请求、上下文、路由、流程结果、响应、trace
  orchestrator.py    # 系统总编排
  context.py         # session/context/memory 加载
  safety.py          # 安全和领域边界
  routing.py         # hybrid router
  procedures.py      # procedure interface and selector
  tools.py           # tool registry facade
  recovery.py        # 失败恢复策略
  composer.py        # 统一响应生成
  trace.py           # trace recorder
  replay.py          # replay case writer
  modules/
    rag/
    appointment/
    memory/
    user_data/
    handoff/
    capability/
```

保留当前 MVP：

```text
aptguide2/rag/
```

历史设计曾计划短期将旧 RAG MVP 作为 baseline strategy 挂入 harness。2026-05-14 的主线集成决策已更新：旧 RAG MVP 只保留为 legacy reference，不再接入 `/chat`、API wiring、harness procedure 或系统 e2e 验收；RAG v2 作为 harness 内部检索模块使用。执行计划见 [../plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md](../plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md)。

## RAG 在 Harness 中的位置

RAG module 不直接拥有 `/chat`。

它接收：

```text
ConversationFrame
RouteDecision
ToolRegistry
TraceRecorder
```

它返回：

```text
ProcedureResult
```

RAG 内部可以继续细分：

```text
query understanding
query rewrite
retrieval planning
room retrieval
kb retrieval
validation
rerank
confidence
grounded response payload
```

最终用户可见回复仍由系统级 `ResponseComposer` 统一生成，保证 room cards、sources、actions、pending_action、metadata 的格式一致。

## 与现有文档的关系

- [02-agent-framework-architecture.md](../02-agent-framework-architecture.md)：描述 Agent 框架和专家模块。
- [08-procedure-driven-agent-runtime.md](../08-procedure-driven-agent-runtime.md)：描述流程驱动运行时。
- [14-api-and-schema-contract.md](../14-api-and-schema-contract.md)：描述外部 API 和响应 envelope。
- [15-tool-registry-and-error-codes.md](../15-tool-registry-and-error-codes.md)：描述工具注册和错误码。
- [20-rag-retrieval-vector-mcp-evaluation-upgrade.md](../20-rag-retrieval-vector-mcp-evaluation-upgrade.md)：描述 RAG module 的升级方向。
- [plans/2026-05-12-enterprise-aptguide-harness-plan.md](../plans/2026-05-12-enterprise-aptguide-harness-plan.md)：描述实施顺序。

本文档负责统一这些文档的主线：**先建设 AptGuide 2.0 系统 harness，再在其中优化 RAG。**

## 实施原则

1. 系统 harness 是主架构，RAG 是子模块。
2. 当前 `aptguide2.rag` 不立即删除，先作为 baseline 接入。
3. 新能力优先通过 `aptguide2.harness` 增加，不继续把所有逻辑塞进 RAG pipeline。
4. 写操作必须走 deterministic workflow。
5. 工具调用必须走 Tool Registry。
6. Trace/replay 覆盖完整用户任务，而不是只覆盖检索阶段。
7. 任何模块都不能直接绕过系统级 Response Composer 返回用户消息。
8. Feature 默认 `passes=false`，只有测试、E2E/eval 和文档证据齐备后才允许置为 `true`。
9. 项目状态必须写入 `project/`、`progress/`、`reports/`，不能只依赖聊天上下文。
10. 第一阶段不强绑定 LangGraph、AutoGen 或 CrewAI；先用 FastAPI、Pydantic、pytest 和普通 Python package 固定契约。

## 当前实现状态

- `aptguide2.harness.contracts`: 已实现 — AptGuideRequest, ConversationFrame, RouteDecision, ProcedureResult, StageTrace, AptGuideTrace, AptGuideResponse
- `aptguide2.harness.errors`: 已实现 — StrategyNotFoundError, ProcedureNotFoundError, ReplayPIIError
- `aptguide2.harness.registry`: 已实现 — StrategyRegistry
- `aptguide2.harness.context`: 已实现 — InMemoryContextStore
- `aptguide2.harness.safety`: 已实现 — SafetyBoundary (关键词匹配)
- `aptguide2.harness.routing`: 已实现 — HybridRouter (规则路由)
- `aptguide2.harness.procedures`: 已实现 — Procedure Protocol + ProcedureRuntime
- `aptguide2.harness.composer`: 已实现 — ResponseComposer
- `aptguide2.harness.trace`: 已实现 — TraceRecorder
- `aptguide2.harness.replay`: 已实现 — ReplayWriter (PII 保护)
- `aptguide2.harness.orchestrator`: 已实现 — AptGuideHarness.run()
- `aptguide2.harness.modules.rag.baseline`: 已实现 — RagBaselineProcedure (挂载现有 RAG MVP)
- `aptguide2.harness.modules.capability`: 已实现 — CapabilityProcedure
- `aptguide2.harness.modules.fallback`: 已实现 — FallbackProcedure
- `/chat` 可通过 `APTGUIDE_PIPELINE_VERSION=harness_v1` 切换到 harness 模式，默认仍为 MVP v1
- 回归测试：147 tests all passed (33 harness unit + 114 existing RAG/e2e)

### Tool Governance Layer (2026-05-14)

- `aptguide2.harness.tools.contracts`: 已实现 — ToolDefinition, ToolCallRequest, ToolCallResult, ToolError, RetryPolicy, 及 MVP 工具输入输出 schema
- `aptguide2.harness.tools.errors`: 已实现 — ToolAlreadyRegisteredError, ToolNotFoundError, ToolTimeoutError, ToolExecutionError
- `aptguide2.harness.tools.registry`: 已实现 — ToolRegistry (register/get/names/by_backend/requires_confirmation)
- `aptguide2.harness.tools.builtins`: 已实现 — build_default_tool_registry() 包含 8 个 MVP 工具定义
- `aptguide2.harness.tools.runtime`: 已实现 — ToolRuntime (权限检查、确认门禁、执行器分发、异常标准化、trace 集成)
- `aptguide2.harness.tools.trace`: 已实现 — summarize_tool_request, summarize_tool_result, redact_pii (PII 脱敏)
- `aptguide2.harness.tools.lease_tools`: 已实现 — LeaseHealthExecutor, RoomSearchExecutor, RoomDetailExecutor, AppointmentCreateExecutor, AppointmentListMineExecutor, LeaseListMineExecutor
- `aptguide2.harness.tools.vector_tools`: 已实现 — KBSearchExecutor
- `api/deps.py`: 已实现 — get_tool_runtime() 依赖注入
- 回归测试：206 tests all passed (59 tools unit + 33 harness unit + 114 existing)

### RAG v2 Hybrid Retrieval And Governed Rerank (2026-05-14)

- `aptguide2.rag.planning`: 已实现 — RetrievalPlan, build_retrieval_plan(), 硬过滤/语义查询分离, module intent 推断, step-back queries
- `aptguide2.rag.sparse`: 已实现 — sparse_score(), CJK + ASCII 本地稀疏词法评分
- `aptguide2.rag.hybrid`: 已实现 — HybridCandidate, normalize_scores(), merge_hybrid_candidates() (去重、分数归一化、channel attribution)
- `aptguide2.rag.rerank`: 已实现 — RerankWeights, rerank_kb_sources() (显式特征权重: dense 0.35, sparse 0.15, module 0.20, risk 0.15, validation 0.10, lexical 0.05)
- `aptguide2.rag.validation`: 已实现 — LeaseRoomValidator Protocol, validate_room_candidates() (lease 验证门禁)
- `aptguide2.rag.pipeline_v2`: 已实现 — run_pipeline_v2() 在 `rag_v2` feature flag 下, 含 trace_recorder 支持
- `aptguide2.rag.tool_validation`: 已实现 — ToolRuntimeRoomValidator 适配器
- `aptguide2.rag.eval_metrics`: 已实现 — hit_at_k, mean_reciprocal_rank, ndcg_at_k
- `evals/runners/run_rag_v2.py`: 已实现 — RAG v2 离线评测 runner
- `reports/rag-v2-character-match-audit.md`: 已完成 — 字符匹配 keep/weaken/replace 分类审计
- `reports/rag-v2-evaluation-report.md`: 已完成 — 执行证据
- `docs/tests/rag-v2-evaluation-gates.md`: 已完成 — 评测门槛文档
- `api/app.py`: 已实现 — `rag_v2` 分支 + ToolRuntimeRoomValidator 接入
- 回归测试：246 tests all passed (19 RAG v2 + 59 tools unit + 33 harness unit + 135 existing)
