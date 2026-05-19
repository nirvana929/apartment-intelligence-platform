# Clarification Schema

Clarifications preserve the alignment loop between planning agents and execution agents.

## Permanent Clarification Files

Each clarification creates two files:

```text
docs/plans/clarifications/YYYY-MM-DD-HHMMSS-task-question.md
.agent-state/clarifications/YYYY-MM-DD-HHMMSS-task-question.json
```

Open clarification pointers live in:

```text
.agent-state/clarifications/open.json
```

## Markdown Required Sections

- Metadata.
- Original Plan Reference.
- Observed Mismatch.
- Evidence.
- Question.
- Options Considered.
- Execution Agent Recommendation.
- Planning Agent Response.
- Updated Plan Impact.
- Resolution.

## JSON Shape

```json
{
  "status": "open | answered | resolved | blocked",
  "task": "Short task title",
  "question": "Precise question",
  "blocking_level": "blocking | non-blocking",
  "clarification_doc": "docs/plans/clarifications/YYYY-MM-DD-HHMMSS-task-question.md",
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp",
  "raised_by": "execution-agent",
  "assigned_to": "planning-agent"
}
```

## Status Rules

- `open`: execution agent raised the issue and needs an answer.
- `answered`: planning agent responded and updated plan/handoff if needed.
- `resolved`: execution agent continued and confirmed the issue no longer blocks work.
- `blocked`: the issue requires user decision or external input.

Do not delete clarification records. Remove resolved items from `open.json` only after the Markdown and JSON files are updated to `resolved`.
