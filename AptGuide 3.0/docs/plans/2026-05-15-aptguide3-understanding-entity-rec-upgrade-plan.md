# AptGuide 3.0 Understanding, Entity Resolution, and Rec Upgrade Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the upper-layer understanding and data-aware retrieval planning so later room-search, KB QA, appointment, lease, memory, and handoff subsystems can be improved against real data instead of prompt guesses.

**Architecture:** Keep the current LLM-first rule: the LLM interprets natural language into a structured plan, deterministic code validates and resolves entities, and retrieval/procedures execute the plan. The first upgrade layer is data sync plus baseline eval; the second is prompt tuning and entity resolution; the third is conservative multi-route room recall and subsystem-specific improvements.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, OpenAI-compatible DashScope client, LangSmith, Milvus, lease internal API, MySQL, Redis, pytest, existing AptGuide 3.0 RAG/eval infrastructure.

---

## Current Status From Project Harness

- Active project: AptGuide 3.0.
- Active plan before this document: `docs/plans/2026-05-15-aptguide3-rec-eval-langsmith-data-inventory-plan.md`.
- Milestone 0-6 are complete.
- Milestone 7 data inventory and baseline analysis files exist.
- Current baseline finding: all 4 seed cases route correctly through understanding, but fail at data/vector layer.
- First confirmed blocker: Milvus room and KB data alignment:
  - room search expects usable room vectors;
  - KB search needs fields such as `chunk_id`, `doc_id`, `module`, and `risk_level`.
- Current full-suite caveat: 35 pre-existing asyncio runner failures remain outside this plan unless they block focused tests.

## Upgrade Principles

- Do not add keyword fallback for intent, task, filters, or preferences.
- Do not let vector recall override lease/database hard validation.
- Do not tune prompt blindly; tune only against eval cases and LangSmith traces.
- Do not ask the LLM to invent database IDs.
- Use lease/API data as the business source of truth for rooms, districts, apartments, appointments, leases, contracts, and user facts.
- Use MySQL for AptGuide agent state, not room business facts.
- Use Milvus as a retrieval index, not an authoritative data source.
- Use Redis for hot state / TTL only.

## Phase 0: Finish Data Baseline Before Optimization

**Purpose:** Make sure future tuning is not hiding data problems.

**Files:**
- Read/modify: `docs/plans/2026-05-15-aptguide3-rec-eval-langsmith-data-inventory-plan.md`
- Read/modify: `docs/system/data-inventory/**`
- Read/modify: `docs/plans/analysis/2026-05-15-rec-eval-baseline-analysis.md`
- Read/modify: `backend/evals/reports/rag-evaluation-report.md`
- Read/modify: `docs/tests/verification-log.md`

- [ ] **Step 1: Sync or align room vectors**

Run or fix the room vector sync path so the code and Milvus agree on the room collection name and schema.

Expected result:

```text
room collection exists
room collection has searchable room records
room metadata includes district/rent/availability fields needed by retrieval
```

- [ ] **Step 2: Sync or align KB vectors**

Run or fix the KB vector sync path so KB records expose stable IDs and module/risk metadata.

Expected required fields:

```text
chunk_id
doc_id
title
module
content
risk_level
```

- [ ] **Step 3: Re-run live rec/RAG eval with LangSmith**

Run from `backend` with live env and LangSmith enabled:

```bash
uv run python evals/runners/run_rag_eval.py --live
```

Expected: failures, if any, are no longer caused only by missing Milvus data/schema.

- [ ] **Step 4: Update baseline analysis**

Update `docs/plans/analysis/2026-05-15-rec-eval-baseline-analysis.md` with:

- data health after sync;
- per-case failure owner;
- whether understanding, entity resolution, vector recall, lease validation, ranking, confidence gate, or rendering should be optimized first.

## Phase 1: Understanding Prompt Tuning

**Purpose:** Improve the upper-layer planner so it reliably decides task, filters, preferences, clarification needs, risk, and retrieval queries.

**Files:**
- Modify: `backend/src/aptguide3/understanding/prompts.py`
- Modify/add tests: `backend/tests/unit/understanding/test_llm_understanding.py`
- Modify/add eval cases: `backend/evals/datasets/rag_retrieval_cases.yaml`
- Read: LangSmith traces from baseline runs

- [ ] **Step 1: Preserve current prompt location and baseline**

Record the current prompt file:

```text
backend/src/aptguide3/understanding/prompts.py
```

Before editing, record current route/task/filter/risk results for the seed eval cases.

- [ ] **Step 2: Add few-shot examples**

Add examples for:

- `room_search`
- `kb_qa`
- `appointment`
- `lease`
- `memory`
- `handoff`
- `clarify`

Each example should show the exact JSON shape expected by `UnderstandingResult`.

- [ ] **Step 3: Add clarification policy examples**

Document and test these strategies:

```text
clarify_only        -> user intent or required context is too vague
recommend           -> enough hard constraints and soft preferences exist
recommend_then_ask  -> enough boundary exists to show candidates, but budget/room type/details are missing
```

The current schema does not yet include `response_strategy`. If adding it, update `UnderstandingResult`, validation tests, eval rendering, and response behavior in one coherent change. If not adding it yet, encode the behavior through `clarification.needed`, `reason`, and procedure metadata.

- [ ] **Step 4: Add hard-filter vs soft-preference examples**

Prompt examples should distinguish:

```text
hard_filters: district/location, rent, room_type, payment_type, apartment_id, availability-like constraints
soft_preferences: quiet, bright, near metro, convenient life, newer feel, facilities, commute comfort
```

- [ ] **Step 5: Add risk examples**

Add high/medium/low examples for rental policy and lease questions.

Expected: high-risk questions such as deposit disputes should set `risk.level=high` and prefer source-grounded or handoff-safe responses.

- [ ] **Step 6: Run focused tests and eval**

Run:

```bash
uv run pytest tests/unit/understanding -q
uv run python evals/runners/run_rag_eval.py --live
```

Expected: prompt changes improve or preserve route/task/filter/risk accuracy on the same eval cases.

## Phase 2: Entity Resolution and Data-Aware Planning

**Purpose:** Add a deterministic bridge between LLM text extraction and database/vector retrieval.

**Files:**
- Create: `backend/src/aptguide3/understanding/entity_resolution.py`
- Modify: `backend/src/aptguide3/rag/planning.py`
- Modify: `backend/src/aptguide3/understanding/validation.py`
- Add tests: `backend/tests/unit/understanding/test_entity_resolution.py`
- Read: `docs/system/data-inventory/**`

- [ ] **Step 1: Define resolver contract**

Create a resolver that accepts LLM hard filters and returns:

```python
{
    "resolved_filters": {},
    "unresolved_filters": {},
    "ambiguities": [],
    "resolution_notes": []
}
```

Expected behavior:

- `番禺`, `番禺区`, `广州番禺` can resolve to canonical district data when the dictionary exists.
- unresolved text remains as `area_text`.
- ambiguous entities return ambiguity instead of guessing.

- [ ] **Step 2: Source dictionaries from real data**

Use data inventory to decide the authoritative dictionary source.

Preferred source order:

```text
lease API / lease database metadata
  -> generated local dictionary snapshot
  -> Milvus metadata only as fallback hints
```

Do not use MySQL agent-state tables as the source of truth for room entities.

- [ ] **Step 3: Normalize enumerations**

Handle enum-like values:

- room type: `单间`, `一房`, `整租`, `合租`;
- payment type: monthly/quarterly/semi-annual/annual variants;
- district/business-area/metro/landmark aliases when data supports them.

- [ ] **Step 4: Integrate before retrieval planning**

Future flow:

```text
LLM UnderstandingResult
  -> entity resolver
  -> normalized RetrievalPlan
  -> route A / route B retrieval
```

`rag/planning.py` should receive or call resolver output before building `hard_filters`.

- [ ] **Step 5: Add diagnostics**

Record resolver output into eval reports:

```text
resolved_filters
unresolved_filters
ambiguities
resolution_notes
```

Expected: eval can tell whether a failure came from LLM extraction or deterministic entity resolution.

## Phase 3: Conservative Multi-Route Room Recall

**Purpose:** Improve room-search coverage while keeping hard constraints authoritative.

**Files:**
- Modify: `backend/src/aptguide3/rag/room_retrieval.py`
- Modify: `backend/src/aptguide3/rag/room_ranking.py`
- Modify: `backend/src/aptguide3/procedures/room_search.py`
- Add tests: `backend/tests/unit/rag/test_room_retrieval.py`
- Add tests: `backend/tests/unit/procedures/test_room_search.py`

- [ ] **Step 1: Preserve current vector route**

Keep Milvus semantic recall as route B.

It should handle:

- quiet;
- bright;
- commute comfort;
- nearby convenience;
- facilities;
- room-description similarity.

- [ ] **Step 2: Add or expose hard-condition recall as route A**

Route A should use lease/database-backed structured filters:

```text
district_id / district_name
business_area_id
metro_station_id
max_rent / min_rent
room_type
availability
```

If lease has no search endpoint that supports this cleanly, document the gap before implementing a workaround.

- [ ] **Step 3: Merge and dedupe**

Merge candidates from route A and route B by canonical room ID.

If vector-only records have no lease room ID, they must not be recommended as final room cards until lease validation can map or validate them.

- [ ] **Step 4: Lease real-time validation**

All final candidates must pass lease validation.

Expected rule:

```text
semantic match is not enough
hard filters and availability must still pass
```

- [ ] **Step 5: Preference reranking**

Use user memory/preferences as rerank input after route A/B candidates exist.

Do not use preference as the first primary recall route in the first version.

- [ ] **Step 6: Eval route contribution**

Report:

```text
route_a_count
route_b_count
merged_count
lease_validated_count
reranked_count
final_room_ids
```

Expected: eval shows whether database recall, vector recall, or reranking caused the final result.

## Phase 4: Subsystem-by-Subsystem Upgrades

**Purpose:** Upgrade each procedure after the shared understanding/resolver/retrieval foundation is observable.

### 4.1 Room Search

- Improve data-backed recall and ranking after Phase 0-3.
- Add eval cases with real expected room IDs.
- Add no-result relaxation strategy only after strict results are explainable.

### 4.2 KB QA

- Re-sync KB vectors with stable metadata.
- Improve risk classification and source-grounded answer behavior.
- Add expected doc/source IDs to eval cases.

### 4.3 Appointment

- Use entity resolution for apartment/room references.
- Keep write operations confirmation-gated.
- Add eval for missing apartment/time, confirmation, and lease API failures.

### 4.4 Lease

- Improve authenticated lease/contract query planning.
- Add risk-aware responses for sensitive user data.
- Keep lease as source of truth.

### 4.5 Memory

- Use explicit user consent or clear user instruction before saving preferences.
- Feed saved preferences into reranking, not primary recall at first.

### 4.6 Handoff

- Route high-risk, ambiguous, or unsupported cases to human handoff.
- Add traceable handoff reasons.

## Verification Gates

Before claiming each phase complete:

- focused unit tests pass;
- relevant live tests pass or are explicitly skipped with reason;
- `uv run ruff check src tests` passes for changed Python files;
- LangSmith run/project reference is recorded when live LLM eval is used;
- eval report identifies failure owner rather than only pass/fail;
- no secrets, PII, full message dumps, full KB content, or vectors are committed.

## Recommended Execution Order

1. Finish Milvus room/KB sync and rerun baseline.
2. Add prompt examples only for failures shown by eval/LangSmith.
3. Add entity resolver from real lease/data dictionaries.
4. Add route A hard-condition recall.
5. Keep route B semantic recall as supplemental.
6. Add preference reranking.
7. Upgrade room_search eval first, then KB QA, then appointment/lease/memory/handoff.

## Completion Criteria

- Updated baseline proves whether failures are now data, understanding, resolver, recall, validation, ranking, confidence, or rendering issues.
- Understanding prompt has targeted examples and tests.
- Entity resolution plan is grounded in real data inventory.
- Multi-route room recall has a conservative implementation plan with hard validation.
- Each future subsystem upgrade has a scoped starting point and verification gate.
