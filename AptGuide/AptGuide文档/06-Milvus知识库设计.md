# 06 · Milvus 知识库设计

## 1. 用途

Milvus 在 AptGuide 中承担两类语义检索：

1. **房源语义召回**：用户模糊偏好（"安静、适合考研"）→ 候选 `room_id` 列表。
2. **租房知识库 RAG**：用户规则类提问（"退租怎么扣"）→ 召回 FAQ / 政策片段。

> Milvus **不是权威数据源**：召回的房源必须由 Java 工具接口按 `room_id` 二次校验真实状态（是否上架、租金、可预约）。

## 2. Collection 设计

### 2.1 `apt_room_vector`（房源语义索引）

| 字段 | 类型 | 主/索引 | 说明 |
|------|------|--------|------|
| `id` | INT64 (auto) | PK | Milvus 自增 |
| `room_id` | INT64 | scalar 索引 | 业务房间 ID（去重键） |
| `apartment_id` | INT64 | scalar 索引 | 所属公寓 |
| `city_id` | INT32 | scalar 索引 | 城市 |
| `district_id` | INT32 | scalar 索引 | 区域 |
| `rent` | INT32 | scalar 索引 | 月租金（元） |
| `payment_types` | VARCHAR | — | "MONTHLY,QUARTERLY" |
| `tags` | VARCHAR | — | 逗号拼接标签 |
| `is_release` | BOOL | scalar 索引 | 是否上架（同步时刷新） |
| `content` | VARCHAR | — | 用于向量化的房源文本 |
| `embedding` | FLOAT_VECTOR(dim) | HNSW | 向量 |
| `updated_at` | INT64 | — | 同步时间戳 |

**说明**

- `embedding` 维度由 `EMBEDDING_DIM` 决定（默认 1024）。
- `is_release / rent / district_id` 用作过滤条件，但 **真实校验仍由 Java 完成**。
- 房间下架时不立即删除 Milvus 行，由定时同步把 `is_release` 置 false，过期数据由清理任务异步删除。

**索引参数（建议起步）**

```text
metric: COSINE
index: HNSW { M=16, efConstruction=200 }
search efSearch=64
```

### 2.2 `apt_rental_kb`（租房知识库）

| 字段 | 类型 | 主/索引 | 说明 |
|------|------|--------|------|
| `id` | INT64 (auto) | PK | |
| `doc_id` | VARCHAR | scalar 索引 | 业务侧条目 ID（如 `KB-RULE-008`） |
| `doc_type` | VARCHAR | scalar 索引 | `faq` / `rule` / `guide` / `policy` / `flow` |
| `module` | VARCHAR | scalar 索引 | `room_search` / `appointment` / `lease` / `payment` / `account` |
| `title` | VARCHAR | — | 条目标题 |
| `content` | VARCHAR | — | 条目正文 |
| `embedding` | FLOAT_VECTOR(dim) | HNSW | 向量 |
| `updated_at` | INT64 | — | |

**约束**

- 条目长度建议 ≤ 600 字，超长需切分。
- `doc_id` 需运营侧唯一，便于回溯。
- 条目正文必须由运营审核，不允许直接放未审核的 LLM 生成内容。

## 3. 向量化文本构造

### 3.1 房源文本（用于 `apt_room_vector.content`）

```text
房间 {room_number}，位于 {apartment_name}，{city_name}{district_name}。
月租 {rent} 元，支持 {payment_types}。
{layout}，面积 {area} 平方米，{tags}。
公寓配套包括 {facilities}。
适合 {audience_summary}。
```

`audience_summary` 由运营侧维护或离线脚本根据标签生成（"预算 3000 内、希望通勤方便的租客"）。

### 3.2 知识库条目（用于 `apt_rental_kb.content`）

直接使用条目正文，并在前缀拼接 `[标题] ` 增强检索可识别性：

```text
[退租政策] 提前退租分两种情况：……
```

## 4. 检索策略

### 4.1 房源召回

```python
expr = (
  f'is_release == true and rent <= {max_rent}'
  + (f' and district_id == {district_id}' if district_id else '')
)
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 64}},
    limit=20,
    expr=expr,
    output_fields=["room_id", "apartment_id", "rent", "tags"],
)
```

返回 `room_ids` 后，再调用 `tools.room.search`（带 `room_ids` 参数）做精确过滤，最终保留 3~5 条。

### 4.2 知识库召回

```python
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 64}},
    limit=3,
    expr=f'doc_type in ["faq","rule","policy"]',
    output_fields=["doc_id", "title", "content", "module"],
)
```

最低相似度阈值（如 cosine ≥ 0.6）需通过评测调优。低于阈值时回退到"暂无明确答案"。

## 5. 同步方案

### 5.1 房源同步（`scripts/sync_room_vectors.py`）

**MVP（每小时全量增量同步）**

```text
1. 通过 lease 提供的 /internal/ai/tools/sync/rooms（或 DB only-read 视图）拉取上架房源
2. 对每条房源拼接 content
3. 调 embedding 模型生成向量
4. upsert 到 Milvus（按 room_id）
5. 把已下架的 room_id 在 Milvus 中置 is_release=false
```

**第二版（事件驱动）**

由 lease 在房源上架 / 下架 / 改价时发出消息（Kafka / RocketMQ），AptGuide 订阅后增量更新。

### 5.2 知识库同步（`scripts/seed_kb.py`）

- 知识库条目以 Markdown / YAML 文件形式维护在 `src/aptguide/knowledge/rules/`。
- 运营审核后提 PR 合并；CI 触发 `seed_kb` 重新写入 Milvus。
- 每次同步前清空旧条目（按 `doc_id`），保证可重放。

## 6. 安全约束

Milvus 内只存以下内容：

- ✅ 公开房源描述、户型、配套、租金区间
- ✅ 公寓介绍、地址、配套
- ✅ 经审核的 FAQ / 规则 / 政策

**禁止写入**：

- ❌ 用户手机号、身份证、邮箱、住址
- ❌ 合同 / 协议全文、电子签
- ❌ 支付记录、银行卡号、押金账户
- ❌ 后台管理员账号、密钥

任何对 Milvus 写入的离线脚本都必须经过同事 review，不允许在主进程中实时写入用户数据。

## 7. 评测要点

- **召回率**：模糊偏好下 top-20 召回中包含人工标注"应推荐"房源 ≥ 80%。
- **精确率**：经过 Java 二次校验后的 top-5 中 ≥ 80% 与人工标注一致。
- **KB 命中率**：FAQ 评测集中 top-3 召回相关条目 ≥ 90%。
- **回退率**：阈值之下回退到"暂无明确答案"的比例可被监控。

具体指标见 `07-测试验收方案.md`。
