# AptInsight API 文档

**服务**: AptInsight
**端口**: 8000
**技术栈**: Python 3.12, FastAPI, LangGraph, sqlglot

## 认证

当前无认证 (开放访问)。

## 主要接口

### 运营分析对话

```
POST /api/chat
Content-Type: application/json

Request:
{
  "question": "上个月天河区的出租率是多少?",
  "session_id": "optional-session-id"
}

Response:
{
  "trace_id": "trace-uuid",
  "answer": "上个月天河区的出租率为 85.3%...",
  "summary": "天河区出租率分析",
  "rows": [["天河区", "85.3%"]],
  "columns": ["区域", "出租率"],
  "chart": {
    "type": "bar",
    "data": {...}
  },
  "sql": "SELECT district, ...",
  "warnings": [],
  "processing_time_ms": 2345
}
```

### 流式对话

```
POST /api/chat/stream
Content-Type: application/json

Request: 同 /api/chat
Response: SSE 事件流
```

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |

### 静态页面

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/static/index.html` | 内置前端 |

## Agent 工作流 (LangGraph)

```
intent_recognition
  → sql_generation (Text-to-SQL)
    → sql_guard (sqlglot AST 安全检查)
      → query_execution (只读查询)
        → chart_building (可选)
          → answer_generation
```

## 安全机制

| 机制 | 说明 |
|------|------|
| 表白名单 | 只允许查询指定表 |
| 列白名单 | 只允许查询指定列 |
| SQL 类型限制 | 只允许 SELECT |
| sqlglot AST 检查 | 解析 SQL AST，阻止危险操作 |
| 敏感字段拦截 | 自动脱敏手机号、身份证等 |
| 结果脱敏 | 返回数据中的敏感信息自动遮蔽 |

## 依赖

| 依赖 | 地址 | 用途 |
|------|------|------|
| MySQL | 192.168.211.128:3306/least | 数据查询 (只读) |
| Redis | 127.0.0.1:6379/0 | 缓存 |
| LLM | 可配置 | SQL 生成 + 答案生成 |

## 配置文件

- `.env` — 环境变量
- `src/aptinsight/core/config.py` — Pydantic Settings
