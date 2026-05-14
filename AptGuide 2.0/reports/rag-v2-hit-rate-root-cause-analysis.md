# RAG v2 Hit Rate Root Cause Analysis

Date: 2026-05-14
Scope: Analyze why `reports/rag-v2-live-evaluation-report.md` reports low KB source hit@3 and room hit@5 before changing retrieval logic.

## 1. Baseline From Existing Reports

### 1.1 MVP retrieval report

Source: `backend/evals/reports/rag_eval_report.md`

| Suite | Cases | Pass | Rate | Gate | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Room | 70 | 50 | 71.4% | >= 70% | PASS |
| KB | 35 | 35 | 100.0% | >= 80% | PASS |
| Fallback | 15 | 15 | 100.0% | >= 80% | PASS |

Interpretation: The earlier MVP report did not show a KB retrieval crisis. Its room suite was already weaker than KB, but passed the MVP gate.

### 1.2 RAG v2 live report

Source: `reports/rag-v2-live-evaluation-report.md`

| Metric | Value | Gate | Status |
| --- | ---: | ---: | --- |
| KB source hit@3 | 48.6% | >= 90% | FAIL |
| KB source hit@5 | 51.4% | - | PASS |
| Room hit@5 | 40.0% | >= 85% | FAIL |
| High-risk fallback | 100.0% | >= 100% | PASS |
| Unvalidated rooms | 0 | = 0 | PASS |

Interpretation: The safety gates are healthy, but retrieval quality gates are not. The sharp KB drop from 100% MVP to 48.6% v2 live is unlikely to be explained only by vector quality. It points to runner, routing, pipeline, or dataset mismatch.

## 2. Report-Level Failure Classification

### 2.1 KB failures

The v2 live report has 17 failed KB cases:

| Failure type | Count | Case ids |
| --- | ---: | --- |
| No KB sources returned | 11 | kb-005, kb-006, kb-007, kb-008, kb-009, kb-010, kb-017, kb-020, kb-022, kb-023, kb-027 |
| Expected source not in top-5 | 6 | kb-002, kb-018, kb-019, kb-030, kb-034, kb-035 |

This split matters:

- "No KB sources returned" usually means routing or source generation failed before ranking can help.
- "Expected source not in top-5" means retrieval happened, but recall/rerank/source alignment is weak.

### 2.2 Room failures

The v2 live report has 3 failed room cases:

| Failure type | Count | Case ids |
| --- | ---: | --- |
| No rooms returned | 2 | room-002, room-004 |
| Expected room not in top-5 | 1 | room-005 |

This suggests two distinct room issues:

- Validation or hard filters may remove all candidates.
- Ranking may prefer candidates from the wrong semantic/metadata cluster.

## 3. Findings From Static Code Inspection

### 3.1 RAG v2 pipeline does not actually use the v2 KB hybrid/rerank path

`backend/src/aptguide2/rag/pipeline_v2.py` builds a `RetrievalPlan`, but the KB branch calls:

```python
sources, is_confident = retrieve_kb(qr, vector_adapter, embed_fn)
```

That function is the MVP KB retrieval path. The v2 modules `hybrid.py` and `rerank.py` are not wired into the runtime path used by `run_rag_v2.py`.

Impact:

- The report is named RAG v2 live eval, but KB is still mostly evaluated through MVP-style dense recall plus light character/module boosts.
- Planning signals such as `module_intent`, `semantic_queries`, `sparse_queries`, and governed rerank weights do not affect KB live metrics.

Likely contribution to KB hit@3 failure: high.

### 3.2 Many failed KB cases are routed away from KB before retrieval

I ran `understand_query()` over the v2 failed cases. The following failed KB cases do not parse as `kb_qa`:

| Case | Query | Parsed task | Expected |
| --- | --- | --- | --- |
| kb-005 | 可以用花呗付房租吗 | fallback | KB-PAY-002 |
| kb-006 | 月付和季付有什么区别 | room_search | KB-PAY-001 / KB-PAY-003 |
| kb-007 | 入住需要带什么 | fallback | KB-LEASE-012 / KB-LIFE-001 |
| kb-008 | 房间空调坏了找谁修 | room_search | KB-LIFE-001 / KB-LIFE-002 |
| kb-009 | 可以养宠物吗 | fallback | KB-LIFE-005 |
| kb-010 | 合租可以带朋友住吗 | room_search | KB-LIFE-009 / KB-POLICY-009 |
| kb-017 | 租房需要什么材料 | room_search | KB-LEASE-002 |
| kb-020 | 电费怎么算 | fallback | KB-PAY-005 |
| kb-022 | 可以转租吗 | fallback | KB-LEASE-008 / KB-LEASE-009 |
| kb-023 | 公共区域卫生谁打扫 | fallback | KB-LIFE-003 / KB-LIFE-006 |
| kb-027 | 预约后迟到怎么办 | fallback | KB-APPT-006 |
| kb-034 | 换房间可以吗 | room_search | KB-LEASE-010 / KB-APPT-004 |

Impact:

- These failures should not initially be treated as vector retrieval misses.
- The primary failure is task routing and query understanding coverage.
- Current keyword routing confuses policy/life/payment questions with room search because terms like `房间`, `月付`, `合租`, and `租房` are treated as room-search signals unless a KB keyword matches earlier.

Likely contribution to KB hit@3 failure: very high.

### 3.3 Some room eval labels are internally inconsistent

The v2 eval file marks its room cases as placeholders:

```yaml
# Room Retrieval Cases (5 placeholder - needs data handoff)
```

Two cases have obvious hard-filter annotation mismatches:

| Case | Query | Parsed by code | YAML hard_filters |
| --- | --- | --- | --- |
| room-004 | 番禺区2000以内适合考研 | district_id=4 | district_id=5 |
| room-005 | 白云区大面积低预算 | district_id=5 | district_id=2 |

Even though the runner does not directly read `hard_filters`, this shows the expected IDs and annotations may not be reliable. The expected room IDs should be revalidated against lease data before using these five cases as a quality gate.

Likely contribution to room hit@5 failure: medium to high.

### 3.4 Room validation can turn recall misses into empty final results

`pipeline_v2.py` retrieves vector candidates, then calls:

```python
validated = validate_room_candidates(candidates, plan.hard_filters, lease_validator)
```

`validation.py` sends all candidate room IDs plus hard filters to lease. If lease returns no rooms, the final output has no rooms and the eval reports "no rooms returned".

This is correct product behavior, but it hides where the failure occurred:

- vector recall returned no relevant candidates;
- vector recall returned expected IDs but lease rejected them;
- expected IDs are not currently active/published in lease;
- hard filters are stricter than the case expectation;
- payment type was parsed but lease does not support/filter it as expected.

The current report does not include candidate IDs before validation, validated IDs, or lease rejection reason. Therefore it cannot distinguish retrieval failure from validation/data mismatch.

Likely contribution to room hit@5 failure: unknown until instrumented.

### 3.5 Current reports lack trace evidence for failed cases

`run_rag_v2.py` only records final `actual_doc_ids` or final `actual_room_ids`. It does not persist:

- parsed task;
- hard filters;
- semantic queries;
- vector raw candidates;
- rerank feature scores;
- validation request payload;
- validation response room IDs;
- confidence gate top score and reason.

This makes the report useful for outcome measurement, but insufficient for root-cause debugging.

## 4. Current Root-Cause Hypotheses

### H1: KB hit@3 is primarily depressed by query-understanding routing gaps

Evidence:

- 12 failed KB cases parse as `fallback` or `room_search`.
- The eval runner labels all of them as KB retrieval failures because `kb_sources` is empty.
- These cases include common policy/payment/life expressions missing from `kb_keywords`.

Status: strongly supported by static experiment.

### H2: KB hit@3 is secondarily depressed because v2 hybrid/rerank is not wired into pipeline_v2

Evidence:

- `pipeline_v2.py` calls MVP `retrieve_kb(qr, ...)`.
- `rerank_kb_sources()` and `merge_hybrid_candidates()` are only covered by unit tests and not used by the live pipeline.
- Ranking failures such as kb-002 and kb-035 show related lease documents retrieved, but the expected one is below top-5.

Status: strongly supported by code inspection.

### H3: Room hit@5 is not yet trustworthy because the five v2 room cases are placeholders with annotation mismatches

Evidence:

- Dataset comment explicitly says the room cases are placeholders.
- Two of five room cases have query-vs-hard-filter mismatches.
- Expected IDs need to be checked against current lease active rooms and Milvus indexed rooms.

Status: supported; needs data validation.

### H4: Room empty-result failures may be caused by lease validation and hard-filter intersection, not only vector recall

Evidence:

- Product pipeline correctly refuses to display unvalidated rooms.
- Current report does not show pre-validation candidates.
- Failures `room-002` and `room-004` are "no rooms returned", which occurs after validation if no room survives.

Status: plausible; needs instrumentation experiment.

## 5. Recommended Experiments Before Fixing

### Experiment E1: Routing audit over all 55 v2 cases

Goal: quantify how many eval expectations disagree with `understand_query()`.

For each case, record:

- `case_id`
- `query`
- `case_type`
- parsed `task`
- parsed `risk_level`
- parsed `hard_filters`
- parsed `soft_preferences`
- expected task/source/rooms

Decision rule:

- If a KB case is parsed as non-KB, fix or redesign routing before touching vector search.
- If a room case has query/expected metadata mismatch, quarantine or correct the case before counting it against retrieval quality.

### Experiment E2: KB retrieval stage trace for failed KB cases

Goal: separate routing, vector recall, rerank, and confidence failures.

For each failed KB case, log:

- task and risk level;
- recall queries generated;
- raw top-10 doc IDs per recall query;
- merged doc IDs before rerank;
- final top-10 doc IDs after rerank;
- confidence gate top score and decision.

Decision rule:

- If expected source appears in raw top-10 but not final top-5, prioritize rerank.
- If expected source never appears, prioritize query rewrite, module filtering, or vector index/data sync.
- If task is wrong, prioritize query understanding.

### Experiment E3: Room retrieval stage trace for failed room cases

Goal: separate vector recall failure from lease validation failure.

For each room case, log:

- parsed hard filters and semantic queries;
- raw vector top-30 room IDs per query;
- merged candidates before validation;
- lease validation payload;
- lease returned room IDs;
- final ranked top-5.

Decision rule:

- Expected IDs in raw candidates but absent after validation means lease data or filters are the issue.
- Expected IDs absent from raw candidates means recall/query/index is the issue.
- Expected IDs validated but below top-5 means ranking weights/features are the issue.

### Experiment E4: Data consistency check

Goal: verify expected IDs exist in every required layer.

Checks:

- expected KB doc IDs exist in YAML;
- expected KB doc IDs exist in Milvus with active/indexed status;
- expected room IDs exist in lease and are released/appointable;
- expected room IDs exist in Milvus as active vectors;
- district/rent/payment fields match eval hard filters.

Decision rule:

- Do not count a case as a RAG quality failure if its expected item is missing or inactive in either authoritative data or vector index.

## 6. Proposed Order Of Work

1. Add a diagnostic report runner that produces E1-E4 evidence without changing retrieval behavior.
2. Quarantine or correct placeholder/mislabeled room cases.
3. Fix query-understanding routing for KB cases that are clearly policy/payment/life/account questions.
4. Wire v2 KB retrieval to actual planning + hybrid + governed rerank.
5. Re-run live eval and compare metrics by failure class, not only aggregate hit@k.

## 7. Current Conclusion

The 48.6% KB hit@3 should not be interpreted as pure vector retrieval weakness. The dominant visible causes are:

1. KB eval cases are often routed away from KB before retrieval.
2. The live v2 pipeline is not using the v2 hybrid/rerank KB path.
3. The report lacks per-stage trace, so ranking and confidence failures are under-explained.

The 40% room hit@5 should be treated cautiously because:

1. The v2 room cases are explicitly placeholders.
2. At least two case annotations conflict with the query text.
3. The current report cannot tell whether failures happen before or after lease validation.

The next engineering step should be diagnostic instrumentation and data validation, not immediate ranking tweaks.
