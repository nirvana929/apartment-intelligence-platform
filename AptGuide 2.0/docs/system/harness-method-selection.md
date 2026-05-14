---
type: system
status: active
---

# Harness Method Selection

## 背景

AptGuide 2.0 当前已经完成 FastAPI + RAG MVP，但目标不是继续堆 RAG 能力，而是建设一个可长期迭代、可恢复、可验证的租房 Agent 系统。项目需要选择一种适合当前阶段的 harness 方法，既能吸收 Anthropic Harness Engineering 的核心思想，又不能把第一版实现复杂化到无法交付。

本文档给出 AptGuide 2.0 的 harness 方法选型，作为后续实现、文档、eval、Agent 执行计划的判断依据。

## 选型结论

AptGuide 2.0 采用：

```text
Procedure-driven Product Harness
+ Eval-first Engineering Harness
+ External Progress State
```

不采用“全自动开放式多 Agent 自治系统”作为第一阶段主方法。

推荐的一句话定义：

```text
用确定性 procedure runtime 管住业务行为，用 eval-first 和 trace/replay 管住工程可信度，用外部 JSON/Markdown 状态文件管住长期迭代。
```

## 候选方法对比

| 方法 | 说明 | 优点 | 风险 | AptGuide 结论 |
| --- | --- | --- | --- | --- |
| RAG-only Harness | 只围绕检索、重排、回答做 harness | 实现快，适合当前 MVP | 预约、记忆、人工接管、写操作无法统一治理 | 不采用 |
| Full Autonomous Multi-Agent Harness | planner/generator/evaluator/doc agent 全部在线协作并自主推进 | 最接近通用 coding agent 理想形态 | 对当前租房产品过重，容易引入不可控状态和难验证行为 | 暂不作为产品运行时 |
| Procedure-driven Product Harness | 以 router + procedure runtime 管理找房、问答、预约、记忆、人工接管 | 业务边界清晰，写操作可控，适合租房场景 | 需要较多契约和测试 | 采用 |
| Eval-first Engineering Harness | feature 默认失败，必须测试、trace、replay、report 后才通过 | 符合 Anthropic Harness Engineering，适合长期开发 | 需要维护 feature/sprint/progress 文件 | 采用 |
| LangGraph-first Runtime | 用图编排实现所有流程 | 可视化流程强，适合复杂状态机 | 当前代码是 FastAPI + Python package，过早引入会增加迁移成本 | 后续可选，不作为第一阶段依赖 |

## 系统定位

AptGuide 2.0 需要两层 harness。

第一层是产品运行时 harness：

```text
ChatRequest
  -> AptGuideRequest
  -> ContextStore
  -> SafetyBoundary
  -> HybridRouter
  -> ProcedureRuntime
      -> rag.room_search
      -> rag.kb_qa
      -> appointment.workflow
      -> memory.workflow
      -> user_data.query
      -> handoff.workflow
      -> capability.profile
      -> fallback.safety
  -> ToolRegistry
  -> ResponseComposer
  -> TraceRecorder
  -> AptGuideResponse
```

第二层是工程执行 harness：

```text
PROJECT_SPEC
  -> feature-list.json
  -> sprint-plan.json
  -> tests/evals
  -> traces/replay
  -> reports/evaluation-report.md
  -> progress/current-plan.md
  -> progress/known-issues.md
  -> progress/completed.md
  -> progress/next-steps.md
```

产品运行时 harness 解决“用户请求如何安全执行”。工程执行 harness 解决“Agent 和开发者如何可信地迭代这个系统”。

## 核心流程

### 1. 用户请求执行流程

每次 `/chat` 请求必须经过统一系统入口。任何模块不能直接绕过 `ResponseComposer` 返回用户消息。

```text
request
  -> load context
  -> classify boundary and safety
  -> route task
  -> run procedure
  -> call governed tools
  -> record trace
  -> compose response
  -> save context
```

### 2. Feature 开发流程

所有 feature 默认失败。

```json
{
  "passes": false,
  "test_status": "not_run",
  "evidence": []
}
```

只有满足以下条件，才允许把 `passes` 改成 `true`：

- 代码或文档实现完成；
- 对应单元测试通过；
- 相关 API/E2E/eval 通过；
- trace 或测试报告能作为 evidence；
- 文档索引和相关契约已同步。

### 3. Sprint 执行流程

每个 sprint 必须有机器可读 contract：

```json
{
  "sprint_id": "sprint_01_harness_foundation",
  "goal": "实现 AptGuide 2.0 harness foundation",
  "features": [
    "feature_harness_contracts",
    "feature_harness_orchestrator",
    "feature_harness_api_switch"
  ],
  "must_pass": [
    "tests/unit/harness",
    "tests/unit/rag",
    "tests/e2e/test_api.py"
  ],
  "e2e_required": true,
  "blocking_bugs_allowed": false
}
```

## 关键设计决策

### 决策 1：第一阶段不用开放式 planner 自主控制业务流程

租房产品里存在预约、合同、押金、隐私、用户数据等高风险路径。开放式 planner 可以辅助生成计划，但不能直接决定写操作。写操作必须通过 deterministic procedure 和 structured confirmation。

### 决策 2：RAG 是 module，不是 app architecture

现有 `aptguide2.rag` 保留为 baseline。第一阶段通过 `harness.modules.rag.baseline.RagBaselineProcedure` 接入，不重写、不删除。后续再逐步把 query understanding、retrieval、rerank、confidence 拆进 harness module。

### 决策 3：trace/replay 记录系统行为，不记录 Chain-of-Thought

Trace 需要记录 stage、strategy、tool、latency、error、result count、fallback reason，但不能记录原始思维链和未脱敏 PII。

### 决策 4：工程状态必须外部持久化

聊天上下文不能作为项目状态来源。长期开发必须维护：

```text
project/feature-list.json
project/sprint-plan.json
progress/current-plan.md
progress/completed.md
progress/known-issues.md
progress/next-steps.md
reports/evaluation-report.md
```

### 决策 5：暂不强绑定 LangGraph / AutoGen / CrewAI

当前最小可靠实现应先使用 FastAPI、Pydantic、pytest 和普通 Python package。等 procedure contract、trace、eval 稳定后，再决定是否把部分 runtime 迁移到 LangGraph 或其他框架。

## 第一阶段落地范围

第一阶段只建设 harness foundation：

- `aptguide2.harness.contracts`
- `aptguide2.harness.context`
- `aptguide2.harness.safety`
- `aptguide2.harness.routing`
- `aptguide2.harness.procedures`
- `aptguide2.harness.composer`
- `aptguide2.harness.trace`
- `aptguide2.harness.replay`
- `aptguide2.harness.orchestrator`
- `aptguide2.harness.modules.rag.baseline`
- `/chat` 的 `APTGUIDE_PIPELINE_VERSION=harness_v1` 开关
- project/progress/reports 状态文件

第一阶段不做：

- 完整自主多 Agent 调度；
- 复杂 eval 平台；
- 线上 A/B；
- 完整前端重构；
- 全量 RAG 重写；
- LangGraph 迁移。

## 验收标准

Harness 方法选型落地后，必须满足：
 
- `/chat` 默认仍走当前 MVP；
- `APTGUIDE_PIPE LINE_VERSION=harness_v1` 可切换到 harness；
- capability、fallback、room_search、kb_qa 可通过 procedure runtime 执行；
- unit/e2e 测试可以证明默认路径未被破坏；
- feature 状态以 JSON 维护，未验证前 `passes=false`；
- sprint contract 能列出 must-pass 测试；
- progress 文件能让新 Agent 接手；
- trace/replay 能支撑一次请求复盘；
- 文档索引能指向当前 source of truth。

## 风险与边界

| 风险 | 处理方式 |
| --- | --- |
| harness 过早复杂化 | 第一阶段只做 foundation，不实现完整多 Agent 自治 |
| RAG MVP 被重写破坏 | 明确保留 `aptguide2.rag`，通过 baseline adapter 接入 |
| feature 状态流于形式 | `passes=true` 必须带测试/eval evidence |
| trace 泄露隐私 | replay writer 拒绝 PII keys，trace 只存摘要 |
| 文档和代码脱节 | 每个 sprint 结束同步 docs、project JSON、progress、reports |

## 相关文档

- [Enterprise Harness Architecture](./enterprise-harness-architecture.md)
- [Agent Framework Architecture](../02-agent-framework-architecture.md)
- [Trace Eval And Observability](../10-trace-eval-and-observability.md)
- [Prompt And Eval Contract](../17-prompt-and-eval-contract.md)
- [Anthropic Agent Eval Methodology](../19-anthropic-agent-eval-methodology.md)
- [Enterprise Harness Implementation Plan](../plans/2026-05-12-enterprise-aptguide-harness-plan.md)
- [Enterprise Harness Agent Execution Plan](../plans/2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md)
