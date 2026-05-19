# Checkpoint Schema

Use these JSON shapes for `.agent-state/` files. Add fields when useful, but do not remove existing fields unless the user requests migration.

## `.agent-state/project.json`

```json
{
  "project_path": "/absolute/path",
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp",
  "docs_model": "docs-first"
}
```

## `.agent-state/handoff.json`

```json
{
  "status": "ready",
  "role": "execution_agent",
  "task": "Short task title",
  "source_docs": [
    "docs/plans/current-plan.md",
    "docs/plans/handoff.md"
  ],
  "acceptance_criteria": [],
  "verification_commands": [],
  "constraints": [],
  "updated_at": "ISO-8601 timestamp"
}
```

## `.agent-state/last-checkpoint.json`

```json
{
  "status": "completed | partial | blocked | empty",
  "current_goal": "Short goal",
  "completed": [],
  "files_changed": [],
  "verification": [],
  "test_status": "passed | failed | not_run | partial",
  "known_issues": [],
  "next_steps": [],
  "updated_at": "ISO-8601 timestamp"
}
```

`last-checkpoint.json` is the current fast-resume pointer and may be overwritten.
It must include `checkpoint_doc` when a permanent checkpoint exists.

## Permanent Checkpoint Files

Each checkpoint creates two permanent files:

```text
docs/plans/checkpoints/YYYY-MM-DD-HHMMSS-task-name.md
.agent-state/checkpoints/YYYY-MM-DD-HHMMSS-task-name.json
```

The Markdown file is the human/agent-readable development history. It should record:

- Goal and context.
- Completed work.
- Files changed.
- Errors, failed commands, exceptions, broken assumptions, and dead ends.
- Root cause and fix decisions when known.
- Verification commands and evidence.
- Known issues and next steps.
- Outcome notes for later `docs/outcomes/` summaries.

The JSON file is the machine-readable pointer for automation. It should record:

```json
{
  "status": "draft | completed | partial | blocked",
  "task": "Short task title",
  "checkpoint_doc": "docs/plans/checkpoints/YYYY-MM-DD-HHMMSS-task-name.md",
  "test_status": "passed | failed | not_run | partial",
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp",
  "errors_recorded": [],
  "verification": [],
  "next_steps": []
}
```
