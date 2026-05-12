from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求。"""

    session_id: str
    message: str
    context: dict | None = None
