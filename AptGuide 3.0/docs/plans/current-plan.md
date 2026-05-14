# Current Plan

## Active Objective

AptGuide 3.0 Milestone 1: Independent Backend Backbone.

## Current State

- Milestone 0 runnable scaffold: COMPLETE.
- Backend: 36 tests passed, 2 skipped; ruff clean.
- Procedures, integrations, in-memory persistence, observability, and validation frontend exist.
- Production-grade Agent-state persistence does not exist yet.
- AptGuide 3.0 is an AptGuide main-system upgrade: independently verifiable first, then integrated through `lease /app/ai/chat`.

## Active Plan

`docs/plans/2026-05-15-aptguide3-independent-backend-backbone-plan.md`

## Next Work

- Define MySQL schema and SQLAlchemy models for Agent state.
- Define repository contracts for sessions, messages, pending actions, memories, handoff, trace events, procedure runs, and audit events.
- Wire Redis hot state and pending-action TTL.
- Persist ChatService messages, procedure runs, and trace events.
- Add auth boundary for final `lease -> AptGuide 3.0` internal-header integration.
- Add readiness checks.

## Guardrails

- No keyword fallback in understanding runtime
- Deterministic safety hard boundaries only
- Final production chain is `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`
- lease remains source of truth for users, rooms, appointments, leases, contracts, and sensitive customer data
