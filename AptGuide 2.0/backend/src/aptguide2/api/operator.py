from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from aptguide2.harness.handoff_repository import HandoffRepository

router = APIRouter(prefix="/operator", tags=["operator"])

# Global repository instance — in production, inject via deps
_handoff_repo = HandoffRepository()


def get_handoff_repository() -> HandoffRepository:
    return _handoff_repo


class OperatorReplyRequest(BaseModel):
    content: str


def require_operator(token: str | None) -> None:
    from aptguide2.api.deps import get_settings as _get_settings

    settings = _get_settings()
    if not settings.operator_console_enabled:
        raise HTTPException(status_code=403, detail="operator console disabled")
    if settings.environment in ("staging", "production") and settings.operator_dev_token == "operator-dev-token":
        raise HTTPException(status_code=500, detail="operator token is not configured")
    if token != settings.operator_dev_token:
        raise HTTPException(status_code=401, detail="invalid operator token")


@router.get("/tickets")
async def list_tickets(x_operator_token: str | None = Header(default=None), status: str = "open"):
    require_operator(x_operator_token)
    repo = get_handoff_repository()
    tickets = await repo.list_tickets(status=status)
    return {"tickets": [ticket.__dict__ for ticket in tickets]}


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, x_operator_token: str | None = Header(default=None)):
    require_operator(x_operator_token)
    ticket = await get_handoff_repository().get_ticket(ticket_id)
    return ticket.__dict__


@router.post("/tickets/{ticket_id}/reply")
async def reply(ticket_id: str, req: OperatorReplyRequest, x_operator_token: str | None = Header(default=None)):
    require_operator(x_operator_token)
    await get_handoff_repository().add_message(ticket_id, sender="operator", content=req.content)
    return {"ok": True}


@router.post("/tickets/{ticket_id}/close")
async def close(ticket_id: str, x_operator_token: str | None = Header(default=None)):
    require_operator(x_operator_token)
    await get_handoff_repository().close_ticket(ticket_id)
    return {"ok": True}
