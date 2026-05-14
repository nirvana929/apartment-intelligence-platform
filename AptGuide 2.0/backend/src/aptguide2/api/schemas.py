"""Request/response schemas for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str
    session_id: str | None = None
    user_id: str | None = None
    action: dict | None = None
    client_context: dict = Field(default_factory=dict)


class RoomResponse(BaseModel):
    """A single room in the chat response."""

    room_id: int
    apartment_name: str = ""
    room_number: str = ""
    rent: int = 0
    district_name: str = ""
    tags: list[str] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    recommendation_reason: str = ""


class KBSourceResponse(BaseModel):
    """A KB source in the chat response."""

    title: str
    content: str
    module: str
    score: float


class ChatResponse(BaseModel):
    """Outgoing chat response."""

    session_id: str | None = None
    request_id: str = ""
    trace_id: str = ""
    task: str
    message: str = ""
    phase: str = ""
    cards: list[dict] = Field(default_factory=list)
    rooms: list[RoomResponse] = Field(default_factory=list)
    kb_sources: list[KBSourceResponse] = Field(default_factory=list)
    is_confident: bool = False
    actions: list[dict] = Field(default_factory=list)
    pending_action: dict | None = None
    metadata: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    milvus: bool = False


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    ready: bool = False
    checks: list[dict] = Field(default_factory=list)
