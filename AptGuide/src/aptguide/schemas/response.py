from pydantic import BaseModel


class Card(BaseModel):
    """卡片。"""

    type: str  # "room" | "faq"
    room_id: int | None = None
    title: str
    rent: int | None = None
    district: str | None = None
    tags: list[str] = []
    description: str | None = None
    thumbnail_url: str | None = None


class Action(BaseModel):
    """操作按钮。"""

    type: str  # "view_detail" | "create_appointment"
    room_id: int | None = None


class PendingConfirmation(BaseModel):
    """待确认操作。"""

    type: str
    params: dict
    summary: str


class ChatResponse(BaseModel):
    """聊天响应。"""

    session_id: str
    request_id: str
    intent: str
    reply: str
    cards: list[Card] = []
    actions: list[Action] = []
    pending_confirmation: PendingConfirmation | None = None
    sources: list[str] = []
