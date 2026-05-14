---
type: outcomes
status: active
---

# 系统集成与 Live Eval 成果复盘

> 日期：2026-05-14
> 范围：`backend/scripts/check_live_dependencies.py`、`backend/evals/runners/run_rag_v2.py`、`backend/src/aptguide2/api/schemas.py`、`backend/src/aptguide2/system/`

## 背景

AptGuide 2.0 已完成 Harness Foundation、Tool Governance、RAG v2、Harness Correction 四个阶段，292 个本地测试全部通过。但从未在真实 Milvus、embedding、lease 环境下运行过 RAG v2 live eval，也没有验证过 `/chat` API 是否能承载 harness 预约确认流程。

本轮目标：补齐系统集成能力，用真实环境跑一次并记录真实状态。

## 做了什么

### 1. Live Dependency Readiness 模块

新建 `aptguide2.system.readiness`：

- `DependencyCheck`：单个依赖检查结果（name, ok, required, detail）
- `ReadinessReport`：聚合多个检查，`all_required_ok` 判断是否全部就绪
- `render_markdown_report()`：生成可读 Markdown 报告
- CLI 脚本 `scripts/check_live_dependencies.py`：检查 Milvus、embedding、lease 三项

```bash
cd "AptGuide 2.0/backend"
uv run python scripts/check_live_dependencies.py --report ../reports/live-dependency-readiness-report.md
```

### 2. RAG v2 Eval Runner 修复

原 `run_rag_v2.py` 有两个问题：

1. 传 `settings=settings` 给 `run_pipeline_v2()`，但函数签名不接受 `settings`
2. 未传 `vector_adapter` 和 `lease_validator`

修复：新增 `RagV2EvalDependencies` dataclass，eval 函数签名改为 `(case, deps)`，`run_eval()` 构建一次 deps 传给所有 evaluator。

### 3. Eval Cases 数据修正

首次运行 live eval 时发现 eval cases 的 doc ID 和 room ID 与 Milvus 真实数据不匹配：

| 问题 | 修正 |
|---|---|
| `KB-APPOINT-*` vs `KB-APPT-*` | 统一为 `KB-APPT-*` |
| `KB-ACCOUNT-*` vs `KB-ACCT-*` | 统一为 `KB-ACCT-*` |
| Room IDs 3001, 3002 等占位符 | 替换为 Milvus 真实 room IDs |
| 部分 query→doc 映射语义不准 | 基于 KB 实际 title 重新映射 |

### 4. /chat API 契约扩展

| 字段 | 方向 | 用途 |
|---|---|---|
| `user_id` | Request | 用户身份，预约创建和查询必需 |
| `action` | Request | 确认/取消动作（含 confirmation_id） |
| `client_context` | Request | 客户端上下文 |
| `phase` | Response | 当前阶段（如 appointment_needs_confirmation） |
| `actions` | Response | 可用操作列表 |
| `pending_action` | Response | 待确认动作 |
| `metadata` | Response | 流程元数据（procedure, room_id 等） |

所有新字段 optional/默认值，不破坏现有客户端。

## 真实环境探索

### 启动顺序

```bash
# 1. Milvus（Docker）
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
docker-compose up -d etcd minio milvus redis
sleep 15

# 2. Lease 后端（Docker，连接宿主 MySQL 和 Redis）
docker run -d --name aip-lease-web-app \
  -e MYSQL_URL="jdbc:mysql://host.docker.internal:3306/least?..." \
  -e MYSQL_USERNAME=chove -e MYSQL_PASSWORD=123456 \
  -e REDIS_HOST=host.docker.internal -e REDIS_PORT=6380 \
  -e AI_INTERNAL_TOKEN=aptguide-internal-token-2026 \
  -p 8081:8081 \
  --add-host=host.docker.internal:host-gateway \
  apartment-intelligence-platform-lease-web-app:latest

# 3. Embedding 已在 .env 配置（DashScope text-embedding-v3, dim=1024）
```

### 数据现状

| 服务 | 状态 | 数据量 |
|---|---|---|
| Milvus | localhost:19530 | 126 rooms, 70 KB vectors |
| Embedding | DashScope API | text-embedding-v3, dim=1024 |
| Lease | localhost:8081 | 健康检查通过 |

## Live Eval 真实结果

### Eval Cases 修正前后对比

| 指标 | 修正前（首次） | 修正后 |
|---|---|---|
| KB hit@3 | 14.3% | 48.6% |
| KB hit@5 | 14.3% | 51.4% |
| Room hit@5 | 0.0% | 40.0% |
| High-risk fallback | 100% | 100% |
| Failed cases | 35 | 20 |

### 剩余失败分类

**KB 检索失败（17/35）：**

- 11 cases 返回空结果（no KB sources）— pipeline 检索层根本没命中
- 6 cases 期望 doc 在 Milvus 但不在 top-5 — 排名质量问题

涉及模块：PAY（支付）、LIFE（生活）、APPT（预约）、LEASE（租约）

**Room 检索失败（3/5）：**

- 2 cases 返回空结果 — district_id 过滤后无匹配
- 1 case 返回错误 district 的房源 — 语义检索优先于 filter

**Fallback（15/15）：** 全部通过，边界保护正常。

### 根因分析

1. **Query Understanding 局限**：规则引擎对部分 query（如"可以用花呗付房租吗"、"入住需要带什么"）未正确识别为 kb_qa，导致走错路径
2. **KB 检索阈值过高**：confidence gate 过滤掉了低分但正确来源
3. **Room Filter 精度**：district_id 匹配依赖 query 中的区域关键词提取，部分 query 提取失败
4. **Eval case 覆盖度**：55 cases 中 35 个 KB case 只覆盖了部分查询模式

## 已产出文件

| 文件 | 说明 |
|---|---|
| `reports/live-dependency-readiness-report.md` | 依赖 readiness 检查结果 |
| `reports/rag-v2-live-evaluation-report.md` | RAG v2 live eval 真实结果 |
| `reports/evaluation-report.md` | 全阶段评测汇总（含 system integration 章节） |
| `docs/tests/system-smoke-checklist.md` | 系统 smoke 验收命令 |
| `backend/src/aptguide2/system/readiness.py` | Readiness 模块 |
| `backend/scripts/check_live_dependencies.py` | Readiness CLI |
| `backend/evals/runners/run_rag_v2.py` | 修复后的 eval runner |
| `backend/tests/unit/evals/test_run_rag_v2.py` | Eval runner 单测 |
| `backend/tests/unit/system/test_readiness.py` | Readiness 单测 |

## 面试可讲述的点

1. **"我跑过真实环境的 eval"** — 不是只跑 mock 测试，而是连真实 Milvus + embedding + lease 跑了 55 cases
2. **"我发现 eval cases 数据有错"** — doc ID 命名不一致（APPOINT vs APPT），room ID 是占位符，修正后结果从 14% 提升到 49%
3. **"我知道剩下的问题是检索质量"** — 11 个 KB 查询返回空结果是 query understanding 的问题，不是数据问题
4. **"我设计了 readiness check"** — 不是直接跑 eval 然后报错，而是先检查依赖是否就绪，再决定是否跑 eval
5. **"API 契约是向后兼容的"** — 所有新字段 optional，不破坏现有客户端

## 下一步

| 优先级 | 任务 | 预期提升 |
|---|---|---|
| P0 | 优化 query understanding，让更多 query 正确识别为 kb_qa | KB hit@3 +20% |
| P1 | 调整 confidence gate 阈值 | KB hit@3 +10% |
| P1 | 修复 room retrieval filter 逻辑 | Room hit@5 +30% |
| P2 | 增加 eval cases 覆盖度（补充 PAY/LIFE 模块） | 评测更全面 |
