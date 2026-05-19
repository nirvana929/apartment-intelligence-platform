# AptGuide 3.0 API 文档

**服务**: AptGuide 3.0
**技术栈**: Python, FastAPI, SQLAlchemy, Milvus, DashScope/Qwen

## 认证

支持三种模式 (通过 `APTGUIDE3_AUTH_MODE` 配置):

| 模式 | 说明 |
|------|------|
| `dev` | 开发模式，自动认证 |
| `internal_header` | 生产模式，需要 `X-Internal-Token` + `X-User-Id` |

## 主要接口

### AI 对话

```
POST /chat
Content-Type: application/json
X-Internal-Token: aptguide-internal-token-2026
X-User-Id: 1

Request:
{
  "session_id": "uuid",       // 可选
  "message": "押金不退怎么办"
}

Response:
{
  "session_id": "uuid",
  "reply": "关于押金退还...",
  "cards": [...],
  "sources": ["KB-LS-011"],
  "metadata": {
    "route": "rag",
    "task": "kb_qa",
    "confidence": 0.95
  }
}
```

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/ready` | 就绪探针 (支持 `?live=true` 深度检查) |

## 7 个业务过程 (Procedures)

| 过程 | 触发条件 | 说明 |
|------|----------|------|
| `clarify` | 理解置信度低 | 请求用户澄清 |
| `room_search` | 用户找房 | Milvus 检索 + lease 验证 + 排序 |
| `kb_qa` | 用户问政策/规则 | 知识库 RAG + 置信度门控 |
| `appointment` | 用户要预约 | 调用 lease API 创建预约 |
| `lease` | 用户查租约 | 查询用户的租约信息 |
| `memory` | 记忆相关 | 长期记忆管理 |
| `handoff` | 转人工 | 创建工单转接人工客服 |

## RAG 流程

```
用户消息
  → LLM 理解 (route/task/filters/confidence)
    → 验证器 (schema 检查, 硬过滤验证)
      → 检索计划 (semantic_queries, hard_filters)
        → 向量检索 (Milvus)
          → lease 验证 (仅 room_search)
            → 排序 (semantic + preference)
              → 置信度门控 (仅 kb_qa)
                → 响应生成
```

## 配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `APTGUIDE3_MYSQL_DSN` | MySQL 连接 | - |
| `APTGUIDE3_REDIS_URL` | Redis 连接 | - |
| `APTGUIDE3_VECTOR_URI` | Milvus 地址 | http://localhost:19530 |
| `APTGUIDE3_LLM_API_KEY` | LLM API Key | - |
| `APTGUIDE3_LLM_MODEL` | LLM 模型 | qwen-turbo-latest |
| `APTGUIDE3_EMBEDDING_API_KEY` | Embedding API Key | - |
| `APTGUIDE3_LEASE_BASE_URL` | lease 服务地址 | http://localhost:8081 |
| `APTGUIDE3_INTERNAL_TOKEN` | 内部认证 token | - |
| `APTGUIDE3_AUTH_MODE` | 认证模式 | dev |
| `LANGSMITH_TRACING` | LangSmith 追踪 | false |

## 数据库

共 11 张表，详见 [database/mysql.md](../database/mysql.md#数据库-aptguide3-aptguide-30-agent-状态)。
