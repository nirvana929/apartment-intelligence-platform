# 21 · RAG Final Implementation Scheme

> 相关文档：[RAG 升级设计](20-rag-retrieval-vector-mcp-evaluation-upgrade.md)、[Tool Registry](15-tool-registry-and-error-codes.md)、[Trace/Eval](10-trace-eval-and-observability.md)、[旧版 Milvus 设计](../../AptGuide/AptGuide文档/06-Milvus知识库设计.md)、[旧版 RAG 数据指南](../../AptGuide/AptGuide文档/09-RAG数据生成与入库指南.md)。

本文是 `AptGuide 2.0` RAG、向量库、知识库更新、检索评估和 MCP 暴露的最终实施方案。

它吸收旧版 AptGuide 中已经落地的数据库字段盘点、Milvus collection 设计和数据地图，但按 `AptGuide 2.0` 的原则升级：

- 运行时不注册 mock backend；
- Milvus 只做候选召回和知识依据检索，不做业务事实源；
- 房源事实以 `lease` 工具返回为准；
- 规则答案以审核后的 KB source 为准；
- 所有检索链路必须 trace、eval、benchmark；
- 知识库和房源索引必须支持增量同步、版本、回滚。

## 1. 升级检查结论

### 1.1 可以保留的旧版设计

| 旧版内容 | 结论 | 并入方式 |
| --- | --- | --- |
| Milvus 同时服务房源语义召回和规则知识库 RAG | 保留 | 继续使用两个 collection，但统一命名和 schema |
| Milvus 不是权威数据源 | 保留 | 明确写入房源链路的 lease validation gate |
| 数据地图：KB、房源公开信息、工具业务数据、会话状态、行为事件、评测数据分层 | 保留 | 作为最终数据治理边界 |
| 房源公开字段盘点 | 保留 | 用于 Java sync DTO 和房源画像文本设计 |
| 禁止手机号、身份证、合同全文、支付记录进入 Milvus | 保留并加强 | 加入 schema 校验、sync report 和 review gate |
| query-positive-negative retrieval eval | 保留 | 扩展为 RAGAS + business grader 双评估 |

### 1.2 必须升级的旧版设计

| 旧版做法 | 问题 | 最终版要求 |
| --- | --- | --- |
| 第一阶段允许 mock backend | 与 2.0 真实依赖原则冲突 | 运行时只注册 `lease`、`vector`、`memory`、`internal`；mock 只允许作离线评测材料 |
| `seed_kb.py` drop collection 后全量重建 | 不支持版本、回滚、线上稳定性 | 改为 content_hash 增量 upsert，删除改为 status=inactive |
| 房源 collection 名称 `room_index` | 与文档 `apt_room_vector` 不一致 | 统一为 `apt_room_vector` |
| KB collection 字段只有 id/content/category/title | 缺少 chunk、版本、状态、模块、hash | 升级为 `doc_id/chunk_id/doc_type/module/tags/version/status/content_hash` |
| 默认 IVF_FLAT | 中小规模召回质量不如 HNSW 稳定 | MVP 默认 HNSW；FLAT 作 baseline；IVF_FLAT/IVF_PQ 进入 benchmark |
| KB top-3 直接塞给 LLM | 属于 naive RAG | 加入 query rewrite、multi-recall、rerank、confidence gate、source-bound answer |
| 房源向量结果直接格式化为房源 | 可能展示过期或下架房源 | 必须用 `room_ids` 调 `lease room.search/detail` 二次校验 |

## 2. 最终目标

RAG 层先服务两个核心任务：

| 任务 | 检索目标 | 权威来源 | 最终输出 |
| --- | --- | --- | --- |
| 房源推荐 | 召回满足软偏好的候选 `room_id` | `lease` 工具 + Milvus 候选 | 真实可展示 room cards + 推荐理由 |
| 租房规则问答 | 召回可靠规则 chunk | 审核后的 KB collection | 带 source 的 grounded answer |

最终链路不是：

```text
query -> vector search -> stuff context -> answer
```

而是：

```text
message
  -> domain / task routing
  -> query understanding
  -> query rewrite
  -> multi-channel retrieval
  -> coarse ranking
  -> business validation
  -> fine ranking
  -> grounded response
  -> trace + eval
```

## 3. 数据分层和边界

| 数据域 | 来源 | 是否入 Milvus | 用途 | 关键约束 |
| --- | --- | --- | --- | --- |
| 规则知识库 | 审核后的 YAML / CMS / 运营后台 | 是 | KB QA | 必须有 `doc_id`、版本、审核状态 |
| 房源公开信息 | `lease` sync DTO | 是 | 语义召回 | 只存公开字段和粗粒度地址 |
| 房源详情事实 | `lease room.search/detail` | 否 | 展示和预约校验 | 每次回答前实时校验 |
| 预约、租约、浏览历史 | `lease` 用户工具 | 否 | 本人数据查询和 workflow | 只按后端身份查本人 |
| 会话状态 | Redis | 否 | 多轮指代、pending action | 不能作为业务事实源 |
| 长期画像 | SQLite/Postgres/MySQL | 否 | 偏好辅助 | 写入需用户确认 |
| 行为事件 | trace / lease event | 否 | 转化分析和 KB gap | 脱敏后给 AptInsight |
| 评测数据 | YAML / 脱敏日志 | 否 | eval / benchmark | 不参与运行时回答 |

禁止进入 Milvus：

- 手机号、身份证、邮箱、银行卡、支付账号；
- 合同全文、电子签文件、押金账户；
- 未脱敏预约、租约、浏览历史；
- 精确门牌、紧急联系人、后台账号、密钥；
- 未审核的 LLM 生成规则。

## 4. Collection 最终设计

### 4.1 `apt_room_vector`

房源 collection 只负责语义召回，最终展示必须经过 `lease` 校验。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `vector_id` | VARCHAR / INT64 PK | Milvus 主键 |
| `room_id` | INT64 scalar index | 业务房间 ID，去重键 |
| `apartment_id` | INT64 scalar index | 所属公寓 |
| `city_id` | INT32 scalar index | 城市 |
| `district_id` | INT32 scalar index | 区域 |
| `district_name` | VARCHAR | 展示和 debug |
| `rent` | INT32 scalar index | 月租金 |
| `payment_types` | VARCHAR / JSON string | `MONTHLY,QUARTERLY` |
| `lease_terms` | VARCHAR / JSON string | 月份列表 |
| `tags` | VARCHAR / JSON string | 房源标签 |
| `facilities` | VARCHAR / JSON string | 设施名称 |
| `profile_type` | VARCHAR | `room` / `apartment` / `audience`，MVP 可固定 `room` |
| `content` | VARCHAR | 向量化文本 |
| `content_hash` | VARCHAR scalar index | 增量同步判断 |
| `source_version` | INT64 | 房源同步版本 |
| `status` | VARCHAR scalar index | `active` / `inactive` |
| `embedding` | FLOAT_VECTOR | 向量 |
| `updated_at` | INT64 | 同步时间戳 |

MVP 可先一房一条 `room` profile；后续扩展为同一 `room_id` 多 profile 召回。

向量文本模板：

```text
[room][广州][番禺区][大学城附近]
房间 302，位于大学城南亭寓。月租 1800 元，支持月付、季付，租期 6、12 个月。
户型 1室1卫，面积 25 平方米，标签包括安静、可月付、近大学城、适合考研。
公寓配套包括空调、洗衣机、热水器、WIFI。
适合希望低预算、安静学习、通勤到大学城附近的租客。
```

### 4.2 `apt_rental_kb`

KB collection 负责租房规则问答依据检索。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `chunk_id` | VARCHAR PK | `KB-LEASE-005#01` |
| `doc_id` | VARCHAR scalar index | 规则文档 ID |
| `doc_type` | VARCHAR scalar index | `faq` / `rule` / `guide` / `policy` / `flow` |
| `module` | VARCHAR scalar index | `room_search` / `appointment` / `lease` / `payment` / `life` / `account` / `policy` |
| `title` | VARCHAR | 标题 |
| `tags` | VARCHAR / JSON string | 标签 |
| `content` | VARCHAR | chunk 正文 |
| `content_hash` | VARCHAR scalar index | 内容 hash |
| `version` | INT64 | 文档版本 |
| `release_id` | VARCHAR scalar index | KB 发布版本 |
| `status` | VARCHAR scalar index | `candidate` / `reviewed` / `indexed` / `evaluated` / `active` / `inactive` |
| `risk_level` | VARCHAR | `low` / `medium` / `high` |
| `embedding` | FLOAT_VECTOR | 向量 |
| `updated_at` | INT64 | 更新时间 |

向量文本模板：

```text
[lease][rule][押金退还规则][押金,退租,扣费][high]
押金退还以退租验房、费用结清和合同约定为前提...
```

## 5. Query Understanding 和 Rewrite

统一输出：

```json
{
  "raw_message": "找大学城南亭附近1500以内安静点的",
  "task": "room_search",
  "reference_resolution": null,
  "hard_filters": {
    "area_text": "大学城南亭",
    "max_rent": 1500
  },
  "soft_preferences": ["安静", "适合学习", "低噪音"],
  "retrieval_queries": [
    "大学城南亭附近 安静 适合学习 低噪音 房源",
    "番禺大学城 低预算 安静 单间",
    "适合考研学生 居住安静 配套便利 公寓"
  ],
  "risk_level": "low"
}
```

房源侧策略：

- 指代补全：从 `last_recommendations` 和 `active_task_state` 解析“第一个”“刚才那个”；
- 口语规范化：“别太吵”映射为“安静、低噪音”；
- multi-query 默认最多 3 条；
- 不用 HyDE 生成房源事实；
- hard filter 和 soft preference 必须分离。

KB 侧策略：

- 简单 FAQ：原 query + 规范化 query；
- 流程规则：原 query + step-back query；
- 召回低分：补 multi-query 或 HyDE 仅用于召回；
- 高风险规则：HyDE 不进入最终事实，只辅助找 source。

## 6. 房源推荐链路

```text
user message
  -> query understanding
  -> area.normalize
  -> exact structured search via lease
  -> vector recall via apt_room_vector
  -> merge room_ids
  -> coarse rank
  -> lease validation with room.search/detail
  -> fine rank
  -> response cards + recommendation reasons
```

### 6.1 多路召回

| 通道 | 工具 | 作用 |
| --- | --- | --- |
| exact search | `room.search` | 预算、区域、支付方式、租期等硬条件 |
| vector recall | `apt_room_vector` | 安静、通勤、考研、采光等软偏好 |
| metadata filter | Milvus filter | 上架、区域、租金粗过滤 |
| fallback recall | `room.search` + vector relaxed query | 放宽预算、区域或标签 |

### 6.2 粗排规则

- 按 `room_id` 去重；
- 剔除 `status != active`；
- 剔除硬条件明显不满足的候选；
- 保留 `recall_sources`、`semantic_score`、`matched_query`；
- 只把候选 `room_ids` 交给 `lease` 校验。

### 6.3 Lease 校验

校验输入：

```json
{
  "room_ids": [3001, 3005, 3008],
  "district_id": 1001,
  "max_rent": 1800,
  "payment_type": "MONTHLY",
  "limit": 10,
  "strategy": "vector_validated_search"
}
```

校验后为空时，不能展示向量原始结果，必须进入恢复：

```text
relax budget -> relax area -> nearby alternative -> handoff / explain no reliable result
```

### 6.4 精排公式

MVP 使用确定性打分：

```text
final_score =
  0.30 * semantic_score
  + 0.25 * budget_score
  + 0.20 * area_score
  + 0.15 * tag_score
  + 0.10 * availability_score
```

LLM 只生成推荐理由，不能改写房源事实字段。

## 7. KB 问答链路

```text
user question
  -> risk classification
  -> query rewrite / step-back / optional HyDE
  -> KB multi-recall
  -> merge + dedupe by chunk_id
  -> source rerank
  -> confidence gate
  -> grounded answer with sources
  -> KB gap logging
```

confidence gate：

| 场景 | 门槛 |
| --- | --- |
| 普通 FAQ | top source score 达阈值且 module 匹配 |
| 押金、合同、退租、违约金 | 提高阈值，必须命中 high-risk source |
| 低分或来源冲突 | 不强答，建议查看房源详情或联系门店 |
| 无 source | 记录 KB gap，不输出政策承诺 |

回答必须返回：

```json
{
  "sources": [
    {
      "doc_id": "KB-LEASE-005",
      "chunk_id": "KB-LEASE-005#01",
      "title": "押金退还规则",
      "module": "lease",
      "score": 0.82
    }
  ]
}
```

## 8. 同步和发布流程

### 8.1 KB 更新状态机

```text
candidate
  -> drafted
  -> reviewed
  -> approved
  -> indexed
  -> evaluated
  -> active
```

未审核内容不能进入 `active`。

### 8.2 KB 增量同步

```text
load docs
  -> validate schema
  -> compute content_hash
  -> detect added / changed / deleted
  -> embed changed chunks only
  -> upsert Milvus
  -> mark deleted chunks inactive
  -> run smoke eval
  -> write sync report
  -> promote release_id if eval passed
```

同步报告：

```json
{
  "sync_id": "kb-sync-20260511-001",
  "release_id": "20260511-233000",
  "added": 3,
  "updated": 5,
  "inactive": 1,
  "embedded": 8,
  "failed": 0,
  "eval_passed": true
}
```

### 8.3 房源同步

最终版禁止 AptGuide 运行时直连 MySQL。房源向量同步有两个合法来源：

1. `lease` 提供 `/internal/ai/tools/sync/rooms` 公开字段 DTO；
2. 离线只读审计脚本生成 sync 输入，但只用于开发核对，不能成为运行时依赖。

房源下架或删除：

- Milvus 中标记 `status=inactive`；
- 不立即硬删除，便于 trace 复盘；
- 后台清理任务按保留周期删除。

## 9. Milvus 选型和 Benchmark

MVP 默认：

```text
metric: COSINE
index: HNSW
M: 16
efConstruction: 200
efSearch: 64
```

必须保留 benchmark 矩阵：

| index | 用途 |
| --- | --- |
| HNSW | MVP 默认在线索引 |
| FLAT | 小数据精确 baseline |
| IVF_FLAT | 大数据低内存备选 |
| IVF_PQ | 更大规模或内存受限备选 |

每次报告记录：

- Milvus 版本；
- embedding model 和 dim；
- collection schema；
- index type 和参数；
- 数据量；
- top_k；
- filter 类型；
- hit@k、recall@k、MRR、nDCG@k；
- p50/p95/p99 latency。

分段耗时字段：

```text
rewrite_latency_ms
embedding_latency_ms
vector_search_latency_ms
merge_latency_ms
lease_validation_latency_ms
rerank_latency_ms
retrieval_total_latency_ms
```

报告路径：

```text
evals/reports/vector-benchmark-YYYY-MM-DD.json
evals/reports/vector-benchmark-YYYY-MM-DD.md
```

## 10. Trace 和 Eval

每次 retrieval 必须记录：

```json
{
  "event": "retrieval_finished",
  "payload": {
    "task": "room_search",
    "rewrite_count": 3,
    "collections": ["apt_room_vector"],
    "top_k": 50,
    "filters": {
      "district_id": 1001,
      "max_rent": 1800
    },
    "candidate_count": 42,
    "validated_count": 5,
    "latency": {
      "embedding_latency_ms": 80,
      "vector_search_latency_ms": 25,
      "lease_validation_latency_ms": 130,
      "rerank_latency_ms": 8
    }
  }
}
```

评估分两层：

| 层级 | 工具 | 评估内容 |
| --- | --- | --- |
| RAGAS | KB QA | context precision、context recall、faithfulness、response relevancy |
| business grader | AptGuide 业务 | source 命中、低置信度回退、房源事实、卡片文本一致、延迟 |

上线门槛：

| 能力 | 门槛 |
| --- | --- |
| KB source hit@3 | >= 90% |
| KB faithfulness | >= 0.9 |
| 高风险规则低置信度回退 | 100% |
| 房源 retrieval hit@5 | >= 85% |
| 房源 p95 vector search | <= 100ms |
| retrieval total p95 | <= 500ms，不含 LLM 生成 |
| card/text 一致率 | >= 95% |
| 编造房源/规则 | 0 |

## 11. MCP 封装

MCP 复用内部 Tool Registry，不单独实现业务访问层。

```text
MCP Server
  -> Tool Registry
      -> LeaseToolAdapter
      -> VectorAdapter
      -> MemoryAdapter
```

MVP 暴露：

| MCP 类型 | 名称 | 说明 |
| --- | --- | --- |
| Tool | `room.search` | 只读找房 |
| Tool | `room.detail` | 只读房源详情 |
| Tool | `kb.search` | 只读知识库检索 |
| Tool | `appointment.list_mine` | 需要用户身份 |
| Resource | `kb://rules/{doc_id}` | 审核后的规则 |
| Resource | `trace://session/{session_id}` | 脱敏 trace |
| Prompt | `aptguide_knowledge_answer` | KB grounded answer prompt |

第一阶段不暴露 `appointment.create`。如果后续暴露，仍必须走 `confirmation_id`、用户身份和权限校验。

## 12. 实施顺序

### Phase R0: Schema Freeze

- 固定 `apt_room_vector` 和 `apt_rental_kb` schema；
- 固定 `QueryUnderstandingResult`；
- 固定 `RetrievalTraceEvent`；
- 固定 `RetrievalEvalCase`。

### Phase R1: KB RAG

- 实现 KB chunk validate；
- 实现 content_hash 增量 sync；
- 实现 original / rewrite / step-back recall；
- 实现 source rerank 和 confidence gate；
- 加 RAGAS + business grader。

### Phase R2: Room Retrieval

- 实现房源 sync DTO；
- 实现房源画像文本；
- 实现 Milvus vector recall；
- 接入 `lease room.search/detail` 校验；
- 实现粗排、精排和恢复策略。

### Phase R3: Benchmark

- 实现 FLAT baseline；
- 实现 HNSW / IVF_FLAT / IVF_PQ 参数矩阵；
- 输出 json + md 报告；
- 把 p95 和 hit@k 加入上线门槛。

### Phase R4: KB Lifecycle

- 实现 candidate -> active 状态流；
- 实现 release_id；
- 实现 smoke eval gate；
- 实现 rollback。

### Phase R5: MCP

- 复用 Tool Registry；
- 暴露只读 tools/resources/prompts；
- 加权限、脱敏和 trace。

## 13. 面试表达

可以概括为：

```text
我把租房助手的 RAG 从 naive vector search 升级成了可评估的检索增强系统。
房源推荐和知识库问答分成两条链路：房源侧 Milvus 只负责软偏好候选召回，最终价格、上架和可预约状态全部由 Java lease 工具校验；规则问答侧要求 source-bound answer，低置信度不强答。
系统支持 query rewrite、multi-recall、coarse/fine ranking、HNSW/IVF/FLAT benchmark、RAGAS + 业务 grader，并且知识库从一次性 seed 升级为带 hash、版本、状态机、smoke eval 和 rollback 的持续更新流程。
MCP 层没有另起业务通道，而是复用内部 Tool Registry 受控暴露只读工具和脱敏资源。
```

## 14. 最终取舍

最终版选择：

- **不**做运行时 mock 成功路径；
- **不**让 LLM 生成房源事实或租赁政策；
- **不**把用户级数据向量化；
- **不**把 MCP 作为绕过内部权限的后门；
- **先**做 KB RAG 和房源检索闭环；
- **再**做 benchmark、生命周期和 MCP。

这套方案可以作为 AptGuide 2.0 RAG 方向的 source-of-truth。后续实现时，若 `20` 与本文冲突，以本文为准。
