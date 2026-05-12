# Distributed Documentation Model

Use this model when the repository contains multiple child projects and each project should own its own documentation.

## Storage

Child project docs:

```text
<project>/docs/
├── README.md
├── system/
├── plans/
├── tests/
└── outcomes/
```

Root docs:

```text
docs/
└── README.md
```

Root docs may also contain platform-level docs when the content spans multiple projects.

## Rules

- Write child-project docs to the child project.
- Write platform docs to root `docs/`.
- Keep generated reports in their source output directory when that location is part of the tool workflow.
- Link generated reports from `tests/README.md`.
- Keep old docs in place unless the user asks for migration.
- If old docs are eventually migrated, preserve an archive index or redirect note.

## Current Repository Scope Pattern

For Apartment Intelligence Platform:

- `AptGuide/docs/`: AptGuide formal indexes.
- `AptGuide 2.0/docs/`: AptGuide 2.0 formal indexes.
- `AptInsight/docs/`: AptInsight formal indexes.
- `docs/`: root navigation.
- `lease`, `rentHouseAdmin`, and `rentHouseH5` should not be touched unless explicitly requested.
