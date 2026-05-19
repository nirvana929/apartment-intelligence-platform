# AptGuide 3.0 Rec Eval, LangSmith, and Data Inventory Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run an eval-first diagnosis of the rec/RAG system with LangSmith enabled and a reliable data inventory so failures can be attributed before optimization.

**Architecture:** Treat evaluation as a two-input process: live trace evidence from LangSmith plus local knowledge of what data exists in MySQL, Redis, Milvus, and lease. Create a durable `docs/system/data-inventory/` folder for data-source facts, then run rec/RAG eval against known data and classify failures by stage.

**Tech Stack:** Python 3.12, FastAPI, OpenAI-compatible DashScope client, LangSmith, MySQL, Redis, Milvus, lease internal API, pytest, existing `backend/evals/runners/run_rag_eval.py`.

---

## Scope Boundary

In scope:

- Enable LangSmith for the eval run only; default remains off.
- Build a project-level data inventory folder that explains what each data source contains.
- Add or use safe read-only inventory commands that do not dump values, secrets, embeddings, messages, or PII.
- Run the current 4 seed rec/RAG eval cases as a baseline.
- Classify each failure as one of: data inventory, understanding, vector recall, lease validation, ranking, confidence gate, response rendering, or dataset label gap.
- Produce an analysis document for the user to review before optimization.

Out of scope:

- Do not tune prompts, retrieval, ranking, chunking, or confidence thresholds during the baseline.
- Do not add keyword fallback.
- Do not implement multi-route room recall in this baseline plan.
- Do not run write-heavy sync scripts unless explicitly approved.
- Do not print `.env`, API keys, internal tokens, MySQL passwords, user messages, lease customer data, full KB content, or embedding vectors.

## Current Findings To Preserve

- LangSmith config and wrapper already exist in `backend/src/aptguide3/config.py` and `backend/src/aptguide3/api/deps.py`.
- Understanding and rec diagnostics already exist in:
  - `backend/src/aptguide3/understanding/diagnostics.py`
  - `backend/src/aptguide3/rag/diagnostics.py`
  - `backend/evals/runners/run_rag_eval.py`
- Current eval report has stale classification text: per-case output shows `room_search` / `kb_qa`, but findings still discuss `clarify`.
- Current room cases have empty `expected_room_ids`, so room Hit@K cannot measure quality yet.
- Current KB live output appears to have vector hits but `unique_chunk_count=0`, suggesting KB vector metadata may be missing `chunk_id`.

## Proposed Agent Split

### Agent A: Data Inventory Folder

**Ownership:**
- Create/modify only `docs/system/data-inventory/**`.
- If script work is needed, propose it first; do not dump live data.

**Deliverable:**
- Human-readable inventory docs for MySQL, Redis, Milvus, lease API, LLM/embedding, and LangSmith.
- A runbook describing safe inventory generation.

### Agent B: Safe Inventory Script

**Ownership:**
- `backend/scripts/generate_data_inventory.py`
- Tests under `backend/tests/unit/scripts/` if script logic is added.

**Deliverable:**
- Read-only script that writes sanitized JSON/Markdown summaries.
- No table row values, Redis values, Milvus vectors, KB full content, lease customer data, or secrets.

### Agent C: Eval Runner and Report Fixes

**Ownership:**
- `backend/evals/runners/run_rag_eval.py`
- `backend/evals/datasets/rag_retrieval_cases.yaml`
- `backend/tests/unit/evals/` if eval helper tests are added.

**Deliverable:**
- Correct findings classification.
- Expected-vs-actual fields for route/task/risk and stage failure.
- Report explicitly calls out dataset gaps instead of treating them as rec quality failures.

### Agent D: Baseline Execution and Analysis

**Ownership:**
- `backend/evals/reports/**`
- `docs/tests/verification-log.md`
- `docs/tests/evaluation-report.md`
- A new analysis document under `docs/plans/analysis/`.

**Deliverable:**
- LangSmith-backed baseline run.
- Local report that explains which stage is broken and what should be optimized next.

## Task 1: Confirm LangSmith Eval Configuration

**Files:**
- Read: `backend/.env.example`
- Read: `backend/src/aptguide3/config.py`
- Read: `backend/src/aptguide3/api/deps.py`
- Test: `backend/tests/unit/api/test_langsmith_config.py`
- Test: `backend/tests/unit/test_config.py`

- [ ] **Step 1: Verify default-off behavior**

Run from `backend`:

```bash
uv run pytest tests/unit/api/test_langsmith_config.py tests/unit/test_config.py -q
```

Expected: tests pass and prove LangSmith is not required when disabled.

- [ ] **Step 2: Prepare eval-only environment**

Use shell exports or a local `.env` that is not committed:

```bash
export APTGUIDE3_LANGSMITH_TRACING=true
export APTGUIDE3_LANGSMITH_PROJECT=aptguide3-rec-eval-local
export APTGUIDE3_UNDERSTANDING_DIAGNOSTICS_ENABLED=true
export LANGSMITH_API_KEY='<set locally, never commit>'
```

Expected: LangSmith is enabled only for this eval session.

- [ ] **Step 3: Record constraints**

Append the command shape, not secret values, to `docs/tests/verification-log.md`.

## Task 2: Create Data Inventory Folder

**Files:**
- Create: `docs/system/data-inventory/README.md`
- Create: `docs/system/data-inventory/sources.md`
- Create: `docs/system/data-inventory/mysql-schema.md`
- Create: `docs/system/data-inventory/redis-keys.md`
- Create: `docs/system/data-inventory/vector-collections.md`
- Create: `docs/system/data-inventory/lease-api.md`
- Create: `docs/system/data-inventory/external-ai.md`
- Create: `docs/system/data-inventory/inventory-runbook.md`

- [ ] **Step 1: Document source responsibilities**

Record:

- MySQL owns AptGuide 3.0 durable agent state.
- Redis owns hot state / TTL patterns only when wired.
- Milvus owns `apt_room_vector` and `apt_rental_kb`.
- lease owns room, apartment, appointment, lease, contract, and user business truth.
- LLM/embedding providers process eval text and retrieval text.
- LangSmith is observability, not a business data store.

- [ ] **Step 2: Document MySQL schema**

Use `backend/src/aptguide3/database/schema.sql` as the source of truth. List the 11 tables and their purpose. Mark message/content/payload/json fields as sensitive and not safe to dump.

- [ ] **Step 3: Document Redis key patterns**

Use `backend/src/aptguide3/persistence/redis_store.py` and config fields. Record key prefix, TTLs, and allowed inventory operations: `SCAN`, `TYPE`, `TTL`, counts only.

- [ ] **Step 4: Document Milvus collections**

Use `backend/src/aptguide3/integrations/vector_client.py` and `backend/src/aptguide3/rag/chunking.py`. Record collection names, fields, count expectations, and the rule that vectors and full `content` are never exported.

- [ ] **Step 5: Document lease API dependency**

Use `backend/src/aptguide3/integrations/lease_client.py`. Record endpoints by purpose, but do not include tokens or customer payload examples.

## Task 3: Add Safe Inventory Generation

**Files:**
- Create: `backend/scripts/generate_data_inventory.py`
- Create: `backend/tests/unit/scripts/test_generate_data_inventory.py`
- Output: `docs/system/data-inventory/generated/`

- [ ] **Step 1: Write tests for sanitization**

Test that DSNs redact passwords, Redis values are never fetched, Milvus vectors/content are not serialized, and known sensitive field names become `<redacted>`.

- [ ] **Step 2: Implement metadata-only inventory**

Implement:

- MySQL: `information_schema` tables, columns, indexes, row counts.
- Redis: key pattern counts, key types, TTL summary only.
- Milvus: collection names, schema, `num_entities`, required field coverage where possible.
- Config: env var presence and model names only; no raw secrets.

- [ ] **Step 3: Generate docs**

Run:

```bash
uv run python scripts/generate_data_inventory.py --output ../docs/system/data-inventory/generated --no-values
```

Expected: generated JSON/Markdown summaries exist and contain no secrets or PII.

## Task 4: Fix Eval Report Classification Before Baseline

**Files:**
- Modify: `backend/evals/runners/run_rag_eval.py`
- Test: `backend/tests/unit/evals/test_run_rag_eval_report.py`

- [ ] **Step 1: Add tests for current failure classes**

Test report rendering for:

- `phase=room_search` with `failure_stage=vector_recall_empty`
- `phase=kb_qa` with `vector_hits_total>0` and `unique_chunk_count=0`
- `expected_room_ids=[]` dataset gap
- `expected risk_level=high` but actual diagnostic risk is `low`

- [ ] **Step 2: Fix stale clarify text**

Change findings logic so it only says `clarify` when the actual phase is `clarify`.

- [ ] **Step 3: Add stage classification**

Each case should render:

```text
failure_owner=<data_inventory|understanding|vector_recall|lease_validation|ranking|confidence_gate|response_rendering|dataset_label_gap|none>
```

Expected: current report can identify empty room recall, KB metadata gap, and dataset gaps without calling them prompt/ranking problems.

## Task 5: Run Baseline Eval With LangSmith

**Files:**
- Read: `backend/evals/datasets/rag_retrieval_cases.yaml`
- Output: `backend/evals/reports/rag-evaluation-report.md`
- Modify: `docs/tests/verification-log.md`
- Modify: `docs/tests/evaluation-report.md`

- [ ] **Step 1: Run service readiness**

Run from `backend` with live env configured:

```bash
uv run pytest tests/integration/test_readiness_live.py -v
```

Expected: live dependencies required for eval are reachable or explicitly reported unavailable.

- [ ] **Step 2: Run rec/RAG live eval**

Run:

```bash
uv run python evals/runners/run_rag_eval.py --live
```

Expected: report is regenerated with per-case understanding diagnostics, rec diagnostics, and failure owner.

- [ ] **Step 3: Capture LangSmith reference**

Record the LangSmith project name and run window in `docs/tests/verification-log.md`. Do not copy raw user payloads or secrets into repo docs.

## Task 6: Analyze Before Optimizing

**Files:**
- Create: `docs/plans/analysis/2026-05-15-rec-eval-baseline-analysis.md`
- Modify: `progress/current-plan.md`
- Modify: `progress/next-steps.md`
- Modify: `reports/evaluation-report.md`

- [ ] **Step 1: Summarize data health**

Use data inventory output to answer:

- Are Milvus collections present?
- How many room and KB vectors exist?
- Are required metadata fields present?
- Does lease expose enough rooms to make `expected_room_ids` meaningful?

- [ ] **Step 2: Summarize eval failures**

For each seed case, record:

- expected route/task/risk
- actual route/task/risk
- failure owner
- evidence from local report
- LangSmith run reference
- whether optimization is allowed now or blocked by data/dataset issues

- [ ] **Step 3: Recommend optimization target**

Pick exactly one first optimization target after baseline:

- data sync / vector metadata
- dataset labels
- understanding prompt/risk classification
- vector recall
- lease validation
- ranking
- confidence gate
- response rendering

Do not implement the optimization in this plan.

## Deferred Extension: Multi-Route Room Recall

This is a future `room_search` optimization direction, not part of the current baseline eval.

The target architecture is a conservative multi-route recall pipeline:

```text
user query
  -> LLM structured understanding
  -> deterministic entity normalization
  -> route A: lease/database hard-condition recall
  -> route B: Milvus semantic soft-preference recall
  -> merge and dedupe candidates
  -> lease real-time validation
  -> user preference reranking
  -> final ranked room cards
```

Route A is the primary recall path for hard constraints:

- district / business area / metro station after normalization to IDs;
- rent range;
- room type;
- availability status;
- other structured lease-backed filters.

Route B is a supplemental recall path for semantic or fuzzy preferences:

- quiet;
- bright;
- suitable for commuting;
- convenient nearby living;
- newer building feel;
- facilities and room-description similarity.

User preference should not become an independent primary recall path in the first version. It should initially rerank candidates produced by Route A and Route B. Preference-driven expansion can be considered later only when strict results are too few, and it should be explicit that hard constraints are being relaxed.

The important implementation rule is that vector recall can expand coverage, but it cannot override lease/database hard validation. A semantically similar room must still pass district, rent, room type, and availability checks before it can be recommended.

## Deferred Extension: Understanding Prompt Tuning

This is a future upper-layer optimization after baseline eval and data inventory are available.

Current prompt location:

- `backend/src/aptguide3/understanding/prompts.py`

Current prompt gaps to evaluate before changing:

- few-shot examples for room search, KB QA, appointment, lease, memory, handoff, and clarify;
- clarification policy examples, such as `clarify_only`, `recommend`, and `recommend_then_ask`;
- hard-filter vs soft-preference examples;
- risk-level examples for high-risk rental policy questions;
- retrieval query generation examples;
- explicit boundary that the LLM may identify location text but should not invent database IDs unless a trusted dictionary/resolver provides them.

Prompt tuning should be driven by eval failures, not by guesswork. The expected workflow is:

```text
baseline eval + LangSmith traces
  -> classify understanding failures
  -> add targeted prompt examples
  -> rerun the same eval cases
  -> keep changes only if route/task/filter/risk accuracy improves without regressions
```

The prompt should produce a structured plan for lower layers:

- `task`
- `hard_filters`
- `soft_preferences`
- `retrieval_queries`
- `clarification.needed`
- `clarification.question`
- `risk`
- future `response_strategy`, if the schema is extended later.

## Deferred Extension: Entity Resolution and Data-Aware Planning

This is a future bridge between upper-layer understanding and lower-layer retrieval.

Current state:

- There is no full entity resolver module.
- `backend/src/aptguide3/integrations/vector_client.py` only has a narrow `_normalize_district()` helper that converts short district text like `番禺` to `番禺区`.
- `backend/src/aptguide3/understanding/validation.py` validates filter shape and allowed keys, but does not map aliases to IDs.
- `backend/src/aptguide3/rag/planning.py` passes `hard_filters` from understanding into retrieval mostly unchanged.

Future resolver responsibilities:

- map `番禺`, `番禺区`, `广州番禺` to a canonical district name and `district_id`;
- map business areas, metro stations, landmarks, and apartment names to canonical IDs when source data supports it;
- normalize room types, payment types, and other enum-like filters;
- preserve unresolved user text as `area_text` when no safe ID match exists;
- return ambiguity when one phrase could map to multiple entities;
- never guess IDs that are absent from the data inventory.

The resolver should be data-aware. It must be planned against the actual data assets documented in `docs/system/data-inventory/`:

- lease API / lease database for authoritative district, business-area, metro, apartment, and room IDs;
- Milvus room collections for indexed room metadata and searchable text;
- MySQL only for AptGuide agent state, not as the source of truth for rooms;
- Redis only for hot state and TTL, not canonical entity data.

The intended future flow is:

```text
LLM understanding output
  -> entity resolver using lease/database dictionaries
  -> normalized retrieval plan with IDs where available
  -> route A lease/database hard-condition recall
  -> route B Milvus semantic recall
  -> merge, validate, rerank
```

This extension should not be implemented until the data inventory confirms which authoritative tables/endpoints/collections contain district, metro, apartment, and room metadata.

## Completion Criteria

- `docs/system/data-inventory/` exists and explains current data assets.
- Safe generated inventory exists or the blocker is recorded.
- LangSmith eval run is enabled for the baseline only.
- `backend/evals/reports/rag-evaluation-report.md` no longer has stale `clarify` conclusions when phase is not `clarify`.
- Baseline analysis identifies the next optimization target with evidence.
- No secrets, PII, full message dumps, full KB content, or vectors are committed.
