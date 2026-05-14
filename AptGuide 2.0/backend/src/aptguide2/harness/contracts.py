from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Task = Literal[
    "room_search",
    "kb_qa",
    "appointment",
    "lease",
    "user_data",
    "memory",
    "handoff",
    "capability",
    "fallback",
]
RiskLevel = Literal["low", "medium", "high"]


class AptGuideRequest(BaseModel):
    session_id: str | None = None
    request_id: str
    user_id: str | None = None
    message: str = ""
    action: dict[str, Any] | None = None
    client_context: dict[str, Any] = Field(default_factory=dict)
    harness_version: str = "harness_v1"


class ConversationFrame(BaseModel):
    session_id: str | None = None
    request_id: str
    user_id: str | None = None
    message: str = ""
    action: dict[str, Any] | None = None
    phase: str = "idle"
    domain_category: str = "unknown"
    active_task: Task | None = None
    task_slots: dict[str, Any] = Field(default_factory=dict)
    recent_messages: list[dict[str, Any]] = Field(default_factory=list)
    rolling_summary: str = ""
    long_term_profile: dict[str, Any] = Field(default_factory=dict)
    pending_action: dict[str, Any] | None = None
    last_recommendations: list[dict[str, Any]] = Field(default_factory=list)
    tool_observations: list[dict[str, Any]] = Field(default_factory=list)
    recovery_decision: dict[str, Any] | None = None
    handoff: dict[str, Any] | None = None


class RouteDecision(BaseModel):
    task: Task
    procedure: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel = "low"
    domain_category: str = "unknown"
    reason: str = ""
    safety_flags: list[str] = Field(default_factory=list)


class ProcedureResult(BaseModel):
    task: Task
    phase: str
    reply: str = ""
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    fallback_reason: str = ""


class StageTrace(BaseModel):
    stage: str
    strategy: str
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    errors: list[str] = Field(default_factory=list)


class AptGuideTrace(BaseModel):
    trace_id: str
    request_id: str
    session_id: str | None = None
    stages: list[StageTrace] = Field(default_factory=list)


class AptGuideResponse(BaseModel):
    session_id: str | None = None
    request_id: str
    trace_id: str
    reply: str
    phase: str
    domain_category: str
    cards: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    trace: AptGuideTrace | None = None
