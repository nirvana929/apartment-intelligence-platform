# 02 · Agent Framework Architecture

> 相关文档：[产品需求](01-product-requirements.md)、[工具与集成契约](04-tool-and-integration-contract.md)、[API Schema](14-api-and-schema-contract.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[记忆状态 Schema](16-memory-state-schema.md)、[运行时设计](08-procedure-driven-agent-runtime.md)、[实施任务](12-implementation-task-plan.md)。

## 1. 设计目标

`AptGuide 2.0` 的架构目标不是把旧版节点补全，而是重新定义一个租房领域 Agent 框架。

核心原则：

- 外层有可观测、可测试的 orchestration；
- 租房域内使用 Agentic reasoning 和 recovery；
- 写操作使用确定性 workflow；
- 工具调用必须白名单和 schema 校验；
- 最终回复由统一 Response Composer 生成；
- 前端交互全部结构化。

## 2. 总体架构

```text
Frontend
  -> Chat API / Stream API
  -> Event Filter
  -> Human Handoff Gate
  -> Conversation Manager
  -> Domain Boundary Router
  -> Phase Router
  -> Task Planner
      -> RoomSearchAgent
      -> RentalKnowledgeAgent
      -> AppointmentWorkflow
      -> UserDataAgent
      -> CapabilityAgent
      -> RecoveryAgent
      -> HandoffAgent
  -> Tool Registry
      -> lease adapter
      -> vector adapter
      -> memory adapter
  -> Response Composer
  -> Structured Response + Trace
```

## 3. 核心模块

### 3.1 Conversation Manager

Conversation Manager 是每轮对话入口。它不直接回答用户，而是整理上下文。

职责：

- 读取和更新 session；
- 抽取短期记忆；
- 检索长期用户画像；
- 维护 rolling summary；
- 维护当前任务；
- 判断上一轮状态；
- 合并用户修正；
- 生成供后续模块使用的 `ConversationFrame`。

建议状态结构：

```python
class ConversationFrame:
    session_id: str
    user_id: str | None
    message: str
    phase: str
    domain_category: str | None
    active_goal: dict
    user_profile: dict
    preferences: dict
    long_term_profile: dict
    memory_candidates: list[dict]
    task_slots: dict
    pending_action: dict | None
    last_recommendations: list[dict]
    last_action_result: dict | None
    conversation_summary: str
    tool_trace: list[dict]
    recovery_trace: list[dict]
```

### 3.2 Domain Boundary Router

判断当前消息是否属于 AptGuide 的服务范围。

它不等同于 intent 分类。intent 是“用户想做什么”，domain boundary 是“这个请求是否属于本产品应该处理的范围”。

输出示例：

```json
{
  "domain_category": "free_riding_generation",
  "confidence": 0.92,
  "reason": "用户要求生成 Vue 网页，属于通用代码生成，不是租房任务"
}
```

### 3.3 Phase Router

同一句话在不同阶段含义不同。

例如：

```text
确认
取消
预算我都接受
第一个
再看看
```

Phase Router 负责判断这些话应该如何解释。

推荐 phase：

```text
idle
collecting_room_requirements
searching_rooms
showing_room_results
collecting_appointment_info
awaiting_confirmation
tool_executed
tool_failed
boundary_declined
```

### 3.4 Task Planner

Task Planner 负责为租房域内任务生成小型计划。

找房示例：

```text
目标：找大学城南亭附近房源
条件：预算 1500，地标 大学城南亭
计划：
1. 归一化地标到番禺区/大学城片区
2. 用预算和地标语义检索
3. 如果为空，去掉预算 hard filter
4. 如果仍为空，推荐附近可租替代
5. 回复时说明放宽原因
```

计划不需要暴露给用户，但应写入 debug metadata 和 eval trace。

产品文档中推荐使用“任务流程驱动 Agent”来描述这一层。内部实现可以在复杂找房中使用 Planner + ReAct，在预约等写操作中使用确定性 workflow。

### 3.5 Specialist Agents

#### RoomSearchAgent

负责找房。它允许有限 ReAct 循环：

```text
Reason -> Search -> Observe -> Relax/Refine -> Search -> Compose Evidence
```

它不能编造房源，只能基于工具结果推荐。

#### RentalKnowledgeAgent

负责租房规则 RAG。

它必须：

- 使用知识库来源；
- 低置信度不强答；
- 对租房相关但缺少资料的问题给出范围内解释和下一步建议。

#### AppointmentWorkflow

负责预约写操作。它不是自由 Agent，而是强 workflow：

```text
resolve room -> collect time -> validate -> create pending confirmation -> wait action -> execute tool
```

#### UserDataAgent

负责我的预约、我的租约、浏览历史等个人数据查询。它只通过工具接口访问，不信任前端 user_id。

#### CapabilityAgent

负责回答“你是谁 / 你能做什么 / 你是什么助手”。内容来自固定 capability profile，不调用通用模型自由发挥。

#### RecoveryAgent

负责处理失败和异常：

- 空搜索；
- 工具失败；
- stale confirmation；
- 重复确认；
- 槽位冲突；
- 用户修正旧条件。

#### HandoffAgent

负责判断是否需要人工接管，并生成给人工客服使用的摘要。

触发条件包括：

- 用户明确要求人工；
- 工具失败多次；
- 涉及合同、押金、投诉等高风险争议；
- 用户情绪明显负面；
- 房源规则缺少可靠来源；
- 预约或租约数据异常。

人工接管不代表丢失上下文。系统应当把用户目标、已尝试操作、失败原因、推荐房源和最近对话摘要交给人工客服。

### 3.6 Tool Registry

工具注册表是 Agent 能力边界。

每个工具必须声明：

```python
class ToolDefinition:
    name: str
    description: str
    input_schema: type
    output_schema: type
    backend: str
    permission: str
    requires_user: bool
    requires_confirmation: bool
    timeout_seconds: int
    error_mapping: dict
```

Agent 不能构造任意 URL，不能绕开 registry。

### 3.7 Memory Center

Memory Center 负责把“当前对话上下文”和“长期用户偏好”分离。

推荐拆分：

```text
recent_messages      最近几轮原文
rolling_summary      可压缩的历史摘要
active_task_state    当前任务状态
long_term_profile    用户长期偏好
memory_candidates    待确认或待提升为长期记忆的事实
memory_audit_log     记忆来源、更新时间和撤销记录
```

长期记忆必须可解释、可撤销、可降级。用户一次性表达的临时需求不能直接变成永久偏好，除非用户明确表达“以后都这样”或同类偏好多次出现。

### 3.8 Response Composer

最终回复统一由 Response Composer 生成。

输入：

- domain category；
- phase；
- task result；
- tool observations；
- recovery decision；
- memory facts；
- UI actions；
- handoff state；
- trace summary。

输出：

```json
{
  "reply": "...",
  "cards": [],
  "actions": [],
  "pending_action": null,
  "sources": [],
  "debug": {}
}
```

### 3.9 Trace Logger

Trace Logger 记录系统做过什么，但不暴露原始思维链。

推荐事件：

```text
message_received
memory_loaded
memory_updated
boundary_classified
phase_detected
plan_created
tool_call_started
tool_call_finished
recovery_started
handoff_triggered
response_composed
```

这些事件用于开发调试、运营分析、质量评测和问题复盘。

## 4. 为什么仍然可以使用 LangGraph

`AptGuide 2.0` 可以继续使用 LangGraph，但不是沿用旧图。

推荐方式：

```text
Main Graph: Conversation Orchestrator
Subgraph: Room Search Agent
Subgraph: Knowledge QA Agent
Subgraph: Appointment Workflow
Subgraph: User Data Query
Subgraph: Boundary Response
```

LangGraph 用于可观测和状态流转，ReAct 循环只存在于受控子图内部。

## 5. 错误处理原则

每个失败都必须带有可解释原因：

```json
{
  "error_type": "empty_search",
  "cause": "budget_too_strict_or_area_unmapped",
  "recoverable": true,
  "next_action": "relax_budget"
}
```

用户不应该看到内部错误，但应该知道下一步能做什么。

## 6. 最小 MVP 图

第一版可以先做最小图：

```text
message
  -> event_filter
  -> handoff_gate
  -> conversation_manager
  -> boundary_router
  -> phase_router
  -> task_router
      -> room_search_agent
      -> appointment_workflow
      -> knowledge_agent
      -> capability_agent
      -> boundary_response
      -> recovery_agent
  -> response_composer
```

这样已经能解决旧版大部分体验问题。
