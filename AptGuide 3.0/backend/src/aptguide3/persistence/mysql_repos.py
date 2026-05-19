from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from aptguide3.database.models import (
    AuditLogRecord,
    HandoffTicketRecord,
    MemoryRecord,
    MessageRecord,
    PendingActionRecord,
    ProcedureRunRecord,
    RoomIdentityMapRecord,
    SessionRecord,
    TraceEventRecord,
)
from aptguide3.rag.room_identity import RoomIdentity


def _run_async(coro):
    """Run an async coroutine from sync code, matching _persist_message pattern."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        loop.create_task(coro)
    else:
        asyncio.run(coro)


class MySqlSessionRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    # -- Sync protocol (SessionRepository from session_repo.py) --
    def save(self, session_id: str, data: dict) -> None:
        user_id = data.get("user_id", "")
        _run_async(self.upsert_session(session_id, user_id, data))

    def load(self, session_id: str) -> dict | None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # Fire-and-forget not viable for load; run in new loop
            return asyncio.run(self.load_session(session_id))
        return asyncio.run(self.load_session(session_id))

    def delete(self, session_id: str) -> None:
        pass  # Not yet needed; placeholder for protocol compliance

    # -- Async protocol (contracts.SessionRepository) --
    async def upsert_session(self, session_id: str, user_id: str, context: dict) -> None:
        async with self.sessionmaker() as session:
            existing = await session.get(SessionRecord, session_id)
            if existing:
                existing.user_id = user_id
                existing.context = context
            else:
                session.add(SessionRecord(
                    session_id=session_id,
                    user_id=user_id,
                    rolling_summary="",
                    context=context,
                ))
            await session.commit()

    async def load_session(self, session_id: str) -> dict | None:
        async with self.sessionmaker() as session:
            record = await session.get(SessionRecord, session_id)
            if record is None:
                return None
            return {
                "session_id": record.session_id,
                "user_id": record.user_id,
                "status": record.status,
                "context": record.context,
            }


class MySqlMessageRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def append_message(
        self, session_id: str, user_id: str, request_id: str, role: str, content: str, metadata: dict,
    ) -> None:
        async with self.sessionmaker() as session:
            session.add(MessageRecord(
                session_id=session_id,
                user_id=user_id,
                request_id=request_id,
                role=role,
                content=content,
                metadata_json=metadata,
            ))
            await session.commit()


class MySqlPendingActionRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def save_pending_action(
        self, pending_action_id: str, session_id: str, user_id: str,
        action_type: str, payload: dict, expires_at: datetime,
    ) -> None:
        async with self.sessionmaker() as session:
            session.add(PendingActionRecord(
                pending_action_id=pending_action_id,
                session_id=session_id,
                user_id=user_id,
                action_type=action_type,
                payload=payload,
                expires_at=expires_at,
            ))
            await session.commit()

    async def load_pending_action(self, pending_action_id: str) -> dict | None:
        async with self.sessionmaker() as session:
            record = await session.get(PendingActionRecord, pending_action_id)
            if record is None:
                return None
            return {
                "pending_action_id": record.pending_action_id,
                "session_id": record.session_id,
                "action_type": record.action_type,
                "payload": record.payload,
                "status": record.status,
            }

    async def mark_completed(self, pending_action_id: str) -> None:
        async with self.sessionmaker() as session:
            await session.execute(
                update(PendingActionRecord)
                .where(PendingActionRecord.pending_action_id == pending_action_id)
                .values(status="completed")
            )
            await session.commit()


class MySqlMemoryRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def list_memories(self, user_id: str) -> list[dict]:
        async with self.sessionmaker() as session:
            result = await session.execute(
                select(MemoryRecord).where(MemoryRecord.user_id == user_id, MemoryRecord.status == "active")
            )
            return [
                {"memory_id": r.memory_id, "kind": r.kind, "key_name": r.key_name, "value_json": r.value_json}
                for r in result.scalars()
            ]

    async def upsert_memory(self, memory_id: str, user_id: str, kind: str, key_name: str, value_json: dict) -> None:
        async with self.sessionmaker() as session:
            existing = await session.get(MemoryRecord, memory_id)
            if existing:
                existing.kind = kind
                existing.key_name = key_name
                existing.value_json = value_json
            else:
                session.add(MemoryRecord(
                    memory_id=memory_id, user_id=user_id, kind=kind, key_name=key_name, value_json=value_json,
                ))
            await session.commit()


class MySqlHandoffRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def create_ticket(
        self, ticket_id: str, session_id: str, user_id: str, trigger_type: str, summary: dict,
    ) -> None:
        async with self.sessionmaker() as session:
            session.add(HandoffTicketRecord(
                ticket_id=ticket_id, session_id=session_id, user_id=user_id, trigger_type=trigger_type, summary=summary,
            ))
            await session.commit()

    async def list_tickets(self, status: str = "open") -> list[dict]:
        async with self.sessionmaker() as session:
            result = await session.execute(
                select(HandoffTicketRecord).where(HandoffTicketRecord.status == status)
            )
            return [
                {
                    "ticket_id": r.ticket_id,
                    "session_id": r.session_id,
                    "trigger_type": r.trigger_type,
                    "summary": r.summary,
                }
                for r in result.scalars()
            ]


class MySqlTraceRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def append_trace_event(
        self, trace_id: str, request_id: str, session_id: str, event_name: str, payload: dict,
    ) -> None:
        async with self.sessionmaker() as session:
            session.add(TraceEventRecord(
                trace_id=trace_id, request_id=request_id, session_id=session_id, event_name=event_name, payload=payload,
            ))
            await session.commit()


class MySqlProcedureRunRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def start_run(
        self, run_id: str, request_id: str, session_id: str, user_id: str,
        procedure_name: str, route: str, task: str, metadata: dict,
    ) -> None:
        async with self.sessionmaker() as session:
            session.add(ProcedureRunRecord(
                run_id=run_id, request_id=request_id, session_id=session_id, user_id=user_id,
                procedure_name=procedure_name, route=route, task=task, status="running", metadata_json=metadata,
            ))
            await session.commit()

    async def complete_run(self, run_id: str, status: str, metadata: dict) -> None:
        async with self.sessionmaker() as session:
            await session.execute(
                update(ProcedureRunRecord)
                .where(ProcedureRunRecord.run_id == run_id)
                .values(status=status, metadata_json=metadata, completed_at=datetime.utcnow())
            )
            await session.commit()


class MySqlAuditRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def append_audit_event(self, user_id: str, session_id: str, event_type: str, payload: dict) -> None:
        async with self.sessionmaker() as session:
            session.add(AuditLogRecord(user_id=user_id, session_id=session_id, event_type=event_type, payload=payload))
            await session.commit()


class MySqlRoomIdentityRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self.sessionmaker = sessionmaker

    async def get_by_source(self, source_system: str, source_record_id: str) -> RoomIdentity | None:
        async with self.sessionmaker() as session:
            record = await session.get(
                RoomIdentityMapRecord,
                {"source_system": source_system, "source_record_id": source_record_id},
            )
            if record is None:
                return None
            return RoomIdentity(
                source_system=record.source_system,
                source_record_id=record.source_record_id,
                canonical_room_id=record.canonical_room_id,
                business_system=record.business_system,
                business_room_id=record.business_room_id,
                verification_status=record.verification_status,
                match_method=record.match_method,
                match_confidence=float(record.match_confidence),
            )

    async def upsert_mapping(self, identity: RoomIdentity) -> None:
        async with self.sessionmaker() as session:
            key = {"source_system": identity.source_system, "source_record_id": identity.source_record_id}
            record = await session.get(RoomIdentityMapRecord, key)
            if record is None:
                session.add(RoomIdentityMapRecord(
                    source_system=identity.source_system,
                    source_record_id=identity.source_record_id,
                    canonical_room_id=identity.canonical_room_id,
                    business_system=identity.business_system,
                    business_room_id=identity.business_room_id,
                    verification_status=identity.verification_status,
                    match_method=identity.match_method,
                    match_confidence=identity.match_confidence,
                    metadata_json={},
                ))
            else:
                record.canonical_room_id = identity.canonical_room_id
                record.business_system = identity.business_system
                record.business_room_id = identity.business_room_id
                record.verification_status = identity.verification_status
                record.match_method = identity.match_method
                record.match_confidence = identity.match_confidence
            await session.commit()
