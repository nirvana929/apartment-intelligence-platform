from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Backend = Literal["lease", "vector", "internal"]
Permission = Literal["public", "user", "admin"]
ErrorCode = Literal[
    "TOOL_TIMEOUT",
    "TOOL_NOT_IMPLEMENTED",
    "MISSING_USER_ID",
    "CONFIRMATION_REQUIRED",
    "UNKNOWN_TOOL_ERROR",
    "LEASE_UNAVAILABLE",
    "VECTOR_UNAVAILABLE",
    "INVALID_PAYLOAD",
]


class RetryPolicy(BaseModel):
    max_attempts: int = 1
    backoff_seconds: float = 0.0


class ToolDefinition(BaseModel):
    name: str
    backend: Backend
    permission: Permission
    input_schema: str
    output_schema: str
    requires_user: bool = False
    requires_confirmation: bool = False
    timeout_seconds: float = 5.0
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    description: str = ""


class ToolCallRequest(BaseModel):
    tool: str
    request_id: str
    trace_id: str | None = None
    user_id: str | None = None
    confirmation_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ToolError(BaseModel):
    code: ErrorCode
    message: str = ""
    recoverable: bool = False


class ToolCallResult(BaseModel):
    tool: str
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: ToolError | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok_result(
        cls,
        tool: str,
        data: dict[str, Any],
        backend: str,
        latency_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolCallResult:
        meta = {"backend": backend, "latency_ms": round(latency_ms, 3)}
        if metadata:
            meta.update(metadata)
        elif "rooms" in data:
            meta["result_count"] = len(data["rooms"])
        elif "sources" in data:
            meta["result_count"] = len(data["sources"])
        elif isinstance(data, list):
            meta["result_count"] = len(data)
        return cls(tool=tool, ok=True, data=data, metadata=meta)

    @classmethod
    def error_result(
        cls,
        tool: str,
        code: ErrorCode,
        message: str = "",
        recoverable: bool = False,
        backend: str = "internal",
    ) -> ToolCallResult:
        return cls(
            tool=tool,
            ok=False,
            error=ToolError(code=code, message=message, recoverable=recoverable),
            metadata={"backend": backend},
        )


# --- Tool input/output schemas ---


class LeaseHealthInput(BaseModel):
    pass


class LeaseHealthOutput(BaseModel):
    healthy: bool
    details: dict[str, Any] = Field(default_factory=dict)


class RoomSearchInput(BaseModel):
    query: str = ""
    district: str | None = None
    max_rent: int | None = None
    tags: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=100)


class RoomSearchOutput(BaseModel):
    rooms: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class RoomDetailInput(BaseModel):
    room_id: int


class RoomDetailOutput(BaseModel):
    room: dict[str, Any] = Field(default_factory=dict)


class KBSearchInput(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] = Field(default_factory=dict)


class KBSearchOutput(BaseModel):
    sources: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class TraceRecordInput(BaseModel):
    stage: str
    strategy: str
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class TraceRecordOutput(BaseModel):
    recorded: bool = True


class AppointmentCreateInput(BaseModel):
    room_id: int
    user_id: str
    preferred_time: str = ""
    notes: str = ""


class AppointmentCreateOutput(BaseModel):
    appointment_id: str = ""
    status: str = "pending"


class AppointmentListMineInput(BaseModel):
    user_id: str
    limit: int = Field(default=20, ge=1, le=100)


class AppointmentListMineOutput(BaseModel):
    appointments: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class LeaseListMineInput(BaseModel):
    user_id: str
    limit: int = Field(default=20, ge=1, le=100)


class LeaseListMineOutput(BaseModel):
    leases: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
