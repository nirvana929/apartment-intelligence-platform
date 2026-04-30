from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    trace_id: str
    session_id: str | None
    question: str
    normalized_question: str
    intent: str
    schema_context: str
    metric_context: str
    generated_sql: str | None
    safe_sql: str | None
    sql_guard_result: dict[str, Any]
    rows: list[dict[str, Any]]
    columns: list[dict[str, Any]]
    chart_type: str | None
    chart_option: dict[str, Any] | None
    answer: str
    warnings: list[str]
    error: str | None

