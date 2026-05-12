# 15 · Tool Registry And Error Codes

> 相关文档：[工具与集成契约](04-tool-and-integration-contract.md)、[API Schema](14-api-and-schema-contract.md)、[运行时设计](08-procedure-driven-agent-runtime.md)、[Trace/Eval](10-trace-eval-and-observability.md)、[实施任务](12-implementation-task-plan.md)。

## 1. 目标

本文档把工具注册表从概念变成实现契约。Agent 只能调用本文档登记过的工具；新增工具必须更新本文档、schema、adapter、trace 和 eval。

## 2. ToolDefinition

```json
{
  "name": "room.search",
  "backend": "lease",
  "permission": "public",
  "requires_user": false,
  "requires_confirmation": false,
  "timeout_seconds": 5,
  "retry": {
    "max_attempts": 1,
    "retry_on": ["TIMEOUT", "NETWORK_ERROR"]
  },
  "input_schema": "RoomSearchInput",
  "output_schema": "RoomSearchOutput",
  "pii_policy": "no_pii"
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `name` | 工具唯一名 |
| `backend` | `lease`、`vector`、`memory`、`internal` |
| `permission` | `public`、`user`、`internal` |
| `requires_user` | 是否需要登录用户 |
| `requires_confirmation` | 是否是写操作确认工具 |
| `timeout_seconds` | 单次调用超时 |
| `retry` | 重试策略 |
| `input_schema` | Pydantic schema 名称 |
| `output_schema` | Pydantic schema 名称 |
| `pii_policy` | PII 处理策略 |

## 3. 工具清单

| Tool | Backend | 权限 | 用户 | 确认 | MVP | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `lease.health` | lease | internal | 否 | 否 | 是 | 检查 lease 工具后端 |
| `area.normalize` | vector/lease | public | 否 | 否 | 是 | 地标、商圈、学校归一化 |
| `room.search` | lease | public | 否 | 否 | 是 | 房源条件检索 |
| `room.detail` | lease | public | 否 | 否 | 是 | 房源详情 |
| `kb.search` | vector | public | 否 | 否 | 是 | 租房规则知识检索 |
| `appointment.create` | lease | user | 是 | 是 | 是 | 创建预约 |
| `appointment.list_mine` | lease | user | 是 | 否 | 是 | 查询本人预约 |
| `lease.list_mine` | lease | user | 是 | 否 | 是 | 查询本人租约 |
| `recommendation.store` | memory | internal | 否 | 否 | 是 | 保存最近推荐房源 |
| `memory.session_update` | memory | internal | 否 | 否 | 是 | 更新短期会话状态 |
| `memory.profile_get` | memory | user | 是 | 否 | 是 | 读取长期偏好 |
| `memory.profile_update` | memory | user | 是 | 是 | 是 | 写长期偏好 |
| `memory.profile_delete` | memory | user | 是 | 是 | 是 | 删除长期偏好 |
| `handoff.create` | lease/internal | user | 是 | 否 | 是 | 创建人工接管请求 |
| `trace.record` | internal | internal | 否 | 否 | 是 | 记录 trace |

## 4. Room Search

### Input

```json
{
  "city_id": null,
  "district_id": null,
  "area_text": "大学城南亭",
  "normalized_area": {
    "district": "番禺区",
    "landmark": "大学城南亭"
  },
  "min_rent": null,
  "max_rent": 1800,
  "payment_type": "月付",
  "lease_term_months": null,
  "tags": ["安静"],
  "room_ids": null,
  "limit": 5,
  "strategy": "exact_search"
}
```

### Adapter Mapping

| AptGuide 字段 | lease DTO 字段 | 说明 |
| --- | --- | --- |
| `city_id` | `cityId` | 城市 ID |
| `district_id` | `districtId` | 区域 ID |
| `min_rent` | `minRent` | 最低租金 |
| `max_rent` | `maxRent` | 最高租金 |
| `payment_type` | `paymentType` | 付款方式 |
| `lease_term_months` | `leaseTermMonths` | 租期 |
| `tags` | `tags` | 标签 |
| `room_ids` | `roomIds` | 指定房源 |
| `limit` | `limit` | 返回数量 |

`area_text` 和 `normalized_area` 不直接传给当前 Java DTO，除非后端补充字段。它们用于向量召回、日志和推荐解释。

### Output

```json
{
  "rooms": [
    {
      "room_id": 3001,
      "apartment_id": 101,
      "apartment_name": "大学城南亭寓",
      "room_number": "301",
      "rent": 1800,
      "payment_types": ["月付"],
      "lease_terms": [6, 12],
      "tags": ["近大学城", "安静"],
      "thumbnail_url": null,
      "is_appointable": true
    }
  ],
  "total": 1,
  "strategy": "exact_search"
}
```

## 5. Appointment Create

### Input

```json
{
  "user_id": "u-001",
  "room_id": 3001,
  "apartment_id": 101,
  "appointment_time": "2026-05-06 14:00",
  "remark": "用户从 AptGuide 2.0 发起预约",
  "confirmation_id": "c-001"
}
```

### 必须校验

- `user_id` 来自后端认证上下文；
- `confirmation_id` 属于当前 session；
- `room_id` 和 `apartment_id` 均存在；
- `appointment_time` 是未来时间；
- 房源仍可预约；
- pending action 未过期且未被消费。

### Adapter Mapping

| AptGuide 字段 | lease DTO 字段 |
| --- | --- |
| `apartment_id` | `apartmentId` |
| `room_id` | `roomId` |
| `appointment_time` | `appointmentTime` |
| `remark` | `remark` |

当前 Java `ViewAppointment` 如果只保存 `apartmentId`，产品回复不能承诺“已预约到 room 级别”，除非后端补齐字段。

## 6. Memory Tools

长期画像写入也视为高风险用户体验操作。MVP 中 `memory.profile_update` 和 `memory.profile_delete` 都需要结构化 action，不能只凭模型判断自动写入。

```json
{
  "candidate_id": "mc-001",
  "user_id": "u-001",
  "operation": "profile_update",
  "key": "preferred_areas",
  "value": "大学城",
  "source": "user_confirmed"
}
```

## 7. Error Envelope

所有工具失败返回统一 envelope：

```json
{
  "ok": false,
  "tool": "appointment.create",
  "data": null,
  "error": {
    "code": "MISSING_ROOM_ID",
    "message": "预约缺少 room_id",
    "recoverable": true,
    "user_message_type": "collect_missing_room"
  },
  "metadata": {
    "backend": "lease",
    "latency_ms": 120,
    "trace_id": "t-001"
  }
}
```

## 8. 标准错误码

| Error Code | Recoverable | 触发场景 | 用户策略 |
| --- | --- | --- | --- |
| `TOOL_TIMEOUT` | 是 | 工具超时 | 解释失败，可重试 |
| `NETWORK_ERROR` | 是 | 后端不可达 | 提示稍后重试或转人工 |
| `LEASE_UNAVAILABLE` | 是 | lease 健康检查失败 | 停止写操作，提示后端不可用 |
| `VALIDATION_ERROR` | 是 | 输入 schema 不合法 | 追问缺失字段 |
| `MISSING_USER_ID` | 是 | 需要登录但无用户 | 引导登录 |
| `MISSING_ROOM_ID` | 是 | 预约缺少房源 | 重新选择房源 |
| `MISSING_APARTMENT_ID` | 是 | 预约缺少公寓 | 重新解析房源 |
| `INVALID_APPOINTMENT_TIME` | 是 | 时间格式/时间点不合法 | 追问时间 |
| `ROOM_NOT_FOUND` | 是 | 房源不存在或下架 | 重新推荐 |
| `ROOM_NOT_APPOINTABLE` | 是 | 房源不可预约 | 推荐替代 |
| `CONFIRMATION_REQUIRED` | 是 | 写操作未确认 | 创建确认卡 |
| `CONFIRMATION_STALE` | 是 | 旧确认被点击 | 拒绝并说明已失效 |
| `PERMISSION_DENIED` | 否 | 越权访问个人数据 | 拒绝并说明隐私边界 |
| `KB_LOW_CONFIDENCE` | 是 | 知识库低置信度 | 保守回答并建议门店确认 |
| `UNKNOWN_TOOL_ERROR` | 是 | 未分类工具失败 | 解释失败，可转人工 |

## 9. Trace 要求

每次工具调用必须记录：

```text
tool_name
backend
input_schema_version
permission
requires_user
requires_confirmation
latency_ms
ok
error_code
result_count
```

不得记录电话、身份证、合同编号等敏感明文。

## 10. Phase 0 验收

实现前必须完成：

- 每个 MVP 工具有 Pydantic input/output schema；
- 每个工具有 timeout 和 error mapping；
- Java DTO 字段映射集中在 `LeaseToolAdapter`；
- eval 覆盖 `MISSING_ROOM_ID`、`CONFIRMATION_STALE`、`TOOL_TIMEOUT`、`PERMISSION_DENIED`；
- 写工具 `requires_confirmation=true`，且 runtime 强制校验。
