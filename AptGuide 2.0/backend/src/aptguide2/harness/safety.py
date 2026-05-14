from __future__ import annotations


class SafetyBoundary:
    """Deterministic safety boundary for clear non-negotiable cases."""

    guarantee_patterns = ("保证", "担保", "一定", "肯定")
    privacy_patterns = ("别人手机号", "其他租户", "身份证", "查别人", "手机号")
    out_of_domain_patterns = ("写 React", "写 Vue", "股票", "航班", "电影", "酒店", "黑客", "黑进")

    def check(self, message: str) -> list[str]:
        flags: list[str] = []
        if any(p in message for p in self.guarantee_patterns):
            flags.append("guarantee")
        if any(p in message for p in self.privacy_patterns):
            flags.append("privacy")
        if any(p in message for p in self.out_of_domain_patterns):
            flags.append("out_of_domain")
        return flags
