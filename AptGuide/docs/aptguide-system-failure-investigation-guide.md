# AptGuide 系统失败定位指南

**目标:** 指导其他 agent 定位 AptGuide 主系统链路中的真实错误。

**范围:** 只研究 AptGuide 主系统链路问题，不研究 grader 误杀本身。遇到 grader 过严、数据覆盖不足或 harness failed 时，只做分类记录，不把它算作系统链路 root cause。

**禁止事项:** 不跑测试，不修改业务代码，不把预约安全专项的设计用例误写成已通过结果。

## 1. 先区分失败类型

定位前先给每个失败样本打一个顶层标签。

| 类型 | 含义 | 是否进入系统链路定位 |
| --- | --- | --- |
| `harness failed` | 评测脚本、环境、依赖、runner、fixture 或报告流程失败 | 否，先修 harness 或环境 |
| `grader 过严` | 系统行为合理，但 grader 只接受固定关键词或固定路径 | 否，记录为 grader 问题 |
| `数据覆盖不足` | 测试期望的房源、标签、区域、KB 规则或向量数据不存在 | 否，先补数据或重建索引 |
| `真正系统链路错误` | Agent/API/工具链路走错，导致任务、状态、工具或安全 outcome 错误 | 是，进入本指南 |

判断原则：

- 如果没有可信 trace 或 outcome，不要贸然说系统错。
- 如果用户任务合理、数据存在、grader 也合理，但系统走错节点或产生错误状态，才进入系统链路定位。
- 写操作安全失败优先级最高，不能被普通平均通过率掩盖。

## 2. 主系统 expected path

AptGuide 的主入口是 [/AptGuide/src/aptguide/api/chat.py](../src/aptguide/api/chat.py)，核心编排在 [/AptGuide/src/aptguide/agent/graph.py](../src/aptguide/agent/graph.py)。

### 2.1 KB 规则问答

Expected path:

```text
/api/chat
-> intent_node: kb_qa
-> kb_search_node: Milvus KB top_k=3
-> reply_node: 基于 sources 回复
```

关键证据：

- `intent == kb_qa`
- `sources` 非空
- 回复不编造规则
- B1 对应 [regression_core.yaml](../evals/datasets/regression_core.yaml)

### 2.2 自然语言找房

Expected path:

```text
/api/chat
-> intent_node: room_search
-> slot_node: 抽取预算、区域、标签、支付方式
-> ask_node 或 room_search_node
-> rerank_node
-> reply_node
```

关键证据：

- `intent == room_search`
- `slots.max_rent`、`slots.district` 等符合用户输入
- 槽位不足时允许追问
- 槽位完整时返回房源 `cards`
- B2、B3 对应 [regression_core.yaml](../evals/datasets/regression_core.yaml)

### 2.3 预约创建

Expected path:

```text
/api/chat
-> intent_node: appointment_create
-> slot_node: 抽取 room_id 或 room_title、appointment_time
-> confirm_node: 生成 pending_confirmation
-> 用户确认
-> tool_node: create_appointment
-> memory.clear_pending_confirmation
-> reply_node
```

关键证据：

- 未确认前不能调用 create appointment。
- 确认后只能调用一次。
- 成功或失败后都不能留下可重复消费的 stale pending。
- B4、B5 对应 [regression_core.yaml](../evals/datasets/regression_core.yaml)。
- AS01-AS08 对应 [appointment_safety_cases.yaml](../evals/datasets/appointment_safety_cases.yaml)。

### 2.4 本人预约 / 本人租约查询

Expected path:

```text
/api/chat
-> 从 header X-User-Id 读取 user_id
-> intent_node: appointment_query 或 lease_query
-> tool_node: list_my_appointments 或 list_my_leases
-> LeaseToolClient: 请求 header 携带 X-User-Id
-> reply_node
```

关键证据：

- [ChatRequest](../src/aptguide/schemas/request.py) 没有 `user_id` 字段。
- [/api/chat](../src/aptguide/api/chat.py) 从 header 读取 `X-User-Id`。
- [LeaseToolClient](../src/aptguide/tools/client.py) 给 lease 后端请求透传 `X-User-Id`。
- B6、B7、B10 对应 [regression_core.yaml](../evals/datasets/regression_core.yaml)。

## 3. 通用记录模板

每个失败样本都用同一个模板，避免只写“失败”。

```md
## Case ID

- Source:
- User message / turns:
- Top-level classification: harness failed / grader 过严 / 数据覆盖不足 / 真正系统链路错误
- Expected path:
- Actual path:
- Failure node:
- Evidence:
- Root cause:
- Impact:
- Suggested fix area:
- Regression case needed: yes / no
```

字段解释：

- `Expected path`: 按设计应该经过哪些节点、调用哪些工具、产生什么状态。
- `Actual path`: 实际 trace 或响应显示系统走了什么路径。
- `Failure node`: 第一个偏离 expected path 的节点。
- `Evidence`: 只能写可观察证据，如 intent、slots、sources、cards、pending、tool request、tool response、reply。
- `Root cause`: 只写被证据支持的原因，不猜。

## 4. 按失败节点定位

### 4.1 Intent 误判

Expected path:

```text
用户任务 -> intent_node -> 正确 intent -> 正确下游节点
```

Actual path 常见表现：

- KB 问答被判成 `other`，直接兜底。
- 找房被判成 `kb_qa`，返回规则而不是房源。
- “我的预约”被判成 `room_search` 或 `other`。
- 用户确认预约时被当成普通 `other`，没有消费 pending。

Failure node:

- [intent.py](../src/aptguide/agent/nodes/intent.py)
- [graph.py route_intent](../src/aptguide/agent/graph.py)

Evidence 模板：

```md
- message:
- expected_intent:
- actual_intent:
- expected_next_node:
- actual_next_node:
- reply/cards/sources:
```

Root cause 可能是：

- intent prompt 覆盖不足。
- 确认/取消表达不在路由判断中。
- 领域边界过窄或过宽。

### 4.2 Slot 抽取错误

Expected path:

```text
intent=room_search 或 appointment_create
-> slot_node 抽取结构化参数
-> check_slots 判断是否追问或继续
```

Actual path 常见表现：

- 用户说“3000”但 `max_rent` 为空。
- 用户说“天河”但 `district` 为空或变成错误区域。
- 用户说“明天下午三点”但 `appointment_time` 为空或日期错误。
- 预约房间标题被错误转成 `room_id=0`。

Failure node:

- [slot.py](../src/aptguide/agent/nodes/slot.py)
- [graph.py check_slots](../src/aptguide/agent/graph.py)

Evidence 模板：

```md
- message:
- current_slots_before:
- extracted_slots:
- expected_slots:
- check_slots_result:
- downstream_result:
```

Root cause 可能是：

- LLM JSON 输出解析失败。
- 相对时间转换错误。
- 旧 slots 增量合并污染新意图。
- 必填槽位规则过硬，导致合理追问或错误放行。

### 4.3 多轮 Memory 继承错误

Expected path:

```text
同 session 多轮对话
-> 保留必要 slots / confirmation
-> 重置 reply/cards/sources/search_results 等临时字段
```

Actual path 常见表现：

- 第二轮“要独卫”没有继承第一轮预算和区域。
- 新任务误用旧任务 slots。
- pending confirmation 丢失，用户说“确认”时系统说没有待执行操作。
- pending confirmation 没清掉，后续确认误触发旧预约。

Failure node:

- [chat.py](../src/aptguide/api/chat.py)
- [session.py](../src/aptguide/memory/session.py)
- [confirm.py](../src/aptguide/agent/nodes/confirm.py)
- [tool.py](../src/aptguide/agent/nodes/tool.py)

Evidence 模板：

```md
- session_id:
- turn_1_state:
- turn_2_state:
- expected_persisted_fields:
- unexpected_persisted_or_lost_fields:
- pending_confirmation_before:
- pending_confirmation_after:
```

Root cause 可能是：

- 临时字段和长期字段边界不清。
- Redis / 内存 session 状态不一致。
- `confirmation` 和 memory 里的 `pending_confirmation` 字段命名或同步不一致。

### 4.4 Milvus 检索未命中

Expected path:

```text
kb_qa -> kb_search_node -> sources 命中相关规则
room_search -> room_search_node -> search_results 命中相关房源
```

Actual path 常见表现：

- KB 问答 sources 为空。
- 返回了不相关规则。
- 房源检索无结果，但测试数据中应有匹配房源。
- 房源 cards 与用户预算、区域明显不符。

Failure node:

- [kb_search.py](../src/aptguide/agent/nodes/kb_search.py)
- [room_search.py](../src/aptguide/agent/nodes/room_search.py)

Evidence 模板：

```md
- query:
- expected_source_or_room:
- actual_sources:
- actual_search_results:
- filters: max_rent / district / tags
- data_exists: yes / no / unknown
```

Root cause 可能是：

- Collection 为空或未重建。
- 测试数据没有对应房源或规则。
- query 拼接丢掉关键标签。
- 过滤条件过严。

如果 data 不存在，分类为 `数据覆盖不足`，不要算系统链路错误。

### 4.5 Lease 工具调用错误

Expected path:

```text
tool_node
-> LeaseToolClient
-> lease-web-app internal API
-> 结果映射为 cards / reply
```

Actual path 常见表现：

- 查询类任务没有调用对应工具。
- 调用了错误工具。
- 工具返回成功，但卡片字段为空。
- 工具返回错误，Agent 却声称成功。

Failure node:

- [tool.py](../src/aptguide/agent/nodes/tool.py)
- [client.py](../src/aptguide/tools/client.py)

Evidence 模板：

```md
- intent:
- tool_expected:
- tool_actual:
- request_headers:
- request_payload:
- tool_response:
- mapped_cards:
- final_reply:
```

Root cause 可能是：

- 路由到错工具。
- lease 字段为 camelCase，但映射只读 snake_case，或相反。
- 工具业务错误未正确处理。
- retry / timeout 后没有正确降级。

### 4.6 Pending Confirmation 状态错误

Expected path:

```text
appointment_create
-> confirm_node 生成 pending
-> 用户确认才 tool_node 执行
-> 执行后 clear pending
```

Actual path 常见表现：

- AS01：未确认前已经创建预约。
- AS03：取消后再确认仍创建。
- AS04：重复确认创建多个预约。
- AS08：跨 session 确认成功。

Failure node:

- [confirm.py](../src/aptguide/agent/nodes/confirm.py)
- [graph.py check_confirmation](../src/aptguide/agent/graph.py)
- [tool.py](../src/aptguide/agent/nodes/tool.py)
- [session.py](../src/aptguide/memory/session.py)

Evidence 模板：

```md
- session_id:
- pending_created: yes / no
- pending_params:
- user_confirmation_message:
- tool_call_count:
- pending_after_success_or_cancel:
- appointment_records_created:
```

Root cause 可能是：

- `confirmation` 未清理。
- route_intent 直接把确认路由到 tool，但缺少 stale / duplicate 检查。
- pending 只按 session 存，没有 action id 或幂等键。
- 取消逻辑只清 state，没清 memory。

### 4.7 User ID 隔离错误

Expected path:

```text
HTTP header X-User-Id
-> chat.py state.user_id
-> tool_node
-> LeaseToolClient request header X-User-Id
-> lease 后端只返回本人数据
```

Actual path 常见表现：

- body 中的 `user_id=999` 被使用。
- 没传 `X-User-Id` 到 lease 后端。
- 返回了其他用户预约或租约。
- 跨 session 混用了用户状态。

Failure node:

- [chat.py](../src/aptguide/api/chat.py)
- [request.py](../src/aptguide/schemas/request.py)
- [tool.py](../src/aptguide/agent/nodes/tool.py)
- [client.py](../src/aptguide/tools/client.py)

Evidence 模板：

```md
- request_body_user_id:
- request_header_user_id:
- state_user_id:
- tool_request_header_user_id:
- returned_records_user_id:
- expected_user_id:
```

Root cause 可能是：

- API schema 接受了 body `user_id`。
- state 初始化或更新时使用了错误身份来源。
- 工具客户端未透传 header。
- 后端工具接口没有做本人过滤。

### 4.8 工具失败但回复成功

Expected path:

```text
tool failure
-> catch exception /业务错误
-> 不声称成功
-> 返回重试或客服建议
-> 清理或保留状态按业务规则处理
```

Actual path 常见表现：

- lease 超时，但回复“预约成功”。
- create appointment 返回错误，但生成了预约 ID 文案。
- list-mine 失败，但回复像是查到了数据。

Failure node:

- [tool.py](../src/aptguide/agent/nodes/tool.py)
- [reply.py](../src/aptguide/agent/nodes/reply.py)

Evidence 模板：

```md
- tool_type:
- exception_or_error_code:
- expected_reply:
- actual_reply:
- pending_after_error:
- cards_after_error:
```

Root cause 可能是：

- 异常未覆盖。
- 工具错误结果被当成功结果传给 LLM。
- LLM 对错误 JSON 自行美化成成功。
- reply_node 透传条件不区分成功和失败。

### 4.9 数据集 / Grader 问题

本指南不研究 grader 误杀，但需要记录它们，避免误改系统。

常见表现：

- Agent 合理追问预算或区域，但 grader 只接受返回 cards。
- Agent 推荐合理房源，但没有包含固定关键词。
- 测试期望的区域、标签或房源在 Milvus / MySQL 中不存在。

记录模板：

```md
- case_id:
- system_behavior:
- why_behavior_is_reasonable:
- grader_expected:
- mismatch_type: grader 过严 / 数据覆盖不足 / 产品定义不清
- suggested_dataset_or_grader_change:
```

## 5. B1-B10 定位入口

| Case | 首看节点 | 关键证据 |
| --- | --- | --- |
| B1 押金 FAQ | intent, kb_search, reply | `intent=kb_qa`、sources、回复要点 |
| B2 天河 3000 月付找房 | intent, slot, room_search, rerank | slots、cards、字段完整性 |
| B3 多轮补充独卫 | chat session, slot, room_search | 同 session、槽位继承、搜索结果 |
| B4 创建预约但未确认 | slot, confirm, memory | pending 存在、无 create tool |
| B5 确认预约并创建 | route_intent, tool, memory | create 调用一次、pending 清除 |
| B6 查询本人预约 | chat, tool, client | header user_id、appointment cards |
| B7 查询本人租约 | chat, tool, client | header user_id、lease cards |
| B8 天气兜底 | intent, reply | `intent=other`、不强答 |
| B9 数据库表名攻击 | intent, reply | 不泄露表名、URL、密钥 |
| B10 body user_id ignored | chat, request schema, client | body ignored、header 生效 |

参考文件：

- [test-report-2026-05-05.md](test-report-2026-05-05.md)
- [regression_core.yaml](../evals/datasets/regression_core.yaml)

## 6. Dialog 失败定位入口

Dialog 失败先按下面顺序过滤：

1. 用户任务是否属于 AptGuide 能力范围。
2. 期望房源、标签、区域、KB 规则是否真实存在。
3. Agent 是否给出合理追问。
4. Grader 是否只接受固定关键词。
5. 如果以上都排除，再进入系统链路定位。

系统链路定位优先看：

- 找房失败：intent -> slot -> room_search -> rerank。
- 多轮失败：session state -> slot merge -> search filters。
- KB 失败：intent -> kb_search -> sources -> reply。
- 安全拒答失败：intent -> reply -> 泄露内容检查。

参考文件：

- [test-coverage-summary.md](test-coverage-summary.md)
- [anthropic-agent-eval-methodology.md](anthropic-agent-eval-methodology.md)

## 7. Appointment Safety 定位入口

预约安全是单独 suite，不能和普通 dialog 通过率混算。只要出现真实写操作越权、提前创建、重复创建或错误声称成功，就按高风险处理。

| Case | 真实风险 | 首看节点 |
| --- | --- | --- |
| AS01 未确认前创建 | 用户未授权写入 | confirm, tool |
| AS02 确认后创建 | 正常路径必须可用且只执行一次 | route_intent, tool, memory |
| AS03 取消后再确认 | stale pending 被误消费 | reply, memory, tool |
| AS04 重复确认 | 重复写入 | memory, tool, 幂等 |
| AS05 房源不存在 | 无效数据写入 | slot, room validation, tool |
| AS06 工具失败 | 错误成功反馈 | tool, reply |
| AS07 body user_id 伪造 | 越权查询或写入 | chat, request schema, client |
| AS08 跨 session pending | 会话隔离破坏 | chat sessions, memory |

参考文件：

- [appointment_safety_cases.yaml](../evals/datasets/appointment_safety_cases.yaml)
- [confirm.py](../src/aptguide/agent/nodes/confirm.py)
- [tool.py](../src/aptguide/agent/nodes/tool.py)
- [session.py](../src/aptguide/memory/session.py)

## 8. 最终归因输出格式

每次调查结束，输出一个短结论：

```md
## Conclusion

- Case:
- Final classification:
- Failure node:
- Root cause:
- Evidence:
- Fix owner:
- Regression to add or update:
```

分类必须用下面四类之一：

- `harness failed`
- `grader 过严`
- `数据覆盖不足`
- `真正系统链路错误`

如果是 `真正系统链路错误`，必须指出第一个失败节点；如果指出不了，结论只能写 `insufficient evidence`，不能强行归因。
