# AptInsight 智能运营分析助手文档

版本：v0.2
日期：2026-05-02
适用项目：尚庭公寓智能运营分析助手（AptInsight）

## 当前状态

**MVP 核心功能完成，Harness 达标**

- ✅ 配置管理和 JSON 日志
- ✅ 表白名单和基于 sqlglot 的 SQL 守卫
- ✅ async MySQL 引擎和只读执行器
- ✅ LLM 客户端和结构化输出
- ✅ LangGraph 工作流节点
- ✅ `/api/chat` 接口接入工作流
- ✅ 评测系统和测试用例
- ✅ 单元测试和契约测试

**评测结果：**
- Agent Eval 通过率：87.5%（35/40）
- 安全测试：6/6（100%）
- 单元测试：22 个全部通过
- Ruff Lint：0 错误

## 文档目标

这套文档用于指导 AptInsight 智能运营分析助手从“独立测试工具”逐步演进为“集成到公寓管理后台的智能运营分析模块”。

第一阶段先不改动已有前后端系统，单独实现一个可测试的 Agent 服务，直接连接现有 MySQL 业务库，只读查询公寓、房间、预约、租约、浏览历史等数据，验证自然语言分析、SQL 生成、图表生成和运营总结能力。

第二阶段再通过 Spring Boot 后端接口和 Vue 管理后台页面完成集成。

## 文档目录

| 文件 | 说明 |
| --- | --- |
| [01-助手总体设计.md](./01-助手总体设计.md) | 模块定位、阶段规划、能力边界、总体架构 |
| [02-产品需求文档.md](./02-产品需求文档.md) | 用户场景、功能需求、页面形态、验收口径 |
| [03-技术架构与模块设计.md](./03-技术架构与模块设计.md) | 独立 Agent 服务、后端集成、模块职责、部署配置 |
| [04-Agent设计与提示词规范.md](./04-Agent设计与提示词规范.md) | Agent 工作流、提示词结构、SQL 生成规则、安全策略 |
| [05-数据库字典与指标口径.md](./05-数据库字典与指标口径.md) | 业务表说明、字段含义、枚举值、核心指标和 SQL 示例 |
| [06-接口契约与集成方案.md](./06-接口契约与集成方案.md) | Python Agent API、Spring Boot 转发接口、前端对接数据结构 |
| [07-测试验收方案.md](./07-测试验收方案.md) | 功能测试、安全测试、SQL 准确率测试、集成验收清单 |
| [08-企业工程规范与Harness.md](./08-企业工程规范与Harness.md) | 技术选型取舍、LangGraph、Agent Eval Harness、企业化交付规范 |
| [09-系统升级路线与缺陷改进.md](./09-系统升级路线与缺陷改进.md) | 系统升级路线、已知缺陷和改进计划 |
| [10-系统集成实施文档.md](./10-系统集成实施文档.md) | Spring Boot / Vue 集成实施步骤 |

## 当前系统依据

文档内容参考了当前项目中的实际结构：

| 范围 | 当前路径 |
| --- | --- |
| 后端工程 | `least` |
| 后台前端 | `1.笔记/rentHouseAdmin` |
| 数据库脚本 | `hello-minio/lease.sql` |
| 数据源配置 | `least/web/web-admin/src/main/resources/application.yml` |
| 实体模型 | `least/model/src/main/java/com/atguigu/lease/model/entity` |
| 枚举模型 | `least/model/src/main/java/com/atguigu/lease/model/enums` |

注意：后端 `application.yml` 当前连接库名是 `least`，SQL dump 中库名显示为 `lease`。本文档统一使用业务表名，不强依赖具体库名；实际实现时以当前运行数据库为准。

## 第一阶段建议交付物

第一阶段只做独立助手，不集成后台页面。这个阶段的目标不是把所有企业工具都堆上去，而是把 AptInsight 的核心 AI Agent 能力做扎实。

第一阶段必须交付：

1. Python FastAPI Agent 服务。
2. 只读 MySQL 账号和连接配置。
3. 数据库 schema 文本和指标口径文件。
4. LangGraph Agent 状态图，覆盖意图识别、SQL 生成、安全校验、执行、图表和总结。
5. sqlglot SQL Guard，保证只读、安全、可控。
6. Agent Eval Harness，用固定问题集回归测试 SQL 正确性、安全性和拒答能力。
7. pytest 单元测试，覆盖 SQL Guard、指标口径、接口响应。
8. 简单 Web 页面、Swagger 或 Postman 调试入口。
9. `README.md`、`.env.example`、基础开发说明和安全说明。

第一阶段推荐交付：

1. Dockerfile，用于后续部署和演示环境一致性。
2. Makefile，用统一命令运行测试、评测和服务。
3. Ruff / pre-commit，保证代码格式和基础质量。
4. Harness CI Pipeline 草案，把 Agent Eval Harness 接入流水线作为面试加分点。

## 第二阶段建议交付物

第二阶段集成到现有系统，建议交付：

1. Spring Boot `/admin/ai/chat` 转发接口。
2. 后台 Vue 路由：`智能运营分析`。
3. 对话区、推荐问题、SQL 折叠区、表格、ECharts 图表。
4. 查询日志、异常展示、权限控制。
5. 端到端验收测试。

## 推荐技术栈

AptInsight AI 项目应作为全新的独立 AI 工程建设，但所有技术都要服务于这个助手本身。

| 类别 | 推荐 | 取舍 |
| --- | --- |
| 运行时 | Python 3.12 | AI Agent 生态成熟，适合独立服务 |
| 包管理 | `uv` | 依赖锁定和启动速度好，推荐 |
| API 服务 | FastAPI + Pydantic v2 | 必要，提供类型化接口 |
| Agent 编排 | LangGraph | 核心加分点，适合 Text-to-SQL 的分支、重试和状态管理 |
| 模型接入 | OpenAI-compatible client / LiteLLM | 单模型可直接 client，多模型再用 LiteLLM |
| 数据库 | SQLAlchemy 2.x async + asyncmy | 推荐，连接现有 MySQL 只读库 |
| SQL 解析 | sqlglot | 必要，大模型生成 SQL 必须做 AST 级校验 |
| 数据处理 | Pandas | 第一版足够；Polars 后期数据量大再考虑 |
| 测试 | pytest + Agent Eval Harness | 必要，保证 prompt 和 SQL 生成可回归 |
| 代码质量 | Ruff + pre-commit | 推荐，成本低 |
| 容器化 | Docker | 推荐，不阻塞 MVP |
| CI/CD | Harness Pipeline as Code | 企业化和面试加分，MVP 可先写草案 |
| 可观测性 | JSON logs + trace_id | MVP 必要；OpenTelemetry/Prometheus 后期增强 |

说明：这里的 “Harness” 包含两层含义：

1. **Agent Eval Harness**：AptInsight 第一阶段就需要，用固定问题集持续回归 Text-to-SQL、SQL 安全和回答质量。
2. **Harness CI/CD**：企业交付和面试加分项，建议把评测、测试、镜像构建接入 Pipeline，但不作为 MVP 核心链路的前置条件。
