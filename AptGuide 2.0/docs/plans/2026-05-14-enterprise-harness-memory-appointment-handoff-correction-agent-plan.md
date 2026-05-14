# Enterprise Harness Memory Appointment Handoff Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the remaining AptGuide 2.0 harness work so appointment writes use a safe two-turn confirmation lifecycle, memory owns pending actions, and handoff can be triggered by repeated tool failures.

**Architecture:** Treat `MemoryManager` as the state owner for pending actions, `AppointmentWorkflowProcedure` as the business workflow, `ToolRuntime` as the only execution path for governed tools, and `HybridRouter`/`AptGuideHarness` as routing and orchestration layers. Keep default `/chat` behavior unchanged; all harness behavior remains behind `APTGUIDE_PIPELINE_VERSION=harness_v1`.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest, existing `aptguide2.harness`, existing `aptguide2.harness.tools`, existing `LeaseAdapter`.

---

## 0. Supersedes The Temporary Claude Plan

Do not execute the old plan that orders work as:

```text
Step 1 Procedure-Tool Runtime Integration
Step 2 Appointment Workflow
Step 3 Memory Module
Step 4 Handoff Module
```

That order is not enterprise-safe because `appointment.create` is a write operation and `ToolRuntime` already requires both `user_id` and `confirmation_id`.

Use this corrected order:

```text
Task 1: Reality audit and baseline verification
Task 2: Finish procedure-tool runtime integration tests
Task 3: Make routing pending-action aware
Task 4: Fix appointment list as the read-only workflow
Task 5: Fix appointment create as a two-turn pending-action workflow
Task 6: Persist pending action and confirmation lifecycle through orchestrator
Task 7: Add tool-failure-triggered handoff
Task 8: Full regression and documentation state cleanup
```

## 1. Non-Negotiable Guardrails

- [ ] Do not execute `appointment.create` in the first turn just because the user supplied room and time.
- [ ] Do not call `appointment.create` without `ToolCallRequest.confirmation_id`.
- [ ] Do not trust frontend-supplied `user_id` inside tool payload; use `frame.user_id`.
- [ ] Do not bypass `ToolRuntime`.
- [ ] Do not change default `/chat` MVP behavior.
- [ ] Do not mark project features as passed without test evidence.
- [ ] Do not run real lease, Milvus, embedding, or LLM services in unit tests.

## 2. Current Reality Snapshot

As of this plan, the workspace appears to contain these implemented but still inconsistent pieces:

| Area | Current state | Required correction |
| --- | --- | --- |
| `ProcedureRuntime` | Accepts and forwards `tool_runtime` | Add explicit forwarding tests if missing. |
| `MemoryManager` | Supports `pending_action`, expiry, recent messages, tool observations | Wire confirmation routing and use it consistently. |
| `AppointmentWorkflowProcedure` | Has listing and create logic, but create directly calls `appointment.create` | Replace direct create with pending-action first turn and confirmed execution second turn. |
| `HybridRouter` | Routes appointment and user handoff by terms | Route confirmation/cancel messages to appointment workflow when pending action exists. |
| `HandoffProcedure` | Supports user and tool-failure procedures | Add orchestrator-level automatic handoff trigger after repeated tool failures. |
| `progress/next-steps.md` | Marks modules complete while still listing confirmation/handoff gaps | Update after implementation to distinguish MVP presence from confirmed completion. |

## 3. Task 1: Reality Audit And Baseline

**Files:**

- Read: `backend/src/aptguide2/harness/procedures.py`
- Read: `backend/src/aptguide2/harness/orchestrator.py`
- Read: `backend/src/aptguide2/harness/memory.py`
- Read: `backend/src/aptguide2/harness/modules/appointment.py`
- Read: `backend/src/aptguide2/harness/modules/handoff.py`
- Read: `backend/src/aptguide2/harness/routing.py`

- [ ] **Step 1: Inspect actual state**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
sed -n '1,220p' src/aptguide2/harness/procedures.py
sed -n '1,260p' src/aptguide2/harness/orchestrator.py
sed -n '1,260p' src/aptguide2/harness/memory.py
sed -n '1,320p' src/aptguide2/harness/modules/appointment.py
sed -n '1,260p' src/aptguide2/harness/routing.py
```

Expected:

- `ProcedureRuntime.run()` accepts `tool_runtime`.
- `AptGuideHarness.run()` passes `tool_runtime`.
- `AppointmentWorkflowProcedure` still contains a first-turn direct `appointment.create` call and must be corrected.

- [ ] **Step 2: Run focused baseline tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_procedures.py tests/unit/harness/test_orchestrator.py tests/unit/harness/test_memory.py tests/unit/harness/modules/test_appointment.py tests/unit/harness/modules/test_handoff.py -q
```

Expected:

- If tests pass, continue.
- If tests fail, record exact failures in `reports/harness-correction-reality-addendum.md` and continue only after the failure is understood.

## 4. Task 2: Finish ProcedureRuntime To ToolRuntime Integration

**Files:**

- Modify: `backend/tests/unit/harness/test_procedures.py`
- Modify: `backend/tests/unit/harness/test_orchestrator.py`

- [ ] **Step 1: Add explicit forwarding test for `ProcedureRuntime`**

Add to `backend/tests/unit/harness/test_procedures.py`:

```python
class ToolAwareProcedure:
    def __init__(self):
        self.seen_tool_runtime = None

    def run(self, frame, decision, tool_runtime=None):
        self.seen_tool_runtime = tool_runtime
        return ProcedureResult(task=decision.task, phase="done", reply="ok")


def test_runtime_forwards_tool_runtime_to_registered_procedure():
    runtime = ProcedureRuntime()
    procedure = ToolAwareProcedure()
    tool_runtime = object()
    runtime.register("fake.tool_aware", procedure)
    frame = ConversationFrame(request_id="r-1", message="hello")
    decision = RouteDecision(task="capability", procedure="fake.tool_aware", confidence=1.0)

    result = runtime.run(frame, decision, tool_runtime=tool_runtime)

    assert result.reply == "ok"
    assert procedure.seen_tool_runtime is tool_runtime
```

- [ ] **Step 2: Add explicit forwarding test for `AptGuideHarness`**

Add to `backend/tests/unit/harness/test_orchestrator.py`:

```python
class CapturingProcedure:
    def __init__(self):
        self.seen_tool_runtime = None

    def run(self, frame, decision, tool_runtime=None):
        self.seen_tool_runtime = tool_runtime
        return ProcedureResult(task=decision.task, phase="done", reply="ok")


def test_harness_forwards_tool_runtime_to_procedure_runtime():
    runtime = ProcedureRuntime()
    procedure = CapturingProcedure()
    runtime.register("capability.profile", procedure)
    tool_runtime = object()
    harness = AptGuideHarness(
        context_store=InMemoryContextStore(),
        router=HybridRouter(),
        procedure_runtime=runtime,
        tool_runtime=tool_runtime,
    )

    response = harness.run(AptGuideRequest(request_id="r-1", session_id="s-1", message="你能做什么"))

    assert response.reply == "ok"
    assert procedure.seen_tool_runtime is tool_runtime
```

- [ ] **Step 3: Run integration tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_procedures.py tests/unit/harness/test_orchestrator.py -q
```

Expected: pass.

## 5. Task 3: Make Routing Pending-Action Aware

**Files:**

- Modify: `backend/src/aptguide2/harness/routing.py`
- Modify: `backend/tests/unit/harness/test_routing.py`

- [ ] **Step 1: Add routing tests for pending appointment confirmation**

Add to `backend/tests/unit/harness/test_routing.py`:

```python
def test_router_sends_confirmation_to_appointment_when_pending_action_exists():
    router = HybridRouter()
    frame = ConversationFrame(
        request_id="r-1",
        message="确认",
        pending_action={
            "type": "appointment.create",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {"room_id": 101, "preferred_time": "明天下午3点"},
        },
    )

    decision = router.route(frame)

    assert decision.task == "appointment"
    assert decision.procedure == "appointment.workflow"
    assert decision.reason == "pending appointment action"


def test_router_sends_cancel_to_appointment_when_pending_action_exists():
    router = HybridRouter()
    frame = ConversationFrame(
        request_id="r-1",
        message="取消",
        pending_action={
            "type": "appointment.create",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {"room_id": 101},
        },
    )

    decision = router.route(frame)

    assert decision.task == "appointment"
    assert decision.procedure == "appointment.workflow"
```

- [ ] **Step 2: Implement pending-action routing before keyword routing**

In `HybridRouter.route()`, after safety boundary and before capability/handoff/appointment term checks, add:

```python
        if frame.pending_action and frame.pending_action.get("type") == "appointment.create":
            if self._is_pending_action_followup(message, frame.action):
                return RouteDecision(
                    task="appointment",
                    procedure="appointment.workflow",
                    confidence=0.98,
                    domain_category="in_domain_task",
                    reason="pending appointment action",
                )
```

Add helper methods to `HybridRouter`:

```python
    def _is_pending_action_followup(self, message: str, action: dict | None) -> bool:
        if action and action.get("type") in {"confirm", "cancel"}:
            return True
        confirm_terms = ("确认", "好的", "是的", "确定", "行", "可以", "yes", "ok")
        cancel_terms = ("取消", "不要了", "算了", "no")
        return any(term in message for term in confirm_terms + cancel_terms)
```

- [ ] **Step 3: Run routing tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_routing.py -q
```

Expected: pass.

## 6. Task 4: Keep Appointment List As Read-Only Workflow

**Files:**

- Modify: `backend/src/aptguide2/harness/modules/appointment.py`
- Modify: `backend/tests/unit/harness/modules/test_appointment.py`

- [ ] **Step 1: Add test that appointment listing requires user identity**

Add to `backend/tests/unit/harness/modules/test_appointment.py`:

```python
def test_list_appointments_requires_user_id():
    proc = AppointmentWorkflowProcedure()
    frame = ConversationFrame(request_id="r-1", message="我的预约")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=FakeToolRuntime())

    assert result.phase == "appointment_auth_required"
    assert "登录" in result.reply
```

- [ ] **Step 2: Update list implementation to fail before tool call when user is missing**

In `_list_appointments()`, before building `ToolCallRequest`, add:

```python
        if not frame.user_id:
            return ProcedureResult(
                task="appointment",
                phase="appointment_auth_required",
                reply="请先登录后再查看您的预约记录。",
                fallback_reason="missing_user_id",
            )
```

Build request payload only from `frame.user_id`:

```python
        request = ToolCallRequest(
            tool="appointment.list_mine",
            request_id=frame.request_id,
            user_id=frame.user_id,
            payload={"user_id": frame.user_id, "limit": 10},
        )
```

- [ ] **Step 3: Run appointment tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/modules/test_appointment.py -q
```

Expected: pass after updating any old tests that assumed anonymous listing.

## 7. Task 5: Replace Direct Appointment Create With Pending Action

**Files:**

- Modify: `backend/src/aptguide2/harness/modules/appointment.py`
- Modify: `backend/tests/unit/harness/modules/test_appointment.py`

- [ ] **Step 1: Replace direct-create success test with pending-action test**

Remove or rewrite any test named like `test_create_appointment_success` that expects a first-turn call to `appointment.create`.

Add:

```python
def test_create_appointment_first_turn_returns_pending_action_without_tool_call():
    proc = AppointmentWorkflowProcedure()
    runtime = FakeToolRuntime(ok=True, data={"appointment_id": "APT-001"})
    frame = ConversationFrame(request_id="r-1", user_id="u-1", message="预约101号房明天下午3点")
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.8)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.task == "appointment"
    assert result.phase == "appointment_needs_confirmation"
    assert result.pending_action is not None
    assert result.pending_action["type"] == "appointment.create"
    assert result.pending_action["payload"]["room_id"] == 101
    assert result.pending_action["payload"]["preferred_time"] == "明天下午3点"
    assert runtime.last_request is None
```

- [ ] **Step 2: Add confirmed execution test**

```python
def test_create_appointment_confirmed_turn_calls_tool_with_confirmation_id():
    proc = AppointmentWorkflowProcedure()
    runtime = FakeToolRuntime(ok=True, data={"appointment_id": "APT-001", "status": "pending"})
    frame = ConversationFrame(
        request_id="r-2",
        user_id="u-1",
        message="确认",
        pending_action={
            "type": "appointment.create",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {
                "room_id": 101,
                "user_id": "u-1",
                "preferred_time": "明天下午3点",
                "notes": "",
            },
        },
    )
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.98)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.phase == "appointment_created"
    assert frame.pending_action is None
    assert runtime.last_request.tool == "appointment.create"
    assert runtime.last_request.user_id == "u-1"
    assert runtime.last_request.confirmation_id == "c-1"
    assert runtime.last_request.payload["room_id"] == 101
```

- [ ] **Step 3: Add cancellation test**

```python
def test_create_appointment_pending_turn_can_be_cancelled():
    proc = AppointmentWorkflowProcedure()
    runtime = FakeToolRuntime(ok=True, data={"appointment_id": "APT-001"})
    frame = ConversationFrame(
        request_id="r-2",
        user_id="u-1",
        message="取消",
        pending_action={
            "type": "appointment.create",
            "confirmation_id": "c-1",
            "status": "pending",
            "payload": {"room_id": 101, "user_id": "u-1", "preferred_time": "明天下午3点"},
        },
    )
    decision = RouteDecision(task="appointment", procedure="appointment.workflow", confidence=0.98)

    result = proc.run(frame, decision, tool_runtime=runtime)

    assert result.phase == "appointment_cancelled"
    assert frame.pending_action is None
    assert runtime.last_request is None
```

- [ ] **Step 4: Implement first-turn pending action creation**

In `_create_appointment()`, after room/time/user checks, replace the direct `ToolCallRequest(tool="appointment.create", ...)` call with:

```python
        if not frame.user_id:
            return ProcedureResult(
                task="appointment",
                phase="appointment_auth_required",
                reply="请先登录后再预约看房。",
                fallback_reason="missing_user_id",
            )

        confirmation_id = str(uuid.uuid4())[:8]
        pending_action = {
            "type": "appointment.create",
            "confirmation_id": confirmation_id,
            "status": "pending",
            "payload": {
                "room_id": room_id,
                "user_id": frame.user_id,
                "preferred_time": preferred_time,
                "notes": "",
            },
        }
        return ProcedureResult(
            task="appointment",
            phase="appointment_needs_confirmation",
            reply=f"请确认预约{room_id}号房，时间为{preferred_time}。回复'确认'继续，或'取消'放弃。",
            pending_action=pending_action,
            actions=[
                {
                    "type": "confirm",
                    "confirmation_id": confirmation_id,
                    "label": "确认预约",
                },
                {
                    "type": "cancel",
                    "confirmation_id": confirmation_id,
                    "label": "取消",
                },
            ],
            metadata={"room_id": room_id, "preferred_time": preferred_time},
        )
```

- [ ] **Step 5: Implement confirmed execution with confirmation id**

In `_handle_confirmation()`, when confirm terms or `frame.action.type == "confirm"` are present, call:

```python
                confirmation_id = pending.get("confirmation_id", "")
                request = ToolCallRequest(
                    tool="appointment.create",
                    request_id=frame.request_id,
                    user_id=frame.user_id or "",
                    confirmation_id=confirmation_id,
                    payload={
                        **pending.get("payload", {}),
                        "user_id": frame.user_id or pending.get("payload", {}).get("user_id", ""),
                    },
                )
```

After successful or failed execution, clear:

```python
                frame.pending_action = None
```

- [ ] **Step 6: Support frontend action confirmation**

At the start of `_handle_confirmation()`, derive booleans from both text and action:

```python
        action_type = (frame.action or {}).get("type")
        is_confirm = action_type == "confirm" or any(term in message for term in confirm_terms)
        is_cancel = action_type == "cancel" or any(term in message for term in cancel_terms)
```

Use `is_confirm` and `is_cancel` instead of text-only checks.

- [ ] **Step 7: Run appointment tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/modules/test_appointment.py -q
```

Expected:

- First turn returns `pending_action`.
- First turn does not call `appointment.create`.
- Confirmed turn calls `appointment.create` with `confirmation_id`.

## 8. Task 6: Verify Pending Action Persists Across Orchestrator Turns

**Files:**

- Modify: `backend/tests/unit/harness/test_orchestrator.py`

- [ ] **Step 1: Add two-turn orchestrator test**

Add:

```python
from aptguide2.harness.modules.appointment import AppointmentWorkflowProcedure
from aptguide2.harness.tools.contracts import ToolCallResult


class FakeAppointmentToolRuntime:
    def __init__(self):
        self.calls = []

    def execute(self, request):
        self.calls.append(request)
        return ToolCallResult.ok_result(
            tool=request.tool,
            data={"appointment_id": "APT-001", "status": "pending"},
            backend="lease",
        )


def test_harness_persists_pending_appointment_across_turns():
    runtime = ProcedureRuntime()
    runtime.register("appointment.workflow", AppointmentWorkflowProcedure())
    tool_runtime = FakeAppointmentToolRuntime()
    harness = AptGuideHarness(
        context_store=InMemoryContextStore(),
        router=HybridRouter(),
        procedure_runtime=runtime,
        tool_runtime=tool_runtime,
    )

    first = harness.run(AptGuideRequest(
        request_id="r-1",
        session_id="s-1",
        user_id="u-1",
        message="预约101号房明天下午3点",
    ))

    assert first.pending_action is not None
    assert tool_runtime.calls == []

    second = harness.run(AptGuideRequest(
        request_id="r-2",
        session_id="s-1",
        user_id="u-1",
        message="确认",
    ))

    assert second.phase == "appointment_created"
    assert len(tool_runtime.calls) == 1
    assert tool_runtime.calls[0].confirmation_id == first.pending_action["confirmation_id"]
```

- [ ] **Step 2: Run orchestrator tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_orchestrator.py -q
```

Expected: pass.

## 9. Task 7: Add Tool-Failure Automatic Handoff Trigger

**Files:**

- Modify: `backend/src/aptguide2/harness/orchestrator.py`
- Modify: `backend/tests/unit/harness/test_orchestrator.py`

- [ ] **Step 1: Add orchestrator test for repeated tool failures**

Add:

```python
class FailingAppointmentProcedure:
    def run(self, frame, decision, tool_runtime=None):
        frame.tool_observations.append({
            "tool": "appointment.list_mine",
            "success": False,
            "error_code": "LEASE_UNAVAILABLE",
        })
        return ProcedureResult(
            task="appointment",
            phase="appointment_list_failed",
            reply="查询预约记录失败，请稍后再试。",
            fallback_reason="appointment_list_failed",
        )


def test_harness_suggests_handoff_after_consecutive_tool_failures():
    runtime = ProcedureRuntime()
    runtime.register("appointment.workflow", FailingAppointmentProcedure())
    runtime.register("handoff.tool_failure", HandoffProcedure())
    harness = AptGuideHarness(
        context_store=InMemoryContextStore(),
        router=HybridRouter(),
        procedure_runtime=runtime,
    )

    harness.run(AptGuideRequest(request_id="r-1", session_id="s-1", user_id="u-1", message="我的预约"))
    second = harness.run(AptGuideRequest(request_id="r-2", session_id="s-1", user_id="u-1", message="我的预约"))

    assert second.phase == "handoff_requested"
    assert second.metadata["procedure"] == "handoff.tool_failure"
```

Import `HandoffProcedure` at the top of the test file:

```python
from aptguide2.harness.modules.handoff import HandoffProcedure
```

- [ ] **Step 2: Implement automatic handoff after procedure run**

In `AptGuideHarness.run()`, after the normal procedure result and before saving context, add:

```python
        if (
            result.task != "handoff"
            and self.memory.get_consecutive_tool_failures(frame) >= 2
            and "handoff.tool_failure" in self.procedure_runtime._procedures
        ):
            handoff_decision = decision.model_copy(
                update={
                    "task": "handoff",
                    "procedure": "handoff.tool_failure",
                    "confidence": 0.9,
                    "domain_category": "handoff",
                    "reason": "consecutive tool failures",
                }
            )
            token = recorder.start_stage("procedure.run", "handoff.tool_failure", {"task": "handoff"})
            result = self.procedure_runtime.run(frame, handoff_decision, tool_runtime=self.tool_runtime)
            recorder.finish_stage(
                token,
                {
                    "phase": result.phase,
                    "card_count": len(result.cards),
                    "source_count": len(result.sources),
                    "fallback_reason": result.fallback_reason,
                },
            )
            decision = handoff_decision
```

If direct access to `_procedures` is unacceptable, add a `has(name: str) -> bool` method to `ProcedureRuntime` and use it:

```python
    def has(self, name: str) -> bool:
        return name in self._procedures
```

Then use `self.procedure_runtime.has("handoff.tool_failure")`.

- [ ] **Step 3: Run handoff-related tests**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/harness/test_orchestrator.py tests/unit/harness/modules/test_handoff.py -q
```

Expected: pass.

## 10. Task 8: Documentation And State Cleanup

**Files:**

- Modify: `progress/current-plan.md`
- Modify: `progress/next-steps.md`
- Modify: `docs/plans/README.md`
- Modify: `reports/evaluation-report.md`
- Modify as needed: `docs/27-current-implementation-guide.md`
- Modify as needed: `docs/system/enterprise-harness-architecture.md`

- [ ] **Step 1: Update `progress/current-plan.md`**

Set active objective to:

```markdown
## Active Objective

Correct harness memory, appointment confirmation, and automatic handoff behavior after the initial module MVPs.

## Active Plan

`docs/plans/2026-05-14-enterprise-harness-memory-appointment-handoff-correction-agent-plan.md`
```

Keep completed plan history below it.

- [ ] **Step 2: Update `progress/next-steps.md`**

Replace the contradictory completed/immediate sections with:

```markdown
## Completed

1. Harness Foundation
2. Tool Registry Governance
3. Enterprise RAG v2
4. Procedure-Tool Runtime Integration
5. Memory Module MVP
6. Appointment List MVP
7. Handoff User-Initiated MVP

## Immediate

8. Appointment confirmation flow correction
9. Tool failure -> automatic handoff trigger
10. Live eval with Milvus/embedding/lease services

## Later

11. Rolling summary generation
12. Long-term profile extraction from conversation history
```

- [ ] **Step 3: Update evaluation report**

Append to `reports/evaluation-report.md`:

````markdown
## Harness Correction Evidence

- Appointment create now uses a two-turn pending-action confirmation flow.
- `appointment.create` is not executed on first turn.
- Confirmed execution sends `confirmation_id` through `ToolCallRequest`.
- Pending appointment confirmation survives across orchestrator turns.
- Repeated tool failures can route to `handoff.tool_failure`.

Verification command:

```bash
uv run pytest tests/unit/harness tests/unit/tools tests/unit/rag tests/e2e -q
```
````

- [ ] **Step 4: Update docs only where behavior changed**

Update `docs/27-current-implementation-guide.md` and `docs/system/enterprise-harness-architecture.md` only if they currently say appointment creation is a direct one-turn action.

Use this wording:

```markdown
Appointment creation is a confirmed write workflow. The first turn creates a `pending_action` with a `confirmation_id`; the confirmed turn executes `appointment.create` through ToolRuntime.
```

## 11. Task 9: Full Regression

**Files:**

- No new files required.

- [ ] **Step 1: Run full local regression**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run pytest tests/unit/rag tests/unit/harness tests/unit/tools tests/e2e -q
```

Expected:

- All tests pass.
- The expected count should be at least the current baseline plus the new confirmation/handoff tests.

- [ ] **Step 2: Run formatting/lint if available**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/backend"
uv run ruff check src tests
```

Expected: pass. If it fails, fix only issues introduced by this plan.

- [ ] **Step 3: Final status**

```bash
cd "/home/chove/桌面/apartment-intelligence-platform"
git status --short
```

Expected:

- Changes are limited to harness correction code, tests, docs, and progress/report files.
- No unrelated user changes are reverted.

## 12. Completion Criteria

This correction plan is complete only when all of these are true:

- First-turn appointment creation returns `pending_action` and does not call `appointment.create`.
- Confirmed appointment turn calls `appointment.create` with `user_id` and `confirmation_id`.
- Pending appointment confirmation routes correctly even when the message is only "确认" or "取消".
- Missing `user_id` blocks appointment listing and creation before tool execution.
- Repeated tool failures can trigger `handoff.tool_failure`.
- All focused tests pass.
- Full regression passes or external blockers are documented without fake pass claims.

## 13. Recommended Agent Handoff Prompt

Give the executing agent this prompt:

```text
Use this plan and execute it task-by-task:

/home/chove/桌面/apartment-intelligence-platform/AptGuide 2.0/docs/plans/2026-05-14-enterprise-harness-memory-appointment-handoff-correction-agent-plan.md

Do not follow the older temporary plan that performs appointment creation before memory/pending-action correction. The critical safety requirement is: appointment.create must be a confirmed two-turn write workflow, and ToolCallRequest must include confirmation_id on the confirmed turn.
```
