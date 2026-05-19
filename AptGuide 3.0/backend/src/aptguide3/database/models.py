from __future__ import annotations

from datetime import datetime

from sqlalchemy import DECIMAL, JSON, DateTime, Integer, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "aptguide3_users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="lease")
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class SessionRecord(Base):
    __tablename__ = "aptguide3_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    active_task: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rolling_summary: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column("context", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class MessageRecord(Base):
    __tablename__ = "aptguide3_messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class PendingActionRecord(Base):
    __tablename__ = "aptguide3_pending_actions"

    pending_action_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    payload: Mapped[dict] = mapped_column("payload", JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class MemoryRecord(Base):
    __tablename__ = "aptguide3_memories"

    memory_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    key_name: Mapped[str] = mapped_column(String(128), nullable=False)
    value_json: Mapped[dict] = mapped_column("value_json", JSON, nullable=False)
    source_session_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class MemoryCandidateRecord(Base):
    __tablename__ = "aptguide3_memory_candidates"

    candidate_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column("payload", JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class HandoffTicketRecord(Base):
    __tablename__ = "aptguide3_handoff_tickets"

    ticket_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open", index=True)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[dict] = mapped_column("summary", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class OperatorMessageRecord(Base):
    __tablename__ = "aptguide3_operator_messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class TraceEventRecord(Base):
    __tablename__ = "aptguide3_trace_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(String(80), nullable=False, default="", index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)
    event_name: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column("payload", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class ProcedureRunRecord(Base):
    __tablename__ = "aptguide3_procedure_runs"

    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    procedure_name: Mapped[str] = mapped_column(String(80), nullable=False)
    route: Mapped[str] = mapped_column(String(64), nullable=False)
    task: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLogRecord(Base):
    __tablename__ = "aptguide3_audit_log"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column("payload", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")


class RoomIdentityMapRecord(Base):
    __tablename__ = "aptguide3_room_identity_map"

    source_system: Mapped[str] = mapped_column(String(32), primary_key=True)
    source_record_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    canonical_room_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    business_system: Mapped[str] = mapped_column(String(32), nullable=False, default="lease")
    business_room_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unmapped", index=True)
    match_method: Mapped[str] = mapped_column(String(64), nullable=False, default="unmapped")
    match_confidence: Mapped[float] = mapped_column(DECIMAL(5, 4), nullable=False, default=0.0)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
