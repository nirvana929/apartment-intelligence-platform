# MySQL Schema -- AptGuide 3.0

Database: `aptguide3` | Charset: `utf8mb4` | Collation: `utf8mb4_unicode_ci`

All tables use the `aptguide3_` prefix.

---

## 1. aptguide3_users

User registry. Maps external user IDs to internal records.

| Column | Type | Notes |
|---|---|---|
| user_id | VARCHAR(64) PK | |
| source | VARCHAR(32) | Default `lease` |
| display_name | VARCHAR(128) | |
| created_at | DATETIME | |
| updated_at | DATETIME | Auto-updated |

---

## 2. aptguide3_sessions

Conversation sessions. Holds rolling summary and structured context.

| Column | Type | Notes |
|---|---|---|
| session_id | VARCHAR(64) PK | |
| user_id | VARCHAR(64) | Indexed |
| status | VARCHAR(32) | Indexed; default `active` |
| active_task | VARCHAR(64) | Nullable |
| rolling_summary | TEXT | **[SENSITIVE]** -- summarizes conversation |
| context | JSON | **[SENSITIVE]** -- structured session state |
| created_at | DATETIME | |
| updated_at | DATETIME | Auto-updated |

---

## 3. aptguide3_messages

Full message log per session.

| Column | Type | Notes |
|---|---|---|
| message_id | BIGINT PK AUTO_INCREMENT | |
| session_id | VARCHAR(64) | Indexed |
| user_id | VARCHAR(64) | Indexed |
| request_id | VARCHAR(80) | Indexed |
| role | VARCHAR(32) | `user`, `assistant`, `system` |
| content | TEXT | **[SENSITIVE]** -- raw message text |
| metadata | JSON | **[SENSITIVE]** |
| created_at | DATETIME | |

---

## 4. aptguide3_pending_actions

Actions awaiting user confirmation (e.g., appointment creation).

| Column | Type | Notes |
|---|---|---|
| pending_action_id | VARCHAR(64) PK | |
| session_id | VARCHAR(64) | Indexed |
| user_id | VARCHAR(64) | Indexed |
| action_type | VARCHAR(80) | |
| status | VARCHAR(32) | Indexed; default `pending` |
| payload | JSON | **[SENSITIVE]** -- action parameters |
| expires_at | DATETIME | |
| created_at | DATETIME | |
| updated_at | DATETIME | Auto-updated |

---

## 5. aptguide3_memories

Persisted user memories extracted from conversations.

| Column | Type | Notes |
|---|---|---|
| memory_id | VARCHAR(64) PK | |
| user_id | VARCHAR(64) | Indexed |
| kind | VARCHAR(64) | Memory category |
| key_name | VARCHAR(128) | |
| value_json | JSON | **[SENSITIVE]** |
| source_session_id | VARCHAR(64) | Origin session |
| status | VARCHAR(32) | Indexed; default `active` |
| created_at | DATETIME | |
| updated_at | DATETIME | Auto-updated |

---

## 6. aptguide3_memory_candidates

Proposed memories pending review before persistence.

| Column | Type | Notes |
|---|---|---|
| candidate_id | VARCHAR(64) PK | |
| user_id | VARCHAR(64) | Indexed |
| session_id | VARCHAR(64) | Indexed |
| kind | VARCHAR(64) | |
| payload | JSON | **[SENSITIVE]** |
| status | VARCHAR(32) | Indexed; default `pending` |
| created_at | DATETIME | |
| updated_at | DATETIME | Auto-updated |

---

## 7. aptguide3_handoff_tickets

Escalation tickets when the agent cannot resolve a request.

| Column | Type | Notes |
|---|---|---|
| ticket_id | VARCHAR(64) PK | |
| session_id | VARCHAR(64) | Indexed |
| user_id | VARCHAR(64) | Indexed |
| status | VARCHAR(32) | Indexed; default `open` |
| trigger_type | VARCHAR(64) | Why handoff was triggered |
| summary | JSON | **[SENSITIVE]** -- conversation summary |
| created_at | DATETIME | |
| updated_at | DATETIME | Auto-updated |

---

## 8. aptguide3_operator_messages

Messages within a handoff ticket (operator and user sides).

| Column | Type | Notes |
|---|---|---|
| message_id | BIGINT PK AUTO_INCREMENT | |
| ticket_id | VARCHAR(64) | Indexed |
| sender | VARCHAR(32) | `operator` or `user` |
| content | TEXT | **[SENSITIVE]** |
| metadata | JSON | **[SENSITIVE]** |
| created_at | DATETIME | |

---

## 9. aptguide3_trace_events

Request-level trace events for debugging and observability.

| Column | Type | Notes |
|---|---|---|
| event_id | BIGINT PK AUTO_INCREMENT | |
| trace_id | VARCHAR(80) | Indexed |
| request_id | VARCHAR(80) | Indexed |
| session_id | VARCHAR(64) | Indexed |
| event_name | VARCHAR(128) | |
| payload | JSON | **[SENSITIVE]** -- may contain request fragments |
| created_at | DATETIME | |

---

## 10. aptguide3_procedure_runs

Logs of every procedure execution (room search, KB QA, appointment, etc.).

| Column | Type | Notes |
|---|---|---|
| run_id | VARCHAR(80) PK | |
| request_id | VARCHAR(80) | Indexed |
| session_id | VARCHAR(64) | Indexed |
| user_id | VARCHAR(64) | |
| procedure_name | VARCHAR(80) | |
| route | VARCHAR(64) | |
| task | VARCHAR(64) | |
| status | VARCHAR(32) | Indexed |
| metadata | JSON | **[SENSITIVE]** |
| started_at | DATETIME | |
| completed_at | DATETIME | Nullable |

---

## 11. aptguide3_audit_log

Security and compliance audit trail.

| Column | Type | Notes |
|---|---|---|
| audit_id | BIGINT PK AUTO_INCREMENT | |
| user_id | VARCHAR(64) | Indexed |
| session_id | VARCHAR(64) | |
| event_type | VARCHAR(128) | Indexed |
| payload | JSON | **[SENSITIVE]** |
| created_at | DATETIME | |
