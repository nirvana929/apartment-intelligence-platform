# 14 · API And Schema Contract

> 相关文档：[README](../README.md)、[前端交互协议](05-frontend-interaction-protocol.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[记忆状态 Schema](16-memory-state-schema.md)、[Trace/Eval](10-trace-eval-and-observability.md)、[实施任务](12-implementation-task-plan.md)。

## 1. 目标

本文档是 AptGuide 2.0 前端、后端 Agent、工具适配器之间的 API source-of-truth。实现时优先以本文档为准，其他文档只解释设计动机。

第一版必须固定：

- HTTP endpoint；
- request / response envelope；
- card / action / pending_action schema；
- SSE event schema；
- 错误响应；
- 字段命名策略。

## 2. 字段命名策略

AptGuide 2.0 自身 API 使用 `snake_case`。

```text
session_id
request_id
trace_id
pending_action
confirmation_id
domain_category
```

对接 `lease/web-app` 时，由 `LeaseToolAdapter` 负责把 `snake_case` 转成 Java DTO 当前使用的 `camelCase`。

```text
AptGuide 2.0 API: max_rent, appointment_time, apartment_id
Lease Tool DTO:   maxRent, appointmentTime, apartmentId
```

禁止在业务流程里散落手写字段转换。字段转换只能出现在 adapter 或 schema alias 层。

## 3. Endpoints

| Endpoint | 方法 | 用途 | MVP |
| --- | --- | --- | --- |
| `/health` | GET | AptGuide 服务健康检查 | 是 |
| `/health/deps` | GET | 检查 lease、Redis、Milvus、LLM 依赖 | 是 |
| `/api/chat` | POST | 非流式对话，返回完整结构化响应 | 是 |
| `/api/chat/stream` | POST | SSE 流式对话，最后发送 `final` | 是 |
| `/api/memory/profile` | GET | 查看用户长期偏好 | 可后置 |
| `/api/memory/profile/{memory_id}` | DELETE | 删除长期偏好 | 可后置 |
| `/api/debug/trace/{trace_id}` | GET | 开发环境查看 trace | 开发环境 |

生产环境不暴露 `/api/debug/*` 给普通用户。

## 4. Chat Request

```json
{
  "session_id": "s-001",
  "message": "帮我找大学城南亭附近的房子",
  "action": null,
  "client_context": {
    "source": "standalone_web",
    "timezone": "Asia/Shanghai",
    "locale": "zh-CN",
    "app_version": "aptguide2-dev"
  }
}
```

结构化 action 请求：

```json
{
  "session_id": "s-001",
  "message": "",
  "action": {
    "type": "confirmation_confirm",
    "action_id": "a-001",
    "confirmation_id": "c-001",
    "payload": {}
  },
  "client_context": {
    "source": "standalone_web",
    "timezone": "Asia/Shanghai"
  }
}
```

约束：

- `session_id` 必填；
- `message` 和 `action` 至少有一个非空；
- 前端不得传可信 `user_id`；
- 预约确认必须通过 `action.confirmation_id`，纯文本“确认”不能绕过校验；
- `client_context.timezone` 必须用于相对时间解析。

## 5. Chat Response

```json
{
  "session_id": "s-001",
  "request_id": "r-001",
  "trace_id": "t-001",
  "reply": "我先按大学城南亭附近帮你找房。",
  "phase": "showing_room_results",
  "domain_category": "in_domain_task",
  "cards": [],
  "actions": [],
  "pending_action": null,
  "sources": [],
  "metadata": {
    "procedure": "room_search",
    "recovery_used": false,
    "memory_used": true,
    "handoff_status": "ai_active"
  }
}
```

必须字段：

| 字段 | 说明 |
| --- | --- |
| `session_id` | 会话 ID |
| `request_id` | 本次请求 ID |
| `trace_id` | 可观测链路 ID |
| `reply` | 展示给用户的文本 |
| `phase` | 当前任务阶段 |
| `domain_category` | 领域边界分类 |
| `cards` | 前端渲染卡片 |
| `actions` | 可执行结构化动作 |
| `pending_action` | 当前待确认写操作 |
| `sources` | 知识来源 |
| `metadata` | 调试和运营信息 |

## 6. Card Schema

### Room Card

```json
{
  "type": "room",
  "room_id": 3001,
  "apartment_id": 101,
  "title": "大学城南亭寓 301",
  "apartment_name": "大学城南亭寓",
  "room_number": "301",
  "rent": 1800,
  "district": "番禺区",
  "area_label": "大学城南亭附近",
  "tags": ["近大学城", "可月付", "安静"],
  "description": "距离大学城南亭步行约 12 分钟",
  "thumbnail_url": null,
  "available_for_appointment": true,
  "recommendation_reason": "位置接近大学城，且支持月付。"
}
```

### Confirmation Card

```json
{
  "type": "confirmation",
  "confirmation_id": "c-001",
  "status": "pending",
  "operation": "appointment.create",
  "summary": "预约大学城南亭寓 301，时间 2026-05-06 14:00",
  "expires_at": "2026-05-05T12:30:00+08:00"
}
```

### Memory Candidate Card

```json
{
  "type": "memory_candidate",
  "candidate_id": "mc-001",
  "summary": "记住你偏好大学城附近、安静、可月付的房源",
  "status": "pending",
  "actions": ["memory_accept", "memory_reject"]
}
```

### Handoff Card

```json
{
  "type": "handoff",
  "handoff_id": "h-001",
  "status": "created",
  "reason": "预约工具连续失败",
  "summary": "我已把你的找房目标和失败原因整理给人工客服。"
}
```

## 7. Action Schema

```json
{
  "type": "create_appointment",
  "action_id": "a-001",
  "label": "预约看房",
  "payload": {
    "room_id": 3001,
    "apartment_id": 101
  },
  "enabled": true,
  "expires_at": null
}
```

Action 类型以 [05-frontend-interaction-protocol.md](05-frontend-interaction-protocol.md) 为准。新增 action 必须同时更新本文档、前端渲染层和 eval。

## 8. Pending Action

```json
{
  "type": "appointment.create",
  "confirmation_id": "c-001",
  "status": "pending",
  "created_at": "2026-05-05T12:20:00+08:00",
  "expires_at": "2026-05-05T12:30:00+08:00",
  "payload": {
    "room_id": 3001,
    "apartment_id": 101,
    "appointment_time": "2026-05-06 14:00"
  }
}
```

执行前必须验证：

- `confirmation_id` 匹配当前 session；
- `status` 是 `pending`；
- 未过期；
- payload 中没有缺失关键字段；
- 用户身份有效；
- 对应 tool 的 `requires_confirmation=true`。

## 9. Error Response

```json
{
  "session_id": "s-001",
  "request_id": "r-001",
  "trace_id": "t-001",
  "reply": "预约信息还不完整，我需要先确认具体房源。",
  "phase": "tool_failed",
  "domain_category": "in_domain_task",
  "cards": [],
  "actions": [
    {
      "type": "search_more",
      "label": "重新找房",
      "payload": {}
    }
  ],
  "pending_action": null,
  "sources": [],
  "metadata": {
    "error_code": "MISSING_ROOM_ID",
    "recoverable": true,
    "handoff_status": "ai_active"
  }
}
```

用户能看到的是 `reply` 和可操作按钮；`metadata.error_code` 用于 trace、eval 和前端调试。

## 10. SSE Events

每个事件格式：

```json
{
  "event": "tool_call_started",
  "request_id": "r-001",
  "trace_id": "t-001",
  "timestamp": "2026-05-05T12:20:01+08:00",
  "payload": {
    "tool": "room.search",
    "strategy": "exact_search"
  }
}
```

最后一个事件必须是：

```json
{
  "event": "final",
  "request_id": "r-001",
  "trace_id": "t-001",
  "payload": {
    "response": {}
  }
}
```

SSE 事件名以 [10-trace-eval-and-observability.md](10-trace-eval-and-observability.md) 为准。前端可以展示进度，但不能依赖中间事件完成业务写操作。

## 11. 兼容旧 H5 的边界

旧 `lease/web-app` 的 `/app/ai/chat` 可以作为代理入口，但 AptGuide 2.0 的真实契约是本文档。

兼容策略：

- `lease` 代理层负责把旧 `ChatRequest.sessionId` 转成 `session_id`；
- 旧 `ChatResponse.pendingConfirmation` 映射为 `pending_action`；
- 旧 H5 暂时无法渲染的新字段可以忽略，但不能删除；
- 新独立前端优先实现完整 card/action/trace 协议。

## 12. Phase 0 验收

Phase 0 完成时必须能回答：

- `/api/chat` 的 request/response 是否有 Pydantic schema；
- 前端能否仅凭 response 渲染所有 cards/actions；
- `confirmation_id` 是否只能通过 action 触发；
- 所有 response 是否都有 `request_id` 和 `trace_id`；
- 字段命名转换是否集中在 adapter / schema alias 层。
