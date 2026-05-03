# 项目进度记录

> 用途：记录 AptGuide 当前的工程进度与下一步要做的事，便于跨天 / 跨人续接。
> 更新时间：2026-05-03

---

## 一、已完成

### 1. 阶段一：项目骨架与基础设施

- ✅ 目录骨架（`src/aptguide/{api,agent/{nodes,prompts},tools,vector,core,llm,knowledge/rules,schemas,security,memory,ui}/`）
- ✅ 顶层文件：README.md、CLAUDE.md、AGENTS.md、SECURITY.md
- ✅ `pyproject.toml`（uv，FastAPI/LangGraph/pymilvus/httpx/openai 等）
- ✅ `Makefile`（dev / test / lint / fmt / typecheck / eval / sync-vectors / seed-kb）
- ✅ `.env.example` + `.env`（LLM、Embedding、Milvus、Redis 配置）
- ✅ `core/config.py`（pydantic-settings，`extra: "ignore"` 处理多余环境变量）
- ✅ `core/logging.py`（JSON 结构化日志）
- ✅ 7 份设计文档（`AptGuide文档/` 目录）

### 2. 阶段二：核心对话能力

- ✅ `llm/client.py` — OpenAI 兼容 LLM 客户端（DashScope/Qwen）
- ✅ `vector/client.py` — Milvus 客户端封装
- ✅ `vector/embedding.py` — Embedding 客户端封装
- ✅ `vector/kb_search.py` — 知识库检索
- ✅ `vector/room_index.py` — 房源向量索引
- ✅ `agent/state.py` — LangGraph 状态定义
- ✅ `agent/graph.py` — 工作流图（9 个节点）
- ✅ Agent 节点：`intent.py`、`slot.py`、`ask.py`、`kb_search.py`、`room_search.py`、`rerank.py`、`reply.py`
- ✅ `api/chat.py` — POST `/api/chat` 路由
- ✅ `api/health.py` — GET `/health`、`/health/deps`
- ✅ `main.py` — FastAPI 应用入口，线程安全的 Agent 图初始化
- ✅ `schemas/request.py` + `schemas/response.py` — Pydantic 请求/响应模型
- ✅ 前端 UI：`ui/index.html`、`ui/app.js`、`ui/style.css`
  - XSS 防护（`escapeHtml()`）
  - 房源卡片渲染（含预约看房按钮 + 时间选择弹窗）
  - 预约确认交互（确认/取消按钮）
  - 预约列表卡片、租约卡片
  - 加载动画（三点跳动）
  - 快捷操作按钮（找房、我的预约、我的租约、押金规则）

### 3. 阶段三：预约流程与会话管理

- ✅ `tools/schemas.py` — 6 个工具接口 Pydantic 模型
- ✅ `tools/mock.py` — MockToolClient（MVP 阶段模拟预约创建/查询、租约查询）
- ✅ `memory/session.py` — SessionMemory（支持 Redis / 内存降级）
- ✅ `agent/nodes/confirm.py` — 确认节点（LLM 生成确认摘要）
- ✅ `agent/nodes/tool.py` — 工具调用节点（预约创建、预约查询、租约查询）
- ✅ 意图识别支持：`appointment_query`、`lease_query`
- ✅ Docker 服务：etcd + minio + Milvus v2.4.17 + Redis 7
- ✅ 知识库已注入：70 条 KB 规则（7 个模块）+ 150 条房源向量

### 4. 测试

- ✅ 48 个测试通过
- ⏭️ 2 个跳过（e2e 测试需要服务运行）

### 5. 知识库原材料（`src/aptguide/knowledge/rules/`）

- ✅ `_schema.yaml` — 字段、枚举、禁用词、敏感模式正则
- ✅ `room_search.yaml`（5 条）
- ✅ `appointment.yaml`（6 条）
- ✅ `lease.yaml`（7 条）
- ✅ `payment.yaml`（6 条）
- ✅ `life.yaml`（5 条）
- ✅ `account.yaml`（8 条）
- ✅ `policy.yaml`（10 条）

---

## 二、未完成

### A. 知识库 YAML

- [x] `src/aptguide/knowledge/rules/account.yaml`（8 条）
- [x] `src/aptguide/knowledge/rules/policy.yaml`（10 条）

知识库共 47 条规则，覆盖 7 个模块。✅

### B. 测试修复

- [x] `tests/unit/test_config.py::test_settings_default_values` — 已修复（`app_env` 默认值 `"dev"`）
- [x] `tests/unit/test_llm.py::test_llm_client_generate` — 已修复（改为直接 mock 实例属性）

### C. 文档收尾

- [x] 更新 `AptGuide文档/06-Milvus知识库设计.md`，加"原材料文件清单"节
- [x] 在 `AptGuide文档/04-Agent设计与提示词规范.md` 追加完整提示词样例

### D. Mock → 真实工具对接

- [ ] 替换 `MockToolClient` 为真实 Java 后端客户端（`LEASE_BASE_URL` 已在 `.env.example` 预留）
- [ ] 实现 `tools/client.py`（httpx，注入鉴权头，超时 + tenacity 重试）

---

## 三、当前运行状态

| 服务 | 端口 | 状态 |
|------|------|------|
| AptGuide FastAPI | 8100 | 运行中 |
| Milvus | 19530 | 运行中（Docker） |
| Redis | 6379 | 运行中（系统服务） |
| etcd | 2379 | 运行中（Docker） |
| MinIO | 9000 | 运行中（Docker） |

访问地址：`http://<Ubuntu-IP>:8100`

---

## 四、未决问题

1. **lease 内部接口前缀**：文档中暂定 `/internal/ai/tools/`，需 Java 同事确认。
2. **embedding 模型**：默认 `text-embedding-v3`（DashScope，1024 维），需确认配额。
3. **Milvus 实例位置**：MVP 本地 standalone，后续是否接公司集群？
4. **知识库审核流程**：YAML 改动走 PR + 运营 review，还是运营后台？
5. **AI 写操作授权**：MVP 用 MockToolClient 模拟，后续是否允许真实创建预约？

---

## 五、续接起手方式

```bash
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
cat AptGuide文档/PROGRESS.md
cat CLAUDE.md

# 补写知识库
$EDITOR src/aptguide/knowledge/rules/account.yaml
$EDITOR src/aptguide/knowledge/rules/policy.yaml

# 或开始 Mock → 真实工具对接
$EDITOR src/aptguide/tools/client.py
```
