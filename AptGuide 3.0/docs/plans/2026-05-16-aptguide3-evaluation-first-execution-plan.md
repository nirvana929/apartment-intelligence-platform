# AptGuide 3.0 Evaluation-First Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to run this plan step-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move AptGuide 3.0 from completed RAG evidence/trace/eval implementation into live evaluation, evidence validation, and go/no-go reporting.

**Architecture:** Treat the eval runner as the gatekeeper, not as a demo script. Run smoke checks first, then live RAG eval against real LLM, Milvus, MySQL, Redis, and lease services, then classify every failure as dataset gap, data alignment, identity mapping, lease validation, retrieval, grounded answer, trace visibility, or runtime error.

**Tech Stack:** Python 3.13, uv, pytest, ruff, YAML eval dataset, FastAPI ChatService, Milvus, MySQL, Redis, lease Java backend, LangSmith optional tracing.

---

## Current Baseline

- Latest reliable checkpoint: `docs/plans/checkpoints/2026-05-16-001445-rag-evidence-trace-eval-roadmap-complete.md`
- Roadmap status: all 6 RAG evidence/trace/eval plans complete.
- Latest unit verification: `347 passed`, 1 pre-existing env-var failure, ruff clean.
- Existing live report: `backend/evals/reports/rag-evaluation-report.md`
- Existing dataset: `backend/evals/datasets/rag_retrieval_cases.yaml`
- Main remaining risk: code supports evidence and lease validation, but live production-grade confidence depends on real `wechat_room_id -> canonical_room_id -> lease_room_id` mappings and current live service data.

## Evaluation Gate Definition

Evaluation passes only if the report can prove:

```text
success_rate >= 95%
runtime_error_rate = 0% for configured dependencies
room invalid_room_rate = 0%
room returned production cards have lease_validation_status=passed
room returned production cards have lease_room_id
room returned production cards have evidence_level in lease_validated/mapped_verified levels
high-risk KB citation_rate = 100%
high-risk unverified_commitment_rate = 0%
grounded_answer_rate = 100% when confidence gate passes
trace output visibility is recorded locally or explicitly marked not enabled
p95 latency is recorded and reviewed
```

## Files

- Read: `docs/plans/checkpoints/2026-05-16-001445-rag-evidence-trace-eval-roadmap-complete.md`
- Read: `docs/system/evidence-contract.md`
- Read: `docs/system/data-inventory/room-id-alignment.md`
- Read: `backend/evals/datasets/rag_retrieval_cases.yaml`
- Read: `backend/evals/runners/run_rag_eval.py`
- Generate: `backend/evals/reports/rag-evaluation-report.md`
- Update: `docs/tests/evaluation-report.md`
- Update: `reports/evaluation-report.md`
- Create: `docs/plans/checkpoints/YYYY-MM-DD-HHMMSS-evaluation-first-live-rag-gate.md`

## Task 1: Project Harness Resume And Baseline

- [ ] Run project harness snapshot.

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Expected:

```text
project = /home/chove/桌面/apartment-intelligence-platform/AptGuide 3.0
branch = codex/update-project-readme
present_state_files includes progress/current-plan.md and reports/evaluation-report.md
```

- [ ] Read the latest roadmap checkpoint.

```bash
sed -n '1,240p' docs/plans/checkpoints/2026-05-16-001445-rag-evidence-trace-eval-roadmap-complete.md
```

Expected:

```text
Status: complete
Test status: 347 passed, 1 pre-existing failure, ruff clean
Next Steps include live RAG eval and RoomIdentityRepository population
```

## Task 2: Preflight Verification

- [ ] Confirm the eval runner imports and smoke mode works.

```bash
cd backend
uv run python evals/runners/run_rag_eval.py
```

Expected:

```text
backend/evals/reports/rag-evaluation-report.md is regenerated in smoke mode
no Python import error
schema validation does not fail
```

- [ ] Run focused eval tests.

```bash
cd backend
uv run pytest tests/unit/evals/test_rag_eval_runner.py -q
```

Expected:

```text
all eval runner unit tests pass
```

- [ ] Run focused RAG tests.

```bash
cd backend
uv run pytest tests/unit/rag tests/unit/procedures/test_kb_qa.py tests/unit/procedures/test_room_search.py -q
```

Expected:

```text
RAG, grounded answer, room retrieval, and room search procedure tests pass
```

## Task 3: Live Dependency Readiness

- [ ] Verify env files contain the required live variables without printing secret values.

```bash
cd backend
uv run python - <<'PY'
from aptguide3.config import get_settings
s = get_settings()
fields = [
    "llm_base_url",
    "llm_model",
    "embedding_base_url",
    "embedding_model",
    "milvus_host",
    "milvus_port",
    "lease_base_url",
    "persistence_mode",
]
for name in fields:
    value = getattr(s, name)
    print(f"{name}: {'SET' if value else 'MISSING'}")
PY
```

Expected:

```text
all required fields are SET
persistence_mode is mysql or hybrid for live persistence checks
```

- [ ] Run live readiness tests if dependencies are running.

```bash
cd backend
uv run pytest tests/integration/test_readiness_live.py tests/integration/test_vector_live.py tests/integration/test_llm_live.py tests/integration/test_embedding_live.py tests/integration/test_lease_gateway_chain.py -q
```

Expected:

```text
tests pass or skip with explicit missing dependency reason
no unclassified failure
```

## Task 4: Run Live RAG Evaluation

- [ ] Run the live RAG gate.

```bash
cd backend
uv run python evals/runners/run_rag_eval.py --live
```

Expected:

```text
backend/evals/reports/rag-evaluation-report.md generated in live mode
report includes Summary, Live Results Detail, Pass/Fail Summary, Failure Owner Classification, Dataset Limitations
```

- [ ] Inspect the summary section.

```bash
sed -n '1,80p' backend/evals/reports/rag-evaluation-report.md
```

Expected:

```text
Total cases reported
Room search cases reported
KB QA cases reported
Unvalidated room count reported
Latency summary reported
Trace output visibility rate reported when enabled
```

## Task 5: Interpret Findings

- [ ] Classify the live result.

Use these rules:

```text
PASS:
  all cases pass
  unvalidated_room_count = 0
  high-risk criteria pass
  no runtime errors

DATA GAP:
  room Hit@K is N/A because expected_room_ids is empty
  report says dataset limitation
  no returned-card evidence failure

IDENTITY MAPPING GAP:
  failure_owner=identity_mapping
  source_record_ids exist but mapped_verified_count=0
  returned rooms cannot be tied to lease_room_id

LEASE VALIDATION GAP:
  failure_owner=lease_validation
  candidate has business identity but lease validation rejects or drops it

RETRIEVAL GAP:
  failure_owner=vector_recall or ranking
  live vector recall cannot find expected KB docs or acceptable rooms

GROUNDED ANSWER GAP:
  failure_owner=grounded_answer
  high-risk answer lacks citations or grounded_answer metadata

TRACE GAP:
  failure_owner=trace_visibility
  final ChatResponse output is not visible in local trace metadata when tracing is enabled
```

- [ ] Record the top 3 findings with owner and next action.

Use this format:

```markdown
| Priority | Finding | Owner | Evidence | Next action |
| --- | --- | --- | --- | --- |
| P0 | ... | identity_mapping | case id / report line | populate RoomIdentityRepository mapping |
```

## Task 6: Update Evaluation Reports

- [ ] Update `docs/tests/evaluation-report.md`.

Required content:

```markdown
## 2026-05-16 Live RAG Gate

- Command: `cd backend && uv run python evals/runners/run_rag_eval.py --live`
- Result: PASS / FAIL / PARTIAL
- Total cases:
- Passed:
- Failed:
- Runtime errors:
- Unvalidated room count:
- High-risk KB citation result:
- Trace visibility:
- Latency:
- Primary findings:
```

- [ ] Update `reports/evaluation-report.md` with the same executive summary.

- [ ] If live eval could not run, record the blocker explicitly instead of marking pass.

Use:

```markdown
Result: NOT RUN
Blocker: missing live dependency / env var / service unavailable
```

## Task 7: Decide Next Work

- [ ] If the result is PASS, move to main-chain integration planning:

```text
rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat
```

- [ ] If the result is IDENTITY MAPPING GAP, prioritize data loading:

```text
populate RoomIdentityRepository with real wechat_room_id -> canonical_room_id -> lease_room_id mappings
rerun live RAG eval
```

- [ ] If the result is DATASET GAP, expand `backend/evals/datasets/rag_retrieval_cases.yaml`:

```text
room_search: add expected.allowed_room_ids or expected_room_ids for known seeded rooms
kb_qa: add more high-risk and medium-risk policy cases
integration: add appointment/lease/memory/handoff cases in a separate eval runner or dataset section
```

- [ ] If the result is RETRIEVAL or GROUNDED ANSWER GAP, create a focused fix plan before tuning prompts or ranking.

## Task 8: Checkpoint

- [ ] Create a factual checkpoint.

Path:

```text
docs/plans/checkpoints/YYYY-MM-DD-HHMMSS-evaluation-first-live-rag-gate.md
```

Required sections:

```markdown
# Checkpoint: evaluation-first live RAG gate

## Metadata
- Created at:
- Task:
- Status:
- Test status:

## Completed Work

## Verification

## Findings

## Known Issues

## Next Steps
```

- [ ] Update project harness state files:

```text
progress/current-plan.md
progress/completed.md
progress/known-issues.md
progress/next-steps.md
reports/evaluation-report.md
```

- [ ] Run project harness snapshot again.

```bash
python3 /home/chove/.codex/skills/project-harness/scripts/project_harness.py snapshot
```

Expected:

```text
snapshot reflects the new evaluation checkpoint and updated next steps
```

## Acceptance Criteria

- [ ] Live RAG eval either runs to completion or records a precise dependency blocker.
- [ ] Every failed live case has exactly one failure owner.
- [ ] Evidence/identity/lease validation failures are separated from retrieval quality failures.
- [ ] High-risk KB answers are checked for citations and unverified commitments.
- [ ] Latency is reported.
- [ ] Project harness state points to evaluation as the active next phase.
