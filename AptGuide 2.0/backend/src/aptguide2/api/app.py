"""FastAPI application for AptGuide 2.0."""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from aptguide2.api.auth import AuthResolver
from aptguide2.api.deps import get_aptguide_harness, get_settings, get_vector_adapter
from aptguide2.api.operator import router as operator_router
from aptguide2.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    KBSourceResponse,
    ReadinessResponse,
    RoomResponse,
)
from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse
from aptguide2.observability.events import emit_event
from aptguide2.system.readiness import build_readiness_report

app = FastAPI(title="AptGuide 2.0", version="0.1.0")

# Include routers
app.include_router(operator_router)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check — verifies Milvus connectivity."""
    adapter = get_vector_adapter()
    milvus_ok = False
    try:
        client = adapter._ensure_client()
        milvus_ok = client.has_collection("apt_room_vector")
    except Exception:
        pass
    return HealthResponse(status="ok", milvus=milvus_ok)


@app.get("/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    """Readiness check — validates all dependency configuration."""
    settings = get_settings()
    report = build_readiness_report(settings)
    return ReadinessResponse(
        ready=report.all_required_ok,
        checks=[check.model_dump() for check in report.checks],
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
    """Main chat endpoint - runs the AptGuide system harness."""
    settings = get_settings()
    try:
        auth = await AuthResolver(settings).resolve(authorization, requested_user_id=req.user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    harness = get_aptguide_harness()
    request_id = f"r-{uuid4().hex}"
    emit_event("chat.received", request_id=request_id, session_id=req.session_id, auth_mode=auth.auth_mode, message_len=len(req.message))
    result = await harness.run_async(
        AptGuideRequest(
            request_id=request_id,
            session_id=req.session_id,
            user_id=auth.user_id,
            message=req.message,
            action=req.action,
            client_context={**req.client_context, "auth_mode": auth.auth_mode, "display_name": auth.display_name},
        )
    )
    resp = _build_response_from_harness(result, session_id=req.session_id, request_id=request_id)
    emit_event(
        "chat.completed",
        request_id=request_id,
        trace_id=resp.trace_id,
        session_id=req.session_id,
        task=resp.task,
        phase=resp.phase,
        has_pending_action=resp.pending_action is not None,
    )
    return resp


def _build_response_from_harness(
    result: AptGuideResponse,
    session_id: str | None = None,
    request_id: str = "",
) -> ChatResponse:
    rooms = []
    for card in result.cards:
        if card.get("type") != "room":
            continue
        rooms.append(
            RoomResponse(
                room_id=card.get("room_id", 0),
                apartment_name=card.get("apartment_name", ""),
                room_number=card.get("room_number", ""),
                rent=card.get("rent", 0),
                district_name=card.get("district", ""),
                tags=card.get("tags", []),
                facilities=card.get("facilities", []),
                recommendation_reason=card.get("recommendation_reason", ""),
            )
        )
    sources = [
        KBSourceResponse(
            title=s.get("title", ""),
            content=s.get("content", ""),
            module=s.get("module", ""),
            score=s.get("score", 0.0),
        )
        for s in result.sources
    ]
    return ChatResponse(
        session_id=session_id,
        request_id=request_id,
        trace_id=result.trace_id,
        task=result.metadata.get("task", "fallback"),
        message=result.reply,
        phase=result.phase,
        cards=result.cards,
        rooms=rooms,
        kb_sources=sources,
        is_confident=bool(result.metadata.get("is_confident", False)),
        actions=result.actions,
        pending_action=result.pending_action,
        metadata=result.metadata,
    )
