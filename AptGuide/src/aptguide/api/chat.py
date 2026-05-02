import uuid

from fastapi import APIRouter

from aptguide.schemas.request import ChatRequest
from aptguide.schemas.response import ChatResponse

router = APIRouter()

# 会话存储 (阶段 1 使用内存)
sessions: dict[str, dict] = {}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口。"""
    from aptguide.main import agent_graph

    request_id = str(uuid.uuid4())

    # 获取或创建会话状态
    session = sessions.get(
        request.session_id,
        {
            "session_id": request.session_id,
            "message": request.message,
            "intent": None,
            "slots": {},
            "search_results": [],
            "confirmation": None,
            "reply": "",
            "cards": [],
            "actions": [],
            "sources": [],
        },
    )

    # 更新消息
    session["message"] = request.message

    # 执行 Agent
    result = await agent_graph.ainvoke(session)

    # 更新会话
    sessions[request.session_id] = result

    return ChatResponse(
        session_id=request.session_id,
        request_id=request_id,
        intent=result.get("intent", "other"),
        reply=result.get("reply", ""),
        cards=result.get("cards", []),
        actions=result.get("actions", []),
        pending_confirmation=result.get("confirmation"),
        sources=result.get("sources", []),
    )
