# Next Steps

## Immediate

1. Execute `docs/plans/2026-05-15-aptguide3-independent-backend-backbone-plan.md`.
2. Add MySQL schema and SQLAlchemy models for Agent state.
3. Add repository contracts before expanding business procedures.
4. Wire Redis hot state and MySQL durable state.
5. Persist messages, pending actions, procedure runs, and trace events.
6. Add auth/readiness boundary for final `lease -> AptGuide 3.0` integration.

## Later

1. Integrate procedures against stable repositories and real services.
2. Keep independent frontend as validation UI.
3. Integrate through `rentHouseH5 -> lease /app/ai/chat -> AptGuide 3.0 /api/chat`.
4. Add production operator flow and deployment hardening.
