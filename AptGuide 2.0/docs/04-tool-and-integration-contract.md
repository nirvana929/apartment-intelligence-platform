# 04 · Tool And Integration Contract

> 相关文档：[Agent 架构](02-agent-framework-architecture.md)、[API Schema](14-api-and-schema-contract.md)、[工具注册与错误码](15-tool-registry-and-error-codes.md)、[前端交互协议](05-frontend-interaction-protocol.md)、[运行时设计](08-procedure-driven-agent-runtime.md)、[Trace/Eval](10-trace-eval-and-observability.md)、[实施任务](12-implementation-task-plan.md)。

## 1. 集成目标

`AptGuide 2.0` 应当作为独立 Agent 应用运行，但业务工具直接调用现有项目真实接口。

因此工具层不提供 mock backend。第一版工具后端就是现有 `lease/web-app`、Milvus 和知识库服务：

```text
lease backend  -> 调用现有租赁系统真实接口
vector backend -> 调用真实向量检索和知识库
memory backend -> Redis / 本地开发内存状态
```

开发、联调、演示和验收都直接面向真实依赖。测试只允许使用真实服务的测试环境、种子数据、契约样例或录制的只读响应样本，不提供可被运行时注册的模拟后端。

## 1.1 Mock 禁止项

禁止：

- 产品运行模式使用 mock backend；
- 开发模式注册 mock backend；
- 独立演示链路使用 mock 房源、mock 预约或 mock 租约；
- `Tool Registry` 注册 `mock` backend；
- 前端展示由 mock 数据伪造的真实业务成功状态；
- 真实 `lease/web-app`、Milvus、Redis 不可用时自动回退到 mock 成功响应；
- 新增 `MockToolClient`、`tools/mock.py`、`knowledge/mock/` 这类运行时可导入的数据源。

允许的测试材料必须满足：

- 来源是真实接口契约或真实测试库种子数据；
- 只用于断言、回放或离线评测，不实现业务成功逻辑；
- 不能被应用启动、工具注册表或前端运行时代码导入。

## 2. 工具注册表

所有工具必须注册后才能被 Agent 调用。

建议工具定义：

```python
class ToolDefinition:
    name: str
    description: str
    input_schema: type
    output_schema: type
    backend: Literal["lease", "vector", "memory"]
    permission: Literal["public", "user", "internal"]
    requires_user: bool
    requires_confirmation: bool
    timeout_seconds: int
    retry_policy: dict
    error_mapping: dict
```

## 3. 推荐工具清单

| Tool | 用途 | 后端 | 是否需要用户 | 是否需要确认 |
| --- | --- | --- | --- | --- |
| `area.normalize` | 地标/商圈/学校归一化 | vector/lease | 否 | 否 |
| `room.search` | 房源搜索 | lease | 否 | 否 |
| `room.detail` | 房源详情 | lease | 否 | 否 |
| `kb.search` | 租房规则知识库检索 | vector | 否 | 否 |
| `appointment.create` | 创建看房预约 | lease | 是 | 是 |
| `appointment.list_mine` | 查询我的预约 | lease | 是 | 否 |
| `lease.list_mine` | 查询我的租约 | lease | 是 | 否 |
| `recommendation.store` | 保存最近推荐 | memory | 否 | 否 |
| `memory.session_update` | 保存短期会话状态 | memory | 否 | 否 |
| `memory.profile_get` | 读取长期偏好画像 | memory | 是 | 否 |
| `memory.profile_update` | 更新长期偏好画像 | memory | 是 | 否 |
| `memory.profile_delete` | 删除长期偏好 | memory | 是 | 否 |
| `handoff.create` | 创建人工接管请求 | lease/internal | 是 | 否 |
| `trace.record` | 记录可审计执行事件 | memory/internal | 否 | 否 |

本文档只给出工具层总体契约；每个工具的字段映射、权限、timeout 和标准错误码以 [15-tool-registry-and-error-codes.md](15-tool-registry-and-error-codes.md) 为准。

## 4. Tool Call Result

所有工具返回统一 envelope：

```json
{
  "ok": true,
  "tool": "room.search",
  "data": {},
  "error": null,
  "metadata": {
    "backend": "lease",
    "latency_ms": 83,
    "trace_id": "..."
  }
}
```

失败时：

```json
{
  "ok": false,
  "tool": "appointment.create",
  "data": null,
  "error": {
    "code": "MISSING_APARTMENT_ID",
    "message": "预约缺少 apartment_id",
    "recoverable": true,
    "user_message_type": "collect_missing_room"
  },
  "metadata": {}
}
```

## 5. 与现有项目接口集成

启动 `AptGuide 2.0` 前必须启动现有 `lease/web-app`，由 `AptGuide 2.0` 通过内部工具接口调用真实业务能力。

推荐链路：

```text
AptGuide 2.0 API
  -> LeaseToolAdapter
  -> lease web-app /internal/ai/tools/*
  -> MySQL
```

调用要求：

- 使用内部 token；
- 透传 request_id；
- 用户数据接口必须有 user_id；
- AptGuide 2.0 不直接访问 MySQL；
- 工具 adapter 负责把 lease 响应转换为统一 Tool Result。

## 6. 真实后端依赖

第一版就按真实依赖运行。开发和联调时需要准备：

- MySQL 中有可用房源、公寓、预约、租约基础数据；
- `lease/web-app` 正常启动并暴露 `/internal/ai/tools/*`；
- `AI_INTERNAL_TOKEN` 与 AptGuide 2.0 配置一致；
- Milvus / KB 已完成规则知识和房源向量同步；
- Redis 可用，用于 session、pending action 和短期记忆；
- 长期画像存储可用，开发期可 SQLite，产品期建议 MySQL/PostgreSQL。

测试数据仍需覆盖：

- 广州主城区；
- 大学城/南亭等地标；
- 低预算、预算不限、跨区推荐；
- 可预约和不可预约房源；
- 用户已有预约；
- 用户已有租约；
- 空结果恢复样本。
- 用户长期偏好样本；
- 人工接管样本；
- 工具失败样本。

## 7. 搜索策略接口

找房不应该只调用一次 `room.search`。

RoomSearchAgent 应该可以执行：

```text
1. exact_search
2. relaxed_budget_search
3. relaxed_area_search
4. nearby_alternative_search
```

每次搜索都记录：

```json
{
  "strategy": "relaxed_budget_search",
  "query": "大学城 南亭 安静",
  "filters": {
    "district": "番禺区",
    "max_rent": null
  },
  "result_count": 4
}
```

## 8. 写操作安全

写工具必须经过：

```text
collect params
  -> validate params
  -> create pending_action with confirmation_id
  -> frontend confirm action
  -> validate confirmation_id
  -> execute tool
  -> clear pending_action
```

任何纯文本“确认”都不能绕过 `confirmation_id` 校验。

## 9. 记忆工具安全

长期记忆工具必须遵守：

```text
extract candidate
  -> classify sensitivity
  -> decide scope
  -> ask confirmation when needed
  -> write profile
  -> write audit log
```

限制：

- 不保存身份证、电话、合同编号等敏感信息；
- 本次临时需求不能默认覆盖长期偏好；
- 用户可删除长期偏好；
- 长期偏好只能辅助推荐，不能自动执行预约。

## 10. 人工接管工具

人工接管工具建议输入：

```json
{
  "session_id": "s-001",
  "user_id": "u-001",
  "reason": "appointment_tool_failed_twice",
  "priority": "medium",
  "summary": "用户想预约大学城南亭附近房源，appointment.create 连续超时。",
  "trace_id": "t-001"
}
```

返回：

```json
{
  "handoff_id": "h-001",
  "status": "created",
  "assigned_group": "tenant_service"
}
```

## 11. 配置建议

```env
APTGUIDE_BACKEND_MODE=lease
LEASE_BASE_URL=http://127.0.0.1:8081
LEASE_INTERNAL_TOKEN=change-me
VECTOR_BACKEND=milvus
REDIS_URL=redis://127.0.0.1:6379/2
MEMORY_BACKEND=postgres
TRACE_BACKEND=jsonlog
LLM_MODEL=qwen-plus
```

第一阶段默认 `lease`，不提供 mock 工具后端。

## 12. 与当前仓库的契约注意事项

当前仓库已经有 `lease/web-app` 的 AI 工具入口，但 AptGuide 2.0 实现前需要对齐以下细节：

- Java DTO 当前使用 `cityId`、`districtId`、`maxRent`、`appointmentTime` 等 camelCase 字段，Python adapter 如果使用 `city_id`、`district_id`、`max_rent`、`appointment_time`，需要做 alias 转换或统一 JSON 命名策略；
- `appointment.create` 必须校验 `apartmentId`、`roomId`、`appointmentTime`，不能在房源未解析时创建预约；
- 如果现有预约表只保存 apartment 级预约，前端卡片和回复不要承诺已预约到具体 room，除非后端补齐 room 级字段；
- 当前房源搜索接口主要支持 city/district/rent 和部分 post-filter，`area.normalize`、语义召回、nearby alternative 需要在 AptGuide 2.0 adapter / vector 层补齐，或推动 lease 工具接口增强；
- 工具失败需要稳定错误码，不能只透传通用 message，否则 Recovery、Handoff 和 Eval 很难稳定。
