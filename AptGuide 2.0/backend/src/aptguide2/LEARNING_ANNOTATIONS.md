# AptGuide 2.0 代码学习注解

> 本文件为项目核心代码生成学习注解，帮助理解 RAG 系统的设计模式、Python 工程实践和关键概念。

---

## 目录

1. [项目架构总览](#1-项目架构总览)
2. [API 层：FastAPI + 依赖注入](#2-api-层)
3. [配置管理：Pydantic Settings](#3-配置管理)
4. [RAG 流程编排](#4-rag-流程编排)
5. [查询理解：确定性解析](#5-查询理解)
6. [房源检索：多路向量召回](#6-房源检索)
7. [知识库召回 + 置信度门控](#7-知识库召回--置信度门控)
8. [多维精排](#8-多维精排)
9. [安全阀机制](#9-安全阀机制)
10. [向量文本构建](#10-向量文本构建)
11. [Milvus 适配器](#11-milvus-适配器)
12. [跨语言 HTTP 适配](#12-跨语言-http-适配)
13. [可观测性与隐私保护](#13-可观测性与隐私保护)
14. [设计模式速查表](#14-设计模式速查表)

---

## 1. 项目架构总览

```
用户消息 → API(app.py) → 流程编排(pipeline.py)
                            ├── 查询理解 (确定性解析，不用大模型)
                            ├── 检索 (多路向量召回)
                            │   ├── 房源检索 → 向量数据库
                            │   └── 知识库检索 → 向量数据库
                            ├── 精排 (多维评分)
                            └── 安全阀 (置信度检查)
                                └── 大模型生成回答 (仅知识库问答且置信度足够时)
```

**核心设计思想**：把 RAG 拆成"理解 → 检索 → 排序 → 生成"四个阶段，每个阶段可独立测试和优化。

**学习要点**：
- RAG 不是"直接问大模型"，而是先检索再生成，减少幻觉
- 确定性解析（规则）和语义检索（向量）互补：规则处理精确条件，向量处理模糊偏好
- 高风险问题有额外保护层，不盲目信任检索结果

---

## 2. API 层

### `api/app.py` — FastAPI 入口

```python
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    adapter = get_vector_adapter()   # 获取向量数据库连接
    embed_fn = get_embed_fn()        # 获取文本向量化函数
    result = run_pipeline(message=req.message, vector_adapter=adapter, embed_fn=embed_fn)
    return _build_response(result)
```

**学习要点**：

1. **同步端点**：`def chat()` 而非 `async def`。FastAPI 会自动在线程池中运行同步函数，避免阻塞事件循环。当函数内部没有 `await` 时，用同步更简单。

2. **响应模型校验**：FastAPI 会自动用 Pydantic 模型校验输出，不合格的数据会在序列化时报错，相当于"输出守门员"。

3. **关注点分离**：`_build_response()` 负责把流程结果转成 API 响应，`_generate_room_message()` 和 `_generate_kb_answer()` 负责生成人类可读的消息。这样 API 层只做"调度 + 格式转换"，不包含业务逻辑。

### `api/schemas.py` — Pydantic 数据模型

```python
class RoomResponse(BaseModel):
    room_id: int
    apartment_name: str = ""
    rent: int = 0
    tags: list[str] = Field(default_factory=list)
```

**学习要点**：

1. **Field(default_factory=list)**：对于可变类型（列表、字典），必须用 `default_factory` 而非 `default=[]`。如果用 `default=[]`，所有实例会共享同一个列表对象——这是 Python 常见的"可变默认参数"陷阱。

2. **Literal 类型**：`task: Literal["room_search", "kb_qa", "fallback"]` 限定了字段只能取这三个值，比 `str` 更精确，IDE 和 Pydantic 都能做静态检查。

### `api/deps.py` — 依赖注入 + 单例模式

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()

@lru_cache
def get_vector_adapter() -> VectorAdapter:
    s = get_settings()
    return VectorAdapter(uri=s.milvus_uri, token=s.milvus_token, dim=s.embedding_dim)
```

**学习要点**：

1. **用 lru_cache 实现单例**：`lru_cache` 会缓存函数返回值，后续调用直接返回缓存对象。这里用来保证全局只有一个 Settings 和 VectorAdapter 实例，比手动写单例类更 Pythonic。

2. **闭包做工厂**：`get_embed_fn()` 返回一个闭包 `embed(text)`，闭包捕获了 `client` 和 `settings`。调用方只需要传一个 `text -> list[float]` 的函数，不需要知道底层用的什么向量化服务。

3. **SecretStr**：API 密钥用 `SecretStr` 而非 `str`，打印时自动显示 `****`，防止日志泄露密钥。

---

## 3. 配置管理

### `core/config.py` — Pydantic Settings

```python
class Settings(BaseSettings):
    milvus_uri: str = "http://localhost:19530"
    embedding_api_key: SecretStr = SecretStr("")
    llm_model: str = "gpt-4o-mini"

    model_config = {"env_prefix": "APTGUIDE_", "env_file": ".env"}
```

**学习要点**：

1. **环境变量前缀**：所有环境变量以 `APTGUIDE_` 开头，例如 `APTGUIDE_MILVUS_URI`。这避免了和其他项目的环境变量冲突。

2. **优先级链**：Pydantic Settings 的加载顺序是：构造函数参数 > 环境变量 > `.env` 文件 > 模型默认值。生产环境通常用环境变量，开发环境用 `.env` 文件。

3. **类型自动转换**：即使环境变量是字符串 `"1536"`，Pydantic 也会自动转成 `int`。这是相比 `os.environ.get()` 的主要优势。

---

## 4. RAG 流程编排

### `rag/pipeline.py` — 流程编排

```python
def run_pipeline(message, vector_adapter, embed_fn, ...) -> PipelineResult:
    # 第一步：确定性解析（不用大模型）
    qr = understand_query(message, previous_state)

    # 第二步：按任务类型路由到不同处理链路
    if qr.task == "room_search":
        return _handle_room_search(qr, vector_adapter, embed_fn, top_n_rooms)
    elif qr.task == "kb_qa":
        return _handle_kb_qa(qr, vector_adapter, embed_fn)
    else:
        return _handle_fallback(qr)
```

**学习要点**：

1. **编排器模式**：`run_pipeline` 是编排器，它不关心每个阶段的具体实现，只负责"按顺序调用、传递数据、处理结果"。每个阶段（`_handle_*`）是独立的，可以单独测试。

2. **任务路由**：先判断任务类型，再走不同链路。这比"所有请求都走同一条链路"更高效——找房不需要查知识库，问答不需要精排房源。

3. **统一出口**：无论走哪条链路，最终都返回 `PipelineResult`。API 层只需要根据 `task` 字段决定怎么序列化，不需要知道内部细节。

---

## 5. 查询理解

### `rag/query_understanding.py` — 确定性查询解析

这是整个项目中**最有教学价值的文件**。它展示了如何用纯规则（不用大模型）把自然语言拆成结构化数据。

```python
def understand_query(message: str, previous_state: dict | None = None) -> QueryUnderstandingResult:
    task = _detect_task(message)           # 判断任务类型
    hard_filters = _extract_budget(message) # 提取硬约束
    soft_preferences = _extract_preferences(message) # 提取软偏好
    risk_level = _detect_risk(message)     # 检测风险等级
    retrieval_queries = _generate_retrieval_queries(hard_filters, soft_preferences, task)
    return QueryUnderstandingResult(...)
```

**学习要点**：

1. **硬过滤 vs 软偏好**：
   - **硬过滤（hard_filters）**：预算、区域——可以直接用 `WHERE rent <= 1500` 过滤
   - **软偏好（soft_preferences）**：安静、近地铁——不适合精确过滤，否则会漏掉"标签写的是'低噪音'但没写'安静'"的房源

2. **多轮对话状态继承**：
   ```python
   if max_rent is not None:
       hard_filters["max_rent"] = max_rent      # 用户明确说了预算
   elif _is_budget_clearing(message):
       hard_filters["max_rent"] = None           # 用户说"预算不限"
   elif "max_rent" in previous_state:
       hard_filters["max_rent"] = previous_state["max_rent"]  # 继承上一轮
   ```
   这是对话系统中常见的"条件继承"模式：用户说"那番禺呢"时，系统保留上一轮的预算约束。

3. **最长匹配优先**：
   ```python
   sorted_areas = sorted(AREA_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True)
   ```
   "大学城南亭"比"大学城"和"南亭"都更精确，所以先匹配长词，避免"大学城南亭"被拆成两个不精确的区域。

4. **查询改写（多路检索）**：
   - 查询 1：用户原始条件 → "番禺区 1500以内 安静 房源"
   - 查询 2：结构化检索词 → "番禺区 低预算 安静 单间"
   - 查询 3：生活方式画像 → "适合考研学生 安静 公寓"
   
   多路召回的目的是：同一个用户问题从不同角度去查向量库，减少单一表达导致的漏召回。

5. **风险等级检测**：
   ```python
   def _detect_risk(message: str) -> str:
       high_risk = ["押金", "违约金", "退租", "合同", "赔偿"]
       medium_risk = ["投诉", "纠纷", "法律"]
   ```
   高风险问题（押金、合同）需要更高置信度才能回答，避免给出错误的法律/财务建议。

---

## 6. 房源检索

### `rag/room_retrieval.py` — 多路向量召回

```python
def retrieve_rooms(query_result, vector_adapter, embed_fn, top_k=30) -> list[RoomCandidate]:
    filters = _build_filters(query_result)  # 硬条件 → 向量数据库过滤表达式
    recall_queries = [...]                  # 多路召回查询

    seen_rooms: dict[int, RoomCandidate] = {}
    for query_text, recall_source in recall_queries:
        vector = embed_fn(query_text)       # 文本 → 向量
        results = vector_adapter.search_rooms(vector=vector, filters=filters, top_k=top_k)
        for r in results:
            room_id = r["room_id"]
            if room_id in seen_rooms:
                if distance > seen_rooms[room_id].semantic_score:
                    seen_rooms[room_id].semantic_score = distance  # 保留最高分
            else:
                seen_rooms[room_id] = RoomCandidate(...)
```

**学习要点**：

1. **"先过滤、再向量"**：向量数据库的过滤表达式 `rent <= 1500 AND district_id == 4` 在向量搜索之前执行，缩小候选池。这比"先向量搜索全部、再在应用层过滤"更高效。

2. **多路去重策略**：用 `dict[room_id, RoomCandidate]` 去重，同一房源被多路命中时保留最高语义分。这是 RAG 中常见的"召回合并"模式。

3. **延迟加载详情**：检索阶段只存轻量信息（ID + 分数），排序阶段再批量取详情。这是"延迟加载"思想——不在召回阶段就加载所有字段，减少数据传输量。

---

## 7. 知识库召回 + 置信度门控

### `rag/kb_retrieval.py` — 知识库召回

```python
def retrieve_kb(query_result, vector_adapter, embed_fn, top_k=10):
    queries = _build_recall_queries(query_result)  # 原始 + 归一化 + 上推查询
    all_results = []
    seen_chunk_ids = set()
    for query_text, recall_source in queries:
        vector = embed_fn(query_text)
        results = vector_adapter.search_kb(vector=vector, ...)
        for r in results:
            if r["chunk_id"] not in seen_chunk_ids:
                seen_chunk_ids.add(r["chunk_id"])
                all_results.append(r)

    merged = _merge_by_chunk_id(all_results)      # 合并同一分块的多次命中
    reranked = _source_rerank(merged, query_result) # 业务规则重排
    sources = [KBSource(...) for r in reranked]
    is_confident = check_confidence(sources, query_result.risk_level)
    return sources, is_confident
```

**学习要点**：

1. **上推查询（Step-back Query）**：把具体问题上提到规则层面。例如"押金多久到账"不只查"多久到账"，还查"押金退还规则/流程"。这是 RAG 中的"问题抽象化"技巧，适合检索结构化的规则文档。

2. **来源重排**：
   ```python
   # 字面重合加分：向量相似度的补充信号
   overlap = len(set(query) & set(title))
   if overlap >= 3: score += 0.08
   # 模块匹配加分：租赁问题优先匹配 lease 模块
   if module == "lease" and "押金" in query: score += 0.06
   ```
   向量相似度是"语义像不像"，字面重合是"关键词在不在"，两者互补。

3. **置信度门控**：检索完不是直接生成回答，而是先检查"证据够不够可靠"。高风险问题（押金、合同）要求更高分数和更强来源。

---

## 8. 多维精排

### `rag/ranking.py` — 多维精排

```python
W_SEMANTIC = 0.35    # 语义匹配度
W_BUDGET = 0.25      # 预算契合度
W_AREA = 0.20        # 区域匹配度
W_TAG = 0.15         # 标签偏好匹配
W_AVAILABILITY = 0.05 # 可用性

final_score = W_SEMANTIC * semantic_score + W_BUDGET * budget_score + ...
```

**学习要点**：

1. **加权融合**：RAG 推荐系统常见做法是"召回粗排 + 业务精排"。向量召回解决"语义上像不像"，精排解决"业务上合不合适"。

2. **预算评分的梯度设计**：
   ```python
   ratio = rent / max_rent
   if ratio <= 0.7:   return 1.0   # 远低于预算，性价比高
   if ratio <= 0.9:   return 0.85  # 合理范围
   if ratio <= 1.0:   return 0.65  # 刚好在预算内
   if ratio <= 1.1:   return 0.3   # 略超预算
   return 0.0                      # 远超预算
   ```
   不是简单的"是/否"判断，而是用连续分数表达"契合程度"，避免边界值附近的排序不稳定。

3. **推荐理由生成**：`_build_recommendation_reason()` 把各维度分数转成人类可读的中文解释，例如"租金1200元，性价比高，位于番禺区，符合偏好：安静、近地铁"。

---

## 9. 安全阀机制

### `rag/confidence.py` — 置信度门控

```python
THRESHOLDS = {"low": 0.45, "medium": 0.55, "high": 0.65}

def check_confidence(sources, risk_level) -> bool:
    threshold = THRESHOLDS[risk_level]
    if top.score < threshold:
        return False
    if risk_level == "medium":
        return any(s.module in HIGH_RISK_MODULES for s in sources[:3])
    if risk_level == "high":
        return any(s.risk_level == "high" and s.module in HIGH_RISK_MODULES for s in sources[:3])
```

**学习要点**：

1. **分级阈值**：风险越高，最低相似度阈值越高。低风险问题 0.45 就够了，高风险问题需要 0.65 以上。

2. **来源约束**：高风险问题不仅要求分数高，还要求来源本身标记为 `risk_level=high` 且来自 `lease`/`payment` 模块。这防止了"低风险泛文档误答高风险问题"。

3. **安全降级**：置信度不够时不是报错，而是返回友好的兜底消息，引导用户联系门店或查看合同。

---

## 10. 向量文本构建

### `rag/chunking.py` — 分块与文本构建

```python
def build_kb_chunks(rule: dict, release_id: str) -> list[KBChunk]:
    if len(content) > 800:
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
    else:
        paragraphs = [content]

    for i, paragraph in enumerate(paragraphs, start=1):
        chunk_id = f"{doc_id}#{i:02d}"
        vector_text = _build_kb_vector_text(module, doc_type, title, tags, risk_level, paragraph)
        content_hash = compute_content_hash(paragraph)
        chunks.append(KBChunk(...))
```

**学习要点**：

1. **分块大小权衡**：分块太大容易稀释语义（一个向量包含太多主题），分块太小容易缺上下文（"押金"单独一个分块不知道是租房押金还是别的）。800 字是初始版本的阈值。

2. **内容哈希增量同步**：
   ```python
   def compute_content_hash(content: str) -> str:
       return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
   ```
   同样的内容不会重复向量化，节省 API 调用成本。同步时先查已有记录的哈希值，只对变化的内容重新向量化。

3. **向量文本构建策略**：
   ```
   [module][doc_type][title][tags][risk_level]
   押金退还规则
   租客退租后，押金将在 7 个工作日内退还...
   关键词：押金,退租,退款
   分类：租赁合同
   ```
   标题放在最前面（用户通常会问和标题相关的问题），标签和模块是检索增强信号。

---

## 11. Milvus 适配器

### `tools/vector_adapter.py` — 向量数据库适配器

```python
class VectorAdapter:
    def __init__(self, uri, token, dim):
        self.client: MilvusClient | None = None  # 延迟连接

    def _ensure_client(self) -> MilvusClient:
        if self.client is None:
            self.connect()  # 只有真正访问向量数据库时才创建连接
        return self.client
```

**学习要点**：

1. **适配器模式**：把 Milvus SDK 的细节封装起来，上层代码只调 `search_rooms()`、`upsert_kb_chunks()` 等业务语义方法。如果以后换向量数据库（如 Qdrant、Pinecone），只需要改这个文件。

2. **延迟连接**：`_ensure_client()` 在第一次调用时才创建连接，方便单元测试（测试时可以模拟掉）和脚本启动（不连向量数据库也能解析参数）。

3. **HNSW 索引**：
   ```python
   index_params.add_index(field_name="embedding", index_type="HNSW",
       metric_type="COSINE", params={"M": 16, "efConstruction": 200})
   ```
   - **HNSW**：分层可导航小世界图，近似最近邻搜索算法，速度快但占内存
   - **余弦相似度**：适合文本向量（方向比长度更重要）
   - **M=16**：每个节点最多连接 16 个邻居，越大越精确但越慢
   - **efConstruction=200**：建索引时的搜索宽度，越大建索引越慢但质量越高

4. **标量索引**：
   ```python
   for field in ("room_id", "district_id", "rent", "status"):
       scalar_idx.add_index(field_name=field, index_type="AUTOINDEX")
   ```
   标量字段（如 `rent <= 1500`）也需要索引，否则过滤表达式会全表扫描。

5. **JSON 序列化**：
   ```python
   "tags": json.dumps(rec.tags, ensure_ascii=False)
   ```
   Milvus 的字符串字段不支持列表，所以把 Python 列表序列化成 JSON 字符串存储。取回来时需要 `json.loads()` 反序列化。

---

## 12. 跨语言 HTTP 适配

### `tools/lease_adapter.py` — 租赁后端适配器

```python
class LeaseAdapter:
    async def sync_rooms(self, limit=200) -> list[dict]:
        client = await self._get_client()
        resp = await client.get("/internal/ai/tools/sync/rooms", params={"limit": limit})
        data = self._handle_response(resp, "sync_rooms")
        return [convert_keys_to_snake(r) for r in rooms]
```

**学习要点**：

1. **命名风格转换**：Python 用下划线命名（`snake_case`），Java 用驼峰命名（`camelCase`）。适配器在发送请求时转成驼峰，收到响应时转回下划线，让上层代码风格统一。

2. **异步 HTTP 客户端**：`httpx.AsyncClient` 支持 `await`，适合 FastAPI 的异步场景。但注意：只有在 `async def` 端点中才能 `await`，同步端点中需要用同步客户端。

3. **自定义异常**：
   ```python
   class LeaseAdapterError(Exception):
       def __init__(self, code, message, recoverable=True):
           self.code = code
           self.recoverable = recoverable
   ```
   `recoverable` 标记区分"可以重试的错误"（如超时）和"需要人工处理的错误"（如参数错误）。

---

## 13. 可观测性与隐私保护

### `trace/retrieval_events.py` — 追踪事件与隐私保护

```python
PII_KEYS = frozenset({"phone", "id_card", "bank_card", "real_name", ...})

def validate_no_pii(data: dict) -> None:
    if isinstance(data, dict):
        for key in data:
            if key.lower() in PII_KEYS:
                raise TracePIIError(f"PII key '{key}' must not appear in trace")
            validate_no_pii(data[key])  # 递归检查嵌套结构
```

**学习要点**：

1. **隐私信息保护**：追踪事件会发送到可观测性系统（如 LangSmith），如果包含手机号、身份证号等敏感信息，会造成数据泄露。所以在发送前递归检查所有字段名。

2. **frozenset**：PII_KEYS 用 `frozenset` 而非 `set`，表示这是一个不可变的常量集合。语义上更清晰，也能防止意外修改。

3. **追踪事件结构**：
   ```python
   {
       "event": "retrieval_finished",
       "trace_id": "trace-abc123",
       "timestamp": 1715000000000,
       "payload": {
           "task": "room_search",
           "candidate_count": 15,
           "latency": {"vector_search_latency_ms": 45.2, ...}
       }
   }
   ```
   结构化的追踪事件可以用来分析性能瓶颈（哪个阶段最慢）、召回质量（候选数量是否合理）等。

---

## 14. 设计模式速查表

| 模式 | 在项目中的应用 | 文件 |
|------|--------------|------|
| **编排器模式** | `run_pipeline()` 按顺序调度各阶段 | `pipeline.py` |
| **适配器模式** | `VectorAdapter` 封装向量数据库 SDK | `vector_adapter.py` |
| **依赖注入** | `get_settings()` / `get_vector_adapter()` | `deps.py` |
| **单例模式** | `@lru_cache` 缓存全局实例 | `deps.py` |
| **闭包工厂** | `get_embed_fn()` 返回 `embed(text)` 函数 | `deps.py` |
| **多路召回** | 原始查询 + 改写查询 + 上推查询 | `room_retrieval.py` / `kb_retrieval.py` |
| **增量同步** | 内容哈希判断内容是否变化 | `chunking.py` |
| **置信度门控** | 高风险问题需要更强证据 | `confidence.py` |
| **加权融合** | 语义分 + 预算分 + 区域分 + 标签分 | `ranking.py` |
| **最长匹配优先** | 区域关键词按长度降序匹配 | `query_understanding.py` |
| **状态继承** | 多轮对话保留上一轮的硬过滤条件 | `query_understanding.py` |
| **隐私校验** | 递归检查追踪事件中的敏感字段 | `retrieval_events.py` |

---

## 关键概念解释

### RAG（检索增强生成）
先从知识库检索相关内容，再把检索结果作为上下文交给大模型生成回答。相比直接问大模型，RAG 能减少幻觉（因为回答基于真实数据），并能回答大模型训练数据中没有的私域知识。

### 向量化（Embedding）
把文本转成高维浮点数组（如 1536 维），语义相近的文本在向量空间中距离更近。例如"安静的房子"和"低噪音公寓"的向量很接近，即使字面完全不同。

### HNSW（分层可导航小世界图）
一种近似最近邻搜索算法。构建一个多层图结构，搜索时从顶层开始逐层下降，每层只检查少量邻居，最终找到近似最近的向量。时间复杂度 O(log n)，比暴力搜索 O(n) 快很多。

### 余弦相似度
两个向量的夹角余弦值，范围 [-1, 1]。值越接近 1 越相似。适合文本向量，因为它只看方向不看长度——"安静"和"非常安静"的向量方向一致，长度不同。

### 置信度门控
在 RAG 的"检索→生成"之间加一个检查：如果检索结果的相似度太低或来源不可靠，就不让大模型生成回答，而是返回安全的兜底消息。这是防止大模型基于弱证据胡编乱造的保护机制。
