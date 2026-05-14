from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from aptguide3.api.deps import get_chat_service
from aptguide3.api.schemas import ChatRequest, ChatResponse
from aptguide3.config import get_settings
from aptguide3.domain.conversation import ConversationFrame

FRONTEND_DIR = Path(__file__).resolve().parents[4] / "frontend"


def create_app() -> FastAPI:
    app = FastAPI(title="AptGuide 3.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        settings = get_settings()
        return {"service": settings.service_name, "status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest):
        frame = ConversationFrame(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id,
            action=request.action,
            client_context=request.client_context,
        )
        return get_chat_service().run(frame)

    if FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

    return app


app = create_app()
