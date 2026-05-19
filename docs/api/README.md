# API 文档

本目录包含公寓智能平台所有子项目的 API 文档。

## 文档索引

| 文件 | 服务 | 端口 | 说明 |
|------|------|------|------|
| [lease-web-app.md](lease-web-app.md) | lease web-app | 8081 | 租户端 API + AI 工具接口 |
| [lease-web-admin.md](lease-web-admin.md) | lease web-admin | 8080 | 管理后台 API |
| [aptguide.md](aptguide.md) | AptGuide 1.0 | 8100 | AI 租房助手 (LangGraph) |
| [aptguide3.md](aptguide3.md) | AptGuide 3.0 | - | AI 租房助手 (LLM-first) |
| [aptinsight.md](aptinsight.md) | AptInsight | 8000 | 运营分析助手 |

## 服务间调用关系

```
rentHouseH5 (5173)
  └── lease web-app (8081)
        └── AptGuide (8100)
              ├── Milvus (19530)
              └── lease web-app (8081) /internal/ai/tools/*

rentHouseAdmin (5173)
  └── lease web-admin (8080)

AptInsight (8000)
  └── MySQL (3306) 只读
```

## 认证方式汇总

| 服务 | 认证方式 | 说明 |
|------|----------|------|
| lease web-app (/app/*) | JWT Token | SMS 登录获取 |
| lease web-app (/internal/*) | X-Internal-Token | 固定值: `aptguide-internal-token-2026` |
| lease web-admin | JWT Token | 账号密码登录获取 |
| AptGuide 1.0 | X-User-Id | 由 lease 网关注入 |
| AptGuide 3.0 | X-Internal-Token + X-User-Id | 或 dev 模式自动认证 |
| AptInsight | 无 | 当前开放访问 |
