---
type: outcomes
status: active
---

# RAG 学习复盘：当前实现、局限与升级方向

> 日期：2026-05-12
> 范围：`backend/src/aptguide2/rag/`、`backend/src/aptguide2/tools/vector_adapter.py`

## 项目背景

当前 AptGuide 2.0 已经实现 FastAPI + RAG 检索 MVP。一次 `/chat` 请求会先进入 `run_pipeline()`，再通过 `understand_query()` 分流到：

- `room_search`：找房推荐；
- `kb_qa`：租房规则知识库问答；
- `fallback`：超范围或不适合回答的问题。

本轮学习重点不是新增功能，而是理解当前 RAG 代码为什么这样拆，以及哪些地方只是 MVP 方案，不应误认为生产级最佳实践。

## 我负责理解的部分

### RAG 主链路

当前主流程：

```text
POST /chat
  -> run_pipeline()
  -> understand_query()
  -> room_search / kb_qa / fallback
```

`run_pipeline()` 是编排器，只负责调度，不直接做检索或生成。

### room_search

`room_search` 的核心目标是找候选房源并排序：

```text
retrieve_rooms()
  -> build filters
  -> original query + generated queries
  -> vector_adapter.search_rooms()
  -> merge by room_id
  -> enrich_candidates_from_vector()
  -> rank_rooms()
```

关键理解：

- `retrieve_rooms()` 只负责多路召回候选房源；
- `enrich_candidates_from_vector()` 根据 `room_id` 补齐租金、区域、标签、设施等排序字段；
- `rank_rooms()` 用语义、预算、区域、标签、可用性做加权融合；
- 当前权重是人工经验值，不是模型训练结果。

### kb_qa

`kb_qa` 的核心目标是先找可靠证据，再决定能不能回答：

```text
retrieve_kb()
  -> original query
  -> normalized query
  -> step-back query
  -> vector_adapter.search_kb()
  -> merge by chunk_id
  -> source rerank
  -> check_confidence()
```

关键理解：

- `normalized query` 来自 `soft_preferences` 拼接，用于补充口语表达；
- `step-back query` 把具体问题提升到规则主题，例如“押金多久到账”提升为“租房押金退还规则 流程”；
- `_merge_by_chunk_id()` 用于合并多路召回中重复命中的同一个 KB chunk；
- `_source_rerank()` 在向量分基础上加入轻量业务规则；
- `check_confidence()` 是 KB 回答前的安全阀。

### confidence gate

`confidence.py` 的作用是防止弱证据进入 LLM 生成：

```text
low    -> top score >= 0.45
medium -> top score >= 0.55 + 前 3 个来源包含 lease/payment
high   -> top score >= 0.65 + 前 3 个来源存在 high risk 的 lease/payment 来源
```

它的设计重点不是“尽量回答”，而是“证据不够就不答”。这对押金、合同、违约金等高风险问题尤其重要。

### Milvus Adapter

`VectorAdapter` 位于 `tools/vector_adapter.py`，封装了 Milvus 细节：

- 创建房源和 KB collection；
- 创建 HNSW 向量索引；
- 创建标量索引用于 `rent`、`district_id`、`status` 等过滤；
- 写入房源和 KB embedding；
- 搜索房源向量和 KB chunk；
- 根据 `room_id` 批量取房源详情。

上层代码只调用 `search_rooms()` / `search_kb()`，不直接依赖 Milvus SDK，这是适配器模式。

## 核心难点

### 字符串匹配不是通用语义理解

当前 `query_understanding.py` 里大量使用：

```python
if keyword in message:
```

它覆盖了 MVP 常见样例，但存在明显问题：

- 用户换一种说法可能识别不到；
- 一词多义时容易误判；
- 关键词列表会越补越长；
- 规则顺序会影响结果；
- 无法表达置信度和意图强弱。

例如“押金低一点的房子有吗”可能被误判为 KB 问答，但用户真实意图也可能是找房。

### 当前 rerank 仍是规则补丁

房源排序中的：

```python
0.35 * semantic_score
+ 0.25 * budget_score
+ 0.20 * area_score
+ 0.15 * tag_score
+ 0.05 * availability_score
```

是人工经验权重，不是基于点击、收藏、预约或人工标注学习出来的排序模型。

KB 的 `_source_rerank()` 也依赖字符重合、模块关键词和固定加分值。这种方法可解释、易测试，但不够科学。

### 历史会话只预留了入口

`understand_query(message, previous_state=None)` 支持从 `previous_state` 继承预算等条件，但当前 `/chat` 没有真正把 `session_id` 对应的历史状态传入主流程。

因此当前是“函数支持多轮状态”，不是“系统已经实现完整会话记忆”。

## 解决方案与升级方向

### Query Understanding 升级

短期可以保留安全硬规则，但语义路由应升级为结构化输出：

```json
{
  "task": "kb_qa",
  "risk_level": "high",
  "topic": "deposit_refund",
  "normalized_query": "押金退还时间和流程",
  "step_back_query": "租房押金退还规则",
  "confidence": 0.91
}
```

推荐方向：

- 安全硬规则负责违法、隐私、保证性承诺等底线；
- LLM structured output 或分类模型负责 `task/risk/topic`；
- schema validator 校验输出合法性；
- 低置信度时追问或 fallback。

### 房源排序升级

当前加权排序可以作为 baseline，但后续应逐步引入：

- 更严格的硬过滤和降权规则；
- 离线 eval case 和人工标注 expected ranking；
- 曝光、点击、收藏、预约等行为日志；
- Learning to Rank，例如 LambdaMART、XGBoost Ranker；
- 成熟后再考虑深度排序模型或 cross-encoder reranker。

### KB rerank 升级

当前 `_source_rerank()` 应逐步替换为更强的语义 reranker：

```text
query: 用户问题
document: KB chunk title + content
-> reranker relevance score
```

可选方案：

- BM25 + 向量混合召回；
- bge-reranker / Jina reranker / Cohere Rerank；
- cross-encoder reranker；
- LLM judge 仅用于离线评测或高成本校验。

风险规则仍然要保留，但不应承担主要语义排序职责。

### 会话记忆升级

完整多轮应补齐：

```text
session_id
  -> load conversation state
  -> run_pipeline(previous_state=state)
  -> update hard_filters / soft_preferences / active task
  -> persist state
```

这样用户说“那番禺呢”时，系统才能继承上一轮预算、户型或偏好。

## 工程化保障

当前 MVP 中值得保留的工程设计：

- `PipelineResult` 统一内部结果模型；
- `VectorAdapter` 隔离 Milvus SDK；
- `confidence gate` 隔离检索与生成；
- 房源检索和 KB 检索分开实现；
- 多路召回后按 `room_id` / `chunk_id` 去重；
- RAG eval runner 和测试覆盖主链路。

后续改造时应避免直接重写所有逻辑，优先替换局部策略：

```text
_detect_task()                 -> structured router
_generate_retrieval_queries()  -> query rewrite model
_source_rerank()               -> semantic reranker
rank_rooms()                   -> calibrated ranking / LTR
```

## 最终学习成果

本轮学习后，对当前 RAG 的判断是：

- 当前实现是清晰、可测试、可演示的 MVP；
- `room_search` 和 `kb_qa` 的职责边界清楚；
- `confidence gate` 是防止 KB 弱证据生成的重要安全层；
- `VectorAdapter` 是隔离向量数据库的合理工程抽象；
- 但 query understanding、query rewrite、rerank 和排序权重仍以规则和人工经验为主；
- 生产级升级方向应是“规则安全兜底 + 结构化语义理解 + 语义 reranker + eval/行为数据闭环”。

## 面试讲法

可以这样概括：

> 我实现并复盘了一个租房领域 RAG MVP。房源侧采用多路向量召回、硬过滤和多维业务重排；知识库侧采用 multi-recall、step-back query、source rerank 和 confidence gate，只有证据足够时才让 LLM 基于来源回答。这个版本的优点是可控、可测试、能快速验证链路，但我也识别出 MVP 中大量规则匹配和人工权重的局限，并规划了向 structured router、semantic reranker、Learning to Rank 和 eval 数据闭环演进的路线。
