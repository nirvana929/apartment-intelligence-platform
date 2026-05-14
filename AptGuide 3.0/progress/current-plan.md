# Current Plan

## Active Objective

AptGuide 3.0 Milestone 1: Independent Backend Backbone.

## Current State

- Milestone 0 runnable scaffold: COMPLETE.
- Backend: 36 tests passed, 2 skipped; ruff clean.
- All 7 procedures exist.
- Persistence exists only as in-memory defaults.
- Observability exists only as trace events with console sink.
- Frontend exists as independent validation UI, not final main-system entry.
- AptGuide 3.0 final integration path is `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`.

## Active Plan

`docs/plans/2026-05-15-aptguide3-independent-backend-backbone-plan.md`

## Next

- Add MySQL schema and SQLAlchemy models for Agent state.
- Add repository contracts.
- Wire Redis hot state and pending-action TTL.
- Persist messages, procedure runs, trace events, memories, handoff tickets, and audit events.
- Add auth and readiness boundaries for final lease integration.
