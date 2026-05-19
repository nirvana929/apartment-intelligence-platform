from aptguide3.persistence.contracts import (
    AuditRepository,
    HandoffRepositoryContract,
    MemoryRepositoryContract,
    MessageRepository,
    PendingActionRepository,
    ProcedureRunRepository,
    SessionRepository,
    TraceRepository,
)


def test_repository_protocols_import():
    assert SessionRepository
    assert MessageRepository
    assert PendingActionRepository
    assert MemoryRepositoryContract
    assert HandoffRepositoryContract
    assert TraceRepository
    assert ProcedureRunRepository
    assert AuditRepository
