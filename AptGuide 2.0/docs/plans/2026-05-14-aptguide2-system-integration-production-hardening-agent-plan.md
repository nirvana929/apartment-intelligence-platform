# AptGuide 2.0 System Integration And Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move AptGuide 2.0 from locally passing modules to a verified system: live RAG eval, real-service readiness, API-level appointment confirmation, and documented production-hardening gates.

**Architecture:** Preserve current feature flags (`v1`, `harness_v1`, `rag_v2`) while adding system verification around them. Fix the public API contract so harness workflows can carry `user_id`, `action`, `actions`, `pending_action`, and `metadata`; then validate real Milvus, embedding, lease, and `/chat` flows without faking pass results.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest, httpx/TestClient, Milvus, OpenAI-compatible embedding/LLM APIs, existing `lease` backend internal tools, existing AptGuide harness/tool/RAG modules.

---

## 0. Scope And Gate

This plan is not a new feature sprint. It is the system integration gate after these completed phases:

- Harness Foundation
- Tool Registry Governance
- Enterprise RAG v2
- Harness Correction

The executing agent must not start rolling-summary, long-term profile, or unrelated UX work until live system verification is complete or exact blockers are documented.

## 1. Required Outcomes

The plan is complete only when all of these are true:

- `reports/evaluation-report.md` no longer reports stale `281` tests when current status is `292`.
- `evals/runners/run_rag_v2.py` correctly wires `run_pipeline_v2()` with `vector_adapter`, `embed_fn`, and `lease_validator`.
- A live dependency readiness report exists, even if it documents unavailable services.
- A live RAG v2 eval report exists, and it does not fake pass metrics.
- `/chat` accepts `user_id` and `action` for harness flows.
- `/chat` returns `actions`, `pending_action`, and `metadata` for harness flows.
- Appointment confirmation can be exercised through the API contract, not only internal harness tests.
- Project progress files point to the next true blocker or next plan.

## 2. Non-Negotiable Guardrails

- [ ] Keep default `/chat` behavior as current MVP `v1`.
- [ ] Keep harness behavior behind `APTGUIDE_PIPELINE_VERSION=harness_v1`.
- [ ] Keep RAG v2 behavior behind `APTGUIDE_PIPELINE_VERSION=rag_v2`.
- [ ] Do not fake live eval success if Milvus, embedding, lease, or data are unavailable.
- [ ] Do not execute live appointment writes unless a specific test user, test room, and `APTGUIDE_LIVE_WRITE_TESTS=1` are configured.
- [ ] Do not bypass `ToolRuntime` for lease business operations.
- [ ] Do not mark feature state as passing without command output and report evidence.

## 3. Task 1: Reality Audit And Stale Report Correction

**Files:**

- Read: `progress/current-plan.md`
- Read: `progress/next-steps.md`
- Modify: `reports/evaluation-report.md`

- [ ] **Step 1: Inspect status and current report**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0"
sed -n '1,220p' progress/current-plan.md
sed -n '1,220p' progress/next-steps.md
tail -n 120 reports/evaluation-report.md
```

Expected:

- `progress/current-plan.md` says 292 tests passing.
- `reports/evaluation-report.md` may still have stale JSON showing `total_tests: 281`.

- [ ] **Step 2: Run local regression before changing state**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q
```

Expected: `292 passed` or a larger passing count if newer tests already exist.

If this fails, do not update reports as passing. Add a section to `reports/evaluation-report.md`:

````markdown
## System Integration Baseline Failure

Command:

```bash
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q
```

Observed failure:

- Paste the exact failing test names and first error line here.
````

- [ ] **Step 3: Correct stale evaluation summary**

If the regression passes with 292 tests, update the JSON block in `reports/evaluation-report.md`:

```json
{
  "harness_foundation_passes": true,
  "tool_registry_passes": true,
  "rag_v2_passes": true,
  "harness_correction_passes": true,
  "total_tests": 292,
  "unit_tests": 279,
  "e2e_tests": 13,
  "new_rag_v2_tests": 19,
  "new_rag_v2_modules": 8,
  "total_features": 33,
  "features_passing": 33,
  "total_sprints": 7,
  "sprints_completed": 7,
  "next_step": "Live eval with Milvus/embedding/lease services"
}
```

## 4. Task 2: Fix RAG v2 Live Eval Runner Wiring

**Files:**

- Modify: `backend/evals/runners/run_rag_v2.py`
- Create: `backend/tests/unit/evals/test_run_rag_v2.py`

The current runner must call:

```python
run_pipeline_v2(
    message=query,
    vector_adapter=...,
    embed_fn=...,
    lease_validator=...,
)
```

Do not pass unsupported keyword arguments such as `settings=`.

- [ ] **Step 1: Add unit tests for eval runner dependency wiring**

Create `backend/tests/unit/evals/test_run_rag_v2.py`:

```python
from types import SimpleNamespace

from evals.runners import run_rag_v2


def test_eval_kb_retrieval_passes_v2_dependencies(monkeypatch):
    captured = {}

    def fake_pipeline(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            task="kb_qa",
            kb_sources=[SimpleNamespace(doc_id="KB-LEASE-005")],
            rooms=[],
            is_confident=True,
        )

    deps = run_rag_v2.RagV2EvalDependencies(
        vector_adapter=object(),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=object(),
    )
    monkeypatch.setattr(run_rag_v2, "run_pipeline_v2", fake_pipeline)

    result = run_rag_v2.eval_kb_retrieval(
        {"query": "押金退还多久到账", "expected_doc_ids": ["KB-LEASE-005"]},
        deps,
    )

    assert result["status"] == "pass"
    assert captured["vector_adapter"] is deps.vector_adapter
    assert captured["embed_fn"] is deps.embed_fn
    assert captured["lease_validator"] is deps.lease_validator


def test_eval_room_retrieval_passes_lease_validator(monkeypatch):
    captured = {}

    def fake_pipeline(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            task="room_search",
            kb_sources=[],
            rooms=[SimpleNamespace(room_id=101)],
            is_confident=False,
        )

    deps = run_rag_v2.RagV2EvalDependencies(
        vector_adapter=object(),
        embed_fn=lambda text: [0.1, 0.2],
        lease_validator=object(),
    )
    monkeypatch.setattr(run_rag_v2, "run_pipeline_v2", fake_pipeline)

    result = run_rag_v2.eval_room_retrieval(
        {"query": "番禺1500以内安静房源", "positive_room_ids": [101]},
        deps,
    )

    assert result["status"] == "pass"
    assert captured["lease_validator"] is deps.lease_validator
```

- [ ] **Step 2: Run failing tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py -q
```

Expected: fails because `RagV2EvalDependencies` does not exist and eval functions still accept `settings`.

- [ ] **Step 3: Add dependency bundle to runner**

In `backend/evals/runners/run_rag_v2.py`, add imports:

```python
from collections.abc import Callable
from dataclasses import dataclass

from aptguide2.api.deps import get_tool_runtime
from aptguide2.rag.tool_validation import ToolRuntimeRoomValidator
from aptguide2.tools.vector_adapter import VectorAdapter
```

Add after imports:

```python
@dataclass
class RagV2EvalDependencies:
    vector_adapter: object
    embed_fn: Callable[[str], list[float]]
    lease_validator: object | None
```

Add:

```python
def build_live_dependencies(settings: Settings) -> RagV2EvalDependencies:
    adapter = VectorAdapter(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        dim=settings.embedding_dim,
    )

    def embed_fn(text: str) -> list[float]:
        return embed_single(text, settings)

    return RagV2EvalDependencies(
        vector_adapter=adapter,
        embed_fn=embed_fn,
        lease_validator=ToolRuntimeRoomValidator(get_tool_runtime()),
    )
```

- [ ] **Step 4: Update per-case evaluators**

Change signatures:

```python
def eval_kb_retrieval(case: dict, deps: RagV2EvalDependencies) -> dict:
def eval_room_retrieval(case: dict, deps: RagV2EvalDependencies) -> dict:
def eval_fallback_retrieval(case: dict, deps: RagV2EvalDependencies) -> dict:
```

Call `run_pipeline_v2()` like this in all three functions:

```python
result = run_pipeline_v2(
    message=query,
    vector_adapter=deps.vector_adapter,
    embed_fn=deps.embed_fn,
    lease_validator=deps.lease_validator,
)
```

In `run_eval()` create dependencies once:

```python
settings = Settings()
deps = build_live_dependencies(settings)
cases = load_cases(cases_path)
```

Then pass `deps` to each evaluator.

- [ ] **Step 5: Run eval runner unit tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/evals/test_run_rag_v2.py -q
```

Expected: pass.

## 5. Task 3: Add Live Dependency Readiness Check

**Files:**

- Create: `backend/src/aptguide2/system/__init__.py`
- Create: `backend/src/aptguide2/system/readiness.py`
- Create: `backend/scripts/check_live_dependencies.py`
- Create: `backend/tests/unit/system/test_readiness.py`

- [ ] **Step 1: Add readiness unit tests**

Create `backend/tests/unit/system/test_readiness.py`:

```python
from aptguide2.system.readiness import DependencyCheck, ReadinessReport, render_markdown_report


def test_readiness_report_passes_only_when_all_required_checks_pass():
    report = ReadinessReport(checks=[
        DependencyCheck(name="milvus", ok=True, required=True, detail="ok"),
        DependencyCheck(name="lease", ok=False, required=True, detail="down"),
        DependencyCheck(name="optional", ok=False, required=False, detail="missing"),
    ])

    assert report.all_required_ok is False


def test_render_markdown_report_includes_blockers():
    report = ReadinessReport(checks=[
        DependencyCheck(name="milvus", ok=False, required=True, detail="connection refused"),
    ])

    markdown = render_markdown_report(report)

    assert "# Live Dependency Readiness Report" in markdown
    assert "connection refused" in markdown
    assert "NO" in markdown
```

- [ ] **Step 2: Implement readiness models**

Create `backend/src/aptguide2/system/__init__.py`:

```python
"""System integration helpers for AptGuide 2.0."""
```

Create `backend/src/aptguide2/system/readiness.py`:

```python
from __future__ import annotations

from pydantic import BaseModel


class DependencyCheck(BaseModel):
    name: str
    ok: bool
    required: bool = True
    detail: str = ""


class ReadinessReport(BaseModel):
    checks: list[DependencyCheck]

    @property
    def all_required_ok(self) -> bool:
        return all(check.ok for check in self.checks if check.required)


def render_markdown_report(report: ReadinessReport) -> str:
    lines = [
        "# Live Dependency Readiness Report",
        "",
        f"**All required dependencies ready:** {'YES' if report.all_required_ok else 'NO'}",
        "",
        "| Dependency | Required | Ready | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for check in report.checks:
        lines.append(
            f"| {check.name} | {'yes' if check.required else 'no'} | "
            f"{'yes' if check.ok else 'no'} | {check.detail} |"
        )
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 3: Implement live dependency CLI**

Create `backend/scripts/check_live_dependencies.py`:

```python
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.system.readiness import DependencyCheck, ReadinessReport, render_markdown_report
from aptguide2.tools.lease_adapter import LeaseAdapter
from aptguide2.tools.vector_adapter import KB_COLLECTION, ROOM_COLLECTION, VectorAdapter


def check_milvus(settings: Settings) -> DependencyCheck:
    try:
        adapter = VectorAdapter(
            uri=settings.milvus_uri,
            token=settings.milvus_token,
            dim=settings.embedding_dim,
        )
        client = adapter._ensure_client()
        room_ok = client.has_collection(ROOM_COLLECTION)
        kb_ok = client.has_collection(KB_COLLECTION)
        return DependencyCheck(
            name="milvus",
            ok=room_ok and kb_ok,
            detail=f"{ROOM_COLLECTION}={room_ok}, {KB_COLLECTION}={kb_ok}",
        )
    except Exception as exc:
        return DependencyCheck(name="milvus", ok=False, detail=f"{type(exc).__name__}: {exc}")


def check_embedding(settings: Settings) -> DependencyCheck:
    try:
        client = OpenAI(
            api_key=settings.embedding_api_key.get_secret_value(),
            base_url=settings.embedding_base_url,
        )
        response = client.embeddings.create(model=settings.embedding_model, input=["AptGuide readiness check"])
        dim = len(response.data[0].embedding)
        return DependencyCheck(
            name="embedding",
            ok=dim == settings.embedding_dim,
            detail=f"model={settings.embedding_model}, dim={dim}, expected={settings.embedding_dim}",
        )
    except Exception as exc:
        return DependencyCheck(name="embedding", ok=False, detail=f"{type(exc).__name__}: {exc}")


def check_lease(settings: Settings) -> DependencyCheck:
    async def _run() -> bool:
        adapter = LeaseAdapter(
            base_url=settings.lease_base_url,
            timeout=settings.lease_timeout_seconds,
            internal_token=settings.lease_internal_token,
        )
        try:
            return await adapter.health()
        finally:
            await adapter.close()

    try:
        ok = asyncio.run(_run())
        return DependencyCheck(name="lease", ok=ok, detail=f"base_url={settings.lease_base_url}")
    except Exception as exc:
        return DependencyCheck(name="lease", ok=False, detail=f"{type(exc).__name__}: {exc}")


def build_report(settings: Settings) -> ReadinessReport:
    return ReadinessReport(checks=[
        check_milvus(settings),
        check_embedding(settings),
        check_lease(settings),
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Check live AptGuide dependencies")
    parser.add_argument("--report", required=True, help="Markdown report path")
    args = parser.parse_args()

    report = build_report(Settings())
    output_path = Path(args.report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(report), encoding="utf-8")
    print(f"Report written to: {output_path}")
    raise SystemExit(0 if report.all_required_ok else 2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run readiness unit tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/system/test_readiness.py -q
```

Expected: pass.

## 6. Task 4: Run Live Dependency Readiness

**Files:**

- Generated: `reports/live-dependency-readiness-report.md`

- [ ] **Step 1: Run readiness check**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run python scripts/check_live_dependencies.py \
  --report ../reports/live-dependency-readiness-report.md
```

Expected:

- Exit code `0` when Milvus, embedding, and lease are ready.
- Exit code `2` when one or more required dependencies are unavailable.
- In both cases, the report file must be written.

- [ ] **Step 2: If dependencies are unavailable, classify blockers**

If the command exits `2`, inspect:

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0"
sed -n '1,220p' reports/live-dependency-readiness-report.md
```

Then add a short blocker section to `progress/next-steps.md`:

```markdown
## Live Dependency Blockers

- Milvus:
- Embedding:
- Lease:
```

Fill only the services that failed. Do not continue to live eval until required dependencies are available, unless the user explicitly asks for a blocker-only report.

## 7. Task 5: Run RAG v2 Live Eval

**Files:**

- Generated: `reports/rag-v2-live-evaluation-report.md`
- Modify if needed: `reports/evaluation-report.md`
- Modify if needed: `progress/next-steps.md`

- [ ] **Step 1: Run live eval**

Only run this after Task 4 reports all required dependencies ready.

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run python evals/runners/run_rag_v2.py \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

Expected:

- The report is generated.
- `All gates passed` is either `YES` or `NO`.
- Failed cases, if any, are listed.

- [ ] **Step 2: Classify live eval failures**

If gates fail, classify each failed case into one primary cause in `reports/rag-v2-live-evaluation-report.md`:

| Cause | Meaning | Next action |
| --- | --- | --- |
| `dependency_unavailable` | Service failed during eval | Fix service/config; do not tune RAG. |
| `data_missing` | Expected rooms or KB docs are not indexed | Run sync/seed workflow; do not fake metrics. |
| `contract_mismatch` | Lease/Milvus payload shape differs from code expectations | Fix adapter contract with tests. |
| `retrieval_quality` | Data exists but ranking/recall misses expected item | Create a focused RAG tuning plan. |
| `eval_case_stale` | Eval expected IDs no longer match real data | Update eval case with evidence. |

Do not make broad RAG changes inside this plan. If `retrieval_quality` is the main cause, create a follow-up plan instead.

- [ ] **Step 3: Update top-level evaluation report**

Append to `reports/evaluation-report.md`:

```markdown
## Live RAG v2 Evaluation

Report: `reports/rag-v2-live-evaluation-report.md`

Result:

- All gates passed:
- KB source hit@3:
- Room hit@5:
- High-risk fallback:
- Unvalidated rooms:

Failure classification:

- dependency_unavailable:
- data_missing:
- contract_mismatch:
- retrieval_quality:
- eval_case_stale:
```

Fill every value from the generated report.

## 8. Task 6: Complete Public `/chat` API Contract For Harness Workflows

**Files:**

- Modify: `backend/src/aptguide2/api/schemas.py`
- Modify: `backend/src/aptguide2/api/app.py`
- Modify: `backend/tests/e2e/test_api.py`

The internal harness already supports `user_id`, `action`, `actions`, `pending_action`, and metadata. The public API currently drops most of that. This blocks real frontend/system appointment confirmation.

- [ ] **Step 1: Add API schema tests**

Add to `backend/tests/e2e/test_api.py`:

```python
def test_harness_chat_exposes_pending_action_and_actions(monkeypatch, client):
    monkeypatch.setenv("APTGUIDE_PIPELINE_VERSION", "harness_v1")

    response = client.post(
        "/chat",
        json={
            "session_id": "s-api-confirm-1",
            "user_id": "u-1",
            "message": "预约101号房明天下午3点",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task"] == "appointment"
    assert body["pending_action"]["type"] == "appointment.create"
    assert body["actions"]
    assert body["metadata"]["procedure"] == "appointment.workflow"
```

Add a second test for confirmed turn using existing fake dependency patterns in `test_api.py`:

```python
def test_harness_chat_accepts_action_for_pending_confirmation(monkeypatch, client):
    monkeypatch.setenv("APTGUIDE_PIPELINE_VERSION", "harness_v1")

    first = client.post(
        "/chat",
        json={
            "session_id": "s-api-confirm-2",
            "user_id": "u-1",
            "message": "预约101号房明天下午3点",
        },
    ).json()

    response = client.post(
        "/chat",
        json={
            "session_id": "s-api-confirm-2",
            "user_id": "u-1",
            "message": "确认",
            "action": {
                "type": "confirm",
                "confirmation_id": first["pending_action"]["confirmation_id"],
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task"] == "appointment"
    assert body["phase"] in {"appointment_created", "appointment_failed"}
```

If `test_api.py` does not expose a `client` fixture, adapt these tests to the existing local style in that file.

- [ ] **Step 2: Extend API schemas**

In `backend/src/aptguide2/api/schemas.py`, update `ChatRequest`:

```python
class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str
    session_id: str | None = None
    user_id: str | None = None
    action: dict | None = None
    client_context: dict = Field(default_factory=dict)
```

Update `ChatResponse`:

```python
class ChatResponse(BaseModel):
    """Outgoing chat response."""

    task: str
    message: str = ""
    phase: str = ""
    rooms: list[RoomResponse] = Field(default_factory=list)
    kb_sources: list[KBSourceResponse] = Field(default_factory=list)
    is_confident: bool = False
    actions: list[dict] = Field(default_factory=list)
    pending_action: dict | None = None
    metadata: dict = Field(default_factory=dict)
```

- [ ] **Step 3: Pass user/action into harness request**

In `backend/src/aptguide2/api/app.py`, update harness branch:

```python
result = harness.run(
    AptGuideRequest(
        request_id=f"r-{uuid4().hex}",
        session_id=req.session_id,
        user_id=req.user_id,
        message=req.message,
        action=req.action,
        client_context=req.client_context,
    )
)
```

- [ ] **Step 4: Preserve structured harness response**

In `_build_response_from_harness()`, include:

```python
return ChatResponse(
    task=result.metadata.get("task", "fallback"),
    message=result.reply,
    phase=result.phase,
    rooms=rooms,
    kb_sources=sources,
    is_confident=bool(result.metadata.get("is_confident", False)),
    actions=result.actions,
    pending_action=result.pending_action,
    metadata=result.metadata,
)
```

For `_build_response()` MVP/RAG response, set `phase` and metadata conservatively:

```python
return ChatResponse(task="fallback", message=result.message, phase=result.fallback_reason or "fallback")
```

Do not break existing clients: all new fields are optional/defaulted.

- [ ] **Step 5: Run API tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/e2e/test_api.py -q
```

Expected: pass.

## 9. Task 7: Add System Smoke Commands

**Files:**

- Create: `docs/tests/system-smoke-checklist.md`
- Modify: `docs/tests/README.md`

- [ ] **Step 1: Create system smoke checklist**

Create `docs/tests/system-smoke-checklist.md`:

````markdown
# System Smoke Checklist

> 状态：active

## Purpose

Verify AptGuide 2.0 against real or locally configured services without changing the default `/chat` behavior.

## Preflight

```bash
cd "AptGuide 2.0/backend"
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q
uv run python scripts/check_live_dependencies.py --report ../reports/live-dependency-readiness-report.md
```

## RAG v2 Live Eval

```bash
cd "AptGuide 2.0/backend"
uv run python evals/runners/run_rag_v2.py \
  --cases evals/datasets/rag_mvp_eval_cases.yaml \
  --report ../reports/rag-v2-live-evaluation-report.md
```

## API Smoke

Start MVP:

```bash
cd "AptGuide 2.0/backend"
APTGUIDE_PIPELINE_VERSION=v1 uv run uvicorn aptguide2.api.app:app --port 8000
```

Start harness:

```bash
APTGUIDE_PIPELINE_VERSION=harness_v1 uv run uvicorn aptguide2.api.app:app --port 8000
```

Start RAG v2:

```bash
APTGUIDE_PIPELINE_VERSION=rag_v2 uv run uvicorn aptguide2.api.app:app --port 8000
```

Smoke requests:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"smoke-1","message":"押金退还多久到账"}'
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"smoke-2","user_id":"test-user","message":"预约101号房明天下午3点"}'
```

## Write Tool Guard

Do not run live `appointment.create` confirmation unless all are true:

- `APTGUIDE_LIVE_WRITE_TESTS=1`
- test user exists
- test room exists
- lease backend is pointed at a non-production database
````

- [ ] **Step 2: Link checklist from tests index**

Add to `docs/tests/README.md`:

```markdown
| [system-smoke-checklist](./system-smoke-checklist.md) | AptGuide 2.0 live dependency、RAG v2 eval 和 `/chat` API smoke 验收命令 | active |
```

## 10. Task 8: Update Progress And Plan Index

**Files:**

- Modify: `docs/plans/README.md`
- Modify: `progress/current-plan.md`
- Modify: `progress/next-steps.md`

- [ ] **Step 1: Mark this plan active in plan index**

Add to `docs/plans/README.md`:

```markdown
| [2026-05-14-aptguide2-system-integration-production-hardening-agent-plan](./2026-05-14-aptguide2-system-integration-production-hardening-agent-plan.md) | 系统集成与生产化验收：live eval、依赖 readiness、API 结构化确认协议、system smoke | active |
```

- [ ] **Step 2: Update current plan**

Set `progress/current-plan.md` active objective:

```markdown
## Active Objective

System integration and production hardening: live dependency readiness, RAG v2 live eval, and `/chat` API contract completion for harness workflows.

## Active Plan

`docs/plans/2026-05-14-aptguide2-system-integration-production-hardening-agent-plan.md`
```

- [ ] **Step 3: Update next steps after execution**

If live eval passes, set `progress/next-steps.md` immediate section to:

```markdown
## Immediate

11. Redis or durable context store plan
12. Rolling summary generation plan
13. Long-term profile extraction plan
```

If live eval fails, set immediate section to the primary blocker:

```markdown
## Immediate

11. Resolve live eval blocker: `<dependency_unavailable|data_missing|contract_mismatch|retrieval_quality|eval_case_stale>`
```

## 11. Task 9: Full Regression And Final Report

**Files:**

- Modify: `reports/evaluation-report.md`

- [ ] **Step 1: Run full local regression**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q
```

Expected: pass.

- [ ] **Step 2: Run lint**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run ruff check src tests
```

Expected: pass. Fix only issues introduced by this plan.

- [ ] **Step 3: Append final integration status**

Append to `reports/evaluation-report.md`:

````markdown
## System Integration And Production Hardening

Plan: `docs/plans/2026-05-14-aptguide2-system-integration-production-hardening-agent-plan.md`

Verification:

```bash
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q
uv run ruff check src tests
```

Reports:

- `reports/live-dependency-readiness-report.md`
- `reports/rag-v2-live-evaluation-report.md`

API contract:

- `ChatRequest.user_id`
- `ChatRequest.action`
- `ChatResponse.actions`
- `ChatResponse.pending_action`
- `ChatResponse.metadata`

Outcome:

- Local regression:
- Live dependency readiness:
- RAG v2 live eval gates:
- Remaining blocker:
````

- [ ] **Step 4: Final status**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform"
git status --short
```

Expected:

- Only intended code, tests, docs, reports, and progress files changed.
- No unrelated user changes reverted.

## 12. Recommended Agent Handoff Prompt

Give the executing agent this prompt:

```text
Use this plan and execute it task-by-task:

/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/docs/plans/2026-05-14-aptguide2-system-integration-production-hardening-agent-plan.md

Do not add rolling summary or long-term profile yet. First complete live dependency readiness, fix the RAG v2 live eval runner wiring, run live eval, and complete the public /chat API contract for harness appointment confirmation.
```
