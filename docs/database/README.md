# 数据库文档

本目录包含公寓智能平台所有子项目的数据库文档。

## 文档索引

| 文件 | 内容 |
|------|------|
| [mysql.md](mysql.md) | MySQL 数据库：库表结构、连接信息、数据关系 |
| [milvus.md](milvus.md) | Milvus 向量数据库：Collection 结构、字段定义、数据来源 |
| [redis.md](redis.md) | Redis 缓存：实例分配、Key 前缀、用途说明 |
| [data-sync.md](data-sync.md) | 数据同步：Milvus 与 MySQL 的数据对齐问题及解决方案 |

## 快速参考

| 数据库 | 端口 | 用途 |
|--------|------|------|
| MySQL | 3306 | 业务数据 + Agent 状态 |
| Milvus | 19530 | 向量检索（房源 + 知识库） |
| Redis | 6379 | 会话缓存 + 状态存储 |
| MinIO | 9000 | 文件存储（图片等） |
| etcd | 2379 | Milvus 元数据 |
