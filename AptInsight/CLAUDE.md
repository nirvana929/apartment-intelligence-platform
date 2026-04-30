# CLAUDE.md

This file gives Claude Code project instructions for AptInsight.

## Role

You are helping build AptInsight, an intelligent apartment operation analysis assistant for the Shangting Apartment system.

The MVP is an independent Python FastAPI Agent service. It receives Chinese natural language operation questions, generates safe read-only SQL, queries the existing MySQL business database, and returns tables, ECharts-compatible chart options, and concise business summaries.

## Communication Language

When communicating with the user, use Chinese by default. The user is Chinese, so progress updates, clarifying questions, technical explanations, and final responses should be written in Chinese.

Use English only for code, commands, logs, identifiers, dependency names, file names, API names, exact error messages, or if the user explicitly requests English.

## Repository Boundary

The current directory is the AptInsight project root. Keep this project independent from the existing `least` Spring Boot/Vue codebase. The Java backend and Vue frontend are integration targets for phase two, not places to put the Python Agent code.

## Must Read

Use these documents as the project source of truth:

- `AptInsight文档/01-助手总体设计.md`
- `AptInsight文档/03-技术架构与模块设计.md`
- `AptInsight文档/04-Agent设计与提示词规范.md`
- `AptInsight文档/05-数据库字典与指标口径.md`
- `AptInsight文档/06-接口契约与集成方案.md`
- `AptInsight文档/07-测试验收方案.md`
- `AptInsight文档/08-企业工程规范与Harness.md`

## Expected Stack

- Python 3.12
- `uv`
- FastAPI
- Pydantic v2
- LangGraph
- OpenAI-compatible LLM client
- SQLAlchemy 2.x async
- asyncmy
- sqlglot
- pandas
- pytest
- Ruff

Do not introduce a heavier stack without a clear reason.

## Directory Guide

```text
src/aptinsight/api/        HTTP API routes
src/aptinsight/agent/      LangGraph workflow, state, nodes, prompts
src/aptinsight/core/       settings, logging, errors
src/aptinsight/db/         database engine and query executor
src/aptinsight/llm/        model client and structured schemas
src/aptinsight/security/   SQL Guard, redaction, table policy
src/aptinsight/knowledge/  database schema, metrics, few-shot examples
src/aptinsight/schemas/    Pydantic request/response models
evals/                    Agent Eval Harness
tests/                    tests
docs/                     engineering docs
AptInsight文档/           product and architecture docs
```

## Non-Negotiable Safety Rules

- Never execute generated SQL before SQL Guard approval.
- Only allow `SELECT`.
- Reject write operations and DDL.
- Reject multi-statement SQL.
- Use table and column whitelists.
- Protect sensitive fields and credentials.
- Use read-only MySQL credentials only.
- Do not invent fields, tables, metrics, revenue, or business causes.
- If the database schema cannot support a question, explain the limitation.

## Coding Style

- Keep route handlers thin.
- Keep prompts in Markdown under `src/aptinsight/agent/prompts/`.
- Keep business schema knowledge in `src/aptinsight/knowledge/`.
- Use Pydantic models for external contracts.
- Add tests for meaningful behavior changes.
- Prefer clear module boundaries over large all-in-one files.
- Keep comments useful and minimal.

## Common Commands

```bash
uv sync
uv run uvicorn aptinsight.main:app --reload
uv run pytest
uv run ruff check src tests
uv run ruff format src tests
make run
make test
make lint
make eval
```

## Development Sequence

Recommended next implementation order:

1. Finish config and JSON logging.
2. Implement table whitelist and SQL Guard with `sqlglot`.
3. Implement async MySQL engine and read-only executor.
4. Implement LLM client and structured output schemas.
5. Implement LangGraph nodes.
6. Wire `/api/chat` to the graph.
7. Expand `evals/datasets/text_to_sql_cases.yaml`.
8. Add Spring Boot and Vue integration only after Agent behavior is stable.

## Final Check Before Responding

Confirm what changed, mention tests or checks run, and call out any limitation clearly.
