# 16 · Memory State Schema

> 相关文档：[记忆架构](07-memory-and-context-architecture.md)、[API Schema](14-api-and-schema-contract.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[运行时设计](08-procedure-driven-agent-runtime.md)、[Trace/Eval](10-trace-eval-and-observability.md)。

## 1. 目标

本文档固定 AptGuide 2.0 的会话状态、任务状态、pending action、长期偏好和 audit log schema。实现时不能只把状态放在聊天摘要里。

## 2. 存储分层

| 数据 | MVP 存储 | 生命周期 | 说明 |
| --- | --- | --- | --- |
| `recent_messages` | Redis | session TTL | 最近原文 |
| `rolling_summary` | Redis | session TTL | 长对话摘要 |
| `active_task_state` | Redis | session TTL | 当前任务结构化状态 |
| `pending_action` | Redis | 5-10 分钟 | 写操作确认状态 |
| `last_recommendations` | Redis | session TTL | 最近推荐房源 |
| `long_term_profile` | SQLite/Postgres/MySQL | 长期 | 用户长期偏好 |
| `memory_candidates` | SQLite/Postgres/MySQL | 7-30 天 | 待确认记忆 |
| `memory_audit_log` | SQLite/Postgres/MySQL | 长期 | 记忆变更审计 |

## 3. Redis Key

```text
aptguide2:session:{session_id}:frame
aptguide2:session:{session_id}:messages
aptguide2:session:{session_id}:summary
aptguide2:session:{session_id}:task_state
aptguide2:session:{session_id}:pending_action
aptguide2:session:{session_id}:recommendations
```

TTL 建议：

| Key | TTL |
| --- | --- |
| session frame | 24 小时 |
| recent messages | 24 小时 |
| rolling summary | 24 小时 |
| active task state | 24 小时 |
| pending action | 5-10 分钟 |
| recommendations | 24 小时 |

## 4. ConversationFrame

```json
{
  "session_id": "s-001",
  "request_id": "r-001",
  "trace_id": "t-001",
  "user_id": "u-001",
  "message": "预算我都接受",
  "action": null,
  "phase": "showing_room_results",
  "domain_category": "in_domain_task",
  "active_goal": {
    "type": "room_search",
    "description": "找大学城南亭附近房源"
  },
  "task_slots": {
    "area_text": "大学城南亭",
    "normalized_district": "番禺区",
    "max_rent": null,
    "payment_type": null,
    "preferences": ["安静"]
  },
  "recent_messages": [],
  "rolling_summary": "用户正在找大学城南亭附近安静房源，预算已清除。",
  "long_term_profile": {},
  "memory_candidates": [],
  "pending_action": null,
  "last_recommendations": [],
  "tool_observations": [],
  "recovery_decision": null,
  "handoff": {
    "status": "ai_active"
  }
}
```

## 5. ActiveTaskState

```json
{
  "task_type": "room_search",
  "phase": "showing_room_results",
  "slots": {
    "area_text": "大学城南亭",
    "normalized_area": {
      "district": "番禺区",
      "landmark": "大学城南亭",
      "confidence": 0.86
    },
    "min_rent": null,
    "max_rent": null,
    "payment_type": null,
    "lease_term_months": null,
    "preferences": ["安静", "可月付"]
  },
  "slot_history": [
    {
      "key": "max_rent",
      "old_value": 1500,
      "new_value": null,
      "reason": "用户说预算我都接受"
    }
  ],
  "last_recommendations": [
    {
      "room_id": 3001,
      "apartment_id": 101,
      "rank": 1
    }
  ],
  "pending_action": null
}
```

规则：

- 用户明确清除预算时，`max_rent` 必须设为 `null`，不能保留旧值；
- 房源 ID、apartment ID、appointment time、confirmation ID 必须在结构化字段中；
- `rolling_summary` 只能辅助生成回复，不能作为写操作依据。

## 6. PendingAction

```json
{
  "type": "appointment.create",
  "session_id": "s-001",
  "user_id": "u-001",
  "confirmation_id": "c-001",
  "status": "pending",
  "payload": {
    "room_id": 3001,
    "apartment_id": 101,
    "appointment_time": "2026-05-06 14:00"
  },
  "created_at": "2026-05-05T12:20:00+08:00",
  "expires_at": "2026-05-05T12:30:00+08:00",
  "consumed_at": null
}
```

状态：

```text
pending
confirmed
cancelled
expired
stale
failed
executed
```

任何执行写工具前，必须原子更新 pending action 状态，防止重复点击。

## 7. LongTermProfile

```json
{
  "user_id": "u-001",
  "enabled": true,
  "preferred_areas": [
    {
      "memory_id": "m-area-001",
      "value": "大学城",
      "confidence": 0.92,
      "source": "user_confirmed",
      "scope": "recurring_preference",
      "created_at": "2026-05-05T12:00:00+08:00",
      "updated_at": "2026-05-05T12:00:00+08:00"
    }
  ],
  "budget_range": {
    "memory_id": "m-budget-001",
    "min": null,
    "max": 2200,
    "confidence": 0.8,
    "source": "user_confirmed",
    "scope": "recurring_preference"
  },
  "preferences": [
    {
      "memory_id": "m-pref-001",
      "value": "安静",
      "confidence": 0.9,
      "source": "user_confirmed"
    }
  ],
  "negative_preferences": []
}
```

禁止保存：

- 身份证；
- 电话；
- 合同编号；
- 完整住址；
- 支付信息；
- 他人预约/租约信息。

## 8. MemoryCandidate

```json
{
  "candidate_id": "mc-001",
  "user_id": "u-001",
  "type": "preference",
  "key": "preferred_areas",
  "value": "大学城",
  "reason": "用户明确说以后主要想住大学城附近",
  "confidence": 0.91,
  "sensitivity": "low",
  "requires_confirmation": true,
  "status": "pending",
  "created_at": "2026-05-05T12:00:00+08:00",
  "expires_at": "2026-06-04T12:00:00+08:00"
}
```

MVP 规则：

- 所有长期画像新增都要求用户确认；
- 临时需求不能自动写长期画像；
- 用户拒绝后不得在同一会话重复追问；
- 删除长期偏好必须写 audit log。

## 9. MemoryAuditLog

```json
{
  "audit_id": "ma-001",
  "user_id": "u-001",
  "memory_id": "m-area-001",
  "operation": "create",
  "old_value": null,
  "new_value": "大学城",
  "source": "memory_candidate:mc-001",
  "request_id": "r-001",
  "trace_id": "t-001",
  "created_at": "2026-05-05T12:02:00+08:00"
}
```

## 10. 压缩验收

上下文压缩后必须保留：

- 当前任务类型；
- 最新 slot 值；
- slot 清除记录；
- `last_recommendations`；
- `pending_action`；
- `confirmation_id`；
- 工具失败次数和错误码；
- handoff 状态。

Eval 必须覆盖：

```text
100 轮对话后 pending_action 不丢
预算清除后 max_rent 不复活
旧 confirmation 被拒绝
新会话只加载用户确认过的长期偏好
敏感信息不进入 long_term_profile
```
