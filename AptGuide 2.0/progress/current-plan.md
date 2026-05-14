# Current Plan

## Active Objective

RAG retrieval quality improvement: increase KB hit@3 from 48.6% to 90%+ and Room hit@5 from 40% to 85%+ on the live RAG v2 evaluation.

## Active Plan

待创建：RAG retrieval quality tuning plan

## Completed Plans (this session)

1. `docs/plans/2026-05-12-enterprise-aptguide-harness-agent-execution-plan.md` — completed
2. `docs/plans/2026-05-13-enterprise-aptguide-harness-agent-handoff-plan.md` — completed
3. `docs/plans/2026-05-13-enterprise-aptguide-tool-registry-adapter-governance-agent-plan.md` — completed
4. `docs/plans/2026-05-14-enterprise-rag-v2-hybrid-retrieval-governed-rerank-agent-plan.md` — completed
5. `docs/plans/2026-05-14-enterprise-harness-memory-appointment-handoff-correction-agent-plan.md` — completed
6. `docs/plans/2026-05-14-aptguide2-system-integration-production-hardening-agent-plan.md` — completed
7. `docs/plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md` — completed

## Current State

- `/chat` enters `AptGuideHarness` by default — no legacy RAG branch
- `api/app.py` has no imports from `aptguide2.rag.pipeline` — legacy RAG disconnected
- `api/deps.py` registers `RagV2Procedure` instead of `RagBaselineProcedure`
- `rag/schemas.py` owns `PipelineResult` — `pipeline_v2.py` imports from schemas, not legacy pipeline
- `aptguide2.harness.modules.rag.v2.RagV2Procedure` — harness procedure adapter for RAG v2
- `aptguide2.harness.modules.lease.LeaseWorkflowProcedure` — lease list through governed tools
- Appointment cancel uses two-turn confirmation with `confirmation_id`
- `appointment.cancel` executor registered in tool runtime
- `ChatResponse` has first-class `cards` field for all card types
- `ResponseComposer` includes standard metadata (card_count, source_count, action_count, has_pending_action)
- `readiness.build_readiness_report()` includes pipeline version check
- 323 tests all passing (308 unit + 15 e2e)
- ruff clean
- Current blocker: live RAG v2 retrieval quality remains below gates (KB hit@3=48.6%, Room hit@5=40%)

## Current Guardrails

- Old RAG MVP code may remain in the repository, but no API, harness procedure, or system e2e path should call it.
- Harness is the product runtime.
- RAG v2 is an internal harness module, not a separate public `/chat` mode.
- Do not mark feature `passes=true` without test evidence.
- `appointment.create` and `appointment.cancel` require two-turn confirmation with `confirmation_id`.
- Retrieval-quality changes must preserve high-risk fallback at 100% and unvalidated room count at 0.
