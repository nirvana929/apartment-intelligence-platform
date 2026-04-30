from uuid import uuid4

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    session_id: str | None = None
    trace_id: str = Field(default_factory=lambda: uuid4().hex)

