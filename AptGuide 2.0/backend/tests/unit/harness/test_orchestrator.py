from aptguide2.harness.context import InMemoryContextStore
from aptguide2.harness.contracts import AptGuideRequest, ConversationFrame, ProcedureResult
from aptguide2.harness.modules.appointment import AppointmentWorkflowProcedure
from aptguide2.harness.modules.capability import CapabilityProcedure
from aptguide2.harness.modules.fallback import FallbackProcedure
from aptguide2.harness.modules.handoff import HandoffProcedure
from aptguide2.harness.orchestrator import AptGuideHarness
from aptguide2.harness.procedures import ProcedureRuntime
from aptguide2.harness.routing import HybridRouter
from aptguide2.interaction.contracts import InteractionIntent
from aptguide2.harness.tools.contracts import ToolCallResult


class StubClassifier:
    def __init__(self, intent: InteractionIntent) -> None:
        self.intent = intent

    def classify(self, message: str) -> InteractionIntent:
        return self.intent.model_copy(update={"raw_message": message})


def _clarify_router():
    return HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
        raw_message="",
        route="fallback",
        action="clarify",
        response_mode="ask_clarification",
        clarification_needed=True,
        confidence=0.0,
    )))


def build_harness():
    runtime = ProcedureRuntime()
    runtime.register("capability.profile", CapabilityProcedure())
    runtime.register("fallback.safety", FallbackProcedure())
    runtime.register("fallback.unknown", FallbackProcedure())
    return AptGuideHarness(
        context_store=InMemoryContextStore(),
        router=_clarify_router(),
        procedure_runtime=runtime,
        include_trace=True,
    )


def test_harness_runs_capability_request():
    harness = AptGuideHarness(
        context_store=InMemoryContextStore(),
        router=HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
            raw_message="",
            route="capability",
            domain="capability",
            action="ask_capability",
            confidence=0.95,
        ))),
        procedure_runtime=build_harness().procedure_runtime,
        include_trace=True,
    )
    response = harness.run(AptGuideRequest(request_id="r-1", session_id="s-1", message="你能做什么"))
    assert response.reply
    assert response.metadata["procedure"] == "capability.profile"
    assert response.trace is not None


def test_harness_runs_safety_fallback():
    harness = AptGuideHarness(
        context_store=InMemoryContextStore(),
        router=HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
            raw_message="",
            route="fallback",
            confidence=0.4,
        ))),
        procedure_runtime=build_harness().procedure_runtime,
        include_trace=True,
    )
    response = harness.run(AptGuideRequest(request_id="r-1", session_id="s-1", message="保证不吵吗"))
    assert response.metadata["procedure"] == "fallback.safety"
    assert response.phase == "boundary_declined"


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
        router=HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
            raw_message="",
            route="capability",
            domain="capability",
            action="ask_capability",
            confidence=0.95,
        ))),
        procedure_runtime=runtime,
        tool_runtime=tool_runtime,
    )

    response = harness.run(AptGuideRequest(request_id="r-1", session_id="s-1", message="你能做什么"))

    assert response.reply == "ok"
    assert procedure.seen_tool_runtime is tool_runtime


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
    runtime.register("fallback.unknown", FallbackProcedure())
    tool_runtime = FakeAppointmentToolRuntime()
    harness = AptGuideHarness(
        context_store=InMemoryContextStore(),
        router=HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
            raw_message="",
            route="appointment",
            domain="appointment",
            action="create",
            needs_tool=True,
            needs_confirmation=True,
            confidence=0.82,
        ))),
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


class FailingAppointmentProcedure:
    def run(self, frame, decision, tool_runtime=None):
        frame.tool_observations = frame.tool_observations or []
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
    runtime.register("fallback.unknown", FallbackProcedure())
    harness = AptGuideHarness(
        context_store=InMemoryContextStore(),
        router=HybridRouter(intent_classifier=StubClassifier(InteractionIntent(
            raw_message="",
            route="appointment",
            domain="appointment",
            action="list",
            needs_tool=True,
            confidence=0.88,
        ))),
        procedure_runtime=runtime,
    )

    harness.run(AptGuideRequest(request_id="r-1", session_id="s-1", user_id="u-1", message="我的预约"))
    second = harness.run(AptGuideRequest(request_id="r-2", session_id="s-1", user_id="u-1", message="我的预约"))

    assert second.phase == "handoff_requested"
    assert second.metadata["procedure"] == "handoff.tool_failure"
