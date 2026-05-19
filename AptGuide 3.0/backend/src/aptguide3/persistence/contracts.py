from __future__ import annotations

from datetime import datetime
from typing import Protocol


class SessionRepository(Protocol):
    async def upsert_session(self, session_id: str, user_id: str, context: dict) -> None: ...
    async def load_session(self, session_id: str) -> dict | None: ...


class MessageRepository(Protocol):
    async def append_message(
        self,
        session_id: str,
        user_id: str,
        request_id: str,
        role: str,
        content: str,
        metadata: dict,
    ) -> None: ...


class PendingActionRepository(Protocol):
    async def save_pending_action(
        self,
        pending_action_id: str,
        session_id: str,
        user_id: str,
        action_type: str,
        payload: dict,
        expires_at: datetime,
    ) -> None: ...
    async def load_pending_action(self, pending_action_id: str) -> dict | None: ...
    async def mark_completed(self, pending_action_id: str) -> None: ...


class MemoryRepositoryContract(Protocol):
    async def list_memories(self, user_id: str) -> list[dict]: ...
    async def upsert_memory(
        self, memory_id: str, user_id: str, kind: str, key_name: str, value_json: dict
    ) -> None: ...


class HandoffRepositoryContract(Protocol):
    async def create_ticket(
        self, ticket_id: str, session_id: str, user_id: str, trigger_type: str, summary: dict
    ) -> None: ...
    async def list_tickets(self, status: str = "open") -> list[dict]: ...


class TraceRepository(Protocol):
    async def append_trace_event(
        self, trace_id: str, request_id: str, session_id: str, event_name: str, payload: dict
    ) -> None: ...


class ProcedureRunRepository(Protocol):
    async def start_run(
        self,
        run_id: str,
        request_id: str,
        session_id: str,
        user_id: str,
        procedure_name: str,
        route: str,
        task: str,
        metadata: dict,
    ) -> None: ...
    async def complete_run(self, run_id: str, status: str, metadata: dict) -> None: ...


class AuditRepository(Protocol):
    async def append_audit_event(
        self, user_id: str, session_id: str, event_type: str, payload: dict
    ) -> None: ...
