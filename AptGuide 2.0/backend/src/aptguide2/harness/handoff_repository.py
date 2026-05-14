from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HandoffTicket:
    ticket_id: str
    user_id: str
    session_id: str
    trigger: str
    summary: dict[str, Any]
    status: str = "open"
    messages: list[dict[str, Any]] = field(default_factory=list)


class HandoffRepository:
    """In-memory base for tests. Override with SQL-backed implementation."""

    def __init__(self) -> None:
        self.tickets: dict[str, HandoffTicket] = {}

    async def create_ticket(self, user_id: str, session_id: str, trigger: str, summary: dict[str, Any]) -> HandoffTicket:
        ticket = HandoffTicket(
            ticket_id=f"hof-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            session_id=session_id,
            trigger=trigger,
            summary=summary,
        )
        self.tickets[ticket.ticket_id] = ticket
        return ticket

    async def list_tickets(self, status: str = "open") -> list[HandoffTicket]:
        return [ticket for ticket in self.tickets.values() if ticket.status == status]

    async def get_ticket(self, ticket_id: str) -> HandoffTicket:
        return self.tickets[ticket_id]

    async def add_message(self, ticket_id: str, sender: str, content: str) -> None:
        self.tickets[ticket_id].messages.append({"sender": sender, "content": content})

    async def close_ticket(self, ticket_id: str) -> None:
        self.tickets[ticket_id].status = "closed"
