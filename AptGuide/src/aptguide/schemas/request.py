from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求。"""

    session_id: str
    message: str
    user_id: str | None = None  # 由 lease 后端注入，AptGuide 不接受客户端伪造
    context: dict | None = None
