# 12 · Implementation Task Plan

> 相关文档：[Agent 架构](02-agent-framework-architecture.md)、[API Schema](14-api-and-schema-contract.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[记忆状态 Schema](16-memory-state-schema.md)、[Prompt/Eval 契约](17-prompt-and-eval-contract.md)、[实施准备清单](18-implementation-readiness-checklist.md)、[可行性计划](11-feasibility-and-development-plan.md)。

## 1. 目标

本文档把 `AptGuide 2.0` 的方案转成可开发任务。它不是最终代码，但规定了推荐目录、模块边界、任务顺序和验收方式。

当前更新后的主线是：先建设 `AptGuide 2.0` 企业级 harness，再把 RAG 作为其中一个模块逐步优化到高质量。不要把 RAG harness 当成整个系统的工程边界。

开发原则：

- 先定 schema，再写流程；
- 先做 trace，再做复杂 Agent；
- 先接真实工具健康检查，再做业务闭环；
- 写操作永远走 deterministic workflow；
- 长期记忆先保守，再逐步自动化；
- 每个阶段都有可跑的 eval。

## 2. 推荐代码目录

```text
AptGuide 2.0/
├── backend/
│   ├── pyproject.toml
│   ├── src/aptguide2/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── stream.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── errors.py
│   │   ├── schemas/
│   │   │   ├── chat.py
│   │   │   ├── cards.py
│   │   │   ├── actions.py
│   │   │   ├── memory.py
│   │   │   ├── tools.py
│   │   │   └── trace.py
│   │   ├── runtime/
│   │   │   ├── frame.py
│   │   │   ├── event_filter.py
│   │   │   ├── graph.py
│   │   │   └── response_composer.py
│   │   ├── harness/
│   │   │   ├── contracts.py
│   │   │   ├── orchestrator.py
│   │   │   ├── context.py
│   │   │   ├── routing.py
│   │   │   ├── procedures.py
│   │   │   ├── tools.py
│   │   │   ├── composer.py
│   │   │   ├── trace.py
│   │   │   ├── replay.py
│   │   │   └── modules/
│   │   │       ├── rag/
│   │   │       ├── appointment/
│   │   │       ├── memory/
│   │   │       ├── user_data/
│   │   │       ├── handoff/
│   │   │       └── capability/
│   │   ├── routing/
│   │   │   ├── boundary.py
│   │   │   ├── phase.py
│   │   │   └── hybrid_router.py
│   │   ├── memory/
│   │   │   ├── store.py
│   │   │   ├── profile.py
│   │   │   ├── compaction.py
│   │   │   └── extractor.py
│   │   ├── procedures/
│   │   │   ├── room_search.py
│   │   │   ├── knowledge.py
│   │   │   ├── appointment.py
│   │   │   ├── user_data.py
│   │   │   ├── recovery.py
│   │   │   └── handoff.py
│   │   ├── tools/
│   │   │   ├── registry.py
│   │   │   ├── lease_adapter.py
│   │   │   ├── vector_adapter.py
│   │   │   └── memory_adapter.py
│   │   ├── llm/
│   │   │   ├── client.py
│   │   │   └── structured.py
│   │   └── trace/
│   │       ├── logger.py
│   │       └── events.py
│   ├── prompts/
│   │   ├── boundary_router.md
│   │   ├── memory_extractor.md
│   │   ├── room_search_planner.md
│   │   ├── knowledge_answer.md
│   │   ├── recovery.md
│   │   └── response_composer.md
│   └── tests/
│       ├── unit/
│       ├── contract/
│       └── e2e/
├── frontend/
│   ├── package.json
│   └── src/
│       ├── api/
│       ├── components/
│       ├── cards/
│       ├── state/
│       └── views/
└── evals/
    ├── cases/
    │   ├── boundary.yaml
    │   ├── memory.yaml
    │   ├── room_search.yaml
    │   ├── appointment.yaml
    │   └── handoff.yaml
    └── runners/
```

如果后续决定直接复用旧版 `AptGuide/src/aptguide`，也应按上述边界逐步拆分，不建议在旧 `graph.py` 里继续堆节点。

如果从当前 MVP 继续演进，推荐保留已实现的 `aptguide2.rag`，新增 `aptguide2.harness`。历史计划曾建议旧 RAG 先作为 harness 的 RAG baseline module 接入；2026-05-14 后的主线决策已调整为：旧 RAG MVP 仅保留为 legacy reference，不再接任何用户可见接口；harness 成为唯一产品运行时；RAG v2 作为 harness 内部检索模块使用。最新执行计划见 [plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md](plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md)。

## 2.1 当前优先实施主线

当前优先级调整为：

```text
1. AptGuide harness contracts
2. Context / routing / procedure runtime
3. Tool registry / trace / replay
4. Mount current RAG MVP as module
5. Upgrade RAG module
6. Appointment / memory / handoff workflows
```

详细实施计划见 [plans/2026-05-12-enterprise-aptguide-harness-plan.md](plans/2026-05-12-enterprise-aptguide-harness-plan.md)。

## 3. Phase 0: Schema 和工程骨架

目标：先固定前后端、工具和 trace 的共同语言。

任务：

- 创建 `backend/src/aptguide2/schemas/chat.py`；
- 创建 `cards.py`、`actions.py`、`tools.py`、`memory.py`、`trace.py`；
- 按 [14-api-and-schema-contract.md](14-api-and-schema-contract.md) 固定 API envelope；
- 按 [15-tool-registry-and-error-codes.md](15-tool-registry-and-error-codes.md) 固定工具定义和错误码；
- 按 [16-memory-state-schema.md](16-memory-state-schema.md) 固定状态结构；
- 创建 FastAPI `main.py`；
- 创建 `/health`；
- 创建基础配置和日志；
- 创建最小 graph，先返回 capability response。

验收命令：

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit -q
uv run uvicorn aptguide2.main:app --host 0.0.0.0 --port 8100
curl http://127.0.0.1:8100/health
```

成功标准：

- `/health` 返回 `ok`；
- `/api/chat` 返回结构化 `ChatResponse`；
- response 包含 `request_id` 和 `trace_id`。
- [18-implementation-readiness-checklist.md](18-implementation-readiness-checklist.md) 的 Phase 0 Exit Criteria 全部满足。

## 4. Phase 1: Boundary、Capability 和 Trace

目标：让系统有领域边界和可观测轨迹。

任务：

- 实现 `EventFilter`；
- 实现 `BoundaryRouter`；
- 实现 `CapabilityAgent`；
- 实现 `TraceLogger`；
- 实现 `ResponseComposer` 基础版；
- 加 boundary eval。

测试用例：

```text
你能做什么 -> 说明找房/规则/预约/租约
广州天气怎么样 -> 拒绝天气并引导找房
帮我写 React 网页 -> 拒绝通用代码生成
查别人的租约 -> 拒绝越权
```

成功标准：

- 域外请求不调用租房工具；
- 能力说明不自由发挥；
- trace 记录 boundary result。

## 5. Phase 2: Memory Center

目标：支持短期记忆、长期画像和上下文压缩。

任务：

- 实现 `ConversationFrame`；
- 实现 `recent_messages`；
- 实现 `active_task_state`；
- 实现 `rolling_summary`；
- 实现 `long_term_profile`；
- 实现 `memory_candidates`；
- 实现 `memory_accept/reject/delete` action；
- 加 memory eval。

测试用例：

```text
我是小明，我想找大学城附近房子
我的名字是谁，我来干嘛的

以后帮我优先看大学城附近安静一点的房子
可以记住
新会话：帮我继续找
```

成功标准：

- 短期问题走当前会话；
- 长期偏好需要确认后保存；
- 用户可以删除偏好；
- 压缩后不丢 pending action。

## 6. Phase 3: Tool Registry 和 Lease Adapter

目标：把真实业务系统接进来。

任务：

- 实现 `ToolDefinition`；
- 实现 `ToolResult` envelope；
- 实现 `LeaseToolAdapter`；
- 实现 `/health/deps`；
- 接入 `room.search`、`room.detail`；
- 接入 `appointment.create`；
- 接入 `appointment.list_mine`、`lease.list_mine`；
- 实现错误映射。

成功标准：

- AptGuide 不直接访问 MySQL；
- 所有工具调用都有 timeout；
- 工具失败返回 recoverable error；
- trace 中记录 tool name、latency、error_code。

## 7. Phase 4: Room Search Procedure

目标：找房从一次检索变成可恢复流程。

任务：

- 实现 `area.normalize`；
- 实现 hard filter / soft preference 拆分；
- 实现 `exact_search`；
- 实现 `relaxed_budget_search`；
- 实现 `relaxed_area_search`；
- 实现 `nearby_alternative_search`；
- 实现推荐卡片；
- 实现推荐理由生成。

测试用例：

```text
找大学城南亭附近1500以内的房子
预算我都接受
天河区3000以内能月付
想找安静一点适合考研的房间
```

成功标准：

- 空结果不死胡同；
- 用户清除预算后不保留旧 max_rent；
- 卡片和文本一致；
- 不编造房源。

## 8. Phase 5: Appointment Workflow

目标：预约安全执行。

任务：

- 实现 `resolve_room`；
- 实现时间解析和校验；
- 实现 `pending_action`；
- 实现 `confirmation_id`；
- 实现 confirmation card；
- 实现 stale action 拦截；
- 实现 appointment.create 调用；
- 实现失败恢复和人工接管触发。

测试用例：

```text
预约第一个，明天下午三点
点击取消
再点击旧确认
手动输入确认
预约天河创客空间1008，明天下午2点
```

成功标准：

- 无 confirmation_id 不执行；
- 旧 confirmation 不能执行；
- 缺 apartment_id 不默认 0；
- 工具失败不显示成功。

## 9. Phase 6: Knowledge 和 User Data

目标：补齐客服常用问答和个人数据查询。

任务：

- 实现 `kb.search`；
- 实现低置信度策略；
- 实现 sources；
- 实现我的预约查询；
- 实现我的租约查询；
- 实现未登录处理。

测试用例：

```text
押金怎么退
提前退租怎么处理
我现在有几个预约
我的租约什么时候到期
```

成功标准：

- 租房知识有来源；
- KB 不足时不强答；
- 个人数据只能查本人；
- 未登录给出登录引导。

## 10. Phase 7: Handoff 和 Operations

目标：符合真实客服场景。

任务：

- 实现 `handoff.create`；
- 实现 handoff summary；
- 实现 AI paused/resumed；
- 实现知识缺口记录；
- 实现基础运营指标日志。

测试用例：

```text
转人工
我要投诉押金问题
预约工具连续失败
这个房源到底能不能养大型犬
```

成功标准：

- 人工接管后 AI 不自动回复；
- handoff summary 包含用户目标、偏好、失败原因；
- 高风险争议不由 AI 裁定；
- 知识缺口可沉淀。

## 11. Phase 8: Frontend

目标：独立前端可演示完整链路。

任务：

- 实现聊天页面；
- 实现 room card；
- 实现 confirmation card；
- 实现 memory candidate card；
- 实现 handoff card；
- 实现 action 请求；
- 实现 SSE 状态展示；
- 实现开发 trace panel。

成功标准：

- 用户能完成找房到预约；
- 旧按钮禁用；
- 记忆保存/删除可操作；
- 人工接管状态清晰；
- trace panel 能看到关键事件。

## 12. Phase 9: Eval 和回归

目标：每次改动都能验证。

任务：

- 建立 YAML eval cases；
- 建立 pytest runner；
- 建立真实工具契约样例和测试库种子数据；
- 建立 prompt version；
- 建立每阶段回归命令。

推荐命令：

```bash
uv run pytest tests/unit -q
uv run pytest tests/contract -q
uv run pytest tests/e2e -q
uv run python evals/runners/run_cases.py evals/cases
```

成功标准：

- boundary eval 通过；
- memory eval 通过；
- room search eval 通过；
- appointment safety eval 通过；
- handoff eval 通过。

## 12.1 Phase 0 Gate: 禁止 Mock 运行路径

目标：开发开始前就阻断 mock 运行路径，后续阶段不得再新增。

任务：

- 不创建 mock backend、mock tool client、mock room data；
- 确认 `Tool Registry` 只注册 `lease`、`vector`、`memory`、`internal` 等真实后端；
- 确认开发和演示链路使用真实 `lease/web-app`、Milvus、Redis 和长期画像存储；
- 测试使用真实测试环境、种子数据、契约样例或录制的只读响应样本；
- 增加启动检查：如果 `APTGUIDE_BACKEND_MODE=mock` 或 mock backend 出现在产品配置中，启动失败。

验收：

- `rg -n "MockToolClient|BACKEND_MODE=mock|backend.*mock|knowledge/mock|tools/mock" backend src` 在产品代码路径无命中；
- 真实找房、预约、我的预约/租约查询均走 `/internal/ai/tools/*`；
- eval 和端到端 smoke test 必须走真实后端或真实测试库；
- 文档中 mock 仅作为禁止项出现。

## 13. 开发优先级

必须先做：

```text
schema
trace
boundary
memory state
tool registry
room search
appointment workflow
```

可以后做：

```text
长期记忆 UI
完整运营后台
复杂情绪识别
多渠道接入
高级 prompt 自动评测
```

不建议第一版做：

```text
全自由多 Agent
自动执行高风险写操作
长期记忆无确认写入
直接查 MySQL
复杂微服务化
```

## 14. 里程碑

| 里程碑 | 交付 | 验收 |
| --- | --- | --- |
| M1 | API + Boundary + Trace | 能拒答和说明能力 |
| M2 | Memory Center | 能记住短期目标和长期偏好 |
| M3 | Room Search | 能真实找房和空结果恢复 |
| M4 | Appointment | 能安全预约和拦截旧确认 |
| M5 | Knowledge/UserData | 能问规则和查本人数据 |
| M6 | Handoff/Ops | 能转人工和沉淀问题 |
| M7 | Frontend/Eval | 完整演示和回归测试 |
