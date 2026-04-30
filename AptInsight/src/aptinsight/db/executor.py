"""Read-only SQL query executor."""

import time
from dataclasses import dataclass

from sqlalchemy import text

from aptinsight.core.config import settings
from aptinsight.core.logging import get_logger
from aptinsight.db.engine import async_session_factory

logger = get_logger(__name__)


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list]
    row_count: int
    duration_ms: float


async def execute_query(sql: str) -> QueryResult:
    """Execute a read-only SQL query and return structured results."""
    start = time.monotonic()
    async with async_session_factory() as session:
        async with session.begin():
            stmt = text(sql).execution_options(timeout=settings.mysql_query_timeout_seconds)
            result = await session.execute(stmt)

            if result.returns_rows:
                columns = list(result.keys())
                raw_rows = result.fetchmany(settings.mysql_max_rows)
                rows = [list(row) for row in raw_rows]
            else:
                columns = []
                rows = []

    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "query_executed",
        extra={
            "sql": sql[:500],
            "row_count": len(rows),
            "duration_ms": round(duration_ms, 2),
        },
    )
    return QueryResult(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        duration_ms=round(duration_ms, 2),
    )
