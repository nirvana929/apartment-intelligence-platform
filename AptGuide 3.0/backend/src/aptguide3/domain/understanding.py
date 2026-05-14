from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

RouteName = Literal[
    "rag", "appointment", "lease", "handoff", "memory", "capability", "clarify", "fallback",
]
TaskName = Literal[
    "room_search", "kb_qa", "appointment", "lease", "handoff", "memory", "capability", "clarify", "fallback",
]
DomainName = Literal[
    "room", "payment", "lease", "life", "appointment", "account",
    "policy", "memory", "handoff", "capability", "unknown",
]
ActionName = Literal[
    "search",
    "ask_policy",
    "query_status",
    "create",
    "cancel",
    "list",
    "confirm",
    "deny",
    "update_preference",
    "delete_preference",
    "request_handoff",
    "ask_capability",
    "ask_clarification",
    "unknown",
]
RiskLevel = Literal["low", "medium", "high"]
ResponseMode = Literal[
    "normal_answer",
    "kb_grounded_answer",
    "authenticated_tool_query",
    "template_answer",
    "handoff_to_human",
    "refuse",
    "ask_clarification",
]


class RiskDecision(BaseModel):
    level: RiskLevel = "low"
    response_mode: ResponseMode = "normal_answer"
    reason: str = ""


class Clarification(BaseModel):
    needed: bool = False
    question: str = ""


class UnderstandingResult(BaseModel):
    raw_message: str
    route: RouteName
    task: TaskName
    domain: DomainName = "unknown"
    action: ActionName = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    retrieval_queries: list[str] = Field(default_factory=list)
    risk: RiskDecision = Field(default_factory=RiskDecision)
    clarification: Clarification = Field(default_factory=Clarification)
    reason: str = ""
