# Docker 常见问题排查

## 1. Redis 连接被拒绝

**症状**: lease 服务返回 `{"code":201,"message":"失败"}`

**原因**: Redis 只监听 `127.0.0.1:6379`，Docker 容器无法访问

**排查**:
```bash
# 检查 Redis 绑定地址
ss -tlnp | grep 6379
# 如果显示 127.0.0.1:6379 而非 0.0.0.0:6379，则有问题
```

**解决**:
```bash
# 1. 停止原生 Redis
sudo systemctl stop redis-server
sudo systemctl disable redis-server

# 2. 启动 Docker Redis
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 3.0/backend"
docker-compose -f docker-compose.local.yml up -d redis

# 3. 确保 Redis 容器连接到 Docker 网络
docker network connect apartment-intelligence-platform_default aptguide3-redis

# 4. 重启 lease 服务
docker restart aip-lease-web-app

# 5. 验证
ss -tlnp | grep 6379  # 应显示 0.0.0.0:6379
redis-cli -h 127.0.0.1 ping  # 应返回 PONG
curl -s http://localhost:8081/internal/ai/tools/health -H "X-Internal-Token: aptguide-internal-token-2026"
```

---

## 2. Milvus 容器启动失败

**症状**: Milvus 容器状态为 Exited 或 unhealthy

**排查**:
```bash
docker logs aip-milvus --tail 50
docker ps -a | grep milvus
```

**常见原因**:
- 内存不足 (Milvus 需要 ~2GB)
- etcd 未启动
- 端口 19530 被占用

**解决**:
```bash
# 确保 etcd 和 MinIO 先启动
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
docker-compose up -d etcd minio
sleep 5
docker-compose up -d milvus
```

---

## 3. MySQL 连接失败

**症状**: `Can't connect to MySQL server`

**排查**:
```bash
docker ps | grep mysql
mysql -u chove -p123456 -h 127.0.0.1 -e "SELECT 1"
```

**解决**:
```bash
# 启动 MySQL
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 3.0/backend"
docker-compose -f docker-compose.local.yml up -d mysql

# 等待 MySQL 就绪
sleep 10
docker logs aptguide3-mysql --tail 20
```

---

## 4. lease 服务返回 401

**症状**: `{"code":401,"message":"Invalid internal token"}`

**原因**: 请求未携带 `X-Internal-Token` header 或 token 值错误

**解决**:
```bash
# 正确的请求格式
curl -X POST http://localhost:8081/internal/ai/tools/room/search \
  -H "Content-Type: application/json" \
  -H "X-Internal-Token: aptguide-internal-token-2026" \
  -d '{"limit": 5}'
```

---

## 5. Docker 容器不在同一网络

**症状**: 容器之间无法通信

**排查**:
```bash
# 查看容器网络
docker inspect <container_name> --format '{{json .NetworkSettings.Networks}}'

# 查看 Docker 网络
docker network ls
docker network inspect apartment-intelligence-platform_default
```

**解决**:
```bash
# 手动连接容器到网络
docker network connect apartment-intelligence-platform_default <container_name>
```

---

## 6. 端口被占用

**症状**: `Bind for 0.0.0.0:3306 failed: port is already allocated`

**排查**:
```bash
ss -tlnp | grep <port>
# 或
lsof -i :<port>
```

**解决**:
```bash
# 停止占用端口的进程
sudo systemctl stop <service>
# 或修改 docker-compose.yml 的端口映射
```

---

## 7. Milvus Room ID 与 MySQL 不一致

**症状**: 房源搜索返回 0 结果，lease 验证全部失败

**原因**: Milvus 中的 room_id (3001+) 与 MySQL `room_info` 中的 room_id (2-38+) 不匹配

**排查**:
```bash
# 查看 Milvus 中的 room_id
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 3.0/backend"
uv run python -c "
from pymilvus import MilvusClient
c = MilvusClient(uri='http://localhost:19530')
rs = c.query('room_index', output_fields=['id'], limit=5)
print([r['id'] for r in rs])
"

# 查看 MySQL 中的 room_id
mysql -u chove -p123456 -h 127.0.0.1 least -e "SELECT id FROM room_info LIMIT 5"
```

**解决**: 参见 [database/data-sync.md](../database/data-sync.md)

---

## 常用命令速查

```bash
# 查看所有容器状态
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 查看容器日志
docker logs <container_name> --tail 50 -f

# 重启容器
docker restart <container_name>

# 进入容器
docker exec -it <container_name> sh

# 查看 Docker 网络
docker network ls
docker network inspect apartment-intelligence-platform_default

# 清理停止的容器
docker container prune

# 查看 Docker 资源使用
docker stats --no-stream
```
