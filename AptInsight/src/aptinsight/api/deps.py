"""
FastAPI 依赖注入模块

本模块定义了 FastAPI 应用的依赖注入函数。
依赖注入是 FastAPI 的核心特性，用于管理共享资源和服务。

学习要点：
1. 依赖注入模式 - 如何在 FastAPI 中管理共享资源
2. 单例模式 - 如何确保某些对象只创建一次
3. 生命周期管理 - 管理资源的创建和销毁
4. 类型提示 - 使用类型提示提高代码可读性

依赖注入的优势：
1. 解耦 - 组件之间不直接依赖，而是通过注入
2. 可测试 - 可以轻松替换依赖进行测试
3. 可复用 - 依赖可以在多个地方复用
4. 生命周期管理 - 框架自动管理资源生命周期

使用示例：
    @app.get("/api/chat")
    async def chat(
        llm_client: LLMClient = Depends(get_llm_client),
        db_session: AsyncSession = Depends(get_db_session),
    ):
        # 使用注入的依赖
        pass
"""

from __future__ import annotations

from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends

from ..agent import AgentExecutor
from ..core.config import Settings, get_settings
from ..core.logging import get_logger
from ..db.engine import engine as db_engine
from ..llm.client import LLMClient

# 获取日志记录器
logger = get_logger(__name__)


# ============================================================================
# LLM 客户端依赖
# ============================================================================


@lru_cache()
def get_llm_client() -> LLMClient:
    """
    获取 LLM 客户端单例

    使用 lru_cache 装饰器确保只创建一次 LLM 客户端。
    这是因为 LLM 客户端包含连接池等重量级资源。

    Returns:
        LLMClient 实例

    学习要点：
    - @lru_cache: Python 的缓存装饰器，确保函数只执行一次
    - 单例模式：全局只有一个 LLM 客户端实例
    - 延迟初始化：第一次调用时才创建实例
    """
    settings = get_settings()

    logger.info(f"创建 LLM 客户端，模型: {settings.llm_model}")

    return LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )


# ============================================================================
# Agent 执行器依赖
# ============================================================================


@lru_cache()
def get_agent_executor() -> AgentExecutor:
    """
    获取 Agent 执行器单例

    Agent 执行器包含 LangGraph 工作流图，是应用的核心组件。

    Returns:
        AgentExecutor 实例

    学习要点：
    - 依赖链：AgentExecutor 依赖 LLMClient
    - 初始化顺序：先创建 LLMClient，再创建 AgentExecutor
    """
    llm_client = get_llm_client()

    logger.info("创建 Agent 执行器")

    return AgentExecutor(llm_client)


# ============================================================================
# 数据库会话依赖
# ============================================================================


async def get_db_session() -> AsyncGenerator:
    """
    获取数据库会话

    使用异步上下文管理器管理数据库会话的生命周期。
    会话在请求结束后自动关闭。

    Yields:
        SQLAlchemy AsyncSession

    学习要点：
    - 异步生成器：使用 async def + yield 定义异步依赖
    - 上下文管理器：自动管理资源的创建和销毁
    - 请求级生命周期：每个请求一个独立的会话
    """
    from ..db.engine import async_session_factory

    # 创建会话
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            # 会话会在退出上下文时自动关闭
            pass


# ============================================================================
# 设置依赖
# ============================================================================


def get_current_settings() -> Settings:
    """
    获取当前设置

    Returns:
        Settings 实例

    学习要点：
    - 配置管理：集中管理应用配置
    - 类型安全：使用 Pydantic 进行配置验证
    """
    return get_settings()


# ============================================================================
# 请求追踪依赖
# ============================================================================


def get_trace_id() -> str:
    """
    获取请求追踪 ID

    用于在日志中关联同一请求的所有操作。

    Returns:
        追踪 ID 字符串
    """
    import uuid

    return str(uuid.uuid4())


# ============================================================================
# 依赖注入组合
# ============================================================================


class AgentDeps:
    """
    Agent 依赖集合

    将多个依赖组合成一个类，方便在路由函数中使用。

    学习要点：
    - 依赖组合：将相关依赖组合在一起
    - 简化路由函数签名：减少参数数量
    """

    def __init__(
        self,
        agent_executor: AgentExecutor = Depends(get_agent_executor),
        settings: Settings = Depends(get_current_settings),
        trace_id: str = Depends(get_trace_id),
    ):
        self.agent_executor = agent_executor
        self.settings = settings
        self.trace_id = trace_id


# ============================================================================
# 清理函数
# ============================================================================


async def cleanup_dependencies():
    """
    清理所有依赖资源

    在应用关闭时调用，释放所有占用的资源。

    学习要点：
    - 资源清理：在应用关闭时释放资源
    - 缓存清理：清除 lru_cache 缓存
    """
    logger.info("清理依赖资源")

    # 清除 LLM 客户端缓存
    get_llm_client.cache_clear()

    # 清除 Agent 执行器缓存
    get_agent_executor.cache_clear()

    # 关闭数据库引擎
    await db_engine.dispose()

    logger.info("依赖资源清理完成")
  