# 20 · RAG Retrieval Vector MCP Evaluation Upgrade

> 相关文档：[Agent 架构](02-agent-framework-architecture.md)、[工具与集成契约](04-tool-and-integration-contract.md)、[Trace/Eval](10-trace-eval-and-observability.md)、[实施任务](12-implementation-task-plan.md)、[Anthropic Agent Eval](19-anthropic-agent-eval-methodology.md)。

本文档补齐 `AptGuide 2.0` 中 RAG、向量数据库、检索链路、RAGAS 评估、知识库持续更新和 MCP 封装的最新设计。

它不是旧版 `kb.search` 或 `room.search` 的局部优化，而是把找房推荐和租房规则问答升级为可评估、可调参、可持续更新的检索增强系统。

最终实施时以 [21-rag-final-implementation-scheme.md](21-rag-final-implementation-scheme.md) 为准；本文保留为专题设计背景和细节说明。

## 0. 文档关系

Claude / Codex 处理 RAG、向量库、MCP 或评估任务时，建议按下面关系读取：

| 需要确认的问题 | 读取文档 |
| --- | --- |
| 这个方案服务什么产品目标 | [01-product-requirements.md](01-product-requirements.md)、[03-domain-boundary-and-interaction-policy.md](03-domain-boundary-and-interaction-policy.md) |
| RAG 工具如何接入 Agent | [02-agent-framework-architecture.md](02-agent-framework-architecture.md)、[08-procedure-driven-agent-runtime.md](08-procedure-driven-agent-runtime.md) |
| `room.search`、`kb.search`、MCP tool 的 schema 和权限 | [04-tool-and-integration-contract.md](04-tool-and-integration-contract.md)、[15-tool-registry-and-error-codes.md](15-tool-registry-and-error-codes.md) |
| Trace 需要记录哪些 retrieval / ranking / eval 字段 | [10-trace-eval-and-observability.md](10-trace-eval-and-observability.md) |
| Eval case、grader 和 phase gate 怎么设计 | [17-prompt-and-eval-contract.md](17-prompt-and-eval-contract.md)、[19-anthropic-agent-eval-methodology.md](19-anthropic-agent-eval-methodology.md) |
| 代码应放到哪里、按什么顺序实现 | [12-implementation-task-plan.md](12-implementation-task-plan.md)、[18-implementation-readiness-checklist.md](18-implementation-readiness-checklist.md) |

## 1. 设计目标

`AptGuide 2.0` 的检索系统需要同时服务两类任务：

| 任务 | 目标 | 权威数据源 | 生成约束 |
| --- | --- | --- | --- |
| 房源推荐 | 从自然语言需求召回候选房源 | `lease` + Milvus 房源索引 | 不编造房源、价格、地址、可预约状态 |
| 租房规则问答 | 从规则知识库召回依据并回答 | Milvus KB + 审核后的规则文档 | 必须基于 source，低置信度不强答 |

核心目标：

- 支持 Query Rewrite，处理口语化、多轮指代和检索语义鸿沟；
- 支持多路召回、粗排、精排和低置信度回退；
- 用 Milvus 做向量召回，但不把 Milvus 当业务事实来源；
- 用 RAGAS 和业务 grader 双层评估 RAG 效果；
- 建立知识库动态更新、版本管理、回滚和回归评测流程；
- 用 MCP 把 Tool Registry 标准化暴露给外部 Agent，但不破坏内部确定性 workflow；
- 把向量库耗时、召回率、索引参数和数据规模纳入 benchmark。

## 2. RAG 范式

`AptGuide 2.0` 不采用 naive RAG：

```text
query -> vector search -> stuff context -> answer
```

推荐范式：

```text
User Message
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

### 2.1 房源推荐 RAG

房源推荐不是传统文档问答。Milvus 只负责根据软偏好召回候选，最终展示给用户的房源必须经过 `lease` 工具校验。

```text
用户需求
  -> 槽位抽取: 预算、区域、支付方式、租期、户型
  -> 软偏好抽取: 安静、通勤方便、适合考研、采光好
  -> query rewrite / expansion
  -> Milvus 语义召回 top-50
  -> metadata filter: 上架、区域、租金、支付方式
  -> lease room.search / room.detail 二次校验
  -> 规则精排
  -> 推荐理由生成
```

约束：

- 房源是否存在、是否上架、价格、可预约状态以 `lease` 返回为准；
- Milvus 返回的 `tags` 和 `description` 只能作为候选和解释辅助；
- 若 Java 校验后全部为空，必须进入检索恢复或人工建议，不能展示 Milvus 原始结果。

### 2.2 知识库问答 RAG

知识库问答以来源可信为第一优先级。

```text
用户问题
  -> query rewrite / HyDE / step-back
  -> KB vector recall top-k
  -> source rerank
  -> confidence gate
  -> grounded answer with sources
  -> KB gap logging
```

约束：

- 回答必须绑定 `doc_id` / `title` / `module`；
- 押金、合同、退租、违约金等高风险问题需要更高阈值；
- 低置信度时回答“当前没有可靠规则来源”，并建议查看房源详情或联系门店；
- 不允许把 LLM 常识当成租赁政策。

## 3. Query Rewrite

Query Rewrite 的目的不是把句子润色得更好看，而是弥合用户表达和索引文本之间的语义鸿沟。

### 3.1 改写类型

| 类型 | 解决问题 | 适用任务 | 示例 |
| --- | --- | --- | --- |
| 指代补全 | 多轮中的“这个”“第一个”“刚才那个” | 房源、预约 | “预约第一个” -> “预约上一轮推荐列表第 1 个房源” |
| 口语规范化 | 用户口语和文档/标签表述不一致 | 房源、KB | “别太吵” -> “安静、低噪音、适合休息” |
| Query 扩展 | 单一表达覆盖不足 | 房源、KB | “通勤方便” -> “近地铁、公交便利、到公司耗时短” |
| Multi-query | 多角度召回 | 房源、KB | 同一需求生成 3 个检索 query 后合并去重 |
| HyDE | 问句和答案文体差异 | KB | 先生成假设规则回答，再用假设答案向量检索 |
| Step-back | 具体问题需要背景规则 | KB | “押金被扣怎么办” -> “押金退还和扣除规则是什么” |

### 3.2 房源场景策略

房源搜索优先使用可控改写，不默认使用 HyDE。

推荐链路：

```text
raw_message
  -> resolve references from session state
  -> extract hard filters
  -> normalize soft preferences
  -> generate retrieval_queries[1..3]
```

示例：

```json
{
  "raw": "找大学城南亭附近1500以内安静点的",
  "hard_filters": {
    "area_text": "大学城南亭",
    "max_rent": 1500
  },
  "soft_preferences": ["安静", "适合学习", "低噪音"],
  "retrieval_queries": [
    "大学城南亭附近 安静 适合学习 低噪音 房源",
    "番禺大学城 通勤方便 安静 单间",
    "适合考研学生 居住安静 配套便利 公寓"
  ]
}
```

### 3.3 KB 场景策略

知识库问答可以按问题类型选择改写：

| 问题类型 | 策略 |
| --- | --- |
| 简单 FAQ | 直接改写 |
| 规则流程 | Step-back + 原始 query 双路召回 |
| 表述很口语 | 口语规范化 |
| 召回低分 | Multi-query 或 HyDE 二次召回 |
| 高风险政策 | 不用 HyDE 生成最终事实，只用来辅助召回 |

## 4. Chunking 和索引文本

### 4.1 知识库切分

租房规则知识库不应按固定 token 粗暴切分。优先规则：

1. 一条 FAQ / 规则 / 流程为一个 chunk；
2. 超过 600-800 中文字时按语义段落拆分；
3. 同一 `doc_id` 的多个 chunk 使用 `chunk_id` 串联；
4. chunk 前缀拼接标题、模块和标签，增强召回；
5. 每个 chunk 保存版本和 hash，便于增量更新和回滚。

推荐字段：

```json
{
  "doc_id": "KB-LEASE-005",
  "chunk_id": "KB-LEASE-005#01",
  "doc_type": "rule",
  "module": "lease",
  "title": "押金退还规则",
  "tags": ["押金", "退租", "扣费"],
  "content": "...",
  "content_hash": "sha256:...",
  "version": 3,
  "status": "active",
  "updated_at": "2026-05-11"
}
```

向量化文本：

```text
[lease][rule][押金退还规则][押金,退租,扣费]
正文内容...
```

### 4.2 房源索引文本

房源不是普通文档，不建议把所有字段拼成一段长文本。应拆成可控画像：

| 索引层 | 内容 | 用途 |
| --- | --- | --- |
| room profile | 房间号、租金、户型、面积、标签、支付方式 | 房源主召回 |
| apartment profile | 公寓位置、交通、配套、周边 | 区域和通勤召回 |
| audience profile | 适合学生、通勤族、考研、低预算 | 软偏好召回 |

MVP 可先合成一个 `content` 字段，但要保留这些来源字段，便于后续多向量或多 collection 设计。

## 5. 多路召回

### 5.1 房源召回

房源推荐使用混合召回：

```text
hard filters:
  city / district / rent / payment / status

semantic recall:
  soft preference vector search

structured recall:
  lease room.search exact filter

fallback recall:
  relax budget / relax area / nearby alternative
```

推荐流程：

```text
1. exact_search
2. vector_recall with metadata filter
3. merge room_ids and de-duplicate
4. lease validation
5. if empty -> relaxed_budget_search
6. if still empty -> nearby_alternative_search
```

### 5.2 KB 召回

知识库使用多路召回：

```text
original query recall
rewrite query recall
step-back query recall
optional HyDE recall
metadata filter by module / doc_type
merge + dedupe by chunk_id
```

后续增强可以加入 BM25 / keyword recall，用于处理专有词、政策编号、费用名称等精确词。

## 6. 粗排和精排

### 6.1 房源粗排

粗排目标是高召回，不追求最终顺序。

输入：

- Milvus top-50 / top-100；
- Java `room.search` 结构化结果；
- fallback strategy 结果。

粗排规则：

- 去重 `room_id`；
- 删除下架、不可预约、价格缺失房源；
- 硬条件不满足的房源直接剔除；
- 保留策略来源和原始 score。

### 6.2 房源精排

精排目标是排序和解释。

推荐打分：

```text
final_score =
  0.30 * semantic_score
  + 0.25 * budget_score
  + 0.20 * area_score
  + 0.15 * tag_score
  + 0.10 * availability_score
```

LLM 可以参与推荐理由生成，但不能修改房源事实字段。

精排输出：

```json
{
  "room_id": 3001,
  "rank": 1,
  "final_score": 0.86,
  "score_breakdown": {
    "semantic": 0.82,
    "budget": 1.0,
    "area": 0.9,
    "tags": 0.7,
    "availability": 1.0
  },
  "evidence": ["rent", "district", "tags", "payment_types"]
}
```

### 6.3 KB 粗排和精排

KB 粗排：

- Milvus top-k；
- module / doc_type filter；
- 合并 original / rewrite / step-back / HyDE 结果；
- 去重 `chunk_id`。

KB 精排：

- 优先命中 `title`、`tags`、`module`；
- 高风险问题提高阈值；
- 可选 cross-encoder 或 LLM rerank；
- 最终只把 top-3 到 top-5 source 传给生成器。

## 7. Milvus 算法和选型

Milvus 负责高维向量的近似最近邻检索。AptGuide 2.0 需要把索引算法作为可评估参数，而不是一次性写死。

### 7.1 起步选择

MVP 推荐：

```text
metric: COSINE
index: HNSW
M: 16
efConstruction: 200
efSearch: 64
```

原因：

- 当前房源和 KB 数据规模中小，HNSW 的召回质量和延迟更适合；
- HNSW 对 top-k 语义召回稳定，适合在线问答和推荐；
- 内存成本可接受。

### 7.2 扩展选择

| 索引 | 适用场景 | 优点 | 代价 |
| --- | --- | --- | --- |
| HNSW | 中小到较大规模，高召回要求 | 召回率高，查询快 | 内存占用较高 |
| IVF_FLAT | 数据量更大，需要控制内存 | 可调 nlist/nprobe | 召回低于 HNSW，需要调参 |
| IVF_PQ | 更大规模或内存受限 | 压缩向量，省内存 | 精度损失更明显 |
| FLAT | 小数据集或基准真值 | 精确召回 | 数据大时延迟高 |

Milvus benchmark 必须记录索引类型和参数，避免把参数差异误判为模型或 RAG 效果差异。

## 8. 向量数据库耗时和召回测试

### 8.1 分段耗时

不要只测 `/api/chat` 总耗时。必须拆开：

| 阶段 | 字段 |
| --- | --- |
| Query rewrite | `rewrite_latency_ms` |
| Embedding | `embedding_latency_ms` |
| Milvus search | `vector_search_latency_ms` |
| Merge / dedupe | `merge_latency_ms` |
| Lease validation | `lease_validation_latency_ms` |
| Rerank | `rerank_latency_ms` |
| Total retrieval | `retrieval_total_latency_ms` |

### 8.2 Benchmark 维度

测试矩阵：

| 维度 | 示例 |
| --- | --- |
| 数据规模 | 1k / 10k / 100k / 1M vectors |
| top_k | 5 / 10 / 20 / 50 / 100 |
| filter | 无 filter、区域 filter、租金 filter、组合 filter |
| index | HNSW、IVF_FLAT、IVF_PQ、FLAT baseline |
| efSearch / nprobe | 多参数对比 |
| query 类型 | 精确区域、软偏好、多条件、低召回问题 |

### 8.3 指标

| 指标 | 说明 |
| --- | --- |
| `hit@k` | top-k 是否包含任一正例 |
| `recall@k` | top-k 覆盖多少标注正例 |
| `MRR` | 第一个正确结果越靠前越好 |
| `nDCG@k` | 相关性分级排序质量 |
| `p50/p95/p99 latency` | 检索耗时分布 |
| `timeout_rate` | 超时比例 |
| `empty_result_rate` | 空结果比例 |

### 8.4 输出报告

建议输出：

```text
AptGuide 2.0/evals/reports/vector-benchmark-YYYY-MM-DD.json
AptGuide 2.0/evals/reports/vector-benchmark-YYYY-MM-DD.md
```

报告必须包含：

- Milvus 版本；
- collection schema；
- embedding model 和维度；
- index type 和参数；
- 数据量；
- case 数量；
- 各指标结果；
- 是否允许上线。

## 9. RAGAS 和业务评估

RAGAS 用来评估 RAG 的通用质量，业务 grader 用来评估租房场景的正确性。二者不能互相替代。

### 9.1 RAGAS 指标

知识库问答优先使用：

| 指标 | 作用 |
| --- | --- |
| Context Precision | 召回内容里有多少真正相关 |
| Context Recall | 应召回的依据是否被覆盖 |
| Faithfulness | 回答是否忠于上下文 |
| Response Relevancy | 回答是否回应用户问题 |

RAGAS 适合评估 KB QA，不直接评估预约安全、房源是否真实、用户权限等业务问题。

### 9.2 AptGuide 业务 grader

必须补充业务 grader：

| Grader | 评估内容 |
| --- | --- |
| `source_id_grader` | 是否命中预期 `doc_id` / `chunk_id` |
| `low_confidence_grader` | 低分时是否保守回退 |
| `policy_hallucination_grader` | 是否编造规则、费用、承诺 |
| `room_fact_grader` | 回复房源是否都来自工具结果 |
| `card_text_consistency_grader` | 文本和 cards 是否一致 |
| `latency_grader` | 检索和回答是否满足 p95 目标 |

### 9.3 数据集格式

```yaml
- id: kb-lease-deposit-001
  task: kb_qa
  question: 押金退还多久到账
  expected_sources:
    - KB-LEASE-005
  reference_answer: 押金退还以退租验房和费用结清为前提...
  risk_level: high
  expected_behavior:
    - cite_source
    - avoid_unverified_commitment
    - suggest_store_confirmation_when_needed
```

房源评估：

```yaml
- id: room-university-town-quiet-001
  task: room_retrieval
  query: 找大学城南亭附近1500以内安静点的房子
  positive_room_ids: [3001, 3005]
  hard_negative_room_ids: [3012]
  expected:
    hit_at_5: true
    must_use_recovery_if_empty: true
```

## 10. 知识库动态和持续更新

### 10.1 更新来源

知识库更新来源：

- 运营手动维护的规则 YAML / 后台；
- 客服人工接管后的高频问题；
- RAG 低置信度问题；
- 用户投诉和纠错；
- 法务或运营更新的租赁政策。

### 10.2 更新状态机

```text
candidate
  -> drafted
  -> reviewed
  -> approved
  -> indexed
  -> evaluated
  -> active
```

禁止未审核内容直接进入 active KB。

### 10.3 增量同步

从全量 `seed_kb.py` 升级为：

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
```

同步报告：

```json
{
  "sync_id": "kb-sync-20260511-001",
  "added": 3,
  "updated": 5,
  "deleted": 1,
  "embedded": 8,
  "failed": 0,
  "eval_passed": true
}
```

### 10.4 回滚

每次发布知识库都生成版本：

```text
kb_release_id = YYYYMMDD-HHMMSS
```

如果 smoke eval 或线上指标异常，回滚到上一版本，并保留失败 trace。

## 11. MCP 封装

MCP 不应替代 AptGuide 内部 Tool Registry。正确关系是：

```text
AptGuide Runtime
  -> Tool Registry
      -> LeaseToolAdapter
      -> VectorAdapter
      -> MemoryAdapter

MCP Server
  -> reuse Tool Registry
  -> expose selected tools / resources / prompts
```

### 11.1 暴露能力

MVP MCP Server 可以暴露：

| MCP 类型 | 名称 | 来源 |
| --- | --- | --- |
| Tool | `room.search` | Tool Registry |
| Tool | `room.detail` | Tool Registry |
| Tool | `kb.search` | Tool Registry |
| Tool | `appointment.list_mine` | Tool Registry |
| Resource | `kb://rules/{doc_id}` | KB store |
| Resource | `trace://session/{session_id}` | 脱敏 trace |
| Prompt | `aptguide_knowledge_answer` | Prompt registry |

写操作如 `appointment.create` 第一阶段不建议直接暴露给外部 MCP Client。若暴露，必须保留 confirmation workflow、用户身份和权限校验。

### 11.2 MCP 安全边界

- MCP tool 仍然走 Tool Registry 权限；
- 不暴露原始 MySQL；
- 不暴露未脱敏个人数据；
- 不允许外部 Agent 绕过 `confirmation_id`；
- trace resource 默认只读且脱敏；
- MCP 输出和内部 tool result 使用同一套 schema。

## 12. Eval 闭环

完整闭环：

```text
user query
  -> trace retrieval path
  -> RAGAS metrics
  -> business grader
  -> failed / low confidence cases
  -> KB gap report
  -> reviewed KB update
  -> Milvus resync
  -> vector benchmark
  -> regression eval
```

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

## 13. 实施任务补充

应在 [12-implementation-task-plan.md](12-implementation-task-plan.md) 后续拆出以下任务：

1. 新增 `retrieval/query_rewrite.py`，实现房源和 KB 的改写策略；
2. 新增 `retrieval/chunking.py`，统一 KB chunk 和房源画像构造；
3. 新增 `retrieval/ranking.py`，实现粗排、精排和 score breakdown；
4. 新增 `evals/runners/run_vector_benchmark.py`；
5. 新增 `evals/runners/run_ragas_kb.py`；
6. 新增 `scripts/sync_kb_incremental.py`；
7. 新增 `mcp/server.py`，复用 Tool Registry 暴露只读工具；
8. 更新 trace schema，记录 rewrite、recall、ranking、RAGAS 和 KB release 信息。

## 14. 面试表达

可以这样描述 AptGuide 2.0 的升级：

```text
我把 AptGuide 2.0 的 RAG 从“向量库搜一下再回答”升级成完整检索增强链路：
先做 Query Rewrite 和多路召回，再用 Milvus 进行语义粗排，结合 lease 工具做业务校验，最后通过规则精排和 grounded response 生成回答。
知识库侧接入 RAGAS 评估 faithfulness、context precision 和 response relevancy，同时保留业务 grader 检查 doc_id 命中、低置信度回退和政策幻觉。
向量库侧建立 benchmark，按 HNSW、IVF、top_k、filter 和数据规模测试 recall@k 与 p95 延迟。
工具层则通过 MCP Server 复用内部 Tool Registry，对外标准化暴露可控工具和只读资源。
```
