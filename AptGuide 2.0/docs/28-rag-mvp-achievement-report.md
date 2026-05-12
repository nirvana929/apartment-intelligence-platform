# 28 · RAG MVP 成果报告

> 日期：2026-05-12
> 状态：已完成

## 一、项目目标

将 AptGuide 2.0 从设计文档落地为可运行的 **FastAPI + RAG 检索 MVP**，实现：

1. 房源向量检索和智能推荐
2. 知识库问答（押金、合同、预约等规则）
3. 与 lease Java 后端真实数据对接
4. 完整的测试覆盖和可观测性

## 二、核心成果

### 2.1 系统架构

```
用户请求 → FastAPI /chat → RAG Pipeline
                            ├── Query Understanding (规则解析)
                            ├── Room Search (Milvus 向量召回 + 多维排序)
                            ├── KB QA (知识库检索 + 置信度门控 + LLM 生成)
                            └── Fallback (领域边界保护)
```

### 2.2 数据规模

| 数据类型 | 数量 | 说明 |
|---------|------|------|
| 活跃房源 | 126 间 | 覆盖广州 5 区 + 北京昌平 |
| KB 知识库 | 70 chunks | 7 个模块，20 条规则 |

**房源分布**

| 区域 | 数量 |
|------|------|
| 天河区 | 30 |
| 海珠区 | 26 |
| 番禺区 | 23 |
| 越秀区 | 22 |
| 白云区 | 22 |
| 昌平区 | 3 |

**KB 模块分布**

| 模块 | 数量 | 说明 |
|------|------|------|
| lease | 12 | 租赁合同规则 |
| appointment | 10 | 预约看房规则 |
| life | 10 | 生活服务规则 |
| payment | 10 | 支付费用规则 |
| policy | 10 | 公寓政策规则 |
| room_search | 10 | 搜索找房规则 |
| account | 8 | 账号安全规则 |

### 2.3 API 端点

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/health` | GET | 健康检查 + Milvus 连接 | ✅ |
| `/chat` | POST | 智能聊天（找房/问答/fallback） | ✅ |

**请求示例**

```json
{
  "message": "番禺区1500以内安静的房子",
  "session_id": "optional"
}
```

**响应示例**

```json
{
  "task": "room_search",
  "message": "为您找到以下房源：",
  "rooms": [
    {
      "room_id": 200092,
      "apartment_name": "市桥老城温馨居",
      "rent": 1200,
      "district_name": "番禺区",
      "tags": ["近地铁", "朝南"],
      "recommendation_reason": "位于番禺区，价格适中"
    }
  ],
  "kb_sources": [],
  "is_confident": true
}
```

### 2.4 搜索质量验证

**房源搜索测试**

| 查询 | 结果 | 评分 |
|------|------|------|
| "番禺区安静的房子" | 市桥老城温馨居 ¥1200 | 0.67 |
| "天河区3000以内" | 天河智慧城公寓 ¥2800 | 0.72 |
| "近地铁独卫" | 多个匹配房源 | 0.65+ |

**KB 问答测试**

| 查询 | 匹配规则 | 评分 |
|------|---------|------|
| "押金退还规则" | KB-LEASE-005 押金退还规则 | 0.84 |
| "怎么预约看房" | KB-APPT-001 预约看房流程 | 0.81 |
| "退租要提前多久" | KB-LEASE-011 退租验房标准 | 0.72 |

### 2.5 测试覆盖

| 测试类型 | 数量 | 状态 |
|---------|------|------|
| 单元测试 | 133 | ✅ 全部通过 |
| E2E 测试 | 16 | ✅ 全部通过 |
| **总计** | **149** | **✅ 100% 通过** |

**单元测试覆盖模块**

- query_understanding (预算、区域、偏好、任务检测)
- chunking (KB chunk 构建、房源向量文本)
- room_retrieval (多路召回、过滤构建)
- kb_retrieval (KB 检索、source rerank)
- ranking (多维排序)
- schemas (Pydantic 模型验证)
- vector_adapter (Milvus 操作)
- lease_adapter (lease 后端对接)
- trace (PII 检测、事件构建)
- data_import (微信数据解析)

**E2E 测试覆盖场景**

- /health 健康检查
- /chat 房源搜索（带预算、带区域）
- /chat KB 问答（高置信、低置信）
- /chat fallback（超范围、保证性承诺）

## 三、技术实现细节

### 3.1 Query Understanding

**确定性规则解析**，不调用 LLM：

- 任务检测：room_search / kb_qa / fallback
- 硬过滤提取：预算、区域、支付方式
- 软偏好提取：安静、近地铁、考研、采光等
- 指代解析：第一个、刚才那个、上一个
- 风险等级：high / medium / low
- 检索改写：生成 2-3 条向量搜索 query

**区域 ID 映射**（与 lease 后端对齐）

| 区域 | ID |
|------|-----|
| 天河区 | 1 |
| 越秀区 | 2 |
| 海珠区 | 3 |
| 番禺区 | 4 |
| 白云区 | 5 |
| 黄埔区 | 6 |
| 南沙区 | 7 |
| 花都区 | 8 |
| 增城区 | 9 |
| 从化区 | 10 |
| 荔湾区 | 11 |
| 昌平区 | 110114 |

### 3.2 房源检索流程

```
QueryUnderstandingResult
  → _build_filters() (district_id, rent range)
  → 多路向量召回 (original + 2-3 generated queries)
  → 按 room_id 去重，保留最高 semantic_score
  → 批量补全房源字段
  → rank_rooms() (语义 + 预算 + 区域 + 标签 + 可用性)
  → Top N 返回
```

**排序权重**

| 维度 | 权重 | 说明 |
|------|------|------|
| semantic_score | 0.35 | 向量余弦相似度 |
| budget_score | 0.25 | 预算匹配度 |
| area_score | 0.20 | 区域匹配度 |
| tag_score | 0.15 | 标签/设施偏好 |
| availability_score | 0.05 | 可用性（默认 1.0） |

### 3.3 KB 问答流程

```
QueryUnderstandingResult
  → 构造多路召回 query (original + normalized + step_back)
  → 搜索 Milvus apt_rental_kb
  → 按 chunk_id 合并
  → source rerank
  → check_confidence()
    ├── high (top score >= 0.65) → LLM 生成回答
    ├── medium (top score >= 0.55) → LLM 生成回答 + 提示
    └── low (top score < 0.55) → 返回"建议查看合同或咨询客服"
```

**置信度门控**

| 等级 | 条件 | 行为 |
|------|------|------|
| high | top_score >= 0.65 且含 high-risk 来源 | LLM 生成 + 标注来源 |
| medium | top_score >= 0.55 且含关键模块 | LLM 生成 + 提示确认 |
| low | top_score < 0.55 | 拒答，建议查看合同 |

### 3.4 数据同步

**房源同步脚本** `scripts/sync_room_vectors.py`

```
lease 后端 /internal/ai/tools/sync/rooms
  → build_room_vector_record()
  → content_hash 增量检测
  → OpenAI-compatible embedding (text-embedding-v3, dim=1024)
  → upsert to Milvus
  → 标记历史房源 inactive
```

**KB 同步脚本** `scripts/sync_kb_vectors.py`

```
knowledge/rules/*.yaml
  → validate_rules() (status, reviewed_by, PII, risk_level)
  → build_kb_chunks()
  → content_hash 增量检测
  → embedding
  → upsert to Milvus
  → 标记历史 chunk inactive
```

**增量同步机制**

- content_hash (SHA-256) 判断内容是否变化
- 只对新增或变化的记录重新 embedding
- 节省 API 调用成本
- 保持同步过程可追踪

### 3.5 Milvus 配置

**Collection: apt_room_vector**

| 字段 | 类型 | 说明 |
|------|------|------|
| vector_id | VARCHAR (PK) | room-{room_id} |
| room_id | INT64 | 房源 ID |
| apartment_id | INT64 | 公寓 ID |
| apartment_name | VARCHAR | 公寓名称 |
| district_id | INT32 | 区域 ID |
| rent | INT32 | 月租 |
| tags | VARCHAR | 标签 JSON |
| facilities | VARCHAR | 设施 JSON |
| embedding | FLOAT_VECTOR | 1024 维向量 |

索引：HNSW (M=16, efConstruction=200, COSINE)

**Collection: apt_rental_kb**

| 字段 | 类型 | 说明 |
|------|------|------|
| chunk_id | VARCHAR (PK) | {doc_id}#NN |
| doc_id | VARCHAR | 文档 ID |
| module | VARCHAR | 模块 (lease/payment/...) |
| title | VARCHAR | 规则标题 |
| content | VARCHAR | 规则内容 |
| risk_level | VARCHAR | 风险等级 |
| embedding | FLOAT_VECTOR | 1024 维向量 |

索引：HNSW (M=16, efConstruction=200, COSINE)

## 四、配置和依赖

### 4.1 环境变量

```bash
# Milvus
APTGUIDE_MILVUS_URI=http://localhost:19530
APTGUIDE_MILVUS_TOKEN=

# Embedding (DashScope)
APTGUIDE_EMBEDDING_API_KEY=sk-xxx
APTGUIDE_EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
APTGUIDE_EMBEDDING_MODEL=text-embedding-v3
APTGUIDE_EMBEDDING_DIM=1024

# LLM (DashScope)
APTGUIDE_LLM_API_KEY=sk-xxx
APTGUIDE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
APTGUIDE_LLM_MODEL=qwen-turbo-latest

# Lease Backend
APTGUIDE_LEASE_BASE_URL=http://localhost:8081
APTGUIDE_LEASE_INTERNAL_TOKEN=aptguide-internal-token-2026

# LangSmith (可选)
APTGUIDE_LANGSMITH_TRACING=true
APTGUIDE_LANGSMITH_API_KEY=lsv2_xxx
APTGUIDE_LANGSMITH_PROJECT=aptguide2

# KB
APTGUIDE_KB_RULES_DIR=knowledge/rules
```

### 4.2 外部依赖

| 服务 | 端口 | 用途 |
|------|------|------|
| Milvus | 19530 | 向量数据库 |
| etcd | 2379 | Milvus 元数据 |
| MinIO | 9000 | Milvus 存储 |
| Redis | 6379 | 缓存（可选） |
| lease Java 后端 | 8081 | 房源数据源 |

### 4.3 启动命令

```bash
# 1. 启动 Milvus (Docker)
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
docker-compose up -d etcd minio milvus redis

# 2. 等待 Milvus 就绪 (约 20 秒)
sleep 20

# 3. 同步 KB 知识库
cd "AptGuide 2.0/backend"
.venv/bin/python scripts/sync_kb_vectors.py --release-id "kb-v1"

# 4. 同步房源数据 (需要 lease 后端运行)
.venv/bin/python scripts/sync_room_vectors.py --limit 200

# 5. 启动 FastAPI
.venv/bin/python -m uvicorn aptguide2.api.app:app --host 0.0.0.0 --port 8000
```

## 五、问题修复记录

### 5.1 District ID 映射错误

**问题**：Query Understanding 使用 1001-1011 作为区域 ID，但 lease 后端使用 1-11, 110114

**修复**：更新 `query_understanding.py` 中的 DISTRICTS 和 AREA_KEYWORDS 字典

```python
# 修复前
"天河区": 1001, "番禺区": 1005

# 修复后
"天河区": 1, "番禺区": 4
```

### 5.2 Lease 后端认证失败

**问题**：使用 `Authorization: Bearer` 头导致 401

**修复**：改为 `X-Internal-Token` 头

```python
headers["X-Internal-Token"] = self.internal_token
```

### 5.3 Lease 响应码不匹配

**问题**：`_handle_response` 检查 `code != 0`，但 lease 返回 `code: 200`

**修复**：改为 `code not in (0, 200)`

### 5.4 KB 同步重复 doc_id

**问题**：`knowledge/rules/` 目录有 `_rules.yaml` 和 `.yaml` 两套文件，包含相同 doc_id

**修复**：修改 `load_rules()` 函数，按 doc_id 去重

```python
def load_rules(rules_dir: str) -> list[dict]:
    seen_ids: set[str] = set()
    for filepath in sorted(glob.glob(pattern)):
        for item in items:
            doc_id = item.get("doc_id", "")
            if doc_id and doc_id in seen_ids:
                continue
            if doc_id:
                seen_ids.add(doc_id)
            rules.append(item)
```

### 5.5 facilities 字段 None 值

**问题**：RoomVectorRecord 期望 list 但收到 None

**修复**：添加 `or []` 默认值

```python
tags = room.get("tags", []) or []
facilities = room.get("facilities", []) or []
```

### 5.6 LangSmith 配置验证错误

**问题**：`LANGCHAIN_*` 环境变量导致 "Extra inputs are not permitted"

**修复**：移除 `LANGCHAIN_*` 变量，只保留 `APTGUIDE_LANGSMITH_*`

## 六、后续计划

### 6.1 短期 (1-2 周)

- [ ] 更多房源同步 (目标 500+)
- [ ] 多轮会话记忆接入
- [ ] 前端聊天应用开发
- [ ] LangSmith trace 完整接入

### 6.2 中期 (1-2 月)

- [ ] Agent planner / specialist agents
- [ ] 预约、签约等写操作 workflow
- [ ] 结构化确认卡片
- [ ] RAGAS 自动化评测闭环

### 6.3 长期 (3-6 月)

- [ ] 长期用户偏好画像
- [ ] 人工接管机制
- [ ] MCP 封装
- [ ] 权限认证体系

## 七、文件清单

### 核心代码

```
backend/src/aptguide2/
├── api/
│   ├── app.py          # FastAPI 入口
│   ├── deps.py         # 依赖注入
│   └── schemas.py      # API 模型
├── core/
│   └── config.py       # 配置管理
├── rag/
│   ├── pipeline.py     # RAG 主流程
│   ├── query_understanding.py  # 查询理解
│   ├── room_retrieval.py       # 房源检索
│   ├── kb_retrieval.py         # KB 检索
│   ├── ranking.py              # 多维排序
│   ├── confidence.py           # 置信度门控
│   ├── chunking.py             # 文本构建
│   └── schemas.py              # 数据模型
├── tools/
│   ├── vector_adapter.py  # Milvus 适配器
│   └── lease_adapter.py   # lease 适配器
└── trace/
    └── retrieval_events.py  # Trace 事件
```

### 脚本

```
backend/scripts/
├── sync_room_vectors.py   # 房源同步
├── sync_kb_vectors.py     # KB 同步
└── seed_mock_rooms.py     # Mock 数据
```

### 测试

```
backend/tests/
├── unit/                  # 133 个单元测试
│   ├── rag/
│   ├── tools/
│   ├── trace/
│   └── data_import/
└── e2e/                   # 16 个 E2E 测试
    ├── test_api.py
    └── test_pipeline.py
```

### 知识库

```
backend/knowledge/rules/
├── account.yaml           # 账号规则
├── appointment.yaml       # 预约规则
├── lease.yaml             # 租赁规则
├── life.yaml              # 生活规则
├── payment.yaml           # 支付规则
├── policy.yaml            # 政策规则
└── room_search.yaml       # 搜索规则
```

## 八、总结

AptGuide 2.0 RAG MVP 已成功实现：

1. **完整的 RAG 流程**：从用户输入到结构化响应
2. **真实数据对接**：126 间房源 + 70 条 KB 规则
3. **高质量搜索**：语义相似度 0.65-0.84
4. **100% 测试通过**：149 个测试全部绿灯
5. **生产就绪配置**：LangSmith 可观测性、增量同步、PII 保护

系统已可用于演示和小规模生产部署。
