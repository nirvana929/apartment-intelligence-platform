# Execution Log

## 2026-05-15 01:15 - clean-backend-foundation

- Commit: 1340c5b
- 23 tests passed, ruff clean
- Built: domain contracts, understanding layer, safety boundary, procedures (clarify/room_search/kb_qa), FastAPI API

## 2026-05-15 01:38 - full-stack-system-complete

- Commit: dc0cf87
- Checkpoint: docs/plans/checkpoints/2026-05-15-013838-full-stack-system-complete.md
- 36 tests passed, 2 skipped, ruff clean
- 4 parallel workstreams: procedures, persistence, frontend, observability
- 56 files changed, 1901 insertions

## 2026-05-15 - independent-backend-backbone-plan

- Plan: docs/plans/2026-05-15-aptguide3-independent-backend-backbone-plan.md
- Status: planned
- Scope: AptGuide 3.0 Agent-state schema, repository contracts, MySQL/Redis persistence, auth boundary, readiness, durable traces, procedure runs
- Boundary: independent validation first; final integration through `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`
- Verification: not run; documentation-only planning update

## 2026-05-15 - independent-backend-backbone-execution-start

- Status: executing
- Tasks: 11 tasks from backbone plan
- Verification: pending

## 2026-05-15 - independent-backend-backbone-complete

- Status: complete
- Checkpoint: docs/plans/checkpoints/2026-05-15-independent-backend-backbone.md
- 55 tests passed, 2 skipped, ruff clean
- Parallel execution: 5 waves, 11 tasks
- New files: 18 created, 8 modified
- Modules: database schema/models, repository contracts, MySQL repos, Redis store, auth boundary, readiness endpoint, trace sink, chat persistence

## 2026-05-15T11:30:34+08:00 - independent-backend-backbone

- Checkpoint: [docs/plans/checkpoints/2026-05-15-113034-independent-backend-backbone.md](docs/plans/checkpoints/2026-05-15-113034-independent-backend-backbone.md)
- Status: draft
- Verification: not_run

## 2026-05-15T12:03:10+08:00 - live-integration-readiness

- Checkpoint: [docs/plans/checkpoints/2026-05-15-120310-live-integration-readiness.md](docs/plans/checkpoints/2026-05-15-120310-live-integration-readiness.md)
- Status: complete
- 68 tests passed, 23 skipped, ruff clean
- Parallel execution: 4 waves, 9 tasks
- New files: 15 created, 12 modified
- Modules: persistence mode selection, docker-compose, schema application, Redis/MySQL/auth/AI/chat integration tests, lease gateway contract, operator docs, procedure integration plan

## 2026-05-15 - procedure-integration

- Status: complete
- 129 tests passed, 27 skipped, ruff clean
- Parallel execution: 4 waves, 11 tasks
- Wave 1 (parallel): Task 1 sync state, Task 3 in-memory repos, Task 4 LeaseClient extensions
- Wave 2 (serial): Task 2 RepoBundle wiring
- Wave 3 (parallel): Tasks 5-10 procedures + readiness + trace/audit
- Wave 4 (serial): Task 11 chain test plan
- New modules: RepoBundle dataclass, InMemoryPendingActionRepo, AppointmentProcedure (pending-action confirmation), LeaseProcedure (lease list + audit), MemoryProcedure (save/list preferences), HandoffProcedure (ticket + audit), LeaseClient.create_appointment/list_appointments/list_leases, RepositoryTraceSink wired into tracer, async /ready with live probes
- Files changed: deps.py, appointment.py, lease.py, memory.py, handoff.py, lease_client.py, memory_repo.py, handoff_repo.py, readiness.py, app.py, repository_sink.py + 12 new test files

## 2026-05-15T13:32:32+08:00 - procedure-integration

- Checkpoint: [docs/plans/checkpoints/2026-05-15-133232-procedure-integration.md](docs/plans/checkpoints/2026-05-15-133232-procedure-integration.md)
- Status: complete
- 129 tests passed, 28 skipped, ruff clean
- Parallel execution: 4 waves, 11 tasks

## 2026-05-15T14:50:00+08:00 - Milestone 4: LLM-first RAG Upgrade

- Checkpoint: [docs/plans/checkpoints/2026-05-15-145000-milestone-4-llm-first-rag-upgrade.md](docs/plans/checkpoints/2026-05-15-145000-milestone-4-llm-first-rag-upgrade.md)
- Status: complete
- 207 tests passed, 33 skipped, ruff clean
- Parallel execution: 5 waves, 10 tasks
- Wave 1 (parallel): Tasks 1-3 (schemas, vector_client, preference_scorer)
- Wave 2 (parallel): Tasks 4, 5, 7 (room retrieval, KB retrieval, sync scripts)
- Wave 3 (serial): Task 6 (dependency wiring)
- Wave 4 (parallel): Tasks 8, 9 (eval metrics, anti-regression guardrails)
- Wave 5 (serial): Task 10 (live RAG smoke + docs)
- New modules: rag/schemas, rag/planning, rag/room_retrieval, rag/room_ranking, rag/kb_retrieval, rag/kb_rerank, rag/confidence, rag/preference_scorer, rag/chunking, rag/eval_metrics, scripts/sync_room_vectors, scripts/sync_kb_vectors, tests/integration/test_rag_live
- Files changed: 16 new, 6 modified, 10 new test files

## 2026-05-15T15:35:11+08:00 - Milestone 5: Frontend E2E + Live RAG Evaluation

- Checkpoint: [docs/plans/checkpoints/2026-05-15-153511-milestone-5-frontend-e2e-live-rag-evaluation.md](docs/plans/checkpoints/2026-05-15-153511-milestone-5-frontend-e2e-live-rag-evaluation.md)
- Status: draft
- Verification: not_run

## 2026-05-15T18:17:00+08:00 - Milestone 6: LangSmith tracing and understanding diagnostics

- Checkpoint: [docs/plans/checkpoints/2026-05-15-181700-milestone-6-langsmith-tracing-and-understanding-diagnostics.md](docs/plans/checkpoints/2026-05-15-181700-milestone-6-langsmith-tracing-and-understanding-diagnostics.md)
- Status: draft
- Verification: not_run

## 2026-05-15T19:05:10+08:00 - Milestone 7: Data inventory + baseline analysis

- Checkpoint: [docs/plans/checkpoints/2026-05-15-190510-milestone-7-data-inventory-baseline-analysis.md](docs/plans/checkpoints/2026-05-15-190510-milestone-7-data-inventory-baseline-analysis.md)
- Status: draft
- Verification: not_run

## 2026-05-15T21:57:50+08:00 - WeChat data pipeline + live RAG re-evaluation

- Checkpoint: [docs/plans/checkpoints/2026-05-15-215750-wechat-data-pipeline-live-rag-re-evaluation.md](docs/plans/checkpoints/2026-05-15-215750-wechat-data-pipeline-live-rag-re-evaluation.md)
- Status: draft
- Verification: not_run

## 2026-05-15T22:21:08+08:00 - Full system upgrade: prompt tuning + entity resolution + multi-route recall + expanded eval

- Checkpoint: [docs/plans/checkpoints/2026-05-15-222108-full-system-upgrade-prompt-tuning-entity-resolution-multi-route-recall-expanded-.md](docs/plans/checkpoints/2026-05-15-222108-full-system-upgrade-prompt-tuning-entity-resolution-multi-route-recall-expanded-.md)
- Status: draft
- Verification: not_run

## 2026-05-15 - Plan 1: Data Evidence Contract

- Plan: docs/plans/2026-05-15-aptguide3-data-evidence-contract-plan.md
- Status: complete
- Verification: 32 tests passed (backend/tests/unit/rag/test_evidence_contract.py)
- Created: docs/system/data-inventory/room-id-alignment.md (field inventory for room search + KB QA pipelines)
- Created: docs/system/evidence-contract.md (5 evidence levels, risk rules, acceptance criteria)
- Created: backend/tests/unit/rag/test_evidence_contract.py (32 contract shape tests)
- Key finding: wechat-to-lease ID mapping path does not exist; synthetic hash ID is not reversible
- Updated: docs/plans/current-plan.md (Plan 1 marked done), docs/plans/known-issues.md (active issue made specific)

## 2026-05-15 - Room Identity Map Prerequisite

- Plan: docs/plans/2026-05-15-aptguide3-room-identity-map-prerequisite-plan.md
- Status: complete
- Verification: 113 rag tests passed (backend/tests/unit/rag/), 11 new tests (6 room_identity + 5 room_identity_repo)
- Created: backend/src/aptguide3/rag/room_identity.py (RoomIdentity model, is_lease_verifiable, evidence_level_for_identity)
- Created: backend/src/aptguide3/persistence/room_identity_repo.py (RoomIdentityRepository Protocol, InMemoryRoomIdentityRepository)
- Created: backend/scripts/inspect_room_identity_sources.py (Milvus field inventory, non-mutating)
- Created: backend/tests/unit/rag/test_room_identity.py (6 tests)
- Created: backend/tests/unit/persistence/test_room_identity_repo.py (5 tests)
- Modified: backend/src/aptguide3/integrations/vector_client.py (_map_wechat_room_results preserves source identity fields)
- Modified: backend/src/aptguide3/rag/diagnostics.py (added identity mapping diagnostic fields)
- Modified: backend/evals/runners/run_rag_eval.py (added identity_mapping failure owner)
- Updated: Plan 2 depends on RoomIdentityRepository; lease validation only for mapped_verified
- Updated: Plan 3 medium/high-risk room language treats vector_only/mapped_candidate as insufficient
- Updated: Plan 5 comprehensive eval blocked until identity mapping exposes verified business IDs

## 2026-05-16 - Plan 5: Comprehensive RAG Evaluation

- Plan: docs/plans/2026-05-15-aptguide3-comprehensive-rag-evaluation-plan.md
- Status: complete
- Verification: 347 tests passed (1 pre-existing failure in test_deps.py), 44 new eval runner tests
- Modified: backend/evals/runners/run_rag_eval.py
  - Task 1: Added `validate_eval_case` + `validate_dataset` schema validation (rejects missing id/task/query, high-risk KB without expected_doc_ids, room_search without lease expectation)
  - Task 2: Strengthened `_check_criteria` `must_validate_with_lease` to check card metadata (lease_validation_status=passed, evidence_level in VALID_LEASE_EVIDENCE_LEVELS, lease_room_id exists)
  - Task 3: Added KB criteria: `must_have_citations_for_high_risk`, `must_have_grounded_answer`, `must_have_source_cards`; added `citations_match_source_cards` helper; strengthened `must_not_make_unverified_commitment`
  - Task 4: Added `trace_output_visibility_rate` metric tracking and reporting; smoke mode returns N/A
  - Task 5: Rewrote `_classify_failure_owner` as public `classify_failure_owner` with canonical owners: understanding, entity_resolution, data_alignment, vector_recall, identity_mapping, lease_validation, ranking, confidence_gate, grounded_answer, trace_visibility, dataset_gap, runtime_error
  - Dataset validation runs at startup in `main()`
  - Report table includes `trace_output_visibility_rate` row
- Created: backend/tests/unit/evals/__init__.py
- Created: backend/tests/unit/evals/test_rag_eval_runner.py (44 tests covering all 7 plan tasks)

## 2026-05-16T00:14:45+08:00 - RAG evidence trace eval roadmap complete

- Checkpoint: [docs/plans/checkpoints/2026-05-16-001445-rag-evidence-trace-eval-roadmap-complete.md](docs/plans/checkpoints/2026-05-16-001445-rag-evidence-trace-eval-roadmap-complete.md)
- Status: draft
- Verification: not_run

## 2026-05-16T00:21:48+08:00 - roadmap-complete-status-review

- Checkpoint: [docs/plans/checkpoints/2026-05-16-002148-roadmap-complete-status-review.md](docs/plans/checkpoints/2026-05-16-002148-roadmap-complete-status-review.md)
- Status: draft
- Verification: not_run

## 2026-05-16 - Live RAG Gate (Evaluation-First Execution Plan)

- Checkpoint: [docs/plans/checkpoints/2026-05-16-evaluation-first-live-rag-gate.md](docs/plans/checkpoints/2026-05-16-evaluation-first-live-rag-gate.md)
- Status: PARTIAL PASS
- Verification: 44 eval runner tests passed, 147 focused RAG/procedure tests passed, live RAG eval 4/9 passed
- Live results: KB QA 4/4 PASS (Hit@3=100%), Room search 5/5 FAIL (dataset_gap), 0 errors
- Latency: avg=9166ms, p95=18220ms
- Findings: P0 dataset_gap, P1 identity_mapping, P2 trace_visibility
- Next: expand dataset, populate identity mappings, re-run eval

## 2026-05-16 - Room Eval Dataset + Identity Map Implementation

- Checkpoint: [docs/plans/checkpoints/2026-05-16-room-eval-dataset-identity-map.md](docs/plans/checkpoints/2026-05-16-room-eval-dataset-identity-map.md)
- Status: PARTIAL PASS (P0 resolved, new P1.5 discovered)
- Verification: 189 tests passed, live RAG eval 4/9 passed
- New modules: aptguide3_room_identity_map table, RoomIdentityMapRecord model, MySqlRoomIdentityRepository, import/export scripts
- Live results: KB QA 4/4 PASS, Room search 5/5 FAIL (failure_owner upgraded: dataset_gap → vector_recall)
- Key finding: Room search results are non-deterministic (LLM generates different queries each run)
- Next: decide evaluation strategy for non-deterministic results, populate identity mappings
