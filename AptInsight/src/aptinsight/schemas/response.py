from typing import Any

from pydantic import BaseModel


class Column(BaseModel):
    name: str
    type: str | None = None


class ChatResponse(BaseModel):
    trace_id: str
    answer: str
    rows: list[dict[str, Any]]
    columns: list[Column]
    chart: dict[str, Any] | None = None
    sql: str | None = None
    warnings: list[str] = []

