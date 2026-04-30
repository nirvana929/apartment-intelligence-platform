from fastapi import APIRouter

from aptinsight.schemas.request import ChatRequest
from aptinsight.schemas.response import ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        trace_id=request.trace_id,
        answer="AptInsight Agent project scaffold is ready. Agent graph is not implemented yet.",
        rows=[],
        columns=[],
        chart=None,
        sql=None,
        warnings=["agent_not_implemented"],
    )

