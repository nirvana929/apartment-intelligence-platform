# 应用服务启动指南

## AptGuide 1.0 (AI 租房助手)

### 依赖

- Python 3.12+
- Milvus (端口 19530)
- lease web-app (端口 8081)

### 启动

```bash
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API keys

# 启动
uv run uvicorn src/aptguide.api.app:app --host 0.0.0.0 --port 8100
```

### 健康检查

```bash
curl http://localhost:8100/health
curl http://localhost:8100/health/deps
```

---

## AptGuide 3.0 (LLM-first AI 助手)

### 依赖

- Python 3.12+
- MySQL (数据库 aptguide3)
- Redis (DB 3)
- Milvus (端口 19530)
- lease web-app (端口 8081)

### 启动

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 3.0/backend"

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入配置

# 启动基础设施
docker-compose -f docker-compose.local.yml up -d

# 创建数据库表
uv run python -c "from aptguide3.database.database import create_tables; import asyncio; asyncio.run(create_tables())"

# 启动服务
uv run uvicorn src/aptguide3.api.app:app --host 0.0.0.0 --port 8000
```

### 健康检查

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready?live=true
```

### 运行测试

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 3.0/backend"
uv run pytest tests/unit -q          # 单元测试
uv run ruff check src tests          # 代码检查
uv run python evals/runners/run_rag_eval.py --live  # RAG 评测
```

---

## AptInsight (运营分析助手)

### 依赖

- Python 3.12+
- MySQL (least 数据库, 只读)
- Redis

### 启动

```bash
cd /home/chove/桌面/apartment-intelligence-platform/AptInsight

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入配置

# 启动
uv run uvicorn src/aptinsight.api.app:app --host 0.0.0.0 --port 8000
```

### 健康检查

```bash
curl http://localhost:8000/health
```

---

## rentHouseH5 (租户端 H5)

### 依赖

- Node.js 18+
- lease web-app (端口 8081)

### 启动

```bash
cd /home/chove/桌面/apartment-intelligence-platform/rentHouseH5

# 安装依赖
npm install

# 开发模式
npm run dev
```

访问: http://localhost:5173

---

## rentHouseAdmin (管理后台)

### 依赖

- Node.js 18+
- lease web-admin (端口 8080)

### 启动

```bash
cd /home/chove/桌面/apartment-intelligence-platform/rentHouseAdmin

# 安装依赖
npm install

# 开发模式
npm run dev
```

访问: http://localhost:5173

---

## 完整启动顺序

1. **基础设施**: MySQL, Redis, Milvus (etcd + MinIO)
2. **lease 服务**: web-app (8081), web-admin (8080)
3. **AI 服务**: AptGuide 1.0 (8100) 或 AptGuide 3.0, AptInsight (8000)
4. **前端**: rentHouseH5, rentHouseAdmin

```bash
# 1. 基础设施
cd /home/chove/桌面/apartment-intelligence-platform
docker-compose -f docker-compose.test.yml up -d mysql redis milvus

# 2. lease 服务
docker-compose -f docker-compose.test.yml up -d lease-web-app

# 3. AI 服务 (选择一个)
cd "AptGuide 3.0/backend"
uv run uvicorn src/aptguide3.api.app:app --port 8000

# 4. 前端
cd rentHouseH5 && npm run dev
```
