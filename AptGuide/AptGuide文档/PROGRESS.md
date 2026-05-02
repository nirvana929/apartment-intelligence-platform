# 项目进度记录

> 用途：记录 AptGuide 当前的工程进度与下一步要做的事，便于跨天 / 跨人续接。
> 更新时间：2026-05-01

---

## 一、已完成

### 1. 目录骨架

```text
AptGuide/
├── src/aptguide/{api,agent/{nodes,prompts},tools,vector,
│                 core,llm,knowledge/rules,schemas,security}/
├── scripts/
├── evals/datasets/
├── tests/{unit,contract}/
├── docs/{architecture,api,security}/
└── AptGuide文档/
```

各 `src/aptguide/*/__init__.py` 已 touch。

### 2. 顶层文件（4 份）

- ✅ `README.md` — 项目定位、与 AptInsight 对比、目录结构、快速开始
- ✅ `CLAUDE.md` — Claude Code 工作指引
- ✅ `AGENTS.md` — 通用 AI 编码 Agent 指引
- ✅ `SECURITY.md` — 安全约束总览

### 3. 工程化配置

- ✅ `pyproject.toml`（uv，FastAPI/LangGraph/pymilvus/httpx/openai 等，**不含** SQLAlchemy 系）
- ✅ `Makefile`（dev / test / lint / fmt / typecheck / eval / sync-vectors / seed-kb）
- ✅ `.env.example`（LLM、Embedding、Milvus、lease 后端、内部 token）
- ✅ `.gitignore`

### 4. 设计文档（`AptGuide文档/`，7 份）

- ✅ `README.md` — 文档索引
- ✅ `01-助手总体设计.md`
- ✅ `02-产品需求文档.md`
- ✅ `03-技术架构与模块设计.md`
- ✅ `04-Agent设计与提示词规范.md`
- ✅ `05-Java工具接口契约.md`
- ✅ `06-Milvus知识库设计.md`
- ✅ `07-测试验收方案.md`

### 5. 知识库原材料（`src/aptguide/knowledge/rules/`）

- ✅ `README.md` — 维护规范、schema 说明、写作要求
- ✅ `_schema.yaml` — 字段、枚举、禁用词、敏感模式正则
- ✅ `room_search.yaml` — 5 条
- ✅ `appointment.yaml` — 6 条
- ✅ `lease.yaml` — 7 条
- ✅ `payment.yaml` — 6 条
- ✅ `life.yaml` — 5 条

### 6. 仓库根 README

- ✅ 已把 AptGuide 加入 `apartment-intelligence-platform/README.md` 的项目结构与说明

---

## 二、未完成（明天优先做）

### A. 知识库剩余 YAML（约 9 条）

- [ ] `src/aptguide/knowledge/rules/account.yaml`（4 条）
  - KB-ACCT-001 注册与实名
  - KB-ACCT-002 修改个人信息和绑定手机
  - KB-ACCT-003 隐私和数据保护
  - KB-ACCT-004 注销账号

- [ ] `src/aptguide/knowledge/rules/policy.yaml`（5 条）
  - KB-POL-001 同住人规则
  - KB-POL-002 宠物政策
  - KB-POL-003 装修和软装变更
  - KB-POL-004 安全与禁止事项
  - KB-POL-005 退租清算细则

完成后知识库共 38 条，覆盖 7 个模块。

### B. 设计文档收尾

- [ ] 更新 `AptGuide文档/06-Milvus知识库设计.md`，加一节"原材料文件清单"，指向 `knowledge/rules/*.yaml`，并说明 `seed_kb.py` 的加载约定。
- [ ] 在 `AptGuide文档/04-Agent设计与提示词规范.md` 第 6 节末尾追加 1~2 个**具体提示词样例**（如 `intent_classify.md`、`recommend_reason.md` 的完整内容），让开发者照搬即可起步。

### C. 知识库工具脚本

- [ ] `scripts/validate_kb.py` — 按 `_schema.yaml` 校验：唯一 doc_id、长度、枚举、禁用词、敏感正则。CI 入口。
- [ ] `scripts/seed_kb.py` — 读取 `knowledge/rules/*.yaml` → embedding → 写入 Milvus `apt_rental_kb`。

---

## 三、下一阶段（代码骨架）

按 `CLAUDE.md`「开发顺序」启动，建议每一步独立提一次 PR：

1. **配置与日志** — `core/config.py`（pydantic-settings 加载 `.env`）+ `core/logging.py`（JSON 日志）。
2. **Java 工具客户端骨架** — `tools/client.py`（httpx，注入 `X-Internal-Token`、`X-User-Id`、`X-Request-Id`，超时 + tenacity 重试）。
3. **Milvus 客户端** — `vector/client.py`（pymilvus 连接）+ `vector/embedding.py`（embedding 客户端封装）+ `vector/room_index.py` + `vector/kb_search.py`。
4. **LLM 客户端** — `llm/client.py`（OpenAI 兼容）+ `llm/schemas.py`（结构化输出 Pydantic）。
5. **LangGraph 节点** — `agent/state.py` → `agent/nodes/{intent,slot,ask,tool,confirm,rerank,reply}.py` → `agent/graph.py`。
6. **HTTP 路由** — `api/chat.py`（POST `/api/chat`）+ `api/health.py`（GET `/health`、`/health/deps`）+ `main.py`。
7. **评测集** — `evals/datasets/{room_search,appointment,lease,kb_qa,multi_turn}_cases.yaml` + `evals/runner.py`。
8. **联调** — 与 `lease`（Java）打通 happy path。

---

## 四、未决问题（明天可与团队确认）

1. **lease 内部接口前缀**：文档中暂定 `/internal/ai/tools/`，需 Java 同事确认是否冲突 / 鉴权方案是否一致。
2. **embedding 模型**：默认 `text-embedding-v3`（DashScope，1024 维），需确认账号 / 配额可用。
3. **Milvus 实例位置**：MVP 期间是否本地起 Milvus standalone，还是直接接公司已有集群？
4. **知识库审核流程**：YAML 改动是否走 PR + 运营 review，还是单独维护一个运营后台？
5. **AI 写操作授权**：MVP 是否允许 AI 创建预约？还是先纯只读、写操作仅给"建议"？

---

## 五、明天续接的最简起手方式

```bash
# 1. 快速回顾上下文
cd /home/chove/桌面/apartment-intelligence-platform/AptGuide
cat AptGuide文档/PROGRESS.md
cat CLAUDE.md

# 2. 续写知识库（先把剩余两个 YAML 写完）
$EDITOR src/aptguide/knowledge/rules/account.yaml
$EDITOR src/aptguide/knowledge/rules/policy.yaml

# 3. 然后继续设计文档收尾或开始写代码
```

或者直接告诉 Claude："继续完成 PROGRESS.md 里未完成的 A、B 部分"。
