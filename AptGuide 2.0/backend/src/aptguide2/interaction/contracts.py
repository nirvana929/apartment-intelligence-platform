from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RouteName = Literal["rag", "appointment", "lease", "handoff", "memory", "capability", "fallback"]
RagTaskName = Literal["kb_qa", "room_search", "none"]
DomainName = Literal[
    "room", "payment", "lease", "life", "appointment", "account",
    "policy", "memory", "handoff", "capability", "unknown",
]
ActionName = Literal[
    "search", "ask_policy", "query_status", "create", "cancel", "list",
    "confirm", "deny", "update_preference", "delete_preference",
    "request_handoff", "ask_capability", "clarify", "unknown",
]
RiskLevel = Literal["low", "medium", "high"]
ResponseMode = Literal[
    "normal_answer", "kb_grounded_answer", "authenticated_tool_query",
    "template_answer", "handoff_to_human", "refuse", "ask_clarification",
]


class EntityMention(BaseModel):
    kind: Literal["district", "area", "budget", "payment_type", "room_id", "appointment_id", "time", "preference", "reference"]
    raw_text: str
    normalized_value: str | int | float | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Literal["llm", "regex", "alias_table", "conversation_state", "frontend_action"] = "llm"
    metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionIntent(BaseModel):
    raw_message: str
    route: RouteName = "fallback"
    rag_task: RagTaskName = "none"
    domain: DomainName = "unknown"
    action: ActionName = "unknown"
    needs_kb: bool = False
    needs_room_search: bool = False
    needs_tool: bool = False
    needs_confirmation: bool = False
    hard_filters: dict[str, Any] = Field(default_factory=dict)
    soft_preferences: list[str] = Field(default_factory=list)
    entities: list[EntityMention] = Field(default_factory=list)
    reference: dict[str, Any] | None = None
    risk_level: RiskLevel = "low"
    response_mode: ResponseMode = "normal_answer"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_queries: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarification_question: str = ""
    reason: str = ""
