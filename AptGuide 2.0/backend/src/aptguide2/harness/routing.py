from __future__ import annotations

from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.safety import SafetyBoundary


class HybridRouter:
    """Baseline router for AptGuide procedures."""

    name = "hybrid_router_v1"

    capability_terms = ("你能做什么", "你是谁", "你是什么助手")
    room_terms = ("找房", "房子", "房源", "租房", "公寓", "以内", "附近", "安静", "近地铁", "推荐")
    kb_terms = ("押金", "退租", "合同", "租约", "预约规则", "怎么预约", "报修", "投诉", "隐私", "注销")
    appointment_terms = ("预约第", "预约看房", "帮我预约", "我的预约", "查看预约", "预约列表", "预约记录", "预约")
    handoff_terms = ("转人工", "找真人", "人工客服", "我要找人工", "转接人工", "真人客服")
    lease_terms = ("我的租约", "查看租约", "租约列表", "合同列表", "我的合同")
    high_risk_terms = ("押金", "违约金", "退租", "合同", "赔偿", "扣钱", "扣多少")

    def __init__(self, safety: SafetyBoundary | None = None) -> None:
        self.safety = safety or SafetyBoundary()

    def _is_pending_action_followup(self, message: str) -> bool:
        confirm_terms = ("确认", "好的", "是的", "确定", "行", "可以", "yes", "ok")
        cancel_terms = ("取消", "不要了", "算了", "no")
        return any(term in message for term in confirm_terms + cancel_terms)

    def route(self, frame: ConversationFrame) -> RouteDecision:
        message = frame.message or ""
        flags = self.safety.check(message)
        if flags:
            return RouteDecision(
                task="fallback",
                procedure="fallback.safety",
                confidence=0.95,
                domain_category="blocked",
                reason="safety boundary matched",
                safety_flags=flags,
            )

        if frame.pending_action and frame.pending_action.get("type") in {"appointment.create", "appointment.cancel"}:
            if self._is_pending_action_followup(message):
                return RouteDecision(
                    task="appointment",
                    procedure="appointment.workflow",
                    confidence=0.98,
                    domain_category="in_domain_task",
                    reason="pending appointment action",
                )

        if any(term in message for term in self.capability_terms):
            return RouteDecision(
                task="capability",
                procedure="capability.profile",
                confidence=0.95,
                domain_category="in_domain_capability",
                reason="capability question",
            )

        if any(term in message for term in self.handoff_terms):
            return RouteDecision(
                task="handoff",
                procedure="handoff.user_initiated",
                confidence=0.9,
                domain_category="handoff",
                reason="user requested human agent",
            )

        if any(term in message for term in self.appointment_terms):
            return RouteDecision(
                task="appointment",
                procedure="appointment.workflow",
                confidence=0.8,
                domain_category="in_domain_task",
                reason="appointment request",
            )

        if any(term in message for term in self.lease_terms):
            return RouteDecision(
                task="lease",
                procedure="lease.workflow",
                confidence=0.85,
                domain_category="in_domain_task",
                reason="lease list request",
            )

        risk_level = "high" if any(term in message for term in self.high_risk_terms) else "low"
        if any(term in message for term in self.kb_terms):
            return RouteDecision(
                task="kb_qa",
                procedure="rag.kb_qa",
                confidence=0.85,
                risk_level=risk_level,
                domain_category="in_domain_knowledge",
                reason="rental knowledge question",
            )

        if any(term in message for term in self.room_terms):
            return RouteDecision(
                task="room_search",
                procedure="rag.room_search",
                confidence=0.75,
                domain_category="in_domain_task",
                reason="room search request",
            )

        return RouteDecision(
            task="fallback",
            procedure="fallback.unknown",
            confidence=0.5,
            domain_category="unknown",
            reason="no supported procedure matched",
        )
