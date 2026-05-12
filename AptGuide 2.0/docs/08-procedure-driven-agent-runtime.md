# 08 · Procedure Driven Agent Runtime

> 相关文档：[Agent 架构](02-agent-framework-architecture.md)、[领域边界策略](03-domain-boundary-and-interaction-policy.md)、[API Schema](14-api-and-schema-contract.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[记忆状态 Schema](16-memory-state-schema.md)、[人工接管](09-human-handoff-and-operations.md)、[Trace/Eval](10-trace-eval-and-observability.md)。

## 1. 为什么使用任务流程驱动

真实客服 Agent 不只是聊天。它需要识别用户目标、收集参数、查询业务系统、解释结果、处理失败、必要时转人工。

因此 `AptGuide 2.0` 对外定位为：

```text
任务流程驱动的租房客服 Agent
```

内部可以混合使用：

```text
规则路由
LLM 分类
Planner
ReAct 搜索恢复
RAG
确定性 Workflow
工具调用
人工接管
```

但产品和文档不应过度强调“自由多 Agent”或“裸思维链”。关键是可控、可测、可审计。

## 2. 运行时总览

```text
Incoming Event
  -> Event Filter
  -> Human Handoff Gate
  -> Conversation Manager
  -> Hybrid Router
  -> Procedure Selector
  -> Specialist Procedure
  -> Tool Registry
  -> Recovery Procedure
  -> Response Composer
  -> Trace Logger
```

## 3. Event Filter

Event Filter 负责区分哪些事件应该触发 Agent。

| 事件 | 处理 |
| --- | --- |
| 用户文本消息 | 进入 Conversation Manager |
| 前端结构化 action | 校验 action 后进入对应 workflow |
| 系统通知 | 记录，不触发自由回复 |
| 过期 action | 拒绝并说明已过期 |
| 重复 action | 拦截并返回当前状态 |
| 人工客服消息 | 记录上下文，不触发 AI 自动回复 |

## 4. Hybrid Router

路由不应完全交给大模型。

推荐顺序：

```text
1. pending_action 确认/取消
2. stale action / duplicate action
3. human handoff 状态
4. 用户数据和越权风险
5. 明确域外/代码生成/敏感请求
6. 能力说明和记忆查询
7. 租房任务
8. 租房知识
9. LLM 分类兜底
10. 后处理安全校验
```

规则优先处理：

- 确认/取消；
- 预约写操作；
- 我的预约/租约；
- 越权查询；
- 旧 confirmation；
- 人工接管；
- 明确无关请求。

LLM 适合处理：

- 模糊找房需求；
- 用户偏好表达；
- 区域和地标理解；
- 租房知识问题；
- 用户修正旧条件。

## 5. Procedure 类型

### 5.1 Room Search Procedure

适合使用 Planner + ReAct 搜索恢复。

```text
collect requirements
  -> normalize area
  -> search exact
  -> observe result
  -> relax budget / area / payment
  -> search alternative
  -> compose recommendations
```

示例：

```text
用户：找大学城南亭附近安静点的房子，预算1500左右。

Plan:
1. 归一化大学城南亭
2. 按1500预算和安静偏好搜索
3. 如果为空，放宽预算
4. 如果仍为空，推荐附近替代
5. 回复时解释放宽原因
```

### 5.2 Rental Knowledge Procedure

适合 RAG + guarded answer。

```text
classify rental knowledge
  -> kb.search
  -> confidence check
  -> answer with sources
  -> if low confidence, explain limitation and suggest next step
```

### 5.3 Appointment Workflow

写操作必须确定性。

```text
resolve room
  -> collect time
  -> validate user
  -> validate room availability
  -> create pending_action
  -> wait confirmation_id
  -> execute appointment.create
  -> clear pending_action
```

不得允许纯文本“确认”绕过 `confirmation_id`。

### 5.4 User Data Query

用于查询我的预约、我的租约、浏览历史。

```text
validate authenticated user
  -> call lease tool
  -> filter by backend user_id
  -> summarize result
```

前端传入的 user_id 不可信，必须由 `lease` 网关注入或后端身份系统提供。

### 5.5 Capability Procedure

用于回答“你是谁 / 你能做什么”。

内容来自固定 capability profile，不调用通用自由生成。

### 5.6 Memory Procedure

用于回答“你记得我什么 / 删除我的偏好 / 以后按这个找”。

```text
read memory
  -> explain remembered facts
  -> update/delete with audit
```

### 5.7 Recovery Procedure

处理异常：

- 空搜索；
- 工具失败；
- 用户改条件；
- stale confirmation；
- 重复确认；
- 房源 ID 缺失；
- 知识库低置信度；
- 个人数据未登录。

## 6. 多专家模块

`AptGuide 2.0` 可以是多专家，但不是多个自由 Agent 互相聊天。

推荐模块：

```text
BoundaryAgent
MemoryAgent
RoomSearchAgent
KnowledgeAgent
AppointmentWorkflow
UserDataAgent
RecoveryAgent
HandoffAgent
ResponseComposer
```

模块之间通过 `ConversationFrame` 和结构化 `ToolResult` 传递状态。

不推荐：

```text
Agent A 用自然语言告诉 Agent B
Agent B 再自由解释给 Agent C
```

推荐：

```json
{
  "phase": "searching_rooms",
  "slots": {
    "area_text": "大学城南亭",
    "max_rent": 1500
  },
  "tool_observations": [
    {
      "tool": "room.search",
      "strategy": "exact_search",
      "result_count": 0
    }
  ],
  "recovery_decision": {
    "type": "relax_budget",
    "reason": "exact search empty"
  }
}
```

## 7. 状态传递

LangGraph 中推荐使用状态传递。

核心状态：

```python
class ConversationFrame:
    session_id: str
    request_id: str
    user_id: str | None
    message: str
    action: dict | None
    phase: str
    domain_category: str
    active_goal: dict
    recent_messages: list[dict]
    rolling_summary: str
    long_term_profile: dict
    task_slots: dict
    pending_action: dict | None
    last_recommendations: list[dict]
    tool_observations: list[dict]
    recovery_decision: dict | None
    handoff: dict | None
    trace: list[dict]
```

## 8. 工具调用约束

所有工具必须通过 Tool Registry。

```text
Agent 不能构造任意 URL
Agent 不能直接访问 MySQL
Agent 不能绕过 confirmation
Agent 不能信任前端 user_id
Agent 不能编造房源和价格
```

## 9. 参考案例启发

企业客服产品通常采用类似结构：

- Intercom Fin 使用知识源、用户属性、Data connectors、Tasks、Procedures；
- Zendesk 使用 procedures、help center、solved tickets、agent-approved actions；
- Salesforce Agentforce 使用 CRM context、Flows、Apex、APIs、guardrails；
- XianyuAutoAgent 使用会话记忆、规则/LLM 混合路由、多专家 prompt 和人工接管。

这些案例说明，真实客服 Agent 的核心不是自由对话，而是：

```text
上下文 + 业务流程 + 工具 + 接管 + 评测
```

## 10. MVP 范围

第一版不需要实现全部专家。

推荐 MVP：

```text
Event Filter
Conversation Manager
BoundaryAgent
MemoryAgent basic
RoomSearchAgent
AppointmentWorkflow
ResponseComposer
TraceLogger
```

后续再加入：

```text
HandoffAgent
UserDataAgent
long-term profile UI
advanced eval
operations dashboard
```
