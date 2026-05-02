"""
HTTP API 层

本模块实现了 AptInsight 的 HTTP API 接口。
使用 FastAPI 框架构建 RESTful API。

学习要点：
1. FastAPI 框架 - 现代 Python Web 框架
2. 路由组织 - 如何组织 API 路由
3. 依赖注入 - FastAPI 的核心特性
4. 数据验证 - 使用 Pydantic 进行请求/响应验证

模块结构：
- chat.py: 聊天 API 路由
- health.py: 健康检查路由
- deps.py: 依赖注入函数

API 端点：
- POST /api/chat: 智能分析聊天接口
- GET /api/health: 健康检查接口

使用示例：
    from aptinsight.api import create_app

    app = create_app()
    # 使用 uvicorn 启动
    # uvicorn aptinsight.api:app --reload
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.logging import get_logger
from .chat import router as chat_router
from .health import router as health_router

# 获取日志记录器
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例

    这是应用的工厂函数，负责：
    1. 创建 FastAPI 实例
    2. 配置中间件
    3. 注册路由
    4. 配置生命周期事件

    Returns:
        FastAPI 应用实例

    学习要点：
    - 工厂模式：使用函数创建应用实例
    - 中间件配置：添加 CORS 等中间件
    - 路由注册：将路由模块注册到应用
    - 生命周期管理：配置启动和关闭事件
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("AptInsight API 启动中...")
        yield
        logger.info("AptInsight API 关闭中...")
        from .deps import cleanup_dependencies
        await cleanup_dependencies()
        logger.info("AptInsight API 关闭完成")

    # 创建 FastAPI 实例
    app = FastAPI(
        title="AptInsight API",
        description="尚庭公寓智能运营分析助手 API",
        version="1.0.0",
        docs_url="/docs",  # Swagger UI 地址
        redoc_url="/redoc",  # ReDoc 地址
        lifespan=lifespan,
    )

    # ----- 配置中间件 -----
    # CORS 中间件：允许跨域请求
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有源（开发环境）
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ----- 注册路由 -----
    app.include_router(health_router)
    app.include_router(chat_router, prefix="/api")

    # ----- 添加全局异常处理 -----
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """全局异常处理器"""
        logger.error(f"未处理的异常，错误: {exc}，路径: {request.url.path}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试",
            },
        )

    return app


# 创建默认应用实例
# 学习要点：模块级别的应用实例，方便直接导入使用
app = create_app()
