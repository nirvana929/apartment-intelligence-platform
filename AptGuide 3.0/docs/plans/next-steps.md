# Next Steps

## Immediate

1. Execute `docs/plans/2026-05-15-aptguide3-independent-backend-backbone-plan.md`.
2. Add database schema and SQLAlchemy models for AptGuide 3.0 Agent state.
3. Define repository contracts before expanding business procedures.
4. Wire Redis hot state and MySQL durable state.
5. Persist messages, pending actions, procedure runs, and trace events.
6. Add auth and readiness boundaries for final `lease -> AptGuide 3.0` integration.

## After Backbone

1. Integrate room_search, kb_qa, appointment, lease, memory, and handoff against stable repositories and real services.
2. Keep independent frontend as validation UI.
3. Integrate through the AptGuide main-system path: `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`.
4. Add production operator flow and deployment hardening.
