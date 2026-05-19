from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from aptguide3.api.auth import AuthContext, AuthResolver
from aptguide3.api.deps import get_chat_service
from aptguide3.api.readiness import build_readiness_report
from aptguide3.api.schemas import ChatRequest, ChatResponse
from aptguide3.config import get_settings
from aptguide3.domain.conversation import ConversationFrame

FRONTEND_DIR = Path(__file__).resolve().parents[4] / "frontend"


async def _resolve_auth(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_internal_token: str | None = Header(default=None),
) -> AuthContext:
    """Resolve auth context from request headers.

    In dev mode this is a pass-through.  In internal_header mode the
    X-Internal-Token and X-User-Id headers are validated.
    """
    settings = get_settings()
    resolver = AuthResolver(settings)
    try:
        return await resolver.resolve(
            authorization=authorization,
            x_user_id=x_user_id,
            x_internal_token=x_internal_token,
            requested_user_id=None,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def create_app() -> FastAPI:
    app = FastAPI(title="AptGuide 3.0")
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.parsed_cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def propagate_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id")
        response = await call_next(request)
        if request_id:
            response.headers["X-Request-Id"] = request_id
        return response

    @app.get("/health")
    def health():
        return {"service": settings.service_name, "status": "ok"}

    @app.get("/ready")
    async def ready(live: bool = Query(default=False)):
        return await build_readiness_report(settings, live=live)

    @app.post("/chat", response_model=ChatResponse)
    def chat(body: ChatRequest, auth_ctx: AuthContext = Depends(_resolve_auth)):  # noqa: B008
        frame = ConversationFrame(
            message=body.message,
            session_id=body.session_id,
            user_id=auth_ctx.user_id,
            action=body.action,
            client_context=body.client_context,
        )
        return get_chat_service().run(frame)

    if FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

    return app


app = create_app()
