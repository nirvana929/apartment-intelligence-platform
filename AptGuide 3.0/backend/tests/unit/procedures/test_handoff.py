from __future__ import annotations

import asyncio
from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.handoff import HandoffProcedure


class StubHandoffRepo:
    def __init__(self) -> None:
        self.tickets: list[dict[str, Any]] = []

    async def create_ticket(
        self,
        ticket_id: str,
        session_id: str,
        user_id: str,
        trigger_type: str,
        summary: dict[str, Any],
    ) -> None:
        self.tickets.append(
            {
                "ticket_id": ticket_id,
                "session_id": session_id,
                "user_id": user_id,
                "trigger_type": trigger_type,
                "summary": summary,
            }
        )

    async def list_tickets(self, status: str = "open") -> list[dict[str, Any]]:
        return self.tickets


class StubAuditRepo:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def append_audit_event(
        self,
        user_id: str,
        session_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        self.events.append(
            {
                "user_id": user_id,
                "session_id": session_id,
                "event_type": event_type,
                "payload": payload,
            }
        )


def _run(coro: Any) -> Any:
    return asyncio.get_event_loop().run_until_complete(coro)


def _frame(**overrides: Any) -> ConversationFrame:
    defaults = {"message": "我要转人工", "session_id": "s-1", "user_id": "u-1"}
    defaults.update(overrides)
    return ConversationFrame(**defaults)


def _understanding(**overrides: Any) -> UnderstandingResult:
    defaults = dict(
        raw_message="我要转人工",
        route="handoff",
        task="handoff",
        domain="handoff",
        action="request_handoff",
        confidence=0.95,
    )
    defaults.update(overrides)
    return UnderstandingResult(**defaults)


def test_no_handoff_repo_returns_unavailable() -> None:
    proc = HandoffProcedure()

    result = proc.run(_frame(), _understanding())

    assert result.phase == "handoff"
    assert "暂时不可用" in result.message
    assert result.metadata == {}


def test_success_creates_ticket_with_correct_args() -> None:
    repo = StubHandoffRepo()
    proc = HandoffProcedure(handoff_repo=repo)

    result = proc.run(_frame(), _understanding(reason="complex_issue"))

    assert result.phase == "handoff"
    assert result.metadata["handoff_created"] is True
    assert len(result.metadata["ticket_id"]) == 12
    assert result.metadata["ticket_id"] in result.message

    assert len(repo.tickets) == 1
    ticket = repo.tickets[0]
    assert ticket["ticket_id"] == result.metadata["ticket_id"]
    assert ticket["session_id"] == "s-1"
    assert ticket["user_id"] == "u-1"
    assert ticket["trigger_type"] == "user_request"
    assert ticket["summary"]["reason"] == "complex_issue"
    assert ticket["summary"]["message"] == "我要转人工"


def test_audit_write_on_handoff_creation() -> None:
    handoff_repo = StubHandoffRepo()
    audit_repo = StubAuditRepo()
    proc = HandoffProcedure(handoff_repo=handoff_repo, audit_repo=audit_repo)

    result = proc.run(_frame(), _understanding())

    assert len(audit_repo.events) == 1
    event = audit_repo.events[0]
    assert event["user_id"] == "u-1"
    assert event["session_id"] == "s-1"
    assert event["event_type"] == "handoff_create"
    assert event["payload"]["ticket_id"] == result.metadata["ticket_id"]
    assert event["payload"]["trigger_type"] == "user_request"


def test_no_audit_repo_does_not_crash() -> None:
    repo = StubHandoffRepo()
    proc = HandoffProcedure(handoff_repo=repo, audit_repo=None)

    result = proc.run(_frame(), _understanding())

    assert result.phase == "handoff"
    assert result.metadata["handoff_created"] is True
    assert len(repo.tickets) == 1
