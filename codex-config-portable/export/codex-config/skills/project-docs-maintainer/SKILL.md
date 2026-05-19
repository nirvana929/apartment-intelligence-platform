---
name: project-docs-maintainer
description: Maintain distributed project documentation for repositories where each child project owns its own docs. Use when creating, updating, classifying, indexing, auditing, or reorganizing Markdown documentation; building docs/README.md indexes; sorting docs into system, plans, tests, and outcomes; or keeping Codex and Claude documentation workflows consistent without centralizing child project docs.
---

# Project Docs Maintainer

## Required Trigger Notice

When this skill triggers, first tell the user:

```text
我正在使用 project-docs-maintainer skill 来维护项目文档索引和四类文档结构。
```

Keep the notice short. Then continue the task.

## Core Rule

Maintain distributed documentation:

- Keep each child project's formal docs inside that project's own `docs/`.
- Use root `docs/` only for platform-level indexes and cross-project navigation.
- Do not centralize child project docs into root `docs/`.
- Do not move old docs unless the user explicitly asks for physical migration.
- Prefer adding indexes and links before reorganizing files.

## Four Documentation Types

Classify docs into exactly one primary type:

| Type | Folder | Purpose |
| --- | --- | --- |
| System | `docs/system/` | Architecture, modules, APIs, data model, workflows, design decisions |
| Plans | `docs/plans/` | Agent-executable implementation plans, task breakdowns, acceptance criteria |
| Tests | `docs/tests/` | Test strategy, test records, eval reports, failure analysis, regression history |
| Outcomes | `docs/outcomes/` | Interview/resume-oriented achievements, lessons, pitfalls, solutions, metrics |

If a document fits multiple types, choose by primary use. Link it from secondary indexes only when useful.

## Workflow

1. Announce the trigger notice.
2. Identify the project owner.
   - Project-level docs go to `<project>/docs/`.
   - Cross-project docs go to root `docs/`.
3. Classify the doc as `system`, `plans`, `tests`, or `outcomes`.
4. For new docs, create the file in `<project>/docs/<type>/`.
5. For existing docs, prefer linking from indexes instead of moving files.
6. Update the nearest category index: `<project>/docs/<type>/README.md`.
7. Update the project index: `<project>/docs/README.md` when a new major doc or category changes.
8. Update root `docs/README.md` only when project-level entry points change.
9. Check links for obvious path mistakes.
10. Summarize changed files and any docs intentionally left in place.

## Index Rules

Use progressive disclosure:

- Root `docs/README.md`: platform overview and links to child project doc centers.
- Project `docs/README.md`: recommended reading order, four category entries, legacy/source locations.
- Category `README.md`: table of concrete docs, short purpose, status.
- Concrete docs: detailed content only.

Avoid putting detailed architecture or implementation content in index files.

## Status Labels

Use simple labels in index tables:

- `active`: current formal doc.
- `draft`: incomplete but intended as formal doc.
- `existing`: existing source doc linked without migration.
- `generated`: tool-generated report.
- `legacy`: historical doc kept for reference.

## References

Load only what is needed:

- `references/distributed-docs.md`: distributed storage model and path rules.
- `references/classification.md`: four-type classification details.
- `references/indexing.md`: README index patterns and link rules.

## Templates

Use templates from `assets/templates/` when creating new concrete docs:

- `system-doc.md`
- `plan-doc.md`
- `test-doc.md`
- `outcome-doc.md`
