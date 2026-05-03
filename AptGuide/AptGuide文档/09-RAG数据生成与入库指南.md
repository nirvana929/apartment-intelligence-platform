# 09 · RAG 数据生成与入库指南

## 1. 给下一个 Agent 的任务说明

你接手的是 AptGuide 的 RAG 数据准备工作。请先理解一点：这里不是训练 embedding 模型，也不需要 GPU。任务是从完整公寓租赁项目视角梳理数据，把租房领域文本、房源数据、行为数据和评测数据整理成可检索、可评测、可逐步接入真实系统的数据资产。

第一阶段先用 mock / YAML 数据跑通独立应用；第二阶段用 `lease` 的真实业务接口和运营后台数据替换 mock。无论阶段如何变化，数据格式、字段边界和安全规则必须保持一致。

优先级：

1. 建立完整项目数据地图：哪些数据进 Milvus，哪些只走 Java 工具，哪些只做评测，哪些禁止进入 AI 链路。
2. 做一次只读数据审计：核对 `lease` 当前库里哪些公开房源字段可复用，哪些字段缺失，哪些字段必须脱敏或排除。
3. 补齐知识库 YAML：`account.yaml`、`policy.yaml`。
4. 准备第一阶段高质量房源数据：固定 150 条；能从真实库提取的公开字段优先对齐真实值，不足部分用 mock 补齐覆盖。
5. 生成 RAG / 推荐评测数据：固定 500 条 query-positive-negative 检索评测，并配套 300 条 Agent 对话评测。
6. 实现或配合实现校验、切分、embedding、Milvus 入库脚本。

本阶段允许 Agent 为了“数据准备和核对”临时只读访问 MySQL，但这只是离线审计手段，不代表 AptGuide 运行时可以直连数据库。最终产品路径仍然是：AptGuide 通过 Java 工具接口查询业务数据，Milvus 只保存公开房源文本和审核后的知识库文本。

## 2. 这不是训练模型

RAG 建库流程：

```text
原始文本 / 房源数据
  → 清洗
  → 切分 chunk
  → 调用远程 embedding API
  → 得到向量
  → 写入 Milvus
  → 查询时对用户问题生成 query vector
  → Milvus top-k 检索
  → LLM 基于召回内容回答
```

不需要做：

- 不从零训练 embedding 模型；
- 不微调 embedding 模型；
- 不需要 GPU；
- 不需要 PyTorch；
- 不把 MinIO 图片二进制写入 Milvus。

推荐第一阶段使用阿里 DashScope `text-embedding-v4`。本地只负责切分、调用 API、写入 Milvus。

## 3. 完整项目数据地图

AptGuide 需要的数据不只有 mock 房源。完整项目里应按“用途、来源、是否入 Milvus、是否含用户信息”分层管理。

| 数据域 | 示例 | 第一阶段来源 | 第二阶段来源 | 是否入 Milvus | 用途 |
|--------|------|--------------|--------------|---------------|------|
| 规则知识库 | 预约规则、退租政策、押金说明、账号规则、宠物政策 | `knowledge/rules/*.yaml` | 运营后台 / 审核后的 YAML 或 CMS | 是，`apt_rental_kb` | FAQ / RAG 问答 |
| 房源公开信息 | 公寓名、区域、租金、户型、配套、标签、图片 URL | `knowledge/mock/rooms.yaml` | `lease internal tools` / MySQL 房源表 | 是，`apt_room_vector` | 语义找房、推荐召回 |
| 房源图片 | MinIO URL、封面图、轮播图 | mock URL 字符串 | MinIO + Java 返回 `graphVoList` | 不存图片二进制，只存 URL 或少量文本描述 | 卡片展示 |
| 工具业务数据 | 预约、租约、浏览历史 | mock tools | Java 内部工具接口 | 不入 Milvus | 查询本人数据、创建预约、个性化推荐 |
| 会话状态 | 槽位、最近推荐、待确认操作 | 内存 / Redis | Redis | 不入 Milvus | 多轮对话、写操作确认 |
| 用户行为埋点 | 推荐曝光、卡片点击、预约确认、预约成功 | 可先写 mock 日志 | 业务库 / 埋点表 | 不入 Milvus | AptInsight 分析 AI 效果 |
| 检索评测数据 | query-positive-negative、hit@k 标注 | YAML 人工/LLM 生成 | 真实搜索日志脱敏后沉淀 | 不入 Milvus | 评估 RAG 和推荐质量 |
| Prompt / few-shot 数据 | 意图样例、槽位样例、拒答样例 | 手写 YAML / Markdown | 评测失败样例沉淀 | 不入 Milvus | 提升 Agent 稳定性 |

### 3.1 数据进入链路

```text
规则知识库 YAML / 运营规则
  → validate_kb.py
  → seed_kb.py
  → embedding
  → Milvus apt_rental_kb

房源公开信息 mock / Java sync
  → sync_room_vectors.py
  → 拼接 content
  → embedding
  → Milvus apt_room_vector

预约 / 租约 / 浏览历史
  → 不入 Milvus
  → 请求时通过 Java tool 实时查询

会话状态 / pending confirmation
  → 不入 Milvus
  → Redis 短期保存

评测数据
  → 不入 Milvus
  → eval runner 读取并验证检索结果
```

### 3.2 禁止进入 Milvus 的数据

以下数据不能写入 Milvus，也不能出现在 RAG chunk 中：

- 手机号、身份证、邮箱、银行卡、支付账号；
- 合同全文、电子签文件、押金账户；
- 用户真实住址、紧急联系人；
- 后台管理员账号、密钥、内部接口 token；
- 未脱敏的预约、租约、浏览历史；
- MinIO 图片二进制文件。

用户级数据只能通过 Java 工具接口按当前用户实时查询，不能做全局向量化。

### 3.3 查库阶段的临时核对边界

当前还处于数据准备阶段，可以临时读取 `lease` 数据库做离线核对，目标是让第一阶段 mock 数据贴近真实业务结构。这个动作必须满足下面约束：

- 只读访问，不写库、不改库、不生成回灌 SQL；
- 优先读取公开业务表：`room_info`、`apartment_info`、`city_info`、`district_info`、`label_info`、`facility_info`、`lease_term`、`payment_type`、`graph_info` 以及这些表的关联表；
- 禁止读取或导出用户级敏感数据：`user_info`、`lease_agreement`、`view_appointment`、`browsing_history`、支付流水、后台账号等；
- `apartment_info.phone` 虽然在公寓表中，但属于联系电话，不进入 RAG chunk、评测集和 mock YAML；
- `apartment_info.address_detail` 可以用于人工核对，但生成数据时只保留粗粒度地址，例如“番禺区大学城附近”，不写精确门牌；
- 临时 SQL 只能选择需要字段，避免 `select *` 导出整表；
- 生成的数据必须能独立运行，不能依赖本地数据库实时存在。

建议审计 SQL 范围：

```sql
select
  r.id as room_id,
  r.room_number,
  r.rent,
  r.apartment_id,
  r.is_release,
  a.name as apartment_name,
  a.city_id,
  a.city_name,
  a.district_id,
  a.district_name,
  a.address_detail
from room_info r
join apartment_info a on a.id = r.apartment_id
where r.is_deleted = 0 and a.is_deleted = 0;
```

### 3.4 当前数据库公开字段盘点

基于 2026-05-02 的本地 `least` 库只读核对，当前可直接利用的公开房源字段如下：

| 来源表 | 可用字段 | 用途 | 注意 |
|--------|----------|------|------|
| `room_info` | `id`、`room_number`、`rent`、`apartment_id`、`is_release` | 房源主数据、价格、上下架状态 | `id` 是真实业务 `room_id`；删除房源不进入 mock 主集 |
| `apartment_info` | `id`、`name`、`introduction`、`city_id`、`city_name`、`district_id`、`district_name`、`address_detail`、`is_release` | 公寓名、城市区域、粗地址、介绍 | `phone`、经纬度不进入向量；地址需粗粒度化 |
| `room_attr_value` + `attr_value` + `attr_key` | 面积、朝向、户型、采光、卫所等 | 生成 `area`、`layout`、补充标签 | 存在历史脏数据，需按 `is_deleted=0` 过滤 |
| `room_label` + `label_info` | 房间标签，如朝南、独卫、阳台 | 生成 `tags` | 可补充“安静、适合通勤”等运营标签，但要标记为生成标签 |
| `room_facility` + `facility_info` | 空调、洗衣机、冰箱、书桌、WIFI、床、热水器等 | 生成 `facilities` | 只写设施名称，不写图片或图标二进制 |
| `room_lease_term` + `lease_term` | 1、3、6、12 个月 | 生成 `lease_terms` | 重复 1 个月租期需去重 |
| `room_payment_type` + `payment_type` | 月付、季付、半年付、年付 | 生成 `payment_types` | 建议转换为 `MONTHLY`、`QUARTERLY`、`HALF_YEARLY`、`YEARLY` |
| `graph_info` | `url` | 生成 `thumbnail_url` 或图片列表 | 只保留 URL，不下载、不入库图片二进制 |

当前库的有效公开房源数量有限：`room_info` 中非删除且已发布房源约 31 条，包含北京昌平区与广州番禺区样本，其中广州样本主要集中在番禺区大学城。第一阶段如果要覆盖天河、越秀、海珠、番禺、白云，需要采用“真实公开字段 + 生成补齐”的混合策略：真实库存在的房源保留真实 `room_id` 和价格；覆盖不足的区域使用 `3001` 起的 mock `room_id`，不能伪装成数据库真实 ID。

## 4. 数据类型与生成格式

### 4.1 知识库数据

路径：

```text
src/aptguide/knowledge/rules/
```

现有文件：

```text
room_search.yaml
appointment.yaml
lease.yaml
payment.yaml
life.yaml
```

待补文件：

```text
account.yaml
policy.yaml
```

每条数据遵循 `_schema.yaml`：

```yaml
- doc_id: KB-ACCT-001
  doc_type: faq
  module: account
  title: 注册与实名认证
  content: |
    用户可以使用手机号注册并登录。首次使用涉及签约、预约、租约查看等功能时，可能需要按页面提示完成实名认证。
    实名认证信息仅用于身份核验和租约相关服务，不会在智能助手回答中展示。
  tags: [账号, 注册, 实名]
  version: 1
  updated_at: 2026-05-02
  reviewed_by: ops
```

写作规则：

- `content` 不超过 600 字；
- 不写手机号、身份证、银行卡、合同全文；
- 不使用“一定”“保证”“绝对”“包退”“100%”；
- 金额、时间、比例如果没有明确依据，就写“以合同约定或门店实际规则为准”；
- 文案要像运营 FAQ，不要像法律合同。

### 4.2 房源向量数据

第一阶段可以先生成 mock 房源数据。若处于数据准备阶段，也可以临时只读查询 MySQL 做字段核对和样本抽取，但生成结果仍然落到 YAML 文件中，AptGuide 运行时不直连 MySQL。

建议路径：

```text
src/aptguide/knowledge/mock/rooms.yaml
```

建议字段：

```yaml
- room_id: 3001
  room_number: "302"
  apartment_id: 2001
  apartment_name: 天河公寓
  city_id: 4401
  city_name: 广州
  district_id: 1001
  district_name: 天河区
  address: 天河区科韵路附近
  rent: 2800
  area: 25
  layout: 1室1卫
  payment_types: [MONTHLY, QUARTERLY]
  lease_terms: [3, 6, 12]
  tags: [独卫, 朝南, 安静, 近地铁, 适合备考]
  facilities: [空调, 洗衣机, 热水器, 电梯]
  thumbnail_url: "http://127.0.0.1:9000/lease/demo/room-3001.jpg"
  is_release: true
  is_appointable: true
  audience_summary: 适合预算 3000 元以内、希望通勤方便和安静学习环境的租客。
```

字段规则：

- `room_id`：真实房源使用数据库 `room_info.id`；纯 mock 房源使用 `3001` 起的独立 ID 段。
- `room_number`：可以使用房号，但不要拼接精确楼栋、单元、门牌。
- `apartment_id`、`apartment_name`：真实房源使用 `apartment_info`；生成补齐房源使用 mock ID 段。
- `city_id`、`district_id`：真实房源保留数据库 ID；生成补齐房源使用稳定 mock ID，不与真实 ID 混用。
- `address`：只保留粗粒度区域或商圈，例如“番禺区大学城附近”，不写完整门牌。
- `rent`：真实房源保留真实月租；生成房源按覆盖区间生成。
- `area`：优先从“面积”属性解析数字；缺失时按户型和租金生成合理值，并在生成脚本中标记来源。
- `layout`：优先从“户型”属性取值；缺失时生成 `1室1卫`、`1室1厅`、`2室1厅` 等稳定枚举。
- `payment_types`：统一使用英文枚举，`月付` → `MONTHLY`，`季付` → `QUARTERLY`，`半年付` → `HALF_YEARLY`，`年付` → `YEARLY`。
- `lease_terms`：保存月份数字并去重，例如 `[1, 3, 6, 12]`。
- `tags`：真实标签优先；运营补充标签要来自字段可推断事实，不写夸张营销。
- `facilities`：只写设施名称，例如空调、洗衣机、热水器、WIFI。
- `thumbnail_url`：可使用 MinIO URL 或 mock URL 字符串；不要求图片真实存在。
- `is_release`：真实房源以 `room_info.is_release` 和 `apartment_info.is_release` 同时为 1 为准。
- `is_appointable`：第一阶段可按 `is_release=true` 生成；第二阶段必须由 Java 回查确认。
- `data_source`：建议增加可选字段，值为 `db_public`、`generated_mock` 或 `manual_seed`，方便评测时区分来源。
- `source_room_id`：可选，仅当 `data_source=generated_mock` 且基于某个真实房源扩展时填写；不能替代 `room_id`。

用于向量化的 `content` 建议由脚本拼接，不手写：

```text
房间 302，位于天河公寓，广州市天河区，地址在天河区科韵路附近。
月租 2800 元，支持月付、季付，租期可选 3、6、12 个月。
户型 1室1卫，面积 25 平方米，标签包括独卫、朝南、安静、近地铁、适合备考。
公寓配套包括空调、洗衣机、热水器、电梯。
适合预算 3000 元以内、希望通勤方便和安静学习环境的租客。
```

数量建议：

| 阶段 | 房源数量 | 用途 |
|------|----------|------|
| 本地 smoke | 30 条 | 快速跑通推荐流程 |
| 第一阶段高质量数据集 | 150 条 | 覆盖区域、价格、标签组合和边界样本 |
| 第二阶段 | 来自 Java / MySQL | 用真实房源同步替换 mock |

第二阶段真实房源字段应优先从 Java 后端统一 DTO 获取，而不是 AptGuide 直连 MySQL。Java DTO 至少应能提供：

- 房间 ID、房号、公寓 ID、公寓名；
- 城市、区域、地址粗粒度描述；
- 租金、面积、户型；
- 支付方式、租期；
- 标签、配套、适合人群摘要；
- 图片 URL；
- 是否上架、是否可预约。

### 4.3 工具业务数据

这些数据不进入 Milvus，只通过工具接口实时查询：

| 数据 | 第一阶段 | 第二阶段 | 注意 |
|------|----------|----------|------|
| 我的预约 | mock appointment | `appointment/list-mine` | 仅返回当前用户 |
| 创建预约 | mock create | `appointment/create` | 必须二次确认 |
| 我的租约 | mock lease | `lease/list-mine` | 不返回合同全文和敏感字段 |
| 浏览历史 | mock history | `browse-history/list-mine` | 只返回 room_id 和时间等最小信息 |
| 房源详情 | mock room detail | `room/{id}` | 真实状态由 Java 校验 |

### 4.4 用户行为与 AptInsight 分析数据

为了第二阶段形成 C 端 AptGuide 和 B 端 AptInsight 的闭环，建议沉淀以下行为数据。第一阶段可先用日志或 mock event 文件表示，第二阶段由 `lease` 或埋点系统写入业务库。

建议事件：

```yaml
- event_id: evt-001
  session_id: demo-s-001
  request_id: req-001
  event_type: recommendation_exposed
  room_id: 3001
  source: AI_GUIDE
  occurred_at: 2026-05-02 15:00:00
```

事件类型：

- `recommendation_exposed`：推荐卡片曝光；
- `room_card_clicked`：用户点击房源卡片；
- `appointment_confirm_shown`：展示预约确认；
- `appointment_confirmed`：用户确认预约；
- `appointment_created`：预约创建成功；
- `rag_answer_viewed`：用户查看规则问答；
- `fallback_triggered`：低置信度回退。

用途：

- AptInsight 分析 AI 推荐带来的预约转化；
- 分析热门区域、热门标签、预算分布；
- 发现 RAG 无答案或低置信度问题；
- 反哺知识库和房源标签维护。

### 4.5 评测数据

建议路径：

```text
evals/datasets/retrieval_cases.yaml
```

格式：

```yaml
- id: rag-room-001
  task: room_retrieval
  query: 我想找天河区三千以内安静一点、适合考研的房子
  positive_ids: [3001, 3008]
  hard_negative_ids: [3012, 3020]
  expected:
    hit_at_5: true
    must_include_tags: [安静, 适合备考]

- id: rag-kb-001
  task: kb_retrieval
  query: 提前退租押金怎么处理
  positive_doc_ids: [KB-LS-004, KB-POL-005]
  hard_negative_doc_ids: [KB-PAY-003]
  expected:
    hit_at_3: true
```

评测指标：

- `hit@1`
- `hit@3`
- `hit@5`
- `MRR`
- 低置信度回退率
- 错误来源引用率

### 4.6 数据规模与条目配额

本项目目标是让 AptGuide 的 RAG、推荐、工具调用和评测效果尽量稳定，不按“刚好能跑”的最低规模执行。第一阶段高质量数据集采用固定数量，不再使用区间。

| 数据资产 | 建议路径 | 固定目标数量 | 是否入 Milvus | 说明 |
|----------|----------|--------------|---------------|------|
| 规则知识库 | `src/aptguide/knowledge/rules/*.yaml` | 70 条 | 是 | 覆盖 7 个模块和 5 类 doc_type |
| 房源公开数据 | `src/aptguide/knowledge/mock/rooms.yaml` | 150 条 | 是 | 真实公开样本 + 广州覆盖补齐 + 边界样本 |
| 工具业务 mock | `src/aptguide/knowledge/mock/tool_data.yaml` | 300 条 | 否 | 支撑工具节点、多轮对话和房源详情回查 |
| 行为事件 mock | `src/aptguide/knowledge/mock/events.yaml` | 500 条 | 否 | 支撑 AptInsight 分析闭环 |
| 检索评测数据 | `evals/datasets/retrieval_cases.yaml` | 500 条 | 否 | 评估房源召回、KB 召回和回退 |
| Agent 对话评测 | `evals/datasets/dialog_cases.yaml` | 300 条 | 否 | 覆盖完整 Agent 流程 |
| Prompt / few-shot 样例 | `src/aptguide/knowledge/prompts/*.yaml` | 300 条 | 否 | 提升意图、槽位、确认、拒答稳定性 |
| 数据审计报告 | `src/aptguide/knowledge/mock/room_audit_report.md` | 1 份 | 否 | 每次生成数据前更新 |

条目统计口径：

- 知识库按 YAML 数组元素计数，一条 `doc_id` 算 1 条。
- 房源按一个 `room_id` 算 1 条。
- 工具业务 mock 按预约、租约、浏览历史、房源详情等数组元素合计。
- 行为事件按一个 `event_id` 算 1 条。
- 检索评测按一个 `case_id` 算 1 条。
- 对话评测按一个完整用户任务或多轮会话算 1 条。
- few-shot 按一个意图样例、槽位样例、拒答样例或确认样例算 1 条。

#### 4.6.1 知识库条目配额

当前已有 5 个模块共 29 条：`room_search` 5 条、`appointment` 6 条、`lease` 7 条、`payment` 6 条、`life` 5 条。第一阶段固定目标为 70 条。

| 模块 | 当前数量 | 目标数量 | 需新增 | 内容重点 |
|------|----------|----------|--------|----------|
| `room_search` | 5 | 10 | 5 | 搜索、筛选、标签、区域、收藏、浏览历史、相似推荐 |
| `appointment` | 6 | 10 | 4 | 预约、改期、取消、失败原因、代看、爽约、到店提醒 |
| `lease` | 7 | 12 | 5 | 签约、材料、租期、续约、退租、违约金、合同查看 |
| `payment` | 6 | 10 | 4 | 支付方式、押金、账单、发票、费用争议、退款 |
| `life` | 5 | 10 | 5 | 入住、钥匙、报修、公共设施、物业服务、邻里规则 |
| `account` | 0 | 8 | 8 | 注册、实名、隐私、信息修改、注销、账号安全 |
| `policy` | 0 | 10 | 10 | 同住人、宠物、软装、安全、清算、投诉、禁止事项 |
| 合计 | 29 | 70 | 41 | 覆盖 FAQ / rule / guide / policy / flow |

第一阶段生成顺序：

1. 先补 `account.yaml` 4 条、`policy.yaml` 5 条，达到 38 条。
2. 再补齐剩余 32 条，达到固定目标 70 条。
3. 新增条目必须优先覆盖真实问答中高频失败问题，不为了凑数写重复规则。

#### 4.6.2 房源条目配额

房源固定目标为 150 条，用于语义召回、推荐排序、卡片展示和对话评测。当前真实库公开房源约 31 条，但区域集中，必须用生成数据补齐广州区域覆盖。

按来源分配：

| 来源 | 目标数量 | `room_id` 规则 | 说明 |
|------|----------|----------------|------|
| `db_public` 真实公开样本 | 31 条 | 使用 `room_info.id` | 使用当前库非删除且已发布公开房源，只保留公开字段 |
| `generated_mock` 广州覆盖补齐 | 104 条 | `3001` 起递增 | 覆盖真实库缺失的广州区域、价格段、标签组合 |
| `manual_seed` 手工边界样本 | 15 条 | 延续 mock ID | 专门测试低置信度、边界预算、跨区推荐、冲突偏好 |
| 合计 | 150 条 | 真实 ID 与 mock ID 分段 | 不把生成样本伪装成真实库存 |

按区域分配：

| 区域 | 目标数量 | 覆盖重点 |
|------|----------|----------|
| 天河区 | 30 条 | 通勤、近地铁、主力预算、白领场景 |
| 越秀区 | 22 条 | 老城区、通勤、医院 / 学校附近 |
| 海珠区 | 26 条 | 江南西、琶洲、客村、通勤场景 |
| 番禺区 | 38 条 | 大学城、低预算、考研、学生场景 |
| 白云区 | 24 条 | 低预算、大面积、生活配套 |
| 北京昌平区样本 | 10 条 | 跨城市和真实库对齐测试，不作为广州主流程核心 |
| 合计 | 150 条 | 广州主流程 + 跨城市边界 |

按租金分配：

| 租金段 | 目标数量 | 典型 query |
|--------|----------|------------|
| 800 到 1500 | 24 条 | “预算很低”“学生”“番禺大学城” |
| 1500 到 2200 | 34 条 | “两千以内”“低预算”“可月付” |
| 2200 到 3200 | 42 条 | “三千以内”“通勤方便”“独卫” |
| 3200 到 4500 | 32 条 | “舒适一点”“采光好”“家电齐全” |
| 4500 以上 | 18 条 | “预算高一点”“空间大”“配套更好” |
| 合计 | 150 条 | 覆盖低预算、主力预算、舒适型和高预算 |

标签覆盖要求：

| 标签 | 目标覆盖房源数 |
|------|----------------|
| 安静 | 45 |
| 近地铁 | 55 |
| 独卫 | 60 |
| 朝南 | 45 |
| 可月付 | 80 |
| 适合考研 | 35 |
| 适合通勤 | 55 |
| 采光好 | 45 |
| 家电齐全 | 70 |
| 可短租 | 25 |

每条房源固定 5 个标签：4 个来自核心标签，1 个来自扩展标签，避免标签过多导致语义噪声。

设施覆盖要求：

| 设施 | 目标覆盖房源数 |
|------|----------------|
| 空调 | 130 |
| 洗衣机 | 115 |
| 热水器 | 120 |
| WIFI | 110 |
| 床 | 145 |
| 衣柜 | 120 |
| 书桌 | 85 |
| 电梯 | 75 |
| 智能锁 | 70 |
| 冰箱 | 85 |

每条房源固定 6 个设施，其中床、空调、热水器为优先基础设施；如果真实公开样本缺失设施，由生成脚本按房源定位补齐 mock 设施并保留 `data_source`。

支付方式覆盖要求：

| 支付方式 | 目标覆盖房源数 |
|----------|----------------|
| `MONTHLY` | 90 |
| `QUARTERLY` | 70 |
| `HALF_YEARLY` | 45 |
| `YEARLY` | 35 |

#### 4.6.3 工具业务 mock 条目配额

工具业务 mock 只用于对话演示和工具节点测试，不进入 Milvus。

| 类型 | 目标数量 | 覆盖要求 |
|------|----------|----------|
| `appointments` | 40 条 | 待看房、已完成、已取消、爽约、时段冲突 |
| `leases` | 30 条 | 生效中、即将到期、已结束、续约中、退租中 |
| `browse_history` | 60 条 | 最近浏览、重复浏览、跨区域浏览、同标签浏览 |
| `favorites` | 20 条 | 收藏房源和推荐联动 |
| `room_detail_cache` | 150 条 | 与 `rooms.yaml` 一一对应 |
| 合计 | 300 条 | 全部使用 mock 用户，不含真实个人信息 |

工具 mock 的用户 ID 只使用 `demo-user-001`、`demo-user-002` 等假 ID。预约、租约、浏览历史中的 `room_id` 必须来自 `rooms.yaml`。

#### 4.6.4 行为事件 mock 条目配额

行为事件用于 AptInsight 后续分析 AI 推荐效果，不进入 Milvus。

| 事件类型 | 目标数量 | 说明 |
|----------|----------|------|
| `recommendation_exposed` | 180 | 推荐卡片曝光 |
| `room_card_clicked` | 110 | 点击房源卡片 |
| `appointment_confirm_shown` | 60 | 展示预约确认 |
| `appointment_confirmed` | 45 | 用户确认预约 |
| `appointment_created` | 35 | 预约创建成功 |
| `rag_answer_viewed` | 45 | 用户查看规则问答 |
| `fallback_triggered` | 25 | 低置信度回退，比例不宜过低 |
| 合计 | 500 | 时间分布固定覆盖 14 天 |

事件链路要求：

- 一个 `appointment_created` 前应能找到同一 `session_id` 或 `request_id` 下的 `appointment_confirmed`。
- 一个 `appointment_confirmed` 前应有 `appointment_confirm_shown`。
- 点击率和预约转化率要合理，不要让所有曝光都转化。
- `room_id` 必须来自 `rooms.yaml`，`source` 使用 `AI_GUIDE` 或 `AI_CHAT`。

#### 4.6.5 检索评测条目配额

检索评测分房源召回、知识库召回和回退评测。固定目标为 500 条，用于 smoke test、调参和回归。

| 类型 | 目标数量 | 说明 |
|------|----------|------|
| `room_retrieval` | 300 | 找房语义召回、预算、区域、标签组合 |
| `kb_retrieval` | 150 | FAQ / rule / policy 召回 |
| `fallback_retrieval` | 50 | 无答案、越权、敏感问题、低置信度回退 |
| 合计 | 500 | 每条都要有 positive 和 hard negative，fallback 可只标注拒答原因 |

房源检索 case 分布：

- 预算类：60 条，覆盖“1500 内”“两千以内”“三千以内”“四千左右”“预算高一点”。
- 区域类：60 条，覆盖天河、越秀、海珠、番禺、白云和跨城市误问。
- 标签类：75 条，覆盖安静、近地铁、独卫、朝南、可月付、适合考研、采光好、家电齐全。
- 组合类：75 条，同时包含预算 + 区域 + 2 个以上标签。
- 边界类：30 条，覆盖预算刚好超限、区域无房、标签冲突、只说模糊偏好。

知识库检索 case 分布：

- `room_search`：20 条。
- `appointment`：22 条。
- `lease`：26 条。
- `payment`：22 条。
- `life`：20 条。
- `account`：18 条。
- `policy`：22 条。

fallback case 分布：

- 敏感信息请求：12 条，例如索要他人手机号、身份证、合同内容。
- 越权查询：12 条，例如查询他人预约、他人租约。
- 平台无规则：10 条，例如要求承诺租金不涨、要求绕过合同。
- 低信息量问题：8 条，例如“随便推荐”“哪个好”。
- 非租房问题：8 条，例如天气、股票、无关闲聊。

#### 4.6.6 Agent 对话评测条目配额

对话评测覆盖完整 Agent 流程，不等同于检索评测。

| 场景 | 目标数量 | 覆盖要求 |
|------|----------|----------|
| 单轮找房 | 70 | 明确预算、区域、标签 |
| 多轮补槽 | 60 | 缺预算、缺区域、缺时间、追问后推荐 |
| 预约确认 | 50 | 先确认后创建，不直接写操作 |
| 租约查询 | 40 | 当前用户租约、到期、续约、退租咨询 |
| KB 问答 | 50 | 押金、支付、宠物、实名、报修 |
| 安全拒答 / 回退 | 30 | 他人数据、敏感信息、无依据承诺 |
| 合计 | 300 | 每条包含输入、期望意图、期望工具、期望输出要点 |

#### 4.6.7 Prompt / few-shot 样例配额

few-shot 用于提升意图识别、槽位抽取和确认话术稳定性，不进入 Milvus。

| 样例类型 | 目标数量 | 说明 |
|----------|----------|------|
| 意图识别 | 90 | room_search、appointment、lease、kb_qa、fallback |
| 槽位抽取 | 80 | budget、district、payment_type、tags、appointment_time |
| 确认话术 | 45 | 预约创建、取消、敏感写操作 |
| 拒答 / 安全 | 50 | 他人数据、隐私、合同全文、支付账号 |
| 多轮续写 | 35 | 用户补充条件、改预算、换区域 |
| 合计 | 300 | 样例必须短、准、可回归 |

## 5. 数据生成策略

### 5.1 知识库 YAML 生成

优先补齐：

```text
account.yaml: 4 条
policy.yaml: 5 条
```

参考条目：

`account.yaml`

- `KB-ACCT-001` 注册与实名认证
- `KB-ACCT-002` 修改个人信息和绑定手机
- `KB-ACCT-003` 隐私和数据保护
- `KB-ACCT-004` 注销账号

`policy.yaml`

- `KB-POL-001` 同住人规则
- `KB-POL-002` 宠物政策
- `KB-POL-003` 装修和软装变更
- `KB-POL-004` 安全与禁止事项
- `KB-POL-005` 退租清算细则

生成时必须遵守 `_schema.yaml` 的 `doc_id` 前缀和枚举。

### 5.2 房源 mock 数据生成

生成房源时要覆盖不同组合。若已完成数据库公开字段审计，先从真实公开房源生成一批 `data_source=db_public` 的 YAML，再用 `generated_mock` 补齐缺失区域、价格段和标签组合。

区域：

- 天河区
- 越秀区
- 海珠区
- 番禺区
- 白云区
- 如真实库包含北京昌平区样本，可保留作为跨城市测试样本，但广州找房主流程不能只依赖昌平区数据。

租金：

- 1500 到 2200：低预算
- 2200 到 3200：主力预算
- 3200 到 4500：舒适型
- 4500 以上：高预算

标签：

- 安静
- 近地铁
- 独卫
- 朝南
- 可月付
- 适合考研
- 适合通勤
- 采光好
- 家电齐全
- 可短租

注意：

- `room_id` 唯一；
- `apartment_id` 可以多个房间复用；
- `thumbnail_url` 使用 MinIO 风格 URL 字符串即可，第一阶段不要求图片真实存在；
- 不生成手机号、身份证、门牌精确地址等敏感信息；
- 房源描述不要夸张营销，不写“全网最低”“保证满意”。

固定生成批次：

| 批次 | 数量 | `room_id` 规则 | 用途 |
|------|------|----------------|------|
| 真实公开样本 | 31 条 | 使用 `room_info.id` | 对齐数据库字段和真实价格分布 |
| 广州覆盖补齐 | 104 条 | 从 `3001` 开始 | 覆盖天河、越秀、海珠、番禺、白云 |
| 长尾偏好补齐 | 15 条 | 延续 mock ID | 覆盖可短租、考研、通勤、低预算、高预算等场景 |
| 合计 | 150 条 | 真实 ID 与 mock ID 分段 | 支撑第一阶段高质量推荐评测 |

真实公开样本的生成步骤：

1. 查询 `room_info` + `apartment_info`，只保留 `is_deleted=0` 且房间、公寓都已发布的记录。
2. 关联标签、设施、租期、支付方式、属性值。
3. 从 `address_detail` 抽取粗地址，去掉具体门牌号、楼栋号、经纬度。
4. 生成 `audience_summary`，只能基于价格、区域、标签、设施推断。
5. 输出到 `src/aptguide/knowledge/mock/rooms.yaml`，并标记 `data_source: db_public`。

生成补齐样本的规则：

- 不复用真实 `room_id`；
- 不复制真实完整地址；
- 区域、价格、标签组合要服务评测覆盖，不追求伪造真实库存；
- 如果基于真实房源做变体，必须保留 `data_source: generated_mock`，必要时用 `source_room_id` 记录参考来源；
- 补齐样本可以覆盖真实库暂时没有的天河、越秀、海珠、白云，用于测试 Agent 槽位和召回能力。

### 5.3 Query 生成

房源检索评测固定生成 300 条 query。不是每条房源平均生成 query，而是按预算、区域、标签、组合、边界五类覆盖；热门和边界房源可被多条 query 引用。

```text
预算 3000 内，想住天河区，最好安静一点
我准备考研，想找个不吵的房子
有没有地铁附近、可以月付的单间
想找朝南、有独卫、通勤方便的房源
```

知识库检索评测固定生成 150 条 query。不是每条知识库平均生成 query，而是按模块配额覆盖高频 FAQ、规则、政策和流程。

```text
提前退租押金怎么算
还没到期想退房会扣钱吗
预约看房怎么取消
可以养宠物吗
```

生成 query 时要保留口语化表达：

- “三千以内”
- “别太吵”
- “能不能月付”
- “离地铁近点”
- “我想考研”
- “明天下午能看房吗”

Query 与数据的一致性要求：

- 房源检索 query 的 `positive_ids` 必须来自 `rooms.yaml` 中真实存在的 `room_id`；
- 如果 query 指定区域，positive 房源必须在同一区域，除非该 case 明确测试回退或跨区推荐；
- 如果 query 指定预算上限，positive 房源租金不能超过预算；hard negative 可以是语义相似但超预算或不同区域；
- 如果 query 指定“近地铁、独卫、朝南、可月付”等硬偏好，positive 房源应包含对应标签或字段；
- “安静、适合考研、适合通勤”等软偏好可以由 `tags` 或 `audience_summary` 支撑；
- KB query 的 `positive_doc_ids` 必须来自 `knowledge/rules/*.yaml`，不能引用计划中尚未创建的 doc_id；
- 不生成依赖个人历史、租约、预约的 retrieval case；这些属于工具调用和对话评测。

### 5.4 数据一致性策略

生成数据时采用三层一致性：

1. **字段一致性**：YAML 字段和 Java DTO / Milvus schema 对齐，字段名、枚举、类型保持稳定。
2. **业务一致性**：租金、区域、标签、支付方式、租期不能互相矛盾，例如 `payment_types` 没有 `MONTHLY` 时，不应作为“可月付”的 positive。
3. **评测一致性**：评测集引用的 `room_id`、`doc_id` 必须真实存在，并且 hard negative 的错误原因可解释。

ID 命名规则：

| 数据 | 真实公开样本 | 生成样本 | 说明 |
|------|--------------|----------|------|
| `room_id` | 使用数据库 `room_info.id` | `3001` 起递增 | 不混用，避免误认为真实库存 |
| `apartment_id` | 使用数据库 `apartment_info.id` | `2001` 起递增 | 同一 mock 公寓可关联多间房 |
| `doc_id` | 不来自数据库 | 按模块前缀递增 | 由知识库维护 |
| `event_id` | 不来自数据库 | `evt-001` 起递增 | 行为事件第一阶段只做 mock |
| `case_id` | 不来自数据库 | `rag-room-001`、`rag-kb-001` | 评测集稳定引用 |

### 5.5 数据审计报告

每次从数据库抽取公开字段后，建议生成一个只含统计信息的审计报告，不提交原始 SQL 导出。建议路径：

```text
src/aptguide/knowledge/mock/room_audit_report.md
```

报告内容：

- 审计时间、数据库名、只读查询范围；
- 房源总数、已发布房源数、参与生成的房源数；
- 城市和区域分布；
- 租金区间分布；
- 标签、设施、支付方式、租期覆盖情况；
- 缺失字段统计，例如面积缺失、户型缺失、图片缺失；
- 被排除字段清单，例如电话、完整地址、经纬度、用户信息；
- 生成补齐策略说明。

### 5.6 完整项目数据生成顺序

不要只生成 mock 房源。后续 agent 应按下面顺序补齐数据资产：

1. **数据库公开字段审计**：只读核对房源、公寓、标签、设施、租期、支付方式，不导出敏感表。
2. **规则知识库**：补齐 7 个模块，固定生成 70 条。
3. **房源公开数据**：固定生成 150 条，其中 31 条真实公开样本优先，119 条用 mock 补齐，字段对齐 Java DTO。
4. **工具业务 mock 数据**：固定生成 300 条，覆盖预约、租约、浏览历史、收藏和 150 条房源详情缓存，但不进 Milvus。
5. **行为事件 mock 数据**：固定生成 500 条，覆盖曝光、点击、确认、创建、RAG 查看、回退。
6. **检索评测数据**：固定生成 500 条，覆盖房源检索、知识库检索和 fallback。
7. **Agent 对话评测数据**：固定生成 300 条，覆盖找房、预约、租约查询、FAQ、多轮确认和拒答。
8. **Prompt / few-shot 数据**：固定生成 300 条，覆盖意图、槽位、确认、拒答和多轮续写。
9. **第二阶段同步接口**：再把 mock 数据替换为 Java 工具和真实业务同步。

## 6. 入库脚本约定

建议脚本：

```text
scripts/audit_room_source.py
scripts/validate_kb.py
scripts/validate_mock_rooms.py
scripts/seed_kb.py
scripts/sync_room_vectors.py
scripts/generate_mock_rooms.py
scripts/generate_retrieval_cases.py
```

建议模块：

```text
src/aptguide/vector/chunker.py
src/aptguide/vector/embedding.py
src/aptguide/vector/kb_search.py
src/aptguide/vector/room_index.py
```

### 6.1 `audit_room_source.py`

只在离线数据准备阶段使用，负责从 `lease` 数据库或只读视图抽取公开房源字段，输出审计报告和可选中间 JSON。它不是 AptGuide 运行时依赖。

输入：

- MySQL 连接信息来自本地 `.env`，不提交到仓库；
- 只读账号优先；
- 默认只查询公开房源相关表。

输出：

```text
src/aptguide/knowledge/mock/room_audit_report.md
src/aptguide/knowledge/mock/room_source_public.json  # 可选，若提交必须已脱敏
```

校验：

- 不允许输出 `phone`、用户 ID、真实姓名、合同号、银行卡、身份证；
- `address_detail` 必须转换为粗地址后再输出；
- 输出文件必须包含 `data_source`，方便后续生成脚本区分真实公开样本和生成样本。

### 6.2 `validate_kb.py`

校验：

- YAML 可解析；
- `doc_id` 全局唯一；
- 字段齐全；
- 枚举合法；
- `content` 长度不超过 600；
- 不出现禁用词；
- 不出现手机号、身份证、银行卡等敏感模式。

### 6.3 `validate_mock_rooms.py`

校验：

- YAML 可解析；
- `room_id` 全局唯一；
- 必填字段齐全；
- `rent`、`area`、`lease_terms` 为正数；
- `payment_types` 只能使用 `MONTHLY`、`QUARTERLY`、`HALF_YEARLY`、`YEARLY`；
- `data_source` 只能使用 `db_public`、`generated_mock`、`manual_seed`；
- `data_source=generated_mock` 时，`room_id` 不得小于 3001；
- `data_source=db_public` 时，地址必须是粗粒度地址，不允许出现完整门牌、手机号、经纬度；
- 标签和设施不能超过合理长度，避免把长文案塞进标签；
- 禁止出现手机号、身份证、银行卡、合同号、内部 token。

### 6.4 `seed_kb.py`

流程：

```text
读取 rules/*.yaml
  → 校验
  → content 切分或直接作为 chunk
  → 调 embedding API
  → 写入 Milvus apt_rental_kb
```

写入字段参考 `06-Milvus知识库设计.md`：

- `doc_id`
- `doc_type`
- `module`
- `title`
- `content`
- `embedding`
- `updated_at`

### 6.5 `sync_room_vectors.py`

第一阶段：

```text
读取 knowledge/mock/rooms.yaml
  → 拼接房源 content
  → 调 embedding API
  → 写入 Milvus apt_room_vector
```

第二阶段：

```text
调用 lease internal sync API 或读取只读视图
  → 拼接房源 content
  → embedding
  → upsert Milvus
  → 下架房源置 is_release=false
```

入库前置条件：

- 必须先跑 `validate_mock_rooms.py` 或真实同步数据校验；
- `apt_room_vector` Collection 名称以配置 `MILVUS_ROOM_COLLECTION` 为准，不硬编码旧名；
- upsert 以 `room_id` 为去重键；
- 同步日志必须输出房源数量、embedding 模型名、向量维度、collection 名称；
- 如果 embedding 模型或维度变化，先重建 Collection，再全量同步。

## 7. Chunk 策略

知识库：

- 单条 `content` ≤ 600 字时，不再二次切分；
- 超过 600 字必须拆成多条规则，不建议依赖自动切分；
- chunk 里保留 `title` 前缀，增强检索：

```text
[退租清算细则] 提前退租时，费用清算以合同约定和门店实际审核为准...
```

房源：

- 每个房源 1 个 chunk；
- 不把图片二进制写入 chunk；
- 只写图片 URL 到房源卡片字段，不参与或少量参与向量化；
- 用标签、配套、适合人群增强语义。

## 8. Embedding 配置

第一阶段配置：

```text
EMBEDDING_PROVIDER=dashscope
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIM=1024
```

如果实际使用 OpenAI-compatible embedding，保持接口封装一致即可。

注意：

- Milvus Collection 的 `embedding` 维度必须和模型输出一致；
- 本项目默认使用阿里 DashScope `text-embedding-v4`，建议固定 `EMBEDDING_DIM=1024`；
- 更换 embedding 模型或维度后，需要重建或全量重写 Collection；
- 建议把模型名、维度、生成时间写入日志，便于排查。

## 9. 生成任务清单

给后续 Agent 的推荐执行顺序：

1. 阅读 `06-Milvus知识库设计.md`、本文件、`knowledge/rules/README.md`。
2. 先按第 3 节确认完整数据地图，不要只看 mock 房源。
3. 执行只读数据库公开字段审计，输出 `room_audit_report.md`。
4. 补齐 `account.yaml`、`policy.yaml`。
5. 创建 `knowledge/mock/rooms.yaml`，固定生成 150 条房源：31 条真实公开样本优先，119 条用 mock 补齐。
6. 实现或更新 `scripts/validate_kb.py` 和 `scripts/validate_mock_rooms.py`。
7. 创建工具 mock 数据，固定生成 300 条。
8. 创建行为事件 mock 数据，固定生成 500 条，用于 AptInsight 后续分析设计。
9. 创建 `evals/datasets/retrieval_cases.yaml`，固定生成 500 条评测用例，并校验所有 ID 引用存在。
10. 创建 `evals/datasets/dialog_cases.yaml`，固定生成 300 条对话评测。
11. 创建 Prompt / few-shot 样例，固定生成 300 条。
12. 实现 `vector/embedding.py` 和 `vector/chunker.py`。
13. 实现 `scripts/seed_kb.py`。
14. 实现 `scripts/sync_room_vectors.py`，读取 YAML 或 Java 同步 DTO，不在运行时直连 MySQL。
15. 跑检索 smoke test：FAQ top-3、房源 top-5。
16. 跑完整评测并输出报告：500 条检索评测、300 条对话评测。

## 10. 质量标准

第一阶段高质量标准：

- 数据审计报告说明真实库字段覆盖、缺失字段和排除字段；
- 知识库条目 = 70 条；
- mock 房源 = 150 条；
- `rooms.yaml` 每条房源必须包含 `data_source` 字段，真实公开样本和生成样本可区分；
- 工具业务 mock 数据 = 300 条，覆盖预约、租约、浏览历史、收藏和房源详情缓存；
- 行为事件 mock 数据 = 500 条，覆盖推荐曝光、点击、确认、成功、RAG 查看和回退；
- retrieval eval = 500 条；
- Agent 对话评测 = 300 条；
- Prompt / few-shot 样例 = 300 条；
- retrieval eval 中所有 `room_id`、`doc_id` 引用都能在 YAML 中找到；
- FAQ top-3 命中率 ≥ 90%；
- 房源推荐 hit@5 ≥ 82%；
- 不出现敏感信息；
- 低置信度问题能回退，不强答。

数据分布标准：

- 房源覆盖 5 个广州区域 + 10 条北京昌平跨城市样本；
- 房源覆盖 5 个租金段、10 个核心标签、10 个核心设施、4 种支付方式；
- 检索评测固定包含 300 条房源检索、150 条知识库检索、50 条 fallback；
- 对话评测固定包含 70 条单轮找房、60 条多轮补槽、50 条预约确认、40 条租约查询、50 条 KB 问答、30 条安全拒答 / 回退；
- 每次更换 embedding 模型或 chunk 策略都能输出对比报告。

## 11. 可直接使用的生成提示词

### 11.0 数据库公开字段审计

```text
你是 AptGuide 的离线数据审计 Agent。请只读核对 lease 数据库中的公开房源字段，为生成 rooms.yaml 做准备。

允许查询：
room_info, apartment_info, city_info, district_info, label_info, facility_info,
lease_term, payment_type, graph_info,
room_attr_value, room_label, room_facility, room_lease_term, room_payment_type。

禁止查询或导出：
user_info, lease_agreement, view_appointment, browsing_history,
手机号、身份证、银行卡、合同全文、后台账号、token。

输出：
1. 房源数量、已发布数量、城市区域分布、租金分布
2. 可映射字段和缺失字段
3. 标签、设施、支付方式、租期覆盖
4. 需要生成补齐的区域、价格段、标签组合
5. 不包含任何敏感值的 room_audit_report.md
```

### 11.1 生成知识库条目

```text
你是公寓租赁平台的运营知识库编辑。请根据以下主题生成 YAML 条目，必须遵守 schema：
- doc_id 前缀正确且唯一
- doc_type 只能是 faq/rule/guide/policy/flow
- module 只能是 room_search/appointment/lease/payment/life/account/policy
- title 不超过 30 字
- content 不超过 600 字
- 不出现手机号、身份证、银行卡、内部系统字段
- 不使用“一定、保证、绝对、包退、100%”
- 金额、时间、比例没有依据时，写“以合同约定或门店实际规则为准”

主题：
1. KB-ACCT-001 注册与实名认证
2. KB-ACCT-002 修改个人信息和绑定手机
3. KB-ACCT-003 隐私和数据保护
4. KB-ACCT-004 注销账号
```

### 11.2 生成 mock 房源

```text
请生成 150 条公寓房源 YAML 数据。字段包括：
room_id, room_number, apartment_id, apartment_name, city_id, city_name,
district_id, district_name, address, rent, area, layout, payment_types,
lease_terms, tags, facilities, thumbnail_url, is_release, is_appointable,
audience_summary。

要求：
- 按来源生成：db_public 31 条、generated_mock 104 条、manual_seed 15 条
- 按区域生成：天河区 30 条、越秀区 22 条、海珠区 26 条、番禺区 38 条、白云区 24 条、北京昌平区样本 10 条
- 按租金生成：800-1500 元 24 条、1500-2200 元 34 条、2200-3200 元 42 条、3200-4500 元 32 条、4500 元以上 18 条
- 标签覆盖安静、近地铁、独卫、朝南、可月付、适合考研、适合通勤、采光好、家电齐全、可短租
- 标签、设施、支付方式按文档 4.6.2 的固定覆盖数量分布
- 不生成真实手机号、身份证、精确门牌
- db_public 样本使用真实 room_info.id；generated_mock 和 manual_seed 样本从 3001 开始递增
- 每条数据增加 data_source，值为 db_public、generated_mock 或 manual_seed
```

如基于数据库公开样本生成，则改用：

```text
请基于给定的公开房源审计结果生成 rooms.yaml。

要求：
- 真实公开样本使用数据库 room_info.id 作为 room_id，data_source=db_public
- 地址只保留粗粒度区域，不输出完整门牌、电话、经纬度
- payment_types 统一转换为 MONTHLY、QUARTERLY、HALF_YEARLY、YEARLY
- lease_terms 只保留月份数字并去重
- 面积、户型优先来自属性表，缺失时可以生成合理默认值，但必须保持运营口径中性
- 如区域覆盖不足，用 3001 起的 generated_mock 补齐，不伪装成真实库存
```

### 11.3 生成工具业务 mock 数据

```text
请为 AptGuide 第一阶段生成 300 条工具业务 mock YAML 数据。

固定分布：
1. appointments: 40 条预约记录
2. leases: 30 条租约记录
3. browse_history: 60 条浏览历史
4. favorites: 20 条收藏记录
5. room_detail_cache: 150 条房源详情缓存，与 rooms.yaml 一一对应

要求：
- 只使用 mock user_id，例如 demo-user-001
- 不生成真实手机号、身份证、银行卡、合同全文
- appointment 需要包含 appointment_id, room_id, apartment_name, room_number, appointment_time, status
- lease 需要包含 lease_id, room_id, apartment_name, room_number, start_date, end_date, rent, payment_type, status
- browse_history 只包含 room_id 和 viewed_at 等最小字段
- 数据要能配合 rooms.yaml 中的 room_id 使用
```

### 11.4 生成行为事件 mock 数据

```text
请为 AptGuide 生成 500 条 AI 行为事件 mock YAML 数据，用于后续 AptInsight 分析。
字段包括：
event_id, session_id, request_id, event_type, room_id, source, occurred_at。

event_type 可选：
recommendation_exposed, room_card_clicked, appointment_confirm_shown,
appointment_confirmed, appointment_created, rag_answer_viewed, fallback_triggered。

要求：
- source 使用 AI_GUIDE 或 AI_CHAT
- room_id 必须来自 rooms.yaml
- 不包含用户手机号、身份证、真实姓名
- 时间分布在 2026-05-01 到 2026-05-14
- 事件类型数量按文档 4.6.4 分布；appointment_created 前应能找到对应的 confirm 事件链路
```

### 11.5 生成检索评测数据

```text
请基于给定房源 YAML 和知识库 YAML 生成 retrieval_cases.yaml。
每条包含：
id, task, query, positive_ids 或 positive_doc_ids, hard_negative_ids 或 hard_negative_doc_ids, expected。

要求：
- 固定生成 500 条：room_retrieval 300 条、kb_retrieval 150 条、fallback_retrieval 50 条
- 用户 query 要口语化
- 按文档 4.6.5 的预算、区域、标签、组合、边界、模块和 fallback 分类配额生成
- hard negative 要语义相似但答案不正确
- 不要生成超出房源字段或规则内容的需求
```

### 11.6 生成 Agent 对话评测数据

```text
请基于 rooms.yaml、tool_data.yaml 和 knowledge/rules/*.yaml 生成 dialog_cases.yaml。

固定生成 300 条：
- 单轮找房 70 条
- 多轮补槽 60 条
- 预约确认 50 条
- 租约查询 40 条
- KB 问答 50 条
- 安全拒答 / 回退 30 条

每条包含：
id, task, turns, expected_intent, expected_slots, expected_tools, expected_reply_points。

要求：
- 写操作必须体现先确认后执行
- 租约和预约查询只能使用 demo user 的 mock 数据
- 不生成真实手机号、身份证、合同全文、银行卡
- 对话要覆盖用户改预算、换区域、补时间、拒绝推荐、要求解释推荐理由等情况
```

### 11.7 生成 Prompt / few-shot 样例

```text
请为 AptGuide 生成 300 条 Prompt / few-shot YAML 样例。

固定分布：
- 意图识别 90 条
- 槽位抽取 80 条
- 确认话术 45 条
- 拒答 / 安全 50 条
- 多轮续写 35 条

要求：
- 每条样例短小明确，不写长篇解释
- 样例中的 room_id 必须来自 rooms.yaml
- 不包含真实个人信息
- 覆盖 room_search、appointment、lease、kb_qa、fallback
```
