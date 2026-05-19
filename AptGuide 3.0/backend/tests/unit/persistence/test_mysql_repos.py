from aptguide3.persistence.mysql_repos import (
    MySqlAuditRepository,
    MySqlHandoffRepository,
    MySqlMemoryRepository,
    MySqlMessageRepository,
    MySqlPendingActionRepository,
    MySqlProcedureRunRepository,
    MySqlSessionRepository,
    MySqlTraceRepository,
)


def test_mysql_repositories_accept_sessionmaker():
    sessionmaker = object()
    assert MySqlSessionRepository(sessionmaker)
    assert MySqlMessageRepository(sessionmaker)
    assert MySqlPendingActionRepository(sessionmaker)
    assert MySqlMemoryRepository(sessionmaker)
    assert MySqlHandoffRepository(sessionmaker)
    assert MySqlTraceRepository(sessionmaker)
    assert MySqlProcedureRunRepository(sessionmaker)
    assert MySqlAuditRepository(sessionmaker)
