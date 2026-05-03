"""
AptGuide 应用入口 —— FastAPI 应用的"组装工厂"。

【学习要点】
1. FastAPI 应用 = 一个 Python 对象 (app)，通过 include_router 注册路由
2. lifespan 是 FastAPI 的生命周期钩子，用于启动/关闭时初始化资源
3. 懒加载（Lazy Loading）：不在启动时创建所有依赖，而是第一次请求时才创建
4. 双重检查锁（Double-Checked Locking）：线程安全的单例模式，避免多线程重复创建
"""

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from aptguide.api import chat, health
from aptguide.core.config import Settings
from aptguide.core.logging import setup_logging

# Settings() 会自动从 .env 文件读取环境变量，填充到 pydantic 模型的字段中
# 这是 pydantic-settings 的核心能力：类型安全的配置管理
settings = Settings()
setup_logging(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理器。

    yield 之前的代码 = 应用启动时执行（如连接数据库）
    yield 之后的代码 = 应用关闭时执行（如释放连接）

    这里故意什么都不做 —— Milvus 连接延迟到第一次请求时（见 get_agent_graph）
    """
    yield


# 创建 FastAPI 应用实例
# title/description 会出现在自动生成的 API 文档中（访问 /docs 可看到）
app = FastAPI(
    title="AptGuide",
    description="智能找房助手。",
    version="0.1.0",
    lifespan=lifespan,
)

# include_router = 把一组相关的路由（URL 端点）注册到应用上
# health.router 提供 /health 健康检查端点
# chat.router 提供 /api/chat 聊天端点
app.include_router(health.router)
app.include_router(chat.router)

# mount = 挂载静态文件目录，让前端页面可以通过根路径访问
# html=True 表示访问 / 时自动返回 index.html
app.mount("/", StaticFiles(directory="src/aptguide/ui", html=True), name="ui")


def _create_agent_graph():
    """
    创建 Agent 处理图的工厂函数。

    这个函数把所有"依赖"组装起来：
    - LLMClient: 调用大语言模型的客户端
    - MilvusClientWrapper: 向量数据库客户端（存房源和知识库的 embedding）
    - KBSearch: 知识库检索（租房规则、FAQ）
    - RoomIndex: 房源检索（按条件搜索房间）
    - LeaseToolClient: Java 后端工具接口客户端
    - SessionMemory: 会话记忆（存用户的确认状态等）

    这些依赖通过参数注入到 create_agent_graph，而不是在函数内部硬编码 —— 这叫"依赖注入"
    """
    from aptguide.agent.graph import create_agent_graph
    from aptguide.llm.client import LLMClient
    from aptguide.memory.session import SessionMemory
    from aptguide.tools.client import LeaseToolClient
    from aptguide.vector.client import MilvusClientWrapper
    from aptguide.vector.embedding import EmbeddingClient
    from aptguide.vector.kb_search import KBSearch
    from aptguide.vector.room_index import RoomIndex

    llm = LLMClient(settings)
    milvus = MilvusClientWrapper(settings)
    milvus.connect()
    embedding = EmbeddingClient(settings)
    kb = KBSearch(milvus, settings)
    room_index = RoomIndex(milvus, settings, embedding)
    tool_client = LeaseToolClient(settings)
    # None 表示没有 Redis，SessionMemory 会降级到内存存储
    memory = SessionMemory(None)

    return create_agent_graph(llm, kb, room_index, tool_client, memory)


# ========== 懒加载单例 ==========
# 为什么用懒加载？
# 因为创建 Agent Graph 需要连接 Milvus 和 LLM，这些操作很慢
# 如果在应用启动时就创建，会拖慢启动速度
# 所以延迟到第一个请求进来时才创建

_agent_lock = threading.Lock()  # 线程锁，防止多线程同时创建
agent_graph = None  # 全局单例


def get_agent_graph():
    """
    获取 Agent 图（懒加载单例）。

    双重检查锁模式（Double-Checked Locking）：
    1. 第一次检查 (agent_graph is None) —— 避免每次都加锁（快速路径）
    2. 加锁 —— 只有一个线程能进入
    3. 第二次检查 (agent_graph is None) —— 防止在等待锁的过程中，其他线程已经创建了

    这在 Java 中对应 synchronized + double-check，在 Python 中对应 threading.Lock
    """
    global agent_graph
    if agent_graph is None:  # 第一次检查：已创建则直接返回（不加锁，性能好）
        with _agent_lock:  # 加锁：同一时刻只有一个线程能进入
            if agent_graph is None:  # 第二次检查：防止重复创建
                agent_graph = _create_agent_graph()
    return agent_graph
