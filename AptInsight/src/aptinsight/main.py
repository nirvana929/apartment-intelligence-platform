from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from aptinsight.api.chat import router as chat_router
from aptinsight.api.health import router as health_router
from aptinsight.core.config import settings
from aptinsight.core.logging import setup_logging

# frontend 目录：相对于项目根目录
_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    app = FastAPI(title=settings.app_name)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 路由
    app.include_router(health_router)
    app.include_router(chat_router, prefix="/api")

    # 根路径重定向到前端页面
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/static/index.html")

    # 静态文件（前端）
    if _FRONTEND_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")

    return app


# [框架] 模块级别的 app 变量 = uvicorn 启动时的入口
# uvicorn aptinsight.main:app 就是找这个变量
app = create_app()
