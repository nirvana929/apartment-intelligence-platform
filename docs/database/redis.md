# Redis 缓存文档

## 概览

Redis 7-alpine，端口 6379。通过 Docker 运行 (`aptguide3-redis`)。

## DB 分配

| DB | 使用者 | Key 前缀 | 用途 |
|----|--------|----------|------|
| 0 | lease web-app, lease web-admin, AptGuide 2.0, AptInsight | 无/各自前缀 | 会话缓存、业务缓存 |
| 3 | AptGuide 3.0 | `aptguide3:` | 会话状态、待确认操作 TTL |

## AptGuide 3.0 Key 模式

| Key 模式 | 类型 | TTL | 说明 |
|----------|------|-----|------|
| `aptguide3:session:{session_id}` | Hash | 24h | 会话状态 |
| `aptguide3:pending:{action_id}` | String | 可配置 | 待确认操作 |

## Docker 启动

```bash
cd "AptGuide 3.0/backend"
docker-compose -f docker-compose.local.yml up -d redis
```

## 注意事项

- Docker Redis 必须连接到 Docker 网络才能被其他容器访问
- 如果主机上有原生 Redis 运行，需要先停止: `sudo systemctl stop redis-server`
- 确保 Redis 绑定到 `0.0.0.0:6379` (而非 `127.0.0.1:6379`)
