# 基础设施服务启动指南

## 方案一: 一键启动 (推荐用于开发)

```bash
cd /home/chove/桌面/apartment-intelligence-platform
docker-compose -f docker-compose.test.yml up -d
```

启动服务:
- MySQL 8.0 (端口 3306)
- Redis 7 (端口 6379)
- Milvus 2.4.17 (端口 19530, 9091)
- etcd 3.5.0
- MinIO
- lease web-app (端口 8081)
- AptGuide 1.0 (端口 8100)

## 方案二: 分步启动

### 1. MySQL + Redis (AptGuide 3.0 本地开发)

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 3.0/backend"
docker-compose -f docker-compose.local.yml up -d
```

启动:
- MySQL 8.0 (端口 3306, 数据库: aptguide3)
- Redis 7 (端口 6379)

### 2. Milvus (etcd + MinIO + Milvus)

```bash
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
docker-compose up -d
```

启动:
- etcd 3.5.0
- MinIO (端口 9000)
- Milvus 2.4.17 (端口 19530, 9091)
- Redis 7 (端口 6380, 注意端口不同)

### 3. lease 服务

lease 服务需要构建 Docker 镜像。如果没有预构建镜像，需要从源码构建:

```bash
cd /home/chove/桌面/apartment-intelligence-platform/lease
mvn clean package -DskipTests
docker build -t apartment-intelligence-platform-lease-web-app -f web/web-app/Dockerfile .
```

然后启动:

```bash
docker run -d \
  --name aip-lease-web-app \
  --network apartment-intelligence-platform_default \
  -p 8081:8081 \
  -e MYSQL_URL="jdbc:mysql://host.docker.internal:3306/least?useUnicode=true&characterEncoding=utf-8&useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=GMT%2b8" \
  -e MYSQL_USERNAME=chove \
  -e MYSQL_PASSWORD=123456 \
  -e REDIS_HOST=host.docker.internal \
  -e REDIS_PORT=6379 \
  apartment-intelligence-platform-lease-web-app
```

## 前置条件检查

```bash
# 检查 Docker 是否运行
docker ps

# 检查端口是否被占用
ss -tlnp | grep -E "3306|6379|19530|8081"

# 检查磁盘空间
df -h
```

## 停止服务

```bash
# 停止 AptGuide 3.0 基础设施
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 3.0/backend"
docker-compose -f docker-compose.local.yml down

# 停止 Milvus
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
docker-compose down

# 停止全部
cd /home/chove/桌面/apartment-intelligence-platform
docker-compose -f docker-compose.test.yml down
```

## 数据持久化

所有数据通过 Docker volumes 持久化:

| Volume | 用途 |
|--------|------|
| `apartment-intelligence-platform_mysql-data` | MySQL 数据 |
| `apartment-intelligence-platform_redis-data` | Redis 数据 |
| `apartment-intelligence-platform_milvus-data` | Milvus 数据 |
| `apartment-intelligence-platform_etcd-data` | etcd 数据 |
| `apartment-intelligence-platform_minio-data` | MinIO 数据 |

## 已知问题

### 1. Redis 端口冲突

如果主机上已有原生 Redis 运行 (监听 127.0.0.1:6379)，Docker Redis 无法绑定到同一端口。

**解决**:
```bash
sudo systemctl stop redis-server    # 停止原生 Redis
sudo systemctl disable redis-server # 禁止开机自启
```

### 2. Docker 网络问题

容器可能没有正确连接到 Docker 网络，导致端口映射不生效。

**解决**:
```bash
# 手动连接容器到网络
docker network connect apartment-intelligence-platform_default <container_name>
```

### 3. Milvus 内存不足

Milvus standalone 默认需要约 2GB 内存。

**解决**: 增加 Docker 内存限制或关闭其他占用内存的服务。

### 4. lease 服务 Redis 连接失败

lease 服务配置为连接 `host.docker.internal:6379`。需要确保:
1. Redis 监听 `0.0.0.0:6379` (而非 `127.0.0.1:6379`)
2. Docker 容器可以访问主机的 6379 端口

**验证**:
```bash
# 检查 Redis 绑定地址
ss -tlnp | grep 6379
# 应显示 0.0.0.0:6379，而非 127.0.0.1:6379
```
