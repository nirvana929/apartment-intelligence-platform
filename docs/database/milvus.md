# Milvus 向量数据库文档

## 概览

Milvus v2.4.17 (standalone 模式)，用于房源语义检索和知识库 RAG。

- 连接地址: `http://127.0.0.1:19530`
- 管理端口: `9091` (Milvus WebUI)
- 后端存储: etcd (元数据) + MinIO (对象存储)

## Collections

### 1. `room_index` — 房源向量索引

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Int64 | 房间 ID (当前范围: 3001-3102) |
| `title` | VarChar | 房间标题，如 "亚运城公寓 3006" |
| `description` | VarChar | 房间描述 |
| `vector` | FloatVector(1536) | 语义向量 (text-embedding-3-small) |
| `rent` | Float | 月租金 |
| `district` | VarChar | 区域名，如 "番禺区"、"天河区" |
| `tags` | VarChar | JSON 字符串，如 `["安静", "近地铁"]` |
| `payment_type` | VarChar | 付款方式 |
| `status` | VarChar | 状态: "available" / "rented" |

**当前数据量**: 150 条 (available)

**区域分布**:

| 区域 | 数量 |
|------|------|
| 番禺区 | 38 |
| 天河区 | 30 |
| 海珠区 | 26 |
| 白云区 | 24 |
| 越秀区 | 22 |
| 昌平区 | 10 |

### 3. `wechat_room_index` — 微信租房数据

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | VarChar | 记录 ID，如 "wechat-001" |
| `content` | VarChar | 向量化文本 (区域+地段+租金+房型+地铁+标签+描述) |
| `district` | VarChar | 区域名，如 "天河区" |
| `area_label` | VarChar | 具体地段，如 "珠江新城/科韵路" |
| `rent_min` | Float | 最低租金 |
| `rent_max` | Float | 最高租金 |
| `tags` | VarChar | JSON 标签，如 `["近地铁","押一付一"]` |
| `metro_stations` | VarChar | JSON 地铁站 |
| `facility_tags` | VarChar | JSON 设施标签 |
| `payment_tags` | VarChar | JSON 付款方式 |
| `vector` | FloatVector(1024) | 语义向量 (DashScope text-embedding-v3) |

**当前数据量**: 44 条 (从微信群消息提取的真实房源)

**数据来源**: `AptGuide/data/wechat_rental_listings_sanitized.jsonl`

**区域分布**:

| 区域 | 数量 |
|------|------|
| 天河区 | 28 |
| 荔湾区 | 9 |
| 海珠区 | 4 |
| 番禺区 | 3 |

**MySQL 对应表**: `least.wechat_listings`

### 2. `apt_rental_kb` — 租赁知识库

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | VarChar | 文档 ID，如 "KB-LS-011" |
| `title` | VarChar | 文档标题，如 "签约后可以反悔吗" |
| `category` | VarChar | 分类: lease/payment/policy/life/appointment/account |
| `content` | VarChar | 文档内容 |
| `vector` | FloatVector(1536) | 语义向量 |

**当前数据量**: 70 条

**分类风险等级映射** (AptGuide 3.0 使用):

| category | risk_level | 说明 |
|----------|------------|------|
| lease | high | 租约相关 |
| payment | high | 支付相关 |
| account | high | 账户相关 |
| appointment | medium | 预约相关 |
| policy | medium | 政策相关 |
| life | low | 生活服务 |
| room_search | low | 房源搜索 |

## 重要: ID 空间不一致问题

**Milvus `room_index` 中的 room_id (3001-3102) 与 MySQL `least.room_info` 中的 room_id (2-38+) 不一致。**

这意味着:
- Milvus 向量检索返回的 room_id 在 lease API 中找不到对应数据
- lease API 的 `validate_rooms` 会返回空结果
- 房源搜索流程在 lease 验证阶段被阻断

详见 [data-sync.md](data-sync.md)。

## 同步脚本

| 脚本 | 状态 | 说明 |
|------|------|------|
| `AptGuide 3.0/backend/scripts/sync_room_vectors.py` | 模板 | 从 lease API 同步房间向量 (未完成) |
| `AptGuide 3.0/backend/scripts/sync_kb_vectors.py` | 模板 | 同步知识库向量 (未完成) |

## Embedding 模型

| 项目 | 模型 | 维度 |
|------|------|------|
| AptGuide 1.0 | text-embedding-v3/v4 (DashScope) | 1024 |
| AptGuide 2.0/3.0 | text-embedding-3-small (OpenAI) | 1536 |

> **注意**: 不同版本使用不同维度的 embedding 模型，向量不能混用。
