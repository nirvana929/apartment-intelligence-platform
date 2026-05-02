from fastapi import FastAPI

from aptinsight.api.chat import router as chat_router
from aptinsight.api.health import router as health_router
from aptinsight.core.config import settings
from aptinsight.core.logging import setup_logging


# [框架] FastAPI 推荐用工厂函数创建 app，而不是直接 app = FastAPI()
# 这样可以在创建前做初始化（比如日志），也方便测试时创建不同的 app 实例
def create_app() -> FastAPI:
    # [框架] setup_logging 在 app 创建前调用，确保后续所有日志都用 JSON 格式
    setup_logging(settings.log_level)

    # [框架] FastAPI() 的 title 参数会显示在 /docs 的 Swagger UI 页面标题上
    app = FastAPI(title=settings.app_name)

    # [框架] include_router 把路由模块挂载到 app 上
    # health_router 不加 prefix，所以 /health 直接在根路径
    # chat_router 加 prefix="/api"，所以 /chat 变成 /api/chat
    app.include_router(health_router)
    app.include_router(chat_router, prefix="/api")
    return app


# [框架] 模块级别的 app 变量 = uvicorn 启动时的入口
# uvicorn aptinsight.main:app 就是找这个变量
app = create_app()
