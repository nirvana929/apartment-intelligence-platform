from __future__ import annotations

from aptguide3.domain.safety import SafetyDecision


class SafetyBoundary:
    def check(self, message: str) -> SafetyDecision:
        privacy_terms = ("室友手机号", "别人手机号", "其他租户电话", "身份证")
        if any(term in message for term in privacy_terms):
            return SafetyDecision(
                blocked=True,
                reason="privacy",
                message="抱歉，我不能查询或透露他人隐私信息。",
            )
        return SafetyDecision()
