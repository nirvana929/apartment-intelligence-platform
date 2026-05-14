# System Feature Completion And Mainline Integration Analysis Report

**Date:** 2026-05-14

## Executive Decision

The old RAG MVP pipeline is now legacy code. It should remain in the repository for reference and backward comparison, but no public API, harness procedure, default configuration, or system-level test should depend on it.

The next project objective is no longer RAG retrieval-quality tuning. The next objective is system feature completion and mainline integration:

- `/chat` uses the system harness as the only product runtime.
- The harness calls the new RAG v2 path for rental knowledge and room search.
- Appointment, lease, memory, handoff, response actions, pending actions, and trace behavior are completed as one coherent system.
- Legacy `aptguide2.rag.pipeline.run_pipeline()` is disconnected from all user-facing interfaces.

## Current Findings

Current code still contains mixed runtime paths:

| Area | Current State | Required Change |
| --- | --- | --- |
| API default | `Settings.pipeline_version` defaults to `v1` | Default must become harness mainline |
| `/chat` API | Branches into `harness_v1`, `rag_v2`, or legacy `v1` | Remove user-facing legacy `v1` and standalone `rag_v2` API branches |
| Harness RAG module | `RagBaselineProcedure` imports `aptguide2.rag.pipeline.run_pipeline` | Replace with a harness RAG v2 procedure |
| RAG result contract | `pipeline_v2.py` imports `PipelineResult` from legacy `pipeline.py` | Move shared result contract to neutral schema module |
| RAG v2 | `pipeline_v2.py` exists and is live-eval runnable | Treat as internal retrieval module, not a separate public API mode |
| API cards | `ChatResponse` has room-specific `rooms` but no generic `cards` field | Add first-class `cards` for appointment, lease, handoff, and other non-room cards |
| Tests | Some e2e tests call old `run_pipeline()` directly | Move system acceptance to harness `/chat` tests |
| Docs/progress | Current objective says retrieval quality tuning | Change objective to system feature completion |

## Mainline Target

The intended runtime becomes:

```text
POST /chat
  -> AptGuideHarness
  -> HybridRouter
  -> ProcedureRuntime
     -> capability.profile
     -> rag.room_search using RAG v2
     -> rag.kb_qa using RAG v2
     -> appointment.workflow using ToolRuntime + LeaseAdapter
     -> handoff.user_initiated / handoff.tool_failure
     -> fallback.safety / fallback.unknown
  -> ResponseComposer
  -> ChatResponse
```

Legacy runtime is retained but disconnected:

```text
aptguide2.rag.pipeline.run_pipeline
  retained for historical reference and legacy unit tests only
  not imported by api.app
  not imported by api.deps
  not registered in harness procedures
  not used by e2e acceptance tests
```

## Functional Completion Scope

### Included

1. Mainline runtime switch to harness.
2. Legacy RAG disconnection from public interfaces.
3. Harness RAG v2 procedure.
4. Appointment create/list/cancel flow completion.
5. Lease list integration.
6. Memory and pending-action lifecycle hardening.
7. Tool failure and handoff completion.
8. API response shape consistency.
9. System smoke and e2e tests against the harness mainline.
10. Documentation and progress updates.

### Deferred

1. KB hit@3 improvement from 48.6% to 90%+.
2. Room hit@5 improvement from 40% to 85%+.
3. BM25/cross-encoder/corpus-level retrieval optimization.
4. Redis or durable context store.
5. LLM rolling summary and long-term profile extraction.

## Acceptance Gates

The next phase is complete only when:

- `/chat` no longer calls legacy `run_pipeline()`.
- Harness RAG procedure no longer imports `aptguide2.rag.pipeline`.
- RAG v2 no longer imports result contracts from legacy `aptguide2.rag.pipeline`.
- Default system runtime is the harness mainline.
- Appointment create requires confirmation and creates through lease.
- Appointment list and lease list are connected through governed tools.
- Cancel appointment uses a two-turn confirmation flow and resolves `appointment_id` from frontend action payload, pending action payload, or message text.
- `ChatResponse.cards` is the canonical API field for non-room cards; `rooms` remains a compatibility projection.
- Responses consistently expose `phase`, `actions`, `pending_action`, and `metadata`.
- System e2e tests cover room, KB, appointment create confirm, appointment list, lease list, handoff, fallback, and tool failure.
- Existing regression suite passes.

## Recommended Plan

Use this plan:

`docs/plans/2026-05-14-aptguide2-system-feature-completion-mainline-integration-plan.md`
