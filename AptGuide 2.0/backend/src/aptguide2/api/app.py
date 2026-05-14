"""FastAPI application for AptGuide 2.0."""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI

from aptguide2.api.deps import get_aptguide_harness, get_vector_adapter
from aptguide2.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    KBSourceResponse,
    RoomResponse,
)
from aptguide2.harness.contracts import AptGuideRequest, AptGuideResponse

app = FastAPI(title="AptGuide 2.0", version="0.1.0")


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


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Main chat endpoint - runs the AptGuide system harness."""
    harness = get_aptguide_harness()
    result = harness.run(
        AptGuideRequest(
            request_id=f"r-{uuid4().hex}",
            session_id=req.session_id,
            user_id=req.user_id,
            message=req.message,
            action=req.action,
            client_context=req.client_context,
        )
    )
    return _build_response_from_harness(result)


def _build_response_from_harness(result: AptGuideResponse) -> ChatResponse:
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
