# 22 · RAG MVP Data And Implementation Plan

> 相关文档：[RAG 最终方案](21-rag-final-implementation-scheme.md)、[RAG 升级设计](20-rag-retrieval-vector-mcp-evaluation-upgrade.md)、[工具契约](04-tool-and-integration-contract.md)、[旧版 RAG 数据指南](../../AptGuide/AptGuide文档/09-RAG数据生成与入库指南.md)。

本文聚焦 `AptGuide 2.0` 的 RAG 初版落地：先做哪些能力、现有数据库数据是否够、哪些数据必须补、补的数据如何不破坏“真实工具校验”原则。

## 1. 结论

当前数据库数据 **不够支撑一个稳定可评测的 RAG 初版**。

旧版数据审计记录显示，当前真实库中非删除且已发布的公开房源约 31 条，且区域集中在北京昌平区和广州番禺区大学城附近。这个规模可以做 smoke test，但不足以覆盖 AptGuide 2.0 的核心演示场景：

- 广州多区域找房：天河、越秀、海珠、番禺、白云；
- 多预算段：1500 内、2000 内、3000 内、4500 以上；
- 软偏好：安静、近地铁、适合考研、通勤方便、采光好、家电齐全；
- 空结果恢复：放宽预算、放宽区域、附近替代；
- 检索评测：hit@k、MRR、nDCG、hard negative；
- 卡片文本一致性和 lease 二次校验。

因此初版必须补数据。但补数据不能只写入 Milvus，否则会违反 2.0 的核心原则：**Milvus 只召回候选，最终房源事实必须由 `lease` 工具确认。**

最终选择：

```text
真实库公开房源 31 条
  + lease 测试库 seed 房源 119 条
  + KB 规则补齐到 70 条
  + retrieval eval 先做 120 条 MVP 集合，后续扩到 500 条
```

## 2. 初版范围

RAG 初版只做两条闭环：

| 链路 | 初版目标 | 不做 |
| --- | --- | --- |
| KB QA | 能基于审核规则回答押金、退租、预约、支付、账号、社区规则问题 | 不做自动运营后台编辑 |
| 房源推荐 | 能通过语义召回 + lease 校验推荐真实可展示房源 | 不做长期画像、复杂个性化、跨会话推荐 |

初版成功标准：

- 用户能问规则，回答带 source；
- 用户能说“找大学城南亭附近 1500 以内安静点的”，系统能拆 hard filters 和 soft preferences；
- Milvus 能召回候选 `room_id`；
- `lease room.search/detail` 能校验候选；
- 空结果能解释并触发恢复；
- 每次检索有 trace；
- 有最小可跑 eval。

## 3. 数据是否够

### 3.1 房源数据

| 项 | 当前情况 | 判断 |
| --- | --- | --- |
| 有效公开房源 | 约 31 条 | 不够 |
| 广州主流程覆盖 | 主要集中番禺大学城 | 不够 |
| 天河 / 越秀 / 海珠 / 白云 | 覆盖不足 | 必须补 |
| 标签组合 | 不足以覆盖软偏好召回 | 必须补 |
| hard negative | 不足以做检索评测 | 必须补 |

初版最低要求：

| 数据层级 | 数量 | 用途 |
| --- | --- | --- |
| smoke | 30 条 | 快速验证服务链路 |
| MVP demo/eval | 150 条 | 初版推荐、恢复、评测 |
| 后续真实运营 | 来自 lease 真实库存 | 替换 seed 数据 |

### 3.2 知识库数据

旧版已有规则约 47 条或更早阶段 29 条，取决于当前分支文件是否已补齐 `account` 和 `policy`。初版建议固定到 70 条。

| 模块 | 目标数量 | 原因 |
| --- | --- | --- |
| room_search | 10 | 找房筛选、标签、相似推荐 |
| appointment | 10 | 预约、改期、取消、迟到、失败 |
| lease | 12 | 签约、续租、退租、押金、违约 |
| payment | 10 | 付款方式、账单、退款、发票 |
| life | 10 | 入住、报修、公共设施、噪音 |
| account | 8 | 登录、实名、隐私、注销 |
| policy | 10 | 宠物、同住人、安全、投诉 |

### 3.3 评测数据

完整目标可以是 500 条 retrieval cases，但初版不必一次写满。建议先做 120 条高质量集合：

| 类型 | MVP 数量 | 后续目标 |
| --- | --- | --- |
| room_retrieval | 70 | 300 |
| kb_retrieval | 35 | 150 |
| fallback_retrieval | 15 | 50 |

## 4. 造数原则

### 4.1 不能做的事

- 不能只在 Milvus 里造房源，然后绕过 `lease` 展示；
- 不能把生成房源伪装成真实库存；
- 不能写精确门牌、手机号、身份证、合同全文；
- 不能让生成规则直接进入 active KB；
- 不能让模型自由生成房源价格、可预约状态并展示给用户。

### 4.2 可以做的事

初版可以造三类数据：

| 数据 | 可以造吗 | 存放位置 | 约束 |
| --- | --- | --- | --- |
| lease 测试库 seed 房源 | 可以 | MySQL 测试库 / Java seed 脚本 | 标记为 demo/test 数据 |
| Milvus 房源向量 | 可以 | `apt_room_vector` | 必须来自 lease seed DTO |
| KB 规则 | 可以 | YAML / CMS -> `apt_rental_kb` | 必须 reviewed/approved 后 active |
| retrieval eval cases | 可以 | `evals/datasets/*.yaml` | positive IDs 必须存在于 seed 数据 |
| 工具业务样本 | 可以 | 测试库或录制样本 | 不进入 Milvus |

关键边界：

```text
房源生成数据如果要出现在用户可见推荐里：
  必须进入 lease 测试库
  -> 再由 lease sync DTO 输出
  -> 再写入 Milvus
  -> 检索时再由 lease 二次校验
```

## 5. 房源数据初版方案

### 5.1 数量和来源

| 来源 | 数量 | ID 规则 | 说明 |
| --- | --- | --- | --- |
| `db_public` | 31 | 使用真实 `room_info.id` | 当前测试库已有公开房源 |
| `generated_seed` | 104 | 使用 seed 分段 ID 或数据库自增后记录映射 | 补广州区域、价格段、标签 |
| `manual_boundary_seed` | 15 | seed 分段 | 专门做边界预算、区域空结果、冲突偏好 |
| 合计 | 150 | 不混淆来源 | 支撑初版检索和评测 |

`generated_seed` 与旧文档中的 `generated_mock` 含义不同：初版推荐链路中，它必须进入 `lease` 测试库，不能只存在 YAML。

### 5.2 区域配额

| 区域 | 数量 | 目的 |
| --- | --- | --- |
| 天河区 | 30 | 通勤、白领、近地铁 |
| 越秀区 | 22 | 老城区、学校、医院附近 |
| 海珠区 | 26 | 客村、琶洲、江南西 |
| 番禺区 | 38 | 大学城、低预算、考研 |
| 白云区 | 24 | 低预算、大面积、生活配套 |
| 北京昌平区 | 10 | 跨城市边界和旧数据兼容 |

### 5.3 租金配额

| 租金段 | 数量 |
| --- | --- |
| 800-1500 | 24 |
| 1500-2200 | 34 |
| 2200-3200 | 42 |
| 3200-4500 | 32 |
| 4500 以上 | 18 |

### 5.4 标签覆盖

| 标签 | 目标覆盖 |
| --- | --- |
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

每条房源建议 4-6 个标签。标签太多会让语义召回变噪。

### 5.5 房源 seed 字段

Java seed / DTO 至少提供：

```yaml
room_id: 3001
room_number: "302"
apartment_id: 2001
apartment_name: 大学城南亭寓
city_id: 4401
city_name: 广州
district_id: 1005
district_name: 番禺区
area_label: 大学城南亭附近
rent: 1800
area: 25
layout: 1室1卫
payment_types: [MONTHLY, QUARTERLY]
lease_terms: [6, 12]
tags: [安静, 可月付, 近大学城, 适合考研]
facilities: [空调, 洗衣机, 热水器, WIFI, 床, 书桌]
thumbnail_url: null
is_release: true
is_appointable: true
data_source: generated_seed
```

禁止字段：

- `phone`
- 精确门牌；
- 经纬度；
- 用户信息；
- 合同或支付字段。

## 6. KB 数据初版方案

### 6.1 条目格式

```yaml
- doc_id: KB-LEASE-005
  doc_type: rule
  module: lease
  title: 押金退还规则
  content: |
    押金退还以退租验房、费用结清和合同约定为前提。若存在未结清费用、设施损坏或违约事项，可能按合同和门店规则扣除相应费用。
    具体到账时间以门店处理和支付渠道为准。
  tags: [押金, 退租, 扣费]
  version: 1
  risk_level: high
  status: reviewed
  reviewed_by: ops
  updated_at: 2026-05-11
```

### 6.2 初版补齐顺序

1. 先补 `account` 和 `policy`，避免账号、隐私、宠物、同住人问题缺 source；
2. 再补 `lease` 和 `payment` 高风险规则；
3. 最后补 `room_search`、`appointment`、`life` 的高频 FAQ。

### 6.3 KB 入库规则

```text
YAML reviewed
  -> validate schema
  -> chunk by FAQ/rule/flow
  -> content_hash
  -> embed changed chunks
  -> upsert apt_rental_kb
  -> run KB smoke eval
  -> promote active
```

## 7. RAG 初版实现顺序

### Step 1: 数据审计和 seed 决策

产物：

- `room_data_audit_report.md`
- seed 房源来源清单；
- 真实 `room_id` 与 generated seed ID 分段规则。

判断标准：

- 当前真实库不足 100 条有效公开房源时，必须启用 seed 数据；
- 如果某区域少于 10 条，不用于该区域主演示，除非补 seed。

### Step 2: Java/lease 测试数据准备

产物：

- lease 测试库 seed SQL 或 Java seed runner；
- `/internal/ai/tools/sync/rooms` 返回公开字段 DTO；
- `/internal/ai/tools/room/search` 支持 `room_ids` 过滤。

验收：

- 150 条房源能通过 `room.search` 查询；
- 下架房源不会返回；
- `room_ids` 候选过滤有效；
- 不返回敏感字段。

### Step 3: Milvus 房源索引

产物：

- `apt_room_vector` collection；
- 房源画像文本构造器；
- 增量同步脚本；
- sync report。

验收：

- Milvus 中 active 房源数量与 lease sync DTO 一致；
- 每条向量都有 `room_id`、`content_hash`、`status`；
- 下架房源 status 变为 inactive。

### Step 4: KB 索引

产物：

- `apt_rental_kb` collection；
- KB validate/chunk/sync；
- KB release report。

验收：

- 70 条规则能形成 active chunks；
- source 中包含 `doc_id/chunk_id/module/title`；
- 高风险规则有 `risk_level=high`。

### Step 5: Query rewrite 和检索

产物：

- `QueryUnderstandingResult` schema；
- room rewrite；
- KB rewrite / step-back；
- multi-recall merge。

验收：

- “别太吵”能规范为安静/低噪音；
- “第一个”能从 last recommendations 解析；
- KB 高风险问题必须命中 source 或低置信度回退。

### Step 6: 校验、排序、回答

产物：

- 房源 coarse rank；
- lease validation gate；
- deterministic fine rank；
- KB confidence gate；
- grounded response composer。

验收：

- 向量召回但 lease 校验失败的房源不展示；
- 卡片价格、区域、标签来自 lease；
- KB 回答必须带 sources；
- 无 source 不编造规则。

### Step 7: 初版 eval

产物：

- `evals/datasets/rag_mvp_retrieval_cases.yaml`
- `evals/reports/rag-mvp-smoke-YYYY-MM-DD.md`

MVP eval 数量：

| 类型 | 数量 |
| --- | --- |
| room_retrieval | 70 |
| kb_retrieval | 35 |
| fallback_retrieval | 15 |

验收门槛：

| 指标 | MVP 门槛 |
| --- | --- |
| room hit@5 | >= 80% |
| KB source hit@3 | >= 85% |
| 高风险低置信度回退 | 100% |
| 编造房源/规则 | 0 |
| card/text 一致率 | >= 95% |

## 8. 初版文档产物

这次 RAG 初版要沉淀以下文档：

| 文档 | 目的 |
| --- | --- |
| `21-rag-final-implementation-scheme.md` | RAG 最终 source-of-truth |
| `22-rag-mvp-data-and-implementation-plan.md` | 初版实现和数据准备计划 |
| `room_data_audit_report.md` | 数据库公开房源审计结果 |
| `kb_seed_report.md` | KB 条目数量、模块覆盖、风险等级 |
| `vector_sync_report.md` | Milvus 同步数量、hash、失败项 |
| `rag_mvp_eval_report.md` | 初版检索和回答评测结果 |

## 9. 对外表达

可以这样解释初版取舍：

```text
初版 RAG 不是简单接 Milvus，而是先把数据基础补齐。现有测试库只有约 31 条有效公开房源，区域和标签覆盖不足，所以我们补了 lease 测试库 seed 数据，而不是只往向量库里造假数据。
房源链路坚持 Milvus 只做候选召回，最终价格、上架状态、可预约状态都由 lease 工具二次校验。KB 链路补齐 70 条审核规则，用 source-bound answer 和低置信度回退避免政策幻觉。
初版用 120 条 retrieval eval 先建立 smoke gate，后续扩展到 500 条 benchmark/eval。
```

## 10. 最终决定

RAG 初版要补数据，而且补数据必须进入正确层级：

- 房源推荐可见数据：补到 lease 测试库，再同步到 Milvus；
- 房源语义文本：由 lease DTO 构造，不能手写漂移；
- KB 数据：补 YAML/CMS reviewed 规则，再入 Milvus；
- eval 数据：可以生成，但只用于评测，不进入运行时；
- mock 工具业务数据：只允许离线测试或录制样本，不注册到 2.0 运行时。

这能同时满足演示效果、真实工具校验和后续上线可迁移性。
