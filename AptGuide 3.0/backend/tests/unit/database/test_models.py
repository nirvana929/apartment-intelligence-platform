from aptguide3.database.models import (
    AuditLogRecord,
    Base,
    HandoffTicketRecord,
    MemoryRecord,
    MessageRecord,
    PendingActionRecord,
    ProcedureRunRecord,
    SessionRecord,
    TraceEventRecord,
)


def test_required_tables_are_declared():
    assert {
        "aptguide3_users",
        "aptguide3_sessions",
        "aptguide3_messages",
        "aptguide3_pending_actions",
        "aptguide3_memories",
        "aptguide3_memory_candidates",
        "aptguide3_handoff_tickets",
        "aptguide3_operator_messages",
        "aptguide3_trace_events",
        "aptguide3_procedure_runs",
        "aptguide3_audit_log",
    }.issubset(Base.metadata.tables.keys())


def test_core_model_table_names():
    assert SessionRecord.__tablename__ == "aptguide3_sessions"
    assert MessageRecord.__tablename__ == "aptguide3_messages"
    assert PendingActionRecord.__tablename__ == "aptguide3_pending_actions"
    assert MemoryRecord.__tablename__ == "aptguide3_memories"
    assert HandoffTicketRecord.__tablename__ == "aptguide3_handoff_tickets"
    assert TraceEventRecord.__tablename__ == "aptguide3_trace_events"
    assert ProcedureRunRecord.__tablename__ == "aptguide3_procedure_runs"
    assert AuditLogRecord.__tablename__ == "aptguide3_audit_log"
