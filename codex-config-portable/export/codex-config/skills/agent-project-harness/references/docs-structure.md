# Docs Structure

Use `docs/` as the durable memory for humans and agents.

## Categories

| Type | Folder | Purpose |
| --- | --- | --- |
| System | `docs/system/` | Architecture, modules, APIs, data model, workflows, design decisions |
| Plans | `docs/plans/` | Current plans, handoffs, execution logs, clarifications, known issues, next steps |
| Tests | `docs/tests/` | Verification logs, evaluation reports, failure analysis, regression notes |
| Outcomes | `docs/outcomes/` | Achievements, lessons learned, pitfalls, portfolio/interview material |

## Index Rules

- Root `docs/README.md` is a reading-order entry point.
- Category `README.md` files list concrete docs in tables.
- Concrete docs hold detailed content.
- Prefer links over moving legacy files.
- Do not put detailed implementation content into index files.

## Status Labels

- `active`: current source of truth.
- `draft`: incomplete but intended as formal doc.
- `existing`: linked source retained in place.
- `generated`: tool-generated report.
- `legacy`: historical reference.

## New File Placement

- Architecture or API change: `docs/system/`.
- Plan or handoff: `docs/plans/`.
- Permanent task checkpoint: `docs/plans/checkpoints/YYYY-MM-DD-HHMMSS-task-name.md`.
- Plan/execution clarification: `docs/plans/clarifications/YYYY-MM-DD-HHMMSS-task-question.md`.
- Test result or verification record: `docs/tests/`.
- Achievement, metric, or durable lesson: `docs/outcomes/`.
