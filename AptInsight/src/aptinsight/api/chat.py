"""
聊天 API 路由模块

本模块实现了 /api/chat 接口，这是 AptInsight 的核心 API。
它接收用户的自然语言问题，调用 Agent 工作流处理，返回分析结果。

学习要点：
1. FastAPI 路由 - 如何定义 API 端点
2. 请求/响应模型 - 使用 Pydantic 进行数据验证
3. 依赖注入 - 如何使用 FastAPI 的依赖注入
4. 错误处理 - 如何优雅地处理 API 错误
5. 异步处理 - 如何处理异步操作

API 设计原则：
1. RESTful - 遵循 REST 架构风格
2. 类型安全 - 使用 Pydantic 进行数据验证
3. 错误处理 - 返回清晰的错误信息
4. 日志记录 - 记录关键操作和错误
5. 性能监控 - 记录请求处理时间

请求流程：
客户端 → FastAPI → 依赖注入 → Agent 工作流 → 返回结果
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..agent import AgentExecutor, run_agent
from ..core.logging import get_logger
from ..llm.client import LLMClient
from ..schemas.request import ChatRequest
from ..schemas.response import ChatResponse, ErrorDetail
from .deps import get_agent_executor, get_llm_client, get_trace_id

# 获取日志记录器
logger = get_logger(__name__)

# 创建路由器
router = APIRouter(
    tags=["chat"],
    responses={
        400: {"model": ErrorDetail, "description": "请求参数错误"},
        500: {"model": ErrorDetail, "description": "服务器内部错误"},
    },
)


# ============================================================================
# 聊天 API 端点
# ============================================================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="智能分析聊天接口",
    description="接收用户的自然语言问题，返回数据分析结果、图表和业务洞察。",
)
async def chat(
    request: ChatRequest,
    agent_executor: AgentExecutor = Depends(get_agent_executor),
    llm_client: LLMClient = Depends(get_llm_client),
    trace_id: str = Depends(get_trace_id),
) -> ChatResponse:
    """
    智能分析聊天接口

    这是 AptInsight 的核心 API，处理流程：
    1. 接收用户的自然语言问题
    2. 调用 Agent 工作流进行处理
    3. 返回分析结果、图表和业务洞察

    Args:
        request: 聊天请求，包含用户问题
        agent_executor: Agent 执行器（依赖注入）
        llm_client: LLM 客户端（依赖注入）
        trace_id: 请求追踪 ID（依赖注入）

    Returns:
        ChatResponse: 包含答案、图表、数据等的响应

    学习要点：
    - 依赖注入：使用 Depends 注入共享资源
    - 异步处理：使用 async/await 处理异步操作
    - 错误处理：使用 try/except 处理异常
    - 日志记录：记录关键操作和错误
    """
    # 记录请求开始
    start_time = time.monotonic()
    logger.info(f"收到聊天请求，问题: {request.question[:50]}，trace_id: {trace_id}")

    try:
        # 调用 Agent 工作流
        result = await run_agent(
            question=request.question,
            llm_client=llm_client,
            trace_id=trace_id,
            session_id=request.session_id,
        )

        # 计算处理时间
        processing_time_ms = (time.monotonic() - start_time) * 1000

        # 构造响应
        response = _build_response(result, trace_id, processing_time_ms)

        logger.info(
            f"聊天请求处理完成，trace_id: {trace_id}，有错误: {bool(result.get('error'))}，耗时: {round(processing_time_ms, 2)}ms"
        )

        return response

    except Exception as e:
        # 计算处理时间（即使失败也要记录）
        processing_time_ms = (time.monotonic() - start_time) * 1000

        logger.error(
            f"聊天请求处理失败，trace_id: {trace_id}，错误: {e}，耗时: {round(processing_time_ms, 2)}ms"
        )

        # 返回错误响应
        raise HTTPException(
            status_code=500,
            detail=ErrorDetail(
                code="AGENT_ERROR",
                message="处理您的问题时发生错误，请稍后重试",
                details={"error": str(e)},
            ).model_dump(),
        )


# ============================================================================
# 流式聊天 API 端点（可选）
# ============================================================================

@router.post(
    "/chat/stream",
    summary="流式聊天接口",
    description="使用 Server-Sent Events (SSE) 流式返回分析结果。",
)
async def chat_stream(
    request: ChatRequest,
    agent_executor: AgentExecutor = Depends(get_agent_executor),
    llm_client: LLMClient = Depends(get_llm_client),
    trace_id: str = Depends(get_trace_id),
):
    """
    流式聊天接口

    使用 Server-Sent Events (SSE) 流式返回分析结果。
    适用于需要实时反馈的场景。

    学习要点：
    - SSE (Server-Sent Events): 服务器向客户端推送事件
    - 流式响应：逐步返回结果，提高用户体验
    - 异步生成器：使用 yield 生成事件流
    """
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        """SSE 事件生成器"""
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'trace_id': trace_id})}\n\n"

            # 执行 Agent 工作流
            result = await run_agent(
                question=request.question,
                llm_client=llm_client,
                trace_id=trace_id,
                session_id=request.session_id,
            )

            # 发送结果事件
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"

            # 发送完成事件
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # 发送错误事件
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============================================================================
# 辅助函数
# ============================================================================

def _build_response(
    result: dict[str, Any],
    trace_id: str,
    processing_time_ms: float,
) -> ChatResponse:
    """
    构建聊天响应

    Args:
        result: Agent 工作流的结果
        trace_id: 请求追踪 ID
        processing_time_ms: 处理耗时（毫秒）

    Returns:
        ChatResponse 对象

    学习要点：
    - 数据转换：将内部数据结构转换为 API 响应格式
    - 默认值处理：为缺失字段提供合理的默认值
    """
    # 处理列信息
    columns = result.get("columns", [])
    if isinstance(columns, list) and columns:
        if isinstance(columns[0], str):
            # 如果是字符串列表，转换为字典列表
            columns = [{"name": col, "type": "string"} for col in columns]

    # 处理图表信息
    chart = None
    if result.get("chart_type") and result.get("chart_option"):
        chart = {
            "type": result["chart_type"],
            "option": result["chart_option"],
        }

    # 构造响应
    return ChatResponse(
        trace_id=trace_id,
        answer=result.get("answer", ""),
        summary=result.get("summary", ""),
        rows=result.get("rows", []),
        columns=columns,
        chart=chart,
        sql=result.get("sql"),
        warnings=result.get("warnings", []),
        error=result.get("error"),
        processing_time_ms=round(processing_time_ms, 2),
    )


def _format_error_message(error: str) -> str:
    """
    格式化错误消息

    Args:
        error: 原始错误消息

    Returns:
        用户友好的错误消息

    学习要点：
    - 错误消息本地化：将技术错误转换为用户友好的消息
    - 错误分类：识别不同类型的错误
    """
    error_lower = error.lower()

    if "timeout" in error_lower:
        return "处理超时，请尝试简化您的问题"
    elif "connection" in error_lower:
        return "服务连接失败，请稍后重试"
    elif "rate limit" in error_lower:
        return "请求过于频繁，请稍后重试"
    else:
        return "处理您的问题时发生错误，请稍后重试"
