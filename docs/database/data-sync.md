# 数据同步文档

## 问题: Milvus 与 MySQL 的 Room ID 不一致

### 现状

| 数据源 | Room ID 范围 | 数据来源 |
|--------|-------------|----------|
| Milvus `room_index` | 3001-3102 | 旧 seed 数据导入 |
| MySQL `least.room_info` | 2-38+ | lease 系统业务数据 |

### 影响

1. Milvus 向量检索返回 room_id=3001，lease API 查不到 → 返回空
2. `validate_rooms` 全部返回空 → 房间全部被丢弃
3. 房源搜索功能完全不可用

### 解决方案

**方案 A: 重新同步 Milvus 数据 (推荐)**

使用 lease API 的 `/internal/ai/tools/sync/rooms` 端点获取真实房间数据，重新生成向量并写入 Milvus。

```bash
# 1. 确保 lease 服务和 Redis 正常运行
# 2. 运行同步脚本
cd "AptGuide 3.0/backend"
uv run python scripts/sync_room_vectors.py
```

**方案 B: 更新 Milvus 中的 room_id**

直接修改 Milvus 中的 room_id 字段，使其与 MySQL 一致。需要建立 ID 映射关系。

**方案 C: 使用 lease API 作为唯一搜索源 (架构改进)**

不再使用 Milvus 做房源搜索，改为直接调用 lease API 的搜索接口。Milvus 仅用于知识库 RAG。

### 同步脚本状态

| 脚本 | 状态 | 待完成 |
|------|------|--------|
| `sync_room_vectors.py` | 模板 | 需要实现: 调用 lease API → 构建向量文本 → embedding → 写入 Milvus |
| `sync_kb_vectors.py` | 模板 | 需要实现: 读取 YAML 规则 → 构建 chunk 文本 → embedding → 写入 Milvus |

### 同步后验证

```bash
# 运行 RAG 评测
cd "AptGuide 3.0/backend"
uv run python evals/runners/run_rag_eval.py --live
```

预期结果: `room_search` cases 的 `lease_validated` 应 > 0。
