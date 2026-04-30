# AGENTS.md

This file is for coding agents working in the AptInsight repository.

## Project Identity

AptInsight is an intelligent operation analysis assistant for the Shangting Apartment management system. The first phase is an independent Python FastAPI Agent service that answers apartment operation questions by generating safe read-only SQL, querying the existing MySQL business database, and returning tables, charts, and concise business summaries.

This repository root is the AptInsight project root. Do not create another nested project root unless explicitly requested.

## Communication Language

When talking with the user in chat, use Chinese by default. The user is Chinese and expects explanations, progress updates, questions, and final summaries in Chinese.

Use English only when it is part of code, command output, dependency names, file names, API names, error messages, or when the user explicitly asks for English.

## Source Of Truth

Read these documents before making architectural or behavior changes:

1. `AptInsight文档/01-助手总体设计.md`
2. `AptInsight文档/03-技术架构与模块设计.md`
3. `AptInsight文档/04-Agent设计与提示词规范.md`
4. `AptInsight文档/05-数据库字典与指标口径.md`
5. `AptInsight文档/06-接口契约与集成方案.md`
6. `AptInsight文档/07-测试验收方案.md`
7. `AptInsight文档/08-企业工程规范与Harness.md`

If code and documentation conflict, pause and align the implementation with the documented MVP scope unless the user explicitly asks to update the docs.

## Current Architecture

Use the current project layout:

```text
src/aptinsight/
  api/          FastAPI routes and dependencies
  agent/        LangGraph state, graph, nodes, prompts
  core/         config, logging, shared errors
  db/           SQLAlchemy async engine and read-only executor
  llm/          OpenAI-compatible model client and schemas
  security/     SQL guard, redaction, table policy
  knowledge/    schema, metrics, few-shot knowledge
  schemas/      Pydantic request and response models
evals/          Agent Eval Harness datasets, runners, reports
tests/          unit and contract tests
docs/           engineering docs
AptInsight文档/ product and architecture docs
```

## Engineering Rules

- Prefer small, focused changes that match the existing directory structure.
- Keep MVP scope tight: FastAPI, Pydantic v2, LangGraph, SQLAlchemy async, asyncmy, sqlglot, pytest, Ruff, and Agent Eval Harness.
- Do not mix this Python AI service into the existing `least` Java/Vue project.
- Use `uv` for dependency management.
- Add or update tests when behavior changes.
- Keep secrets out of the repository. Use `.env` locally and `.env.example` for placeholders.
- Do not add large generated artifacts unless requested. Existing PDFs in `AptInsight文档/` are documentation deliverables.

## Safety Rules

AptInsight must be conservative with database access:

- Only generate and execute `SELECT` statements.
- Always pass generated SQL through the SQL Guard before execution.
- Use a dedicated read-only MySQL account.
- Deny dangerous SQL, including `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `REPLACE`, stored procedures, and multi-statement SQL.
- Deny system databases and non-whitelisted tables.
- Deny sensitive fields such as identity numbers, passwords, tokens, salts, and credential-like values.
- Do not claim actual received revenue if the schema only supports contract rent and has no payment-flow table.
- If schema support is missing, say so clearly instead of fabricating results.

## Coding Conventions

- Python version: 3.12 or newer.
- Use Pydantic models for API request and response contracts.
- Keep API routes thin. Put orchestration in `agent/`, SQL work in `db/`, and validation/security in `security/`.
- Use typed functions and clear module boundaries.
- Prefer async database access.
- Use structured errors and trace IDs for request-level diagnosis.
- Keep prompts in `src/aptinsight/agent/prompts/`, not hardcoded inside Python modules.
- Keep schema and metric knowledge in `src/aptinsight/knowledge/`.

## Commands

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

## Implementation Priority

When continuing development, build in this order:

1. Configuration and logging.
2. SQL table policy and SQL Guard.
3. Database engine and read-only executor.
4. LLM client with structured outputs.
5. LangGraph Agent state, nodes, and graph.
6. `/api/chat` real implementation.
7. Eval runner and regression dataset expansion.
8. Spring Boot and Vue integration only after the independent Agent is stable.

## Review Checklist

Before finishing a change, verify:

- The change matches the documented MVP.
- No secrets were introduced.
- Generated SQL cannot bypass the guard.
- Unsupported schema questions are refused or caveated.
- API responses still match Pydantic schemas.
- Tests or evals cover the behavior when appropriate.
