# Docker 启动文档

本目录包含公寓智能平台的 Docker 部署和启动文档。

## 文档索引

| 文件 | 内容 |
|------|------|
| [infrastructure.md](infrastructure.md) | 基础设施服务启动 (MySQL, Redis, Milvus 等) |
| [services.md](services.md) | 应用服务启动 (lease, AptGuide 等) |
| [troubleshooting.md](troubleshooting.md) | 常见问题排查 |

## 快速启动 (一键启动全部基础设施)

```bash
cd /home/chove/桌面/apartment-intelligence-platform

# 启动集成测试环境 (MySQL + Redis + Milvus + lease + AptGuide)
docker-compose -f docker-compose.test.yml up -d
```

## 按需启动

```bash
# 只启动 AptGuide 3.0 的基础设施 (MySQL + Redis)
cd "AptGuide 3.0/backend"
docker-compose -f docker-compose.local.yml up -d

# 只启动 Milvus (etcd + minio + milvus)
cd AptGuide
docker-compose up -d
```

## 服务端口总览

| 服务 | 端口 | 用途 |
|------|------|------|
| MySQL | 3306 | 业务数据库 |
| Redis | 6379 | 缓存 |
| Milvus | 19530 | 向量数据库 |
| Milvus WebUI | 9091 | Milvus 管理界面 |
| MinIO | 9000 | 文件存储 |
| etcd | 2379 | Milvus 元数据 |
| lease web-app | 8081 | 租户端 API |
| lease web-admin | 8080 | 管理后台 API |
| AptGuide 1.0 | 8100 | AI 助手 |
| AptInsight | 8000 | 运营分析 |

## 网络架构

所有容器通过 `apartment-intelligence-platform_default` Docker 网络通信。

```
                    ┌─────────────────────────────────────┐
                    │    apartment-intelligence-platform   │
                    │           _default network           │
                    │                                     │
                    │  ┌─────┐ ┌─────┐ ┌───────┐         │
                    │  │MySQL│ │Redis│ │Milvus │         │
                    │  │3306 │ │6379 │ │19530  │         │
                    │  └─────┘ └─────┘ └───────┘         │
                    │       ▲       ▲       ▲             │
                    │       │       │       │             │
                    │  ┌────┴───────┴───────┴────┐        │
                    │  │    lease web-app :8081   │        │
                    │  └────────────┬────────────┘        │
                    │               │                      │
                    │  ┌────────────┴────────────┐        │
                    │  │   AptGuide 1.0 :8100    │        │
                    │  └─────────────────────────┘        │
                    └─────────────────────────────────────┘
```

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存 (Milvus 需要较多内存)
- 端口 3306, 6379, 19530, 8081, 8100 未被占用
