from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from aptguide.api import chat, health
from aptguide.core.config import Settings
from aptguide.core.logging import setup_logging

# 全局实例
settings = Settings()
setup_logging(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期。"""
    # Milvus 连接延迟到实际使用时
    yield


app = FastAPI(
    title="AptGuide",
    description="智能找房助手。",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(health.router)
app.include_router(chat.router)

# 静态文件
app.mount("/", StaticFiles(directory="src/aptguide/ui", html=True), name="ui")


def _create_agent_graph():
    """延迟创建 Agent 图 - 避免启动时需要 LLM/Milvus 连接。"""
    from aptguide.agent.graph import create_agent_graph
    from aptguide.llm.client import LLMClient
    from aptguide.vector.client import MilvusClientWrapper
    from aptguide.vector.kb_search import KBSearch

    llm = LLMClient(settings)
    milvus = MilvusClientWrapper(settings)
    kb = KBSearch(milvus, settings)
    return create_agent_graph(llm, kb)


# Agent 图延迟初始化
agent_graph = None


def get_agent_graph():
    """获取 Agent 图(懒加载)。"""
    global agent_graph
    if agent_graph is None:
        agent_graph = _create_agent_graph()
    return agent_graph
