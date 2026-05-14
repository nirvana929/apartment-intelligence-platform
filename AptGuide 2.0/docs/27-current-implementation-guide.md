# 27 · 当前实现导览

本文档按当前代码说明 `AptGuide 2.0` 已经实现了什么、主程序在哪里、一次请求如何流转、数据如何进入向量库，以及应该按什么顺序阅读代码。

> 如果你只想理解”现在项目能跑什么”，先读本文档。其他 `docs/01` 到 `docs/26` 里有很多完整产品规划和后续架构设计，不都等于当前已经落地的代码。
>
> 完整成果报告见 [docs/28-rag-mvp-achievement-report.md](docs/28-rag-mvp-achievement-report.md)。

## 当前实现一句话

当前 `AptGuide 2.0` 已经实现为一个 **企业级租房 Agent harness + RAG v2 检索系统**：

- 对外提供 `/health` 和 `/chat` 两个 API；
- `/chat` 默认进入 `AptGuideHarness`，harness 是唯一产品运行时；
- 旧 RAG MVP pipeline 已从 API、harness procedure 和 system e2e acceptance 中断开，仅保留为 legacy reference；
- RAG v2 作为 harness 内部检索模块，用于 room search 和 KB QA；
- `run_pipeline_v2()` 提供 RetrievalPlanning、Lease Validation Gate、Trace 支持；
- 房源和知识库数据通过离线脚本写入 Milvus；
- 知识库问答在检索后用 LLM 基于来源内容生成中文回答；
- 房源推荐返回结构化房源列表和推荐理由；
- 单元测试和端到端测试覆盖主要链路。

**当前数据规模**：126 间房源（广州 5 区 + 北京昌平）、70 条 KB 规则（7 个模块）、323 个测试全部通过（308 unit + 15 e2e），ruff clean。

**Live 验证状态**：Milvus、embedding、lease 全部就绪，readiness 含 pipeline 版本检查。RAG v2 live eval 已真实运行（55 cases），KB hit@3=48.6%，Room hit@5=40%，Fallback 100%。当前 active objective 是 RAG 检索质量提升。

**已完成主线**：系统功能完善与主线统一已完成。执行记录见 [plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md](./plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md)。

## 当前主程序

当前 Web 服务入口是：

```text
backend/src/aptguide2/api/app.py
```

FastAPI app 定义在：

```python
app = FastAPI(title="AptGuide 2.0", version="0.1.0")
```

目前实现了两个接口：

```text
GET  /health
POST /chat
```

本地启动方式：

```bash
cd "AptGuide 2.0/backend"
uv run uvicorn aptguide2.api.app:app --reload
```

启动前需要准备 `.env`，参考：

```text
backend/.env.example
```

核心环境变量包括：

```text
APTGUIDE_MILVUS_URI
APTGUIDE_EMBEDDING_API_KEY
APTGUIDE_EMBEDDING_BASE_URL
APTGUIDE_EMBEDDING_MODEL
APTGUIDE_EMBEDDING_DIM
APTGUIDE_LLM_API_KEY
APTGUIDE_LLM_BASE_URL
APTGUIDE_LLM_MODEL
APTGUIDE_LEASE_BASE_URL
APTGUIDE_KB_RULES_DIR
```

## 代码结构

```text
backend/src/aptguide2/
├── api/
│   ├── app.py          # FastAPI 入口，定义 /health 和 /chat（/chat 进入 harness mainline）
│   ├── deps.py         # API 依赖：Settings、VectorAdapter、embedding、LLM client、harness、tool_runtime
│   └── schemas.py      # API 请求和响应模型
├── core/
│   └── config.py       # 环境变量配置（含 pipeline_version 和 harness_include_trace）
├── harness/            # 企业级 harness 系统底座
│   ├── contracts.py    # AptGuideRequest, ConversationFrame, RouteDecision, ProcedureResult, StageTrace, AptGuideTrace, AptGuideResponse
│   ├── errors.py       # StrategyNotFoundError, ProcedureNotFoundError, ReplayPIIError
│   ├── registry.py     # StrategyRegistry
│   ├── context.py      # InMemoryContextStore
│   ├── safety.py       # SafetyBoundary (keyword matching)
│   ├── routing.py      # HybridRouter (priority: safety > capability > handoff > appointment > kb > room > fallback)
│   ├── procedures.py   # Procedure Protocol + ProcedureRuntime
│   ├── composer.py     # ResponseComposer
│   ├── trace.py        # TraceRecorder
│   ├── replay.py       # ReplayWriter (PII-guarded JSONL)
│   ├── memory.py       # MemoryManager (recent messages, pending action, tool observations)
│   ├── orchestrator.py # AptGuideHarness.run()
│   ├── modules/
│   │   ├── appointment.py
│   │   ├── capability.py
│   │   ├── fallback.py
│   │   ├── handoff.py
│   │   ├── lease.py
│   │   └── rag/v2.py       # RAG v2 harness procedure
│   └── tools/          # 工具治理层
│       ├── contracts.py    # ToolDefinition, ToolCallRequest, ToolCallResult, ToolError, 8 MVP schemas
│       ├── errors.py       # ToolAlreadyRegisteredError, ToolNotFoundError, ToolTimeoutError, ToolExecutionError
│       ├── registry.py     # ToolRegistry
│       ├── builtins.py     # build_default_tool_registry() with 8 MVP tools
│       ├── runtime.py      # ToolRuntime (permission checks, confirmation gates, executor dispatch)
│       ├── trace.py        # summarize_tool_request, summarize_tool_result, redact_pii
│       ├── lease_tools.py  # 6 lease executors
│       └── vector_tools.py # KBSearchExecutor
├── rag/
│   ├── pipeline.py         # 旧 RAG MVP 主工作流，仅 legacy reference
│   ├── pipeline_v2.py      # RAG v2 主工作流，作为 harness 内部模块
│   ├── planning.py         # RetrievalPlan, build_retrieval_plan()
│   ├── sparse.py           # sparse_score() 本地稀疏词法评分
│   ├── hybrid.py           # HybridCandidate, merge_hybrid_candidates()
│   ├── rerank.py           # RerankWeights, rerank_kb_sources()
│   ├── validation.py       # LeaseRoomValidator, validate_room_candidates()
│   ├── tool_validation.py  # ToolRuntimeRoomValidator
│   ├── eval_metrics.py     # hit_at_k, mean_reciprocal_rank, ndcg_at_k
│   ├── query_understanding.py
│   ├── room_retrieval.py
│   ├── kb_retrieval.py
│   ├── ranking.py
│   ├── confidence.py
│   ├── chunking.py
│   └── schemas.py
├── tools/
│   ├── vector_adapter.py
│   └── lease_adapter.py
├── system/
│   ├── __init__.py
│   └── readiness.py      # DependencyCheck, ReadinessReport, render_markdown_report
├── trace/
│   └── retrieval_events.py
└── data_import/
    └── wechat_local_mysql_parser.py
```

其他重要目录：

```text
backend/scripts/          # 离线同步和造数脚本
backend/evals/            # RAG 评测数据和 runner
backend/tests/            # 单元测试和 e2e 测试
backend/knowledge/rules/  # 租房规则知识库 YAML
```

## 一次 /chat 请求如何流转

`POST /chat` 的入口在 `api/app.py`。当前 `/chat` 只进入 harness mainline：

```text
ChatRequest
  ↓
get_aptguide_harness()
  ↓
AptGuideHarness.run()
  ↓
HybridRouter
  ├── capability.profile
  ├── rag.room_search -> RagV2Procedure -> run_pipeline_v2()
  ├── rag.kb_qa -> RagV2Procedure -> run_pipeline_v2()
  ├── appointment.workflow
  ├── lease.workflow
  ├── handoff.user_initiated / handoff.tool_failure
  └── fallback.safety / fallback.unknown
  ↓
ResponseComposer
  ↓
_build_response_from_harness()
  ↓
ChatResponse
```

请求模型：

```json
{
  "message": "番禺区1500以内的房子",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id",
  "action": {"type": "confirm", "confirmation_id": "..."},
  "client_context": {}
}
```

响应模型：

```json
{
  "task": "room_search",
  "message": "...",
  "phase": "room_results",
  "cards": [],
  "rooms": [],
  "kb_sources": [],
  "is_confident": false,
  "actions": [],
  "pending_action": null,
  "metadata": {}
}
```

`user_id` 用于 harness 预约和用户身份校验。`action` 用于 harness 确认流程（如预约确认）。`cards` 是正式支持的通用卡片字段，`rooms` 是 room card 的兼容投影。`pending_action` 和 `actions` 在 harness 预约流程中返回。

## RAG 主工作流

当前主工作流在：

```text
backend/src/aptguide2/rag/pipeline.py
```

核心函数：

```python
run_pipeline(message, vector_adapter, embed_fn, previous_state=None, top_n_rooms=5)
```

整体流程：

```text
用户 message
  ↓
understand_query()
  ↓
得到 QueryUnderstandingResult
  ↓
按 task 分流
  ├── room_search → retrieve_rooms → enrich_candidates_from_vector → rank_rooms
  ├── kb_qa       → retrieve_kb → check_confidence
  └── fallback    → 固定安全回复
```

`PipelineResult` 是内部结果模型，包含：

```text
task
message
rooms
kb_sources
is_confident
fallback_reason
query_understanding
```

## Query Understanding

文件：

```text
backend/src/aptguide2/rag/query_understanding.py
```

它不调用 LLM，使用规则把用户输入拆成结构化结果：

```text
raw_message
task
reference_resolution
hard_filters
soft_preferences
retrieval_queries
risk_level
```

当前支持的任务类型：

```text
room_search  # 找房
kb_qa        # 租房规则、押金、合同、预约、报修等知识库问答
fallback     # 超出范围或不适合回答
```

典型例子：

```text
输入：番禺区1500以内安静一点的房子
输出：
task = room_search
hard_filters = {"district_id": 4, "area_text": "番禺", "max_rent": 1500}
soft_preferences = ["安静", "适合学习", "低噪音"]
retrieval_queries = [...]
```

这里的核心思想是：

- 预算、区域属于硬过滤，适合交给 Milvus filter；
- 安静、近地铁、考研、采光属于软偏好，适合做向量召回和排序；
- 押金、退租、合同等问题会被标记为高风险，后续需要更严格的置信度。

## 找房路径

找房路径从 `pipeline.py` 进入：

```text
_handle_room_search()
```

然后依次调用：

```text
retrieve_rooms()
enrich_candidates_from_vector()
rank_rooms()
```

对应文件：

```text
backend/src/aptguide2/rag/room_retrieval.py
backend/src/aptguide2/rag/ranking.py
```

当前找房流程：

```text
QueryUnderstandingResult
  ↓
_build_filters()
  ↓
Milvus filter:
  status == active
  district_id == ...
  rent <= ...
  ↓
多路向量召回:
  original user query
  generated_0
  generated_1
  generated_2
  ↓
按 room_id 去重，保留最高 semantic_score
  ↓
按 room_id 批量补全房源字段
  ↓
rank_rooms()
```

排序维度：

```text
semantic_score      语义匹配
budget_score        预算匹配
area_score          区域匹配
tag_score           标签/设施偏好匹配
availability_score  当前默认 1.0，后续应由 lease 校验
```

当前需要注意：

- `rank_rooms()` 里的 `availability_score` 还是默认值；
- 真实可租、可预约校验还没有完整接入主流程；
- 找房 API 返回的是推荐列表，不会自动执行预约等写操作。

## 知识库问答路径

知识库问答路径从 `pipeline.py` 进入：

```text
_handle_kb_qa()
```

然后调用：

```text
retrieve_kb()
check_confidence()
```

对应文件：

```text
backend/src/aptguide2/rag/kb_retrieval.py
backend/src/aptguide2/rag/confidence.py
```

当前 KB 检索流程：

```text
QueryUnderstandingResult
  ↓
构造多路召回 query
  ├── original
  ├── normalized
  └── step_back
  ↓
搜索 Milvus apt_rental_kb
  ↓
按 chunk_id 合并
  ↓
source rerank
  ↓
转成 KBSource
  ↓
check_confidence()
```

`step_back` 的作用是把具体问题上提到规则层面，例如：

```text
押金什么时候退
  → 租房押金退还规则 流程
```

置信度规则：

```text
low    top score >= 0.45
medium top score >= 0.55，并且前 3 个来源里有关键模块
high   top score >= 0.65，并且前 3 个来源里有 high risk 的 lease/payment 来源
```

如果置信度不够，系统不生成答案，而是返回人工确认或查看合同的提示。

如果置信度足够，`api/app.py` 会调用 LLM：

```text
KBSource top 3
  ↓
拼成 context
  ↓
OpenAI-compatible chat.completions.create()
  ↓
生成最终中文回答
```

这一步的原则是：只根据检索到的知识库内容回答，不允许编造。

## Fallback 路径

如果 `understand_query()` 判断问题不属于租房服务范围，进入 fallback：

```text
帮我写代码
你保证没问题
1+1等于几
```

返回固定话术：

```text
抱歉，这个问题超出了我的服务范围。我是租房助手，可以帮您找房或回答租房相关问题。
```

fallback 的作用是保护产品边界：`AptGuide 2.0` 不是通用聊天机器人，而是租房助手。

## 数据如何进入向量库

当前使用 Milvus 两个 collection：

```text
apt_room_vector   # 房源向量
apt_rental_kb     # 知识库 chunk 向量
```

Milvus 适配器：

```text
backend/src/aptguide2/tools/vector_adapter.py
```

它负责：

```text
ensure_room_collection()
ensure_kb_collection()
upsert_room_records()
upsert_kb_chunks()
search_rooms()
search_kb()
get_room_by_ids()
get_kb_chunks_by_ids()
mark_room_inactive()
mark_kb_inactive()
```

### 房源入库

脚本：

```text
backend/scripts/sync_room_vectors.py
```

流程：

```text
lease 后端 /internal/ai/tools/sync/rooms
  ↓
build_room_vector_record()
  ↓
embedding
  ↓
upsert_room_records()
  ↓
Milvus apt_room_vector
```

房源文本构造在：

```text
backend/src/aptguide2/rag/chunking.py
```

### 知识库入库

脚本：

```text
backend/scripts/sync_kb_vectors.py
```

流程：

```text
backend/knowledge/rules/*.yaml
  ↓
validate_rules()
  ↓
build_kb_chunks()
  ↓
embedding
  ↓
upsert_kb_chunks()
  ↓
Milvus apt_rental_kb
```

入库前会检查：

```text
doc_id 是否存在
doc_id 是否重复
status 是否 reviewed/approved/active
reviewed_by 是否存在
content 是否包含手机号/身份证/银行卡等 PII
高风险模块是否标注 risk_level
```

### Mock 房源入库

脚本：

```text
backend/scripts/seed_mock_rooms.py
```

用途：

- 本地调试；
- RAG MVP 评测；
- 在真实 lease 数据不完整时先跑通房源召回。

## 外部系统适配

### LeaseAdapter

文件：

```text
backend/src/aptguide2/tools/lease_adapter.py
```

当前实现：

```text
health()
sync_rooms()
search_rooms()
get_room_detail()
```

它负责把 Python snake_case 和 Java camelCase 互相转换，并处理 lease 后端统一响应 envelope。

当前主 RAG pipeline 主要通过 `sync_room_vectors.py` 使用 `sync_rooms()` 做离线房源同步；在线 `/chat` 的房源检索主要查 Milvus。

### OpenAI-compatible API

当前 embedding 和 LLM 都走 OpenAI 兼容接口：

```text
embedding:
  client.embeddings.create()

LLM:
  client.chat.completions.create()
```

所以可以接 OpenAI，也可以接兼容 OpenAI API 的供应商。

## Trace 和安全

文件：

```text
backend/src/aptguide2/trace/retrieval_events.py
```

当前实现了：

```text
build_retrieval_finished_event()
build_tool_trace_event()
validate_no_pii()
```

Trace 里禁止出现这些 PII key：

```text
phone
id_card
contract_no
address_detail
bank_card
email
real_name
id_number
passport
payment_account
```

当前 trace builder 已有单元测试，但主 `/chat` 请求还没有把 trace 事件完整接入持久化或外部观测平台。

## 评测和测试

### 单元测试

覆盖：

```text
query_understanding (28 tests)
chunking (12 tests)
room_retrieval (8 tests)
kb_retrieval (10 tests)
ranking (9 tests)
schemas (8 tests)
vector_adapter (6 tests)
lease_adapter (12 tests)
trace (12 tests)
data_import (28 tests)
harness (57 tests)
harness/tools (59 tests)
harness/appointment (11 tests)
harness/memory (19 tests)
harness/handoff (5 tests)
rag/planning (3 tests)
rag/hybrid (3 tests)
rag/rerank (2 tests)
rag/validation (3 tests)
rag/eval_metrics (3 tests)
rag/pipeline_v2_trace (1 test)
```

运行：

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit
```

### E2E 测试

覆盖：

```text
/health
/chat harness mainline capability
/chat harness mainline fallback
/chat harness mainline room_search through RAG v2
/chat harness mainline kb_qa through RAG v2
/chat appointment pending_action
/chat appointment confirmation
/chat appointment cancel confirmation
/chat lease list
/chat handoff
legacy RAG isolated tests (not system acceptance)
```

运行：

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/e2e
```

完整测试报告见 [evals/reports/test_report.md](../evals/reports/test_report.md)。

### RAG 评测

评测 runner：

```text
backend/evals/runners/run_rag_mvp.py
backend/evals/runners/run_rag_eval.py
backend/evals/runners/run_rag_v2.py
```

评测数据：

```text
backend/evals/datasets/rag_mvp_eval_cases.yaml
backend/evals/datasets/rag_mvp_retrieval_cases.yaml
```

评测报告：

```text
backend/evals/reports/
```

## 当前已经实现和未实现

### 已经实现

```text
FastAPI /health
FastAPI /chat (harness mainline only)
API request/response schema
RAG pipeline v1 (legacy reference only, disconnected from public interfaces)
RAG pipeline v2 (harness internal module with hybrid retrieval + governed rerank + lease validation)
Harness orchestrator (contracts, routing, procedures, trace, replay, memory)
Tool governance (registry, runtime, executors, trace summaries)
Appointment workflow (create/cancel with two-turn pending-action confirmation, list with auth check)
Lease workflow (lease.list_mine through governed tools)
Handoff procedure (user-initiated, tool-failure-triggered, orchestrator auto-trigger after 2 consecutive failures)
Memory manager (recent messages, pending action lifecycle, tool observations)
Pending-action-aware routing (confirmation/cancel messages route to appointment workflow)
确定性 query understanding
Retrieval planning (hard filters / semantic queries 分离)
Hybrid retrieval (dense + sparse merge, dedup, channel attribution)
Governed rerank (显式特征权重, lexical capped at 5%)
Lease validation gate (无 lease 验证不展示房源)
房源向量召回
房源多维重排
KB 多路召回
KB source rerank
KB confidence gate
KB LLM answer generation
Milvus adapter
Lease adapter (含 X-Internal-Token 认证)
KB YAML 入库脚本 (含 doc_id 去重)
房源同步入库脚本
Mock 房源 seed 脚本
Trace event builder
RAG eval runner (v1 + v2)
Eval metrics (hit@k, MRR, nDCG)
Character-match audit (keep/weaken/replace)
Eval gates 文档
LangSmith 可观测性配置
District ID 映射修正 (1-11, 110114)
Live dependency readiness check (aptguide2.system.readiness)
RAG v2 live eval runner (RagV2EvalDependencies, 正确 wiring)
System smoke checklist
API contract 扩展 (user_id, action, cards, pending_action, actions, metadata)
unit tests (308 个)
e2e tests (15 个)
```

### 尚未完整实现

```text
前端聊天应用
长期用户偏好画像
Agent planner / specialist agents
真实在线 lease availability validation 需要继续观察 live 环境一致性
人工接管（HandoffProcedure 已实现，待接入外部客服系统）
Trace 持久化和可观测平台接入
权限认证和用户身份体系
MCP 封装
RAGAS 自动化评测闭环
RAG v2 live eval 检索质量优化 (当前 KB hit@3=48.6%, Room hit@5=40%)
```

## 推荐阅读顺序

如果你是第一次学习项目，按这个顺序读：

1. `README.md`：了解项目定位。
2. `docs/00-start-here.md`：了解文档地图。
3. 本文档：理解当前已经实现的系统。
4. `backend/src/aptguide2/api/app.py`：看 API 入口。
5. `docs/plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md`：看已完成的主线集成计划。
6. `backend/src/aptguide2/harness/orchestrator.py`：看系统主线编排。
7. `backend/src/aptguide2/harness/modules/appointment.py`：看预约流程。
8. `backend/src/aptguide2/harness/modules/rag/v2.py`：看 harness 如何挂载 RAG v2。
9. `backend/src/aptguide2/rag/query_understanding.py`：看用户输入如何被结构化。
10. `backend/src/aptguide2/rag/room_retrieval.py` 和 `ranking.py`：看找房链路。
11. `backend/src/aptguide2/rag/kb_retrieval.py` 和 `confidence.py`：看知识库问答链路。
12. `backend/src/aptguide2/rag/pipeline_v2.py`：看 RAG v2 检索主流程。
13. `backend/src/aptguide2/rag/chunking.py`：看入库文本如何构造。
14. `backend/src/aptguide2/tools/vector_adapter.py`：看 Milvus 如何封装。
15. `backend/scripts/sync_kb_vectors.py` 和 `sync_room_vectors.py`：看数据如何进入向量库。
16. `backend/tests/e2e/test_system_mainline.py` 和 `test_api.py`：看系统期望行为。

如果你想理解未来完整产品，再读：

```text
docs/01-product-requirements.md
docs/02-agent-framework-architecture.md
docs/03-domain-boundary-and-interaction-policy.md
docs/04-tool-and-integration-contract.md
docs/05-frontend-interaction-protocol.md
docs/14-api-and-schema-contract.md
docs/15-tool-registry-and-error-codes.md
docs/20-rag-retrieval-vector-mcp-evaluation-upgrade.md
docs/21-rag-final-implementation-scheme.md
```

## 学习时抓住的主线

读这个项目时不要先陷入所有设计文档。先抓住这条主线：

```text
用户输入
  ↓
API /chat
  ↓
run_pipeline()
  ↓
understand_query()
  ↓
room_search / kb_qa / fallback
  ↓
Milvus 检索
  ↓
排序或置信度判断
  ↓
API response
```

再抓住离线数据主线：

```text
业务数据 / YAML 知识库
  ↓
chunking.py 构造 embedding 文本
  ↓
OpenAI-compatible embedding
  ↓
Milvus
  ↓
在线 /chat 可检索
```

这两条线合起来，就是当前 AptGuide 2.0 已经实现的系统。
