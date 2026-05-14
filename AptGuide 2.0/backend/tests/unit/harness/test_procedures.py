import pytest

from aptguide2.harness.contracts import ConversationFrame, ProcedureResult, RouteDecision
from aptguide2.harness.errors import ProcedureNotFoundError
from aptguide2.harness.procedures import ProcedureRuntime


class FakeProcedure:
    def run(self, frame, decision, tool_runtime=None):
        return ProcedureResult(task=decision.task, phase="done", reply="ok")


def test_runtime_runs_registered_procedure():
    runtime = ProcedureRuntime()
    runtime.register("fake.run", FakeProcedure())
    frame = ConversationFrame(request_id="r-1", message="hello")
    decision = RouteDecision(task="capability", procedure="fake.run", confidence=1.0)
    result = runtime.run(frame, decision)
    assert result.reply == "ok"


def test_runtime_raises_for_missing_procedure():
    runtime = ProcedureRuntime()
    frame = ConversationFrame(request_id="r-1", message="hello")
    decision = RouteDecision(task="capability", procedure="missing", confidence=1.0)
    with pytest.raises(ProcedureNotFoundError):
        runtime.run(frame, decision)


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
