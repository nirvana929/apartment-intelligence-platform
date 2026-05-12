"""FastAPI application for AptGuide 2.0."""

from __future__ import annotations

from fastapi import FastAPI

from aptguide2.api.deps import get_embed_fn, get_llm_client, get_settings, get_vector_adapter
from aptguide2.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    KBSourceResponse,
    RoomResponse,
)
from aptguide2.rag.pipeline import PipelineResult, run_pipeline

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
    """Main chat endpoint — runs the RAG pipeline and returns structured response."""
    adapter = get_vector_adapter()
    embed_fn = get_embed_fn()

    result = run_pipeline(
        message=req.message,
        vector_adapter=adapter,
        embed_fn=embed_fn,
    )

    return _build_response(result)


def _build_response(result: PipelineResult) -> ChatResponse:
    """Convert PipelineResult to ChatResponse."""
    if result.task == "room_search":
        rooms = [
            RoomResponse(
                room_id=r.room_id,
                apartment_name=r.apartment_name,
                room_number=r.room_number,
                rent=r.rent,
                tags=r.tags,
                facilities=r.facilities,
                recommendation_reason=r.recommendation_reason,
            )
            for r in result.rooms
        ]
        message = _generate_room_message(result) if rooms else result.message
        return ChatResponse(task="room_search", message=message, rooms=rooms)

    if result.task == "kb_qa":
        if result.is_confident:
            message = _generate_kb_answer(result)
        else:
            message = result.message
        sources = [
            KBSourceResponse(
                title=s.title,
                content=s.content,
                module=s.module,
                score=round(s.score, 3),
            )
            for s in result.kb_sources[:3]
        ]
        return ChatResponse(
            task="kb_qa",
            message=message,
            kb_sources=sources,
            is_confident=result.is_confident,
        )

    # fallback
    return ChatResponse(task="fallback", message=result.message)


def _generate_room_message(result: PipelineResult) -> str:
    """Generate a natural language summary for room search results."""
    if not result.rooms:
        return result.message

    top = result.rooms[0]
    parts = [f"为您找到以下房源推荐："]
    for i, r in enumerate(result.rooms[:3], 1):
        tag_str = "、".join(r.tags[:3]) if r.tags else ""
        line = f"{i}. {r.apartment_name or '公寓'}"
        if r.room_number:
            line += f" {r.room_number}"
        line += f"，月租{r.rent}元"
        if tag_str:
            line += f"，{tag_str}"
        if r.recommendation_reason:
            line += f"（{r.recommendation_reason}）"
        parts.append(line)

    if len(result.rooms) > 3:
        parts.append(f"还有{len(result.rooms) - 3}套备选，可以告诉我您的偏好进一步筛选。")

    return "\n".join(parts)


def _generate_kb_answer(result: PipelineResult) -> str:
    """Generate a KB answer from sources using LLM."""
    if not result.kb_sources:
        return result.message

    # Build context from top sources
    context_parts = []
    for i, s in enumerate(result.kb_sources[:3], 1):
        context_parts.append(f"[来源{i}: {s.title}]\n{s.content}")
    context = "\n\n".join(context_parts)

    query = result.query_understanding.raw_message if result.query_understanding else ""

    client = get_llm_client()
    s = get_settings()
    resp = client.chat.completions.create(
        model=s.llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是租房助手，根据提供的知识库内容回答用户问题。"
                    "只使用知识库中的信息回答，不要编造。"
                    "如果知识库信息不足以回答，坦诚说明。用简洁中文回答。"
                ),
            },
            {
                "role": "user",
                "content": f"知识库内容：\n{context}\n\n用户问题：{query}",
            },
        ],
        temperature=0.3,
        max_tokens=500,
    )
    return resp.choices[0].message.content or result.message
