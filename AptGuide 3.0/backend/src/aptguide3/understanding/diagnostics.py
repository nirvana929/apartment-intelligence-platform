from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "token",
    "internal_token",
    "password",
    "mysql_dsn",
}


@dataclass
class UnderstandingDiagnostic:
    raw_message: str
    raw_llm_json: str = ""
    parse_error: str = ""
    parsed_route: str = ""
    parsed_task: str = ""
    parsed_domain: str = ""
    parsed_confidence: float | None = None
    parsed_clarification_needed: bool | None = None
    parsed_clarification_question: str = ""
    parsed_risk_response_mode: str = ""
    parsed_hard_filters: dict[str, Any] = field(default_factory=dict)
    validator_reason: str = ""
    final_route: str = ""
    final_task: str = ""
    final_domain: str = ""
    final_confidence: float | None = None

    def to_report_dict(self) -> dict[str, Any]:
        return sanitize_for_report(asdict(self))


def sanitize_for_report(value: Any) -> Any:
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                clean[key] = "<redacted>"
            else:
                clean[key] = sanitize_for_report(item)
        return clean
    if isinstance(value, list):
        return [sanitize_for_report(item) for item in value]
    return value
