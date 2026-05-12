# AptGuide LangSmith 测试追踪配置指南

**目标:** 本轮 AptGuide 补充测试必须接入 LangSmith，保证每个 B1-B10、AS01-AS08 和 dialog 失败复核样本都有可追踪证据。

**项目隔离要求:** 可以复用 AptInsight 已配置好的 LangSmith API key，但 LangSmith project 必须新建 / 使用 `aptguide`。AptGuide 的评测结果文件仍保存到 `AptGuide/evals/results/` 和 `AptGuide/docs/`，不要写入 AptInsight 目录。

**依据:** LangSmith 官方文档说明，LangGraph / LangChain 应用可以通过环境变量开启 tracing；常用变量包括 `LANGSMITH_TRACING`、`LANGSMITH_API_KEY`、`LANGSMITH_ENDPOINT`、`LANGSMITH_PROJECT`。如果 API key 绑定多个 workspace，需要设置 `LANGSMITH_WORKSPACE_ID`。

参考：

- [LangSmith Observability Quickstart](https://docs.langchain.com/langsmith/observability-quickstart)
- [Trace LangChain applications](https://docs.langchain.com/langsmith/trace-with-langchain)
- [Log traces to a specific project](https://docs.langchain.com/langsmith/log-traces-to-project)
- [Custom instrumentation](https://docs.langchain.com/langsmith/annotate-code)

## 1. 必需环境变量

在运行 AptGuide 服务和 eval runner 的 shell 中设置：

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_ENDPOINT=https://api.smith.langchain.com
export LANGSMITH_API_KEY="<your-langsmith-api-key>"
export LANGSMITH_PROJECT="aptguide"
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="$LANGSMITH_API_KEY"
export LANGCHAIN_PROJECT="aptguide"
```

如果 LangSmith API key 属于多个 workspace，再加：

```bash
export LANGSMITH_WORKSPACE_ID="<workspace-id>"
```

不要把真实 `LANGSMITH_API_KEY` 写入 git。

如果本机已经配置过 AptInsight，可以复用 AptInsight 的 LangSmith key，但必须覆盖 project：

```bash
set -a
source AptInsight/.env
set +a
export LANGSMITH_PROJECT=aptguide
export LANGCHAIN_PROJECT=aptguide
```

执行 agent 需要在 LangSmith UI 中创建或确认存在 `aptguide` project；如果 LangSmith 在首次 trace ingestion 时自动创建 project，也要在报告里确认最终 traces 落在 `aptguide`，而不是 `aptinsight`。

执行前确认不要打印真实 key：

```bash
python - <<'PY'
import os
print("LANGSMITH_TRACING=", os.getenv("LANGSMITH_TRACING"))
print("LANGSMITH_PROJECT=", os.getenv("LANGSMITH_PROJECT"))
print("LANGCHAIN_PROJECT=", os.getenv("LANGCHAIN_PROJECT"))
print("LANGSMITH_API_KEY_SET=", bool(os.getenv("LANGSMITH_API_KEY")))
PY
```

## 2. 服务端 tracing

AptGuide 使用 LangGraph 编排主链路。运行真实系统测试前，必须在启动 AptGuide 服务的同一个环境里启用 LangSmith 变量。

最低要求：

- LangGraph workflow 调用能出现在 `aptguide` project 中。
- 每次 `/api/chat` 请求能通过 `session_id`、`request_id` 或 run metadata 对应到测试 case。
- B1-B10 和 AS01-AS08 的报告中要记录 LangSmith project 名称。

## 3. LLM tracing

AptGuide 当前 [LLMClient](../src/aptguide/llm/client.py) 直接使用 OpenAI-compatible `AsyncOpenAI`。为了让 raw OpenAI 调用也进入 LangSmith，执行 agent 应复用 AptInsight 的实现模式：配置层同步 LangSmith 环境变量，LLM client 使用 LangSmith OpenAI wrapper。

目标改法：

```python
from langsmith.wrappers import wrap_openai
from openai import AsyncOpenAI

self.client = wrap_openai(
    AsyncOpenAI(
        api_key=settings.llm_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
    ),
    chat_name=settings.llm_model,
)
```

如果 wrapper API 与本地 `langsmith` 版本不兼容，执行 agent 必须记录为 `harness failed / langsmith_config`，并改用 `@traceable` 或 `trace` context manager 包裹 `LLMClient.generate`。

配置层建议参考 [AptInsight config](../../AptInsight/src/aptinsight/core/config.py)，在 AptGuide settings 中增加 `langsmith_*` 和 `langchain_*` 字段，并在 `get_settings()` 后同步到 `os.environ`。原因是 LangSmith / LangGraph SDK 直接读取进程环境变量，pydantic-settings 只读 `.env` 不会自动 export。

## 4. Eval runner tracing

补充测试 runner 也要写入 LangSmith，至少做到 case 级 trace。

建议 metadata：

```text
suite: regression_core / appointment_safety / dialog_failed_review
case_id: B1 / AS01 / ...
model: qwen-turbo-latest / deepseek
session_id: actual session id
classification: passed / harness failed / grader 过严 / 数据覆盖不足 / 真正系统链路错误
```

报告中每个 suite 至少记录：

```text
LangSmith project:
Run naming convention:
Representative trace:
```

如果无法自动获取 run URL，至少记录 project、case_id、session_id、timestamp，保证可以在 LangSmith UI 中检索。

## 5. 验证清单

- [ ] 启动 AptGuide 服务的 shell 已设置 `LANGSMITH_TRACING=true`。
- [ ] eval runner 的 shell 已设置 `LANGSMITH_PROJECT=aptguide`。
- [ ] LangSmith UI 中已创建或确认存在 `aptguide` project。
- [ ] `LANGSMITH_API_KEY` 没有写入 git。
- [ ] B1-B10 执行后，LangSmith `aptguide` project 中能看到对应 traces。
- [ ] AS01-AS08 执行后，LangSmith `aptguide` project 中能看到对应 traces。
- [ ] 报告记录 LangSmith project 和代表 trace 检索方式。
- [ ] JSON 结果保存到 `AptGuide/evals/results/`，报告保存到 `AptGuide/docs/`。
- [ ] 如果 tracing 缺失，测试结论不能写成完整通过，只能写“功能结果通过，LangSmith 观测缺失”。
