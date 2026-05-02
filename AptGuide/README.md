# AptGuide

> **公寓管理系统 · 智能找房助手**
>
> 面向租客用户的对话式 AI 服务，基于自然语言完成找房推荐、看房预约、租约咨询和租房规则问答。

---

## 项目定位

AptGuide 是 `apartment-intelligence-platform` 仓库中面向 **租客（C 端）** 的智能助手服务，与面向运营人员（B 端）的 [`AptInsight`](../AptInsight) 互为补充。项目分两步建设：第一阶段先做可独立运行、带浏览器聊天界面的 AptGuide 应用；第二阶段再接入 `rentHouseH5`、`lease` 和 `AptInsight`，形成 C 端找房助手与 B 端运营分析助手的数据闭环。

| 项目 | 服务对象 | 数据访问方式 | 核心能力 |
|------|---------|------------|--------|
| `AptInsight` | 运营 / 管理员 | Text-to-SQL，直查 MySQL | 经营分析、指标看板 |
| **`AptGuide`** | 租客用户 | Tool-calling，调用 Java 接口 + Milvus | 找房、预约、咨询 |

AptGuide **不直接访问 MySQL**。所有业务数据通过 `lease`（Spring Boot）后端封装的工具接口获取，确保权限与脱敏在 Java 侧统一管控。模糊语义需求（如"安静、适合考研、通勤方便"）由 Milvus 向量检索召回候选房源，再由 Java 后端做精确字段过滤。

## 核心功能（MVP）

1. **独立聊天应用**：第一阶段提供浏览器界面，支持多轮对话、房源卡片、操作按钮和预约确认。
2. **自然语言找房**：解析预算、区域、支付方式、租期等显式条件 + 模糊偏好。
3. **智能房源推荐**：Milvus 语义召回 + Java 精确过滤 + Agent 推荐理由生成。
4. **多轮需求补全**：信息不足时主动追问，沿用上下文继续推荐。
5. **看房预约**：抽取房间、时间、用户身份；写操作前必须二次确认。
6. **个人租约 / 预约查询**：按当前登录用户 ID 查询，仅返回其本人数据。
7. **租房规则问答**：基于 Milvus 知识库的 RAG，回答预约、退租、续约、押金等 FAQ。
8. **系统集成闭环**：第二阶段由 `rentHouseH5 → lease → AptGuide` 接入真实业务，AI 预约和偏好数据可被 `AptInsight` 分析。

## 技术栈

- **运行时**：Python 3.12 + `uv`
- **Web 框架**：FastAPI + Pydantic v2
- **Agent 编排**：LangGraph
- **LLM**：OpenAI 兼容客户端（默认 Qwen / DashScope）
- **向量库**：Milvus 2.4
- **会话状态**：Redis
- **流式响应**：SSE
- **HTTP 客户端**：httpx（调用 Java 内部接口）
- **测试 / 工程化**：pytest、Ruff、mypy
- **本地编排**：Docker Compose（第二阶段）

## 系统架构（请求链路）

第一阶段独立应用：

```text
用户浏览器
        ↓ POST /api/chat
AptGuide Web UI + FastAPI + LangGraph
        ├─ Mock / Stub 工具数据（演示）
        ├─ Redis 会话状态 / 待确认操作
        └─ Milvus 房源语义召回 / 知识库 RAG
```

第二阶段系统集成：

```text
租客（rentHouseH5 移动端）
        ↓ POST /app/ai/chat   (用户态 JWT)
lease (Spring Boot)
        ↓ POST /api/chat       (内部 token + userId)
AptGuide (FastAPI + LangGraph)
        ├─ Milvus       房源语义召回 / 知识库 RAG
        ├─ Redis        多轮会话 / pending confirmation
        └─ Java 工具接口 房源精确过滤 / 预约 / 租约 / 浏览历史
                        ↓
                      MySQL
```

详见 `AptGuide文档/03-技术架构与模块设计.md`。

## 目录结构

```text
AptGuide/
├── AptGuide文档/        产品与架构文档（事实来源）
├── docs/                工程文档（API、安全、架构）
├── src/aptguide/
│   ├── api/             FastAPI 路由（/api/chat、/health）
│   ├── agent/           LangGraph 状态、图、节点、提示词
│   ├── tools/           Java 工具接口 HTTP 客户端
│   ├── vector/          Milvus 房源索引与知识库 RAG
│   ├── core/            配置、日志、错误
│   ├── llm/             LLM 客户端封装
│   ├── knowledge/       意图清单、待入库的规则原文
│   ├── schemas/         Pydantic 请求 / 响应 / 工具模型
│   └── security/        身份透传、敏感字段过滤
├── scripts/             离线脚本（同步房源向量、初始化 KB）
├── evals/               Agent 评测数据集与运行器
└── tests/               单元测试与契约测试
```

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 准备环境变量
cp .env.example .env
# 填入 LLM_API_KEY、MILVUS_URI、LEASE_BASE_URL、LEASE_INTERNAL_TOKEN

# 3. 初始化向量数据
uv run python scripts/seed_kb.py
uv run python scripts/sync_room_vectors.py

# 4. 启动开发服务器
make dev
```

服务默认监听 `http://0.0.0.0:8100`，由 `lease` 后端通过内部 token 调用。

## 文档

- `AptGuide文档/01-助手总体设计.md` — 定位、用户场景、范围边界
- `AptGuide文档/02-产品需求文档.md` — 功能清单、对话样例、验收标准
- `AptGuide文档/03-技术架构与模块设计.md` — 模块、链路、依赖
- `AptGuide文档/04-Agent设计与提示词规范.md` — LangGraph、意图、槽位、提示词
- `AptGuide文档/05-Java工具接口契约.md` — 内部工具 HTTP 接口
- `AptGuide文档/06-Milvus知识库设计.md` — Collection schema、向量化、同步
- `AptGuide文档/07-测试验收方案.md` — 单元、契约、Agent 评测
- `AptGuide文档/08-跨项目集成与两阶段实施.md` — 独立应用、系统集成、与 H5 / lease / AptInsight 的交互

## 大模型应用亮点

- LangGraph 任务型 Agent 编排：意图、槽位、工具、确认、回复节点可观测。
- Milvus RAG：房源语义召回、规则知识库、来源引用、低置信度回退。
- Tool Calling 安全层：工具白名单、Pydantic 参数校验、超时重试、错误映射。
- Redis 会话状态：支持“第一个房源”“确认”等多轮任务状态。
- SSE 流式响应：展示工具调用进度、增量回答和最终房源卡片。
- Agent Eval：评估意图识别、槽位抽取、工具调用、RAG 命中和写操作安全。
- Prompt 版本管理：提示词可评测、可灰度、可回滚。
- JSON 日志和 trace_id：从用户问题到检索、工具调用、回答全链路排查。

## 安全

阅读 [`SECURITY.md`](SECURITY.md) 与 `docs/security/`：

- 用户数据（租约、预约、浏览历史）一律按 `userId` 在 Java 侧过滤；
- Milvus 不存敏感数据；
- 写操作（预约、取消）必须经过用户二次确认；
- AptGuide ↔ lease 之间使用共享密钥的内部接口，不对公网暴露。

## 许可证

仅作为公司内部公寓管理系统的子项目使用，未授权前不得对外发布。
