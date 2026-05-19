# AptGuide 1.0 API 文档

**服务**: AptGuide 1.0
**端口**: 8100
**技术栈**: Python 3.12, FastAPI, LangGraph, DashScope/Qwen

## 认证

通过 `X-User-Id` header 传入用户 ID (由 lease 网关注入)。

## 主要接口

### AI 对话

```
POST /api/chat
Content-Type: application/json

Request:
{
  "session_id": "abc123",    // 可选，不传则新建会话
  "message": "天河区近地铁2000以内的房子"
}

Response:
{
  "session_id": "abc123",
  "request_id": "req-456",
  "intent": "room_search",
  "reply": "为您找到以下房源...",
  "cards": [
    {
      "room_id": 3001,
      "apartment_name": "体育西居",
      "rent": 1171,
      "tags": ["近地铁"]
    }
  ],
  "actions": [],
  "pending_confirmation": null,
  "sources": ["KB-LS-011"]
}
```

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 简单健康检查 |
| GET | `/health/deps` | 依赖健康 (Milvus, lease, Redis) |

### 静态页面

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 内置聊天 UI |

## Agent 工作流 (LangGraph)

```
intent_classification
  → slot_filling
    → room_search / kb_search / tool_calling
      → confirmation (if needed)
        → reply_generation
```

## 依赖

| 依赖 | 地址 | 用途 |
|------|------|------|
| Milvus | localhost:19530 | 向量检索 |
| lease web-app | localhost:8081 | 业务数据 (via /internal/ai/tools/*) |
| Redis | localhost:6380 | 会话存储 (可选，默认内存) |
| DashScope | api.dashscope.aliyuncs.com | LLM + Embedding |

## 配置文件

- `.env` — 环境变量 (API keys, URLs)
- `src/aptguide/core/config.py` — Pydantic Settings
