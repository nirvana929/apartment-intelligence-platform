# API 文档

> 权威来源：[`AptInsight文档/06-接口契约与集成方案.md`](../AptInsight文档/06-接口契约与集成方案.md)

## 已实现接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查，返回 `{"status": "ok"}` |
| `/api/chat` | POST | 智能分析聊天，接收自然语言问题 |

## 快速验证

```bash
# 健康检查
curl http://localhost:8000/health

# 聊天接口
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "有多少个已发布的公寓"}'
```

## 响应格式

请求和响应的完整字段定义、类型约束、错误码详见接口契约文档。

`/api/chat` 响应包含：`trace_id`、`answer`、`summary`、`rows`、`columns`、`chart`、`sql`、`error`、`processing_time_ms`。
