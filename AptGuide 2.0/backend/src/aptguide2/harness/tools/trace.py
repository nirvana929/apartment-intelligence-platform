from __future__ import annotations

from typing import Any

from aptguide2.harness.tools.contracts import ToolCallRequest, ToolCallResult, ToolDefinition

PII_KEYS = frozenset({"phone", "id_card", "bank_card", "real_name", "email", "mobile"})


def redact_pii(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if k.lower() in PII_KEYS else redact_pii(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_pii(item) for item in value]
    return value


def summarize_tool_request(request: ToolCallRequest, definition: ToolDefinition) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "tool": request.tool,
        "backend": definition.backend,
        "permission": definition.permission,
    }
    redacted_payload = redact_pii(request.payload)
    if redacted_payload:
        summary["payload_keys"] = sorted(redacted_payload.keys())
    if request.trace_id:
        summary["trace_id"] = request.trace_id
    return summary


def summarize_tool_result(result: ToolCallResult) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "tool": result.tool,
        "ok": result.ok,
    }
    backend = result.metadata.get("backend")
    if backend:
        summary["backend"] = backend
    latency = result.metadata.get("latency_ms")
    if latency is not None:
        summary["latency_ms"] = latency
    if result.ok:
        result_count = result.metadata.get("result_count")
        if result_count is not None:
            summary["result_count"] = result_count
        status = result.metadata.get("status")
        if status is not None:
            summary["status"] = status
    else:
        if result.error:
            summary["error_code"] = result.error.code
            summary["recoverable"] = result.error.recoverable
    return summary
