# 公寓智能平台系统架构设计

> 文档版本：1.0
> 创建日期：2026-05-03
> 作者：Claude Code

## 1. 概述

### 1.1 背景

公寓智能平台是一个集成了 AI 能力的公寓租赁管理系统，包含以下子系统：

- **lease**：核心业务后端（Spring Boot）
- **rentHouseH5**：租客端前端（Vue）
- **rentHouseAdmin**：管理端前端（Vue）
- **AptGuide**：AI 找房助手（Python FastAPI + LangGraph）
- **AptInsight**：运营分析助手（Python FastAPI + LangGraph）

### 1.2 目标

1. 将 AI 能力集成到现有业务系统中
2. 提供统一的 AI 助手入口
3. 保证系统安全、可扩展、高性能
4. 支持多 AI 服务并行扩展

### 1.3 设计原则

- **职责分离**：业务逻辑在 lease，AI 能力在独立服务
- **安全第一**：JWT 鉴权 + 内部 Token + 用户隔离
- **渐进集成**：先独立运行，再逐步集成
- **可扩展性**：支持新增 AI 服务，不影响现有系统

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    公寓智能平台架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    用户层                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │ rentHouseH5 │  │rentHouseAdmin│  │  其他渠道    │    │   │
│  │  │  (租客端)    │  │  (管理端)    │  │             │    │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │   │
│  └─────────┼────────────────┼────────────────┼─────────────┘   │
│            │                │                │                  │
│  ┌─────────▼────────────────▼────────────────▼─────────────┐   │
│  │                    网关层                                │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  lease 后端 (Spring Boot)                       │   │   │
│  │  │  - JWT 鉴权                                     │   │   │
│  │  │  - 路由分发                                     │   │   │
│  │  │  - 统一响应                                     │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                    AI 能力层                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │  AptGuide   │  │  AptInsight │  │   其他AI     │    │   │
│  │  │  (找房助手)  │  │  (运营分析)  │  │             │    │   │
│  │  │  FastAPI    │  │  FastAPI    │  │             │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                    数据层                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │    MySQL    │  │    Redis    │  │    Milvus   │    │   │
│  │  │  (业务数据)  │  │  (缓存)     │  │  (向量)     │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 分层职责

| 层次 | 职责 | 技术栈 |
|------|------|--------|
| 用户层 | 用户界面、交互 | Vue |
| 网关层 | 统一入口、鉴权、路由 | Spring Boot |
| AI 能力层 | 智能处理、自然语言理解 | Python + LangGraph |
| 数据层 | 数据存储、缓存 | MySQL + Redis + Milvus |

### 2.3 接口分层

```
lease 后端接口
├── /app/*              # 面向前端（需要 JWT）
│   ├── /app/ai/chat    # AI 对话入口
│   └── ...
│
├── /admin/*            # 面向管理端（需要 JWT + 权限）
│   └── ...
│
└── /internal/*         # 内部接口（需要 Token）
    └── /ai/tools/*     # AI 工具接口
        ├── /room/search
        ├── /appointment/create
        ├── /appointment/list-mine
        ├── /lease/list-mine
        └── /health
```

## 3. 阶段设计

### 3.1 阶段 1：AI 服务独立运行

**目标**：验证 AI 能力，不依赖 lease 后端

**当前状态**（已完成）：
- AptGuide 独立运行，使用 MockToolClient
- AptInsight 独立运行，直接查数据库
- 有独立的 Web UI

**验证内容**：
- 意图识别
- 槽位抽取
- 知识库检索
- 房源推荐
- 预约确认

**交付物**：
- AptGuide：48 个测试通过，可独立运行
- AptInsight：可独立运行，能查询数据

### 3.2 阶段 2：对接 lease 内部接口

**目标**：AI 服务通过 lease 内部接口获取业务数据

**接口设计**：
- `/internal/ai/tools/room/search` - 搜索房源
- `/internal/ai/tools/appointment/create` - 创建预约
- `/internal/ai/tools/appointment/list-mine` - 查询预约
- `/internal/ai/tools/lease/list-mine` - 查询租约
- `/internal/ai/tools/health` - 健康检查

**鉴权设计**：
- `X-Internal-Token`：服务间信任
- `X-User-Id`：用户身份透传
- `X-Request-Id`：链路追踪

**数据流**：
```
AptGuide
    │
    │ POST /internal/ai/tools/room/search
    │ Headers: X-Internal-Token, X-User-Id
    │
    ▼
lease 后端
    │
    │ 验证 Token
    │ 调用 RoomInfoService
    │
    ▼
MySQL
    │
    │ 返回数据
    │
    ▼
lease 后端
    │
    │ 返回统一格式
    │
    ▼
AptGuide
    │
    │ 生成回复
    │
    ▼
用户
```

### 3.3 阶段 3：集成到前端

**目标**：前端集成 AI 助手，用户可正常使用

**前端集成**：
- 悬浮窗按钮
- 侧边栏对话界面
- 调用 `/app/ai/chat` 接口

**lease 入口接口**：
- `POST /app/ai/chat`
- JWT 鉴权
- 调用 AptGuide
- 返回统一格式

**完整链路**：
```
用户（前端）
    │
    │ ① 登录，拿 JWT
    │
    ▼
lease 后端
    │
    │ ② POST /app/ai/chat（带 JWT）
    │
    │ ③ 验证 JWT，提取 userId
    │
    │ ④ 调用 AptGuide（带 Token + UserId）
    │
    ▼
AptGuide
    │
    │ ⑤ 处理用户消息
    │
    │ ⑥ 需要业务数据时，调用 lease 内部接口
    │    POST /internal/ai/tools/room/search
    │
    ▼
lease 后端
    │
    │ ⑦ 返回业务数据
    │
    ▼
AptGuide
    │
    │ ⑧ 生成回复
    │
    ▼
lease 后端
    │
    │ ⑨ 返回给前端
    │
    ▼
用户看到结果
```

## 4. 接口详细设计

### 4.1 AI 工具接口（lease 内部）

#### 4.1.1 搜索房源

```
POST /internal/ai/tools/room/search

请求头：
X-Internal-Token: <shared-secret>
X-User-Id: <user-id>
X-Request-Id: <request-id>

请求体：
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

响应体：
{
  "code": 0,
  "message": "ok",
  "data": {
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
}
```

#### 4.1.2 创建预约

```
POST /internal/ai/tools/appointment/create

请求头：
X-Internal-Token: <shared-secret>
X-User-Id: <user-id>
X-Request-Id: <request-id>

请求体：
{
  "apartment_id": 2001,
  "room_id": 3001,
  "appointment_time": "2026-05-02 15:00",
  "remark": "AptGuide 预约"
}

响应体：
{
  "code": 0,
  "message": "ok",
  "data": {
    "appointment_id": 90001,
    "appointment_no": "A20260502302",
    "status": "CONFIRMED",
    "appointment_time": "2026-05-02 15:00",
    "apartment_name": "天河公寓",
    "room_number": "302"
  }
}
```

#### 4.1.3 查询预约列表

```
GET /internal/ai/tools/appointment/list-mine

请求头：
X-Internal-Token: <shared-secret>
X-User-Id: <user-id>
X-Request-Id: <request-id>

响应体：
{
  "code": 0,
  "message": "ok",
  "data": {
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
}
```

#### 4.1.4 查询租约列表

```
GET /internal/ai/tools/lease/list-mine

请求头：
X-Internal-Token: <shared-secret>
X-User-Id: <user-id>
X-Request-Id: <request-id>

响应体：
{
  "code": 0,
  "message": "ok",
  "data": {
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
}
```

#### 4.1.5 健康检查

```
GET /internal/ai/tools/health

请求头：
X-Internal-Token: <shared-secret>
X-Request-Id: <request-id>

响应体：
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "ok"
  }
}
```

### 4.2 AI 入口接口（前端调用）

```
POST /app/ai/chat

请求头：
Authorization: Bearer <JWT>
Content-Type: application/json

请求体：
{
  "message": "帮我找天河区3000以内的房子",
  "sessionId": "session-123"
}

响应体：
{
  "code": 0,
  "message": "ok",
  "data": {
    "reply": "好的，为您推荐以下房源...",
    "cards": [
      {
        "type": "room",
        "room_id": 3001,
        "title": "天河公寓 302",
        "rent": 2800,
        "district": "天河区",
        "tags": ["独卫", "朝南"],
        "description": "25㎡，1室1卫",
        "thumbnail_url": null
      }
    ],
    "actions": [
      {
        "type": "create_appointment",
        "room_id": 3001
      }
    ],
    "pending_confirmation": null,
    "sources": [],
    "sessionId": "session-123"
  }
}
```

## 5. 鉴权设计

### 5.1 鉴权流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      鉴权流程                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 用户登录（前端 → lease）                                    │
│     ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│     │ 前端    │ →  │ lease   │ →  │ 返回JWT │                 │
│     └─────────┘    └─────────┘    └─────────┘                 │
│                                                                 │
│  2. 前端调用 AI（前端 → lease → AI 服务）                       │
│     ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│     │ 前端    │ →  │ lease   │ →  │ AI 服务 │                 │
│     │ (JWT)   │    │ 验证JWT │    │ (Token) │                 │
│     └─────────┘    └─────────┘    └─────────┘                 │
│                                                                 │
│  3. AI 服务调用 lease（AI 服务 → lease）                        │
│     ┌─────────┐    ┌─────────┐                                │
│     │ AI 服务 │ →  │ lease   │                                │
│     │(Token+  │    │ 验证Token│                                │
│     │UserId) │    │         │                                │
│     └─────────┘    └─────────┘                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 鉴权方式

| 接口类型 | 鉴权方式 | 说明 |
|---------|---------|------|
| `/app/*` | JWT | 前端用户登录后获得 |
| `/admin/*` | JWT + 权限 | 管理员登录后获得 |
| `/internal/*` | Token + UserId | 服务间调用，不对外暴露 |

### 5.3 安全规则

1. **用户隔离**：所有用户数据按 userId 隔离
2. **Token 验证**：内部接口必须验证 X-Internal-Token
3. **身份透传**：lease 从 JWT 提取 userId，通过 X-User-Id 传给 AI 服务
4. **敏感数据**：AI 服务不接触用户密码、手机号等敏感信息

## 6. 数据流设计

### 6.1 找房流程

```
用户输入："帮我找天河区3000以内的房子"
    │
    ▼
AptGuide（意图识别）
    │
    │ 意图：room_search
    │ 槽位：district=天河区, max_rent=3000
    │
    ▼
AptGuide（槽位检查）
    │
    │ 槽位完整，调用 lease 接口
    │
    ▼
lease（/internal/ai/tools/room/search）
    │
    │ 查询 MySQL
    │
    ▼
MySQL
    │
    │ 返回房源列表
    │
    ▼
lease
    │
    │ 返回统一格式
    │
    ▼
AptGuide（生成回复）
    │
    │ 生成房源卡片 + 推荐理由
    │
    ▼
用户看到结果
```

### 6.2 预约流程

```
用户输入："预约第一个房源明天下午3点看房"
    │
    ▼
AptGuide（意图识别）
    │
    │ 意图：appointment_create
    │ 槽位：room_id=3001, appointment_time=明天15:00
    │
    ▼
AptGuide（槽位检查）
    │
    │ 槽位完整，生成确认摘要
    │
    ▼
用户确认
    │
    │ 用户回复："确认"
    │
    ▼
AptGuide（调用 lease 接口）
    │
    │ POST /internal/ai/tools/appointment/create
    │
    ▼
lease
    │
    │ 创建预约记录
    │
    ▼
MySQL
    │
    │ 返回预约结果
    │
    ▼
lease
    │
    │ 返回统一格式
    │
    ▼
AptGuide（生成回复）
    │
    │ 生成预约成功卡片
    │
    ▼
用户看到结果
```

## 7. 并行执行策略

### 7.1 按子系统并行

```
主 Agent（规划）
    │
    ├── 子 Agent 1：lease 后端
    │   ├── 实现 /internal/ai/tools/* 接口
    │   ├── 实现 /app/ai/chat 入口
    │   └── 测试接口
    │
    ├── 子 Agent 2：AptGuide
    │   ├── 更新 LeaseToolClient
    │   ├── 对接新接口
    │   └── 测试完整流程
    │
    ├── 子 Agent 3：AptInsight
    │   ├── 实现 LeaseAnalyticsClient
    │   ├── 对接新接口
    │   └── 测试完整流程
    │
    └── 子 Agent 4：前端
        ├── 实现 AI 助手组件
        ├── 对接 /app/ai/chat
        └── 测试完整流程
```

### 7.2 任务依赖关系

```
阶段 1：AI 服务独立运行（已完成）
    │
    ▼
阶段 2：对接 lease 内部接口
    │
    ├── lease 实现内部接口（无依赖）
    │
    ├── AptGuide 更新客户端（依赖 lease 接口定义）
    │
    └── AptInsight 更新客户端（依赖 lease 接口定义）
    │
    ▼
阶段 3：集成到前端
    │
    ├── lease 实现入口接口（依赖阶段 2）
    │
    ├── 前端实现 AI 助手组件（依赖 lease 接口定义）
    │
    └── 联调测试（依赖所有子系统）
```

## 8. 验收标准

### 8.1 阶段 2 验收

- [ ] lease 内部接口可正常调用
- [ ] Token 鉴权正常工作
- [ ] AptGuide 能通过接口获取业务数据
- [ ] AptInsight 能通过接口获取统计数据
- [ ] 所有接口有单元测试

### 8.2 阶段 3 验收

- [ ] 前端 AI 助手组件正常工作
- [ ] 用户可通过 AI 助手找房
- [ ] 用户可通过 AI 助手预约看房
- [ ] 用户可通过 AI 助手查询租约
- [ ] 完整链路有 e2e 测试

## 9. 风险与缓解

### 9.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 接口不兼容 | 数据流中断 | 提前定义接口契约，使用 Pydantic 校验 |
| 性能问题 | 响应慢 | 缓存热点数据，异步处理非关键路径 |
| 安全漏洞 | 数据泄露 | 严格鉴权，敏感数据脱敏 |

### 9.2 进度风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 子系统进度不一致 | 联调延迟 | 并行开发，提前定义接口 |
| 需求变更 | 返工 | 渐进式集成，每阶段可独立验收 |

## 10. 附录

### 10.1 参考文档

- `AptGuide文档/08-跨项目集成与两阶段实施.md`
- `AptInsight文档/10-系统集成实施文档.md`
- `AptGuide文档/05-Java工具接口契约.md`

### 10.2 术语表

| 术语 | 说明 |
|------|------|
| JWT | JSON Web Token，用户登录凭证 |
| X-Internal-Token | 服务间调用的信任凭证 |
| X-User-Id | 用户身份标识，由 lease 透传 |
| X-Request-Id | 请求链路追踪标识 |
