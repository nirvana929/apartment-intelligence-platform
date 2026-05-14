from __future__ import annotations

from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.safety import SafetyBoundary
from aptguide2.interaction.classifier import HeuristicInteractionClassifier, InteractionClassifier, apply_policy_corrections


class HybridRouter:
    """Semantic intent router for AptGuide procedures."""

    name = "semantic_router_v1"

    def __init__(self, safety: SafetyBoundary | None = None, intent_classifier: InteractionClassifier | None = None) -> None:
        self.safety = safety or SafetyBoundary()
        self.intent_classifier = intent_classifier or HeuristicInteractionClassifier()

    def _is_pending_action_followup(self, message: str) -> bool:
        confirm_terms = ("确认", "好的", "是的", "确定", "行", "可以", "yes", "ok")
        cancel_terms = ("取消", "不要了", "算了", "no")
        return any(term in message for term in confirm_terms + cancel_terms)

    def route(self, frame: ConversationFrame) -> RouteDecision:
        message = frame.message or ""

        # 1. Deterministic safety boundary — always first
        flags = self.safety.check(message)
        if flags:
            risk_level = "high" if "privacy" in flags else "medium"
            return RouteDecision(
                task="fallback",
                procedure="fallback.safety",
                confidence=0.95,
                risk_level=risk_level,
                domain_category="blocked",
                reason="safety boundary matched",
                safety_flags=flags,
            )

        # 2. Pending action followup — must route to same procedure
        if frame.pending_action and frame.pending_action.get("type") in {"appointment.create", "appointment.cancel"}:
            if self._is_pending_action_followup(message):
                return RouteDecision(
                    task="appointment",
                    procedure="appointment.workflow",
                    confidence=0.98,
                    domain_category="in_domain_task",
                    reason="pending appointment action",
                )

        # 3. Semantic intent classification
        intent = apply_policy_corrections(self.intent_classifier.classify(message))
        intent_metadata = {"intent": intent.model_dump(mode="json")}

        if intent.route == "capability":
            return RouteDecision(task="capability", procedure="capability.profile", confidence=intent.confidence, domain_category="in_domain_capability", reason=intent.reason or "semantic capability intent", metadata=intent_metadata)
        if intent.route == "handoff":
            return RouteDecision(task="handoff", procedure="handoff.user_initiated", confidence=intent.confidence, risk_level=intent.risk_level, domain_category="handoff", reason=intent.reason or "semantic handoff intent", metadata=intent_metadata)
        if intent.route == "appointment":
            return RouteDecision(task="appointment", procedure="appointment.workflow", confidence=intent.confidence, domain_category="in_domain_task", reason=intent.reason or "semantic appointment intent", metadata=intent_metadata)
        if intent.route == "lease":
            return RouteDecision(task="lease", procedure="lease.workflow", confidence=intent.confidence, domain_category="in_domain_task", reason=intent.reason or "semantic lease intent", metadata=intent_metadata)
        if intent.route == "memory":
            return RouteDecision(task="memory", procedure="memory.workflow", confidence=intent.confidence, domain_category="in_domain_task", reason=intent.reason or "semantic memory intent", metadata=intent_metadata)
        if intent.route == "rag" and intent.rag_task == "kb_qa":
            return RouteDecision(task="kb_qa", procedure="rag.kb_qa", confidence=intent.confidence, risk_level=intent.risk_level, domain_category="in_domain_knowledge", reason=intent.reason or "semantic kb intent", metadata=intent_metadata)
        if intent.route == "rag" and intent.rag_task == "room_search":
            return RouteDecision(task="room_search", procedure="rag.room_search", confidence=intent.confidence, domain_category="in_domain_task", reason=intent.reason or "semantic room intent", metadata=intent_metadata)

        return RouteDecision(
            task="fallback",
            procedure="fallback.unknown",
            confidence=intent.confidence,
            domain_category="unknown",
            reason=intent.reason or "no supported procedure matched",
            metadata=intent_metadata,
        )
