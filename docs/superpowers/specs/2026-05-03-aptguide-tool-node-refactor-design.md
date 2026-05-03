# AptGuide Tool Node Refactor Design

Date: 2026-05-03

## Context

`AptGuide/src/aptguide/agent/nodes/tool.py` currently handles multiple responsibilities in one node:

- Query current user's appointments.
- Query current user's leases.
- Execute confirmed appointment creation.
- Convert backend results into frontend cards.
- Generate tool result replies with the LLM.
- Handle backend, network, and tool errors.

This is acceptable for an early demo, but it will become hard to maintain when more tool operations are added, such as appointment cancellation, rescheduling, lease signing, payment query, maintenance ticket creation, or room detail lookup.

## Problem

The current `tool_node` is becoming a large conditional dispatcher plus business implementation file. That creates several risks:

- Adding a new operation increases `if/elif` branching in one file.
- Query operations and write operations are mixed together.
- Confirmation-based write execution is mixed with direct query execution.
- Tests for one business action need to load unrelated branches.
- Changes to appointment behavior can accidentally affect lease behavior.
- Cancellation cleanup and confirmation memory handling are easy to miss.

## Design Goal

Keep LangGraph's graph shape stable while narrowing the responsibility of `tool_node`.

`tool_node` should become a thin router:

- Read `state["intent"]`.
- Read `state["confirmation"]`.
- Dispatch to a focused handler.
- Return the handler's state update.

Concrete business logic should move into tool handlers grouped by domain.

## Proposed Structure

```text
AptGuide/src/aptguide/agent/nodes/tool.py
AptGuide/src/aptguide/agent/tools/handlers/appointment.py
AptGuide/src/aptguide/agent/tools/handlers/lease.py
AptGuide/src/aptguide/agent/tools/handlers/common.py
```

Responsibilities:

```text
tool.py
  Thin LangGraph node.
  Routes by intent or confirmation["type"].

handlers/appointment.py
  handle_appointment_query
  handle_appointment_create
  future: handle_appointment_cancel
  future: handle_appointment_reschedule

handlers/lease.py
  handle_lease_query
  future: handle_lease_sign
  future: handle_lease_renew

handlers/common.py
  Shared error reply constants.
  Tool reply prompt.
  LLM reply helper.
  Defensive int parsing.
```

## Data Flow

Direct query operations:

```text
intent_node
  -> route_intent returns "tool"
  -> tool_node
  -> handler based on state["intent"]
  -> reply_node
  -> END
```

Example:

```text
intent = "appointment_query"
tool_node -> handle_appointment_query(...)
```

Confirmed write operations:

```text
intent_node
  -> slot_node
  -> confirm_node stores confirmation
  -> user sends "确认"
  -> route_intent sees state["confirmation"]
  -> tool_node
  -> handler based on confirmation["type"]
  -> clear pending confirmation
  -> reply_node
  -> END
```

Example:

```python
confirmation = {
    "type": "appointment_create",
    "params": {
        "room_id": 3001,
        "appointment_time": "2026-05-04 14:00",
        "room_title": "天河公寓 302"
    }
}
```

`tool_node` dispatches to:

```python
handle_appointment_create(...)
```

## Routing Contract

The router should support two routing keys:

```python
intent = state.get("intent", "")
confirmation = state.get("confirmation")
```

Dispatch rule:

```text
If confirmation exists:
  route by confirmation["type"]

Else:
  route by intent
```

This matters because after the user replies "确认", the current message may be classified as `other`. The operation type must come from `confirmation["type"]`, not the current intent.

## Initial Handler Map

```text
intent: appointment_query
  -> handle_appointment_query

intent: lease_query
  -> handle_lease_query

confirmation type: appointment_create
  -> handle_appointment_create
```

Future extensions:

```text
confirmation type: appointment_cancel
  -> handle_appointment_cancel

confirmation type: appointment_reschedule
  -> handle_appointment_reschedule

confirmation type: lease_sign
  -> handle_lease_sign

confirmation type: lease_renew
  -> handle_lease_renew
```

## Error Handling

Each handler should catch backend and network failures close to the call it makes:

```python
httpx.HTTPStatusError
httpx.TimeoutException
httpx.NetworkError
LeaseToolError
```

Shared user-facing fallback:

```text
抱歉，系统暂时无法完成您的请求，请稍后再试。如有紧急需求，请联系客服。
```

Write-operation failures should clear pending confirmation after the backend call fails, because the stored operation may no longer be safe to retry blindly.

Cancellation should also clear both:

```text
state["confirmation"]
memory.pending_confirmation
```

The current implementation clears `state["confirmation"]` through `reply_node`, but does not clear `SessionMemory.pending_confirmation` on cancellation. That should be fixed when the tool/confirmation flow is refactored.

## Testing Plan

Focused unit tests should cover:

- `tool_node` routes `appointment_query` to the appointment query handler.
- `tool_node` routes `lease_query` to the lease query handler.
- `tool_node` routes `confirmation["type"] == "appointment_create"` to the appointment create handler even if current intent is `other`.
- Unknown intent returns a clear "no executable operation" response.
- Unknown confirmation type returns a clear unsupported operation response.
- Appointment query formats appointment cards.
- Lease query formats lease cards.
- Appointment create clears pending confirmation after success.
- Appointment create clears pending confirmation after backend failure.
- Cancellation clears both state confirmation and memory confirmation.

## Migration Steps

1. Add handler modules without changing graph topology.
2. Move appointment query logic from `tool.py` to `handlers/appointment.py`.
3. Move appointment create logic from `tool.py` to `handlers/appointment.py`.
4. Move lease query logic from `tool.py` to `handlers/lease.py`.
5. Keep `tool_node` as a thin router.
6. Add tests for router dispatch and handler behavior.
7. Fix cancellation cleanup so memory and state stay consistent.

## Non-Goals

This refactor should not change:

- LangGraph node names.
- API response schema.
- Existing Java tool endpoint paths.
- Existing intent names.
- Existing appointment query, lease query, or appointment create user behavior.

New write operations such as `lease_sign` should be added after this refactor, not during the first cleanup.

