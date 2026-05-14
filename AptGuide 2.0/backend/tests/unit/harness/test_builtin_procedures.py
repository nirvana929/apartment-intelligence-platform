from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.modules.capability import CapabilityProcedure
from aptguide2.harness.modules.fallback import FallbackProcedure


def test_capability_procedure_returns_fixed_profile():
    frame = ConversationFrame(request_id="r-1", message="你能做什么")
    decision = RouteDecision(task="capability", procedure="capability.profile", confidence=1.0)
    result = CapabilityProcedure().run(frame, decision)
    assert result.task == "capability"
    assert "找房" in result.reply
    assert result.phase == "idle"


def test_fallback_procedure_uses_safety_reason():
    frame = ConversationFrame(request_id="r-1", message="保证不吵")
    decision = RouteDecision(
        task="fallback",
        procedure="fallback.safety",
        confidence=0.95,
        safety_flags=["guarantee"],
    )
    result = FallbackProcedure().run(frame, decision)
    assert result.task == "fallback"
    assert result.fallback_reason == "safety_boundary"
    assert "无法保证" in result.reply
