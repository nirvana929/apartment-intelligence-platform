# Enterprise AptGuide Harness Agent Handoff Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `project-harness resume` first, then use `subagent-driven-development` or `executing-plans` to implement task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a zero-context handoff plan so a fresh agent can implement AptGuide 2.0 harness foundation safely, update project state, verify behavior, and checkpoint progress.

**Architecture:** This plan sits above the code-level execution plan. It selects the project harness method, defines feature/sprint state, points agents to the canonical implementation tasks, and enforces verification before any feature can be marked complete.

**Tech Stack:** Python 3, FastAPI, Pydantic, pytest, uv, existing `aptguide2.rag`, new `aptguide2.harness`, local `project-harness` skill.

---

## 0. Executive Summary For The Next Agent

AptGuide 2.0 currently has a working FastAPI + RAG MVP. The next engineering step is to add a system-level `aptguide2.harness` package without breaking the existing MVP path.

The canonical code-level implementation plan is:

```text
docs/plans/2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md
```

This handoff plan defines how to execute that plan across agent sessions.

The selected harness method is:

```text
Procedure-driven Product Harness
+ Eval-first Engineering Harness
+ External Progress State
```

The non-negotiable rule is:

```text
No feature gets passes=true without verification evidence.
```

## 1. Required First Commands

Run these before editing code:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform"
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Expected:

- default project is `/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0`;
- `project/feature-list.json` exists;
- `project/sprint-plan.json` exists;
- `progress/current-plan.md` exists;
- `reports/evaluation-report.md` exists.

Then inspect current worktree:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0"
git status --short
```

Expected at time of writing:

- there are existing documentation changes;
- there are new project harness state directories;
- do not revert unrelated changes.

## 2. Required Reading Order

Read only enough to understand the task; do not bulk-load every document.

- [ ] Read `docs/00-start-here.md`
- [ ] Read `docs/27-current-implementation-guide.md`
- [ ] Read `docs/system/harness-method-selection.md`
- [ ] Read `docs/system/enterprise-harness-architecture.md`
- [ ] Read `docs/plans/2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- [ ] Read `project/feature-list.json`
- [ ] Read `project/sprint-plan.json`
- [ ] Read `progress/current-plan.md`
- [ ] Read `progress/known-issues.md`

## 3. Current Source Of Truth

| Purpose | File |
| --- | --- |
| Current project overview | `docs/00-start-here.md` |
| Current code reality | `docs/27-current-implementation-guide.md` |
| Harness method selection | `docs/system/harness-method-selection.md` |
| Harness architecture | `docs/system/enterprise-harness-architecture.md` |
| Code-level task instructions | `docs/plans/2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md` |
| Machine-readable feature state | `project/feature-list.json` |
| Machine-readable sprint contract | `project/sprint-plan.json` |
| Human-readable progress | `progress/current-plan.md` |
| Known blockers | `progress/known-issues.md` |
| Verification report | `reports/evaluation-report.md` |

## 4. Non-Negotiable Constraints

- [ ] Do not delete or rewrite `backend/src/aptguide2/rag`.
- [ ] Keep default `/chat` behavior on the existing MVP path unless `APTGUIDE_PIPELINE_VERSION=harness_v1`.
- [ ] Write tests before implementation for each harness task.
- [ ] Unit tests must not call external Milvus, lease, or LLM services.
- [ ] Use fake adapters and fake strategies in harness tests.
- [ ] Keep harness stage contracts typed with Pydantic models.
- [ ] Do not set `passes=true` in `project/feature-list.json` unless the evidence field includes commands that passed.
- [ ] Checkpoint after each completed sprint or before stopping work.

## 5. Target Runtime

Implement this first-stage runtime:

```text
ChatRequest
  -> AptGuideRequest
  -> InMemoryContextStore
  -> HybridRouter
  -> ProcedureRuntime
      -> capability.profile
      -> fallback.safety
      -> fallback.unknown
      -> rag.room_search
      -> rag.kb_qa
  -> ResponseComposer
  -> TraceRecorder
  -> AptGuideResponse
  -> ChatResponse compatibility mapping
```

The final public API response remains `ChatResponse` from `aptguide2.api.schemas`.

## 6. Target Files

Create:

```text
backend/src/aptguide2/harness/
├── __init__.py
├── contracts.py
├── errors.py
├── registry.py
├── context.py
├── safety.py
├── routing.py
├── procedures.py
├── composer.py
├── trace.py
├── replay.py
├── orchestrator.py
└── modules/
    ├── __init__.py
    ├── capability.py
    ├── fallback.py
    └── rag/
        ├── __init__.py
        └── baseline.py
```

Create:

```text
backend/tests/unit/harness/
├── test_contracts.py
├── test_registry.py
├── test_context.py
├── test_safety.py
├── test_routing.py
├── test_procedures.py
├── test_builtin_procedures.py
├── test_composer.py
├── test_trace.py
├── test_replay.py
├── test_orchestrator.py
└── modules/
    └── rag/
        └── test_baseline.py
```

Modify:

```text
backend/src/aptguide2/core/config.py
backend/src/aptguide2/api/deps.py
backend/src/aptguide2/api/app.py
backend/tests/e2e/test_api.py
docs/system/enterprise-harness-architecture.md
docs/plans/README.md
docs/system/README.md
```

## 7. Sprint Plan

### Sprint 0: Handoff State And Plan Alignment

Goal: make the plan executable by future agents.

- [ ] Confirm `project/feature-list.json` lists all harness foundation features.
- [ ] Confirm `project/sprint-plan.json` lists all sprint contracts.
- [ ] Confirm this handoff plan is linked from `docs/plans/README.md`.
- [ ] Confirm `progress/current-plan.md` points to Sprint 1 as the next execution step.

Verification:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0"
rg -n "enterprise-aptguide-harness-agent-handoff-plan|enterprise-aptguide-harness-agent-execution-plan" docs project progress
```

### Sprint 1: Core Harness Shell

Goal: create typed contracts and deterministic shell utilities.

Features:

- `feature_harness_contracts`
- `feature_harness_registry`
- `feature_harness_trace`
- `feature_harness_context`

Canonical tasks:

- Task 1 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 2 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 3 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 4 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`

Required verification:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_contracts.py -q
uv run pytest tests/unit/harness/test_registry.py -q
uv run pytest tests/unit/harness/test_trace.py -q
uv run pytest tests/unit/harness/test_context.py -q
```

Exit criteria:

- `aptguide2.harness` imports successfully.
- Pydantic defaults use isolated mutable collections.
- Registry raises clear missing strategy errors.
- Trace records stage latency and errors.
- Context store preserves session state by `session_id`.

### Sprint 2: Routing And Procedure Runtime

Goal: support capability, safety fallback, route decisions, procedure execution, and response composition.

Features:

- `feature_harness_safety`
- `feature_harness_routing`
- `feature_harness_procedure_runtime`
- `feature_harness_composer`
- `feature_harness_builtin_procedures`

Canonical tasks:

- Task 5 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 6 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 7 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 8 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 9 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`

Required verification:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_safety.py -q
uv run pytest tests/unit/harness/test_routing.py -q
uv run pytest tests/unit/harness/test_procedures.py -q
uv run pytest tests/unit/harness/test_composer.py -q
uv run pytest tests/unit/harness/test_builtin_procedures.py -q
```

Exit criteria:

- Capability question routes to `capability.profile`.
- Guarantee/privacy/out-of-domain safety flags route to fallback.
- Missing procedures raise `ProcedureNotFoundError`.
- Composer can include or hide trace.
- Built-in procedures do not call external services.

### Sprint 3: RAG Baseline And Orchestrator

Goal: mount existing RAG MVP as a harness procedure and run an end-to-end harness request internally.

Features:

- `feature_harness_rag_baseline`
- `feature_harness_orchestrator`

Canonical tasks:

- Task 10 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 11 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`

Required verification:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/modules/rag/test_baseline.py -q
uv run pytest tests/unit/harness/test_orchestrator.py -q
```

Exit criteria:

- `RagBaselineProcedure` maps room results into room cards.
- `RagBaselineProcedure` maps KB results into sources.
- `AptGuideHarness.run()` records context, routing, procedure, and response composition.
- Context save preserves last recommendations.

### Sprint 4: API Switch, Replay, Docs, And Regression

Goal: expose harness behind config, keep MVP default, add replay writer, and complete verification.

Features:

- `feature_harness_api_switch`
- `feature_harness_replay`
- `feature_harness_docs_sync`
- `feature_harness_regression_verification`

Canonical tasks:

- Task 12 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 13 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 14 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`
- Task 15 in `2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md`

Required verification:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_replay.py -q
uv run pytest tests/e2e/test_api.py -q
uv run pytest tests/unit/harness -q
uv run pytest tests/unit/rag tests/e2e -q
```

Docs verification:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0"
rg -n "harness-method-selection|enterprise-aptguide-harness-agent-execution-plan|enterprise-aptguide-harness-agent-handoff-plan" docs README.md project progress
```

Exit criteria:

- Default `/chat` still returns current MVP `ChatResponse`.
- `APTGUIDE_PIPELINE_VERSION=harness_v1` returns capability response for “你能做什么”.
- Replay writer writes JSONL and rejects PII keys.
- Harness unit tests pass.
- Existing RAG unit tests and API e2e tests pass.
- Documentation states implemented package status.

## 8. Feature State Update Rules

When a feature is started:

```json
{
  "status": "in_progress",
  "passes": false,
  "test_status": "running",
  "evidence": []
}
```

When a feature implementation is complete but tests were not run:

```json
{
  "status": "implemented_unverified",
  "passes": false,
  "test_status": "not_run",
  "evidence": []
}
```

When a feature passes verification:

```json
{
  "status": "completed",
  "passes": true,
  "test_status": "passed",
  "evidence": [
    "uv run pytest tests/unit/harness/test_contracts.py -q"
  ]
}
```

When a test fails:

```json
{
  "status": "blocked",
  "passes": false,
  "test_status": "failed",
  "evidence": [
    "uv run pytest tests/unit/harness/test_contracts.py -q failed: <short reason>"
  ]
}
```

## 9. Checkpoint Protocol

Run checkpoint after each sprint, before stopping, or after any failed verification.

Use:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform"
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Then update:

```text
progress/current-plan.md
progress/completed.md
progress/known-issues.md
progress/next-steps.md
reports/evaluation-report.md
project/feature-list.json
project/sprint-plan.json
```

Final response after checkpoint must include:

```text
Checkpoint Summary
- Project:
- Current goal:
- Completed this session:
- Files changed:
- Verification:
- Known issues:
- Next steps:
```

## 10. Commit Guidance

The executing agent may commit only if explicitly asked by the user. If committing is allowed, use small commits by sprint:

```bash
git add backend/src/aptguide2/harness backend/tests/unit/harness
git commit -m "feat: add aptguide harness foundation"
```

Do not include unrelated user changes. Do not revert unrelated worktree changes.

## 11. Final Definition Of Done

The full harness foundation is done only when all are true:

- [ ] `backend/src/aptguide2/harness` exists.
- [ ] Harness unit tests pass.
- [ ] Existing RAG unit tests pass.
- [ ] API e2e tests pass.
- [ ] `/chat` defaults to MVP behavior.
- [ ] `/chat` can run `harness_v1`.
- [ ] Current RAG MVP is mounted as a harness module.
- [ ] Trace is available internally through `AptGuideTrace`.
- [ ] Replay writer produces PII-guarded JSONL cases.
- [ ] `project/feature-list.json` has completed features with evidence.
- [ ] `reports/evaluation-report.md` records the final verification.
- [ ] `progress/current-plan.md` points to the next post-foundation task.
