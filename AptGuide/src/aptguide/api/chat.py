"""
聊天 API 路由 —— 用户和 Agent 交互的入口。

【学习要点】
1. FastAPI 路由：@router.post("/api/chat") 把一个函数绑定到 POST /api/chat 端点
2. Pydantic 请求/响应模型：
   - ChatRequest：定义请求体的结构（session_id, message）
   - ChatResponse：定义响应体的结构（reply, cards, actions）
3. 会话管理：用内存 dict 存储会话状态（生产环境应换成 Redis）
4. 状态重置：每轮对话重置临时字段，防止上一轮数据污染
5. graph.ainvoke()：异步执行 LangGraph 工作流
"""

import uuid

from fastapi import APIRouter

from aptguide.schemas.request import ChatRequest
from aptguide.schemas.response import ChatResponse

router = APIRouter()

# 会话存储（内存版）—— 生产环境应换成 Redis
# key = session_id, value = 会话状态 dict
sessions: dict[str, dict] = {}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口。

    流程：
    1. 获取或创建会话状态
    2. 更新用户消息，重置临时字段
    3. 执行 Agent 工作流（graph.ainvoke）
    4. 保存结果并返回响应

    response_model=ChatResponse 让 FastAPI 自动：
    - 校验返回值是否符合 ChatResponse 的结构
    - 在 /docs 文档中展示响应格式
    """
    from aptguide.main import get_agent_graph

    # uuid.uuid4() 生成随机唯一 ID，用于追踪请求
    request_id = str(uuid.uuid4())

    # 获取已有会话，或创建新会话
    # sessions.get(key, default) —— key 存在返回值，不存在返回 default
    session = sessions.get(
        request.session_id,
        {
            "session_id": request.session_id,
            "message": request.message,
            "user_id": request.user_id,
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

    # 更新消息并重置每轮临时字段
    # 为什么要重置？因为 session 是跨轮次的，上一轮的 reply/cards 会残留
    session["message"] = request.message
    session["user_id"] = request.user_id
    session["reply"] = ""           # 重置回复
    session["cards"] = []           # 重置卡片
    session["actions"] = []         # 重置操作按钮
    session["sources"] = []         # 重置来源
    session["search_results"] = []  # 重置检索结果
    session["intent"] = None        # 重置意图（让 intent_node 重新分类）
    # 注意：confirmation 不重置！如果用户正在回复确认/取消，需要保留

    # 执行 Agent 工作流
    # graph.ainvoke(session) 会按照图的定义，依次执行各个节点
    # 每个节点返回的 dict 会自动合并到 session 中
    graph = get_agent_graph()
    result = await graph.ainvoke(session)

    # 保存会话结果（供下一轮对话使用）
    sessions[request.session_id] = result

    # 构造响应
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
