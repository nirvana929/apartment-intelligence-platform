# 05 · Java 工具接口契约

本文件定义 AptGuide 与 `lease`（Spring Boot）之间的 HTTP 接口契约。所有接口都是 **服务间内部接口**，不直接对外暴露。

## 1. 通用约定

### 1.1 鉴权

每个请求必须携带：

| Header | 含义 | 是否必填 |
|--------|------|----------|
| `X-Internal-Token` | AptGuide ↔ lease 共享密钥 | ✅ |
| `X-User-Id` | 用户 ID（lease 在 /app/ai/chat 入口校验 JWT 后注入） | ✅（除非接口为公开数据）|
| `X-Request-Id` | 链路追踪 | ✅ |

**AptGuide 永远不接受、不解析、不伪造客户端的 userId。** 所有写操作和用户级查询均由 Java 按 `X-User-Id` 过滤后返回。

### 1.2 通用响应格式

```json
{
  "code": 0,
  "message": "ok",
  "data": { ... },
  "request_id": "req-uuid"
}
```

错误：

```json
{
  "code": 40001,
  "message": "appointment time conflict",
  "data": null,
  "request_id": "req-uuid"
}
```

| code | 含义 |
|------|------|
| 0 | 成功 |
| 4xxxx | 业务校验失败 |
| 401xx | 鉴权失败 |
| 403xx | 权限不足 |
| 5xxxx | 内部错误 |

### 1.3 路径前缀

所有 AI 工具接口统一前缀：`/internal/ai/tools/`。这一前缀只允许内网访问。

### 1.4 超时

- AptGuide 默认 10s 超时；
- 单次失败重试 1 次（仅对 5xx / 网络错误）；
- 业务失败（4xxxx）不重试。

## 2. 房源 / 公寓接口

### 2.1 `POST /internal/ai/tools/room/search`

精确条件 + 候选 ID 过滤。Milvus 召回结果通过 `room_ids` 传入。

**Request**

```json
{
  "city_id": 4401,
  "district_id": 1001,
  "max_rent": 3000,
  "min_rent": null,
  "payment_type": "MONTHLY",
  "lease_term_months": null,
  "tags": ["独卫", "朝南"],
  "room_ids": [3001, 3002, 3003],
  "limit": 5
}
```

**Response.data**

```json
{
  "rooms": [
    {
      "room_id": 3001,
      "room_number": "302",
      "apartment_id": 2001,
      "apartment_name": "天河公寓",
      "rent": 2800,
      "payment_types": ["MONTHLY", "QUARTERLY"],
      "lease_terms": [3, 6, 12],
      "area": 25,
      "layout": "1室1卫",
      "tags": ["独卫", "朝南"],
      "thumbnail_url": null,
      "is_appointable": true
    }
  ],
  "total": 1
}
```

**约束**

- 服务端必须做"上架 / 在售 / 价格匹配"校验，不允许返回不可用房源。
- `tags` 是模糊提示，服务端按"包含任一"匹配，不做严格相等。

### 2.2 `GET /internal/ai/tools/room/{room_id}`

返回单个房源的详情（同 2.1 中 `rooms[*]` 字段，附配套、图片列表）。

### 2.3 `GET /internal/ai/tools/apartment/{apartment_id}`

返回公寓详情：名称、地址、配套、可租房间列表（仅基本字段）。

## 3. 看房预约接口

### 3.1 `POST /internal/ai/tools/appointment/create`

**Request**

```json
{
  "apartment_id": 2001,
  "room_id": 3001,
  "appointment_time": "2026-05-02 15:00",
  "remark": "AptGuide 预约"
}
```

`X-User-Id` 由 header 决定，body 不允许传 `user_id`。

**Response.data**

```json
{
  "appointment_id": 90001,
  "appointment_no": "A20260502302",
  "status": "CONFIRMED",
  "appointment_time": "2026-05-02 15:00",
  "apartment_name": "天河公寓",
  "room_number": "302"
}
```

**业务错误**

| code | 含义 |
|------|------|
| 40010 | 房源不可预约（已下架 / 已签约） |
| 40011 | 时段冲突（用户已存在同时段预约） |
| 40012 | 时段不在门店开放时间内 |

### 3.2 `GET /internal/ai/tools/appointment/list-mine`

仅返回当前用户的预约。

**Response.data**

```json
{
  "appointments": [
    {
      "appointment_id": 90001,
      "appointment_no": "A20260502302",
      "status": "CONFIRMED",
      "appointment_time": "2026-05-02 15:00",
      "apartment_name": "天河公寓",
      "room_number": "302"
    }
  ]
}
```

### 3.3 `POST /internal/ai/tools/appointment/cancel`（第二版）

```json
{ "appointment_id": 90001 }
```

## 4. 租约接口

### 4.1 `GET /internal/ai/tools/lease/list-mine`

仅返回当前用户的租约（含历史与在租）。

**Response.data**

```json
{
  "leases": [
    {
      "lease_id": 70001,
      "status": "ACTIVE",
      "apartment_name": "科韵公寓",
      "room_number": "506",
      "start_date": "2025-08-01",
      "end_date": "2026-07-31",
      "rent": 2950,
      "payment_type": "MONTHLY",
      "renewal_window_days": 30
    }
  ]
}
```

**敏感字段**

- 不返回合同 PDF、押金账户、银行卡等。
- 不返回手机号、身份证。

## 5. 浏览历史接口（第二版用于个性化）

### 5.1 `GET /internal/ai/tools/browse-history/list-mine`

```json
{
  "items": [
    {"room_id": 3001, "viewed_at": "2026-04-30 12:30"},
    {"room_id": 3002, "viewed_at": "2026-04-29 19:10"}
  ]
}
```

仅返回 `room_id` 与时间戳，便于 AptGuide 用来做相似推荐时再调用 2.1 取详情。

## 6. 健康检查

### 6.1 `GET /internal/ai/health`

```json
{ "code": 0, "data": {"status": "ok"} }
```

AptGuide `/health/deps` 会调用此接口确认 lease 可达。

## 7. 字段命名约定

- 统一蛇形命名（snake_case）。
- 时间统一 `YYYY-MM-DD HH:mm`，时区为本地时区。
- 货币（租金）统一为元（CNY），整数。
- 枚举值大写，例如 `MONTHLY`、`QUARTERLY`、`ACTIVE`。

## 8. 版本与兼容

- 接口加字段不视为破坏性变更；删除 / 重命名字段需要协商。
- AptGuide 调用时使用 Pydantic 模型解析；新增字段不应导致解析失败。
- 计划在路径中加版本号（`/internal/ai/v1/tools/...`）后再扩展。
