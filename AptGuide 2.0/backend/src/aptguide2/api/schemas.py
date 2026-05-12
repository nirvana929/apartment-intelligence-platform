"""Request/response schemas for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str
    session_id: str | None = None


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

    task: str
    message: str = ""
    rooms: list[RoomResponse] = Field(default_factory=list)
    kb_sources: list[KBSourceResponse] = Field(default_factory=list)
    is_confident: bool = False


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    milvus: bool = False
