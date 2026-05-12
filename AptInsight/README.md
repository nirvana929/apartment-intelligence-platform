# AptInsight

AptInsight 是面向尚庭公寓后台的智能运营分析助手。当前工程用于第一阶段独立验证：通过 FastAPI 暴露 Agent 服务，接入只读 MySQL，完成自然语言问题到 SQL 查询、表格、图表和运营总结的链路。

## 项目状态

**当前阶段：** MVP 核心功能完成，Harness 达标

**完成度：**
- ✅ 配置管理和 JSON 日志
- ✅ 表白名单和基于 sqlglot 的 SQL 守卫
- ✅ async MySQL 引擎和只读执行器
- ✅ LLM 客户端和结构化输出
- ✅ LangGraph 工作流节点
- ✅ `/api/chat` 接口接入工作流
- ✅ 评测系统和测试用例
- ✅ 单元测试和契约测试

**评测基线：** 87.5% 通过率（35/40 测试用例）
- 安全测试：6/6 ✅ (100%)
- 边界情况：5/5 ✅ (100%)
- 业务分析：24/29 (82.8%)

**Harness 达标情况：**
- 功能用例通过率：87.5% (要求 >= 80%) ✅
- 安全用例通过率：100% (要求 = 100%) ✅
- 核心指标口径：100% ✅
- 单元测试：22 个全部通过 ✅
- Ruff Lint：0 错误 ✅

## 目录结构

```text
.
├── AptInsight文档/          # 项目设计、需求、测试和集成文档
├── docs/                   # 工程级 API、架构、安全补充文档
├── evals/                  # Agent Eval Harness 数据集、执行器、报告
│   ├── datasets/           # 测试用例（YAML 格式）
│   ├── runners/            # 评测运行器
│   └── reports/            # 评测报告输出
├── src/aptinsight/         # Python 服务源码
│   ├── agent/              # LangGraph 工作流、状态、节点、提示词
│   ├── api/                # HTTP API 路由
│   ├── core/               # 配置、日志、错误处理
│   ├── db/                 # 数据库引擎和查询执行器
│   ├── knowledge/          # 数据库 schema、指标、few-shot 示例
│   ├── llm/                # 模型客户端
│   ├── schemas/            # Pydantic 请求/响应模型
│   └── security/           # SQL 守卫、脱敏、表策略
├── tests/                  # 单元测试与接口契约测试
├── scripts/                # 本地开发脚本
├── pyproject.toml
├── .env.example
└── SECURITY.md
```

## 本地开发

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写 LLM_API_KEY、MYSQL_PASSWORD 等

# 启动服务
uv run uvicorn aptinsight.main:app --reload

# 或使用 Makefile
make run
```

## 常用命令

```bash
make run          # 启动开发服务器
make test         # 运行测试
make lint         # 代码检查
make eval         # 运行评测
```

## API 接口

### 健康检查

```bash
curl http://localhost:8000/health
# 返回: {"status": "ok"}
```

### 智能分析聊天

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "有多少个已发布的公寓"}'
```

**响应示例：**

```json
{
  "trace_id": "xxx",
  "answer": "当前平台有 2 个已发布的公寓。",
  "summary": "已发布公寓数量为 2 个",
  "rows": [{"published_apartment_count": 2}],
  "columns": ["published_apartment_count"],
  "chart": null,
  "sql": "SELECT COUNT(*) AS published_apartment_count FROM apartment_info WHERE is_release = 1 AND is_deleted = 0",
  "error": null,
  "processing_time_ms": 21996.84
}
```

## 安全机制

1. **SQL 守卫** - 使用 sqlglot 进行 AST 级别的安全检查
   - 只允许 SELECT 语句
   - 表和列白名单机制
   - 敏感字段拦截（身份证号、密码等）
   - 多语句 SQL 拒绝

2. **数据脱敏** - 查询结果中的敏感字段自动脱敏
   - 手机号：138****1234
   - 姓名：张*（2字姓名）/ 张**（3字姓名）

3. **只读账号** - 数据库使用只读权限账号

## 评测系统

评测系统用于评估 Agent 的性能，包括：

- **意图识别准确率** - 是否正确识别用户意图
- **SQL 生成准确率** - 生成的 SQL 是否正确
- **安全检查通过率** - SQL 守卫是否正常工作
- **执行成功率** - SQL 是否能成功执行

**运行评测：**

```bash
make eval
# 或
python -m evals.runners.text_to_sql --cases evals/datasets/text_to_sql_cases.yaml
```

**测试用例类别（共 40 个）：**
- appointment: 预约相关（5 个）- 通过率 100%
- lease: 租约相关（6 个）- 通过率 100%
- rent: 租金相关（4 个）- 通过率 50%
- browsing: 浏览相关（3 个）- 通过率 67%
- review: 评价相关（3 个）- 通过率 100%
- apartment: 公寓相关（3 个）- 通过率 67%
- room: 房间相关（2 个）- 通过率 100%
- security: 安全测试（6 个）- 通过率 100%
- edge_case: 边界情况（5 个）- 通过率 100%
- complex: 复杂查询（3 个）- 通过率 67%

**评测报告：**
- `evals/reports/eval_report.json` - JSON 格式详细报告
- `evals/reports/eval_report.md` - Markdown 格式可读报告
- `evals/reports/harness_compliance_report.md` - Harness 达标报告
- `docs/anthropic-agent-eval-methodology.md` - 基于 Anthropic Agent eval 方法的 AptInsight 专属评估与测试报告方案
- `docs/aptinsight-system-failure-investigation-guide.md` - 系统失败原因定位指南
- `docs/aptinsight-system-failure-root-cause-report.md` - 系统失败根因分析报告

## 技术栈

- Python 3.12
- FastAPI
- LangGraph
- OpenAI 兼容 LLM（阿里云百炼 Qwen）
- SQLAlchemy 2.x async + asyncmy
- sqlglot
- Pydantic v2
- pandas
- cryptography（MySQL 认证）
- redis
- langsmith（LLM 调用追踪）

## 下一步计划

1. 优化 LLM 提示词，提高 SQL 生成质量
2. 添加更多 few-shot 示例
3. 集成 Spring Boot 和 Vue 前端
4. 添加缓存机制（Redis）
5. 生产环境部署方案
