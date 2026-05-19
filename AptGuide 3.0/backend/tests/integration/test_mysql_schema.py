"""Integration test: verify AptGuide 3.0 schema can be applied to MySQL.

Skipped unless MYSQL_DSN or APTGUIDE3_MYSQL_DSN env var is set.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest

# ---------------------------------------------------------------------------
# Skip if no MySQL DSN is configured
# ---------------------------------------------------------------------------

_raw_dsn = os.getenv("MYSQL_DSN") or os.getenv("APTGUIDE3_MYSQL_DSN", "")
pytestmark = pytest.mark.skipif(
    not _raw_dsn,
    reason="MYSQL_DSN / APTGUIDE3_MYSQL_DSN not set; skipping MySQL integration tests",
)


def _parse_dsn(dsn: str) -> tuple[str, int, str, str, str]:
    """Extract (host, port, user, password, database) from a DSN string."""
    normalized = re.sub(r"^mysql\+\w+://", "mysql://", dsn)
    parsed = urlparse(normalized)
    return (
        parsed.hostname or "localhost",
        parsed.port or 3306,
        unquote(parsed.username or "root"),
        unquote(parsed.password or ""),
        (parsed.path or "/aptguide3").lstrip("/"),
    )


@pytest.fixture()
def schema_sql() -> str:
    """Read the schema.sql file and return its content."""
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "src" / "aptguide3" / "database" / "schema.sql"
    )
    assert path.exists(), f"schema.sql not found at {path}"
    return path.read_text(encoding="utf-8")


@pytest.fixture()
def connection_params() -> tuple[str, int, str, str, str]:
    return _parse_dsn(_raw_dsn)


EXPECTED_TABLES = [
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
]


@pytest.mark.asyncio
async def test_apply_schema(connection_params: tuple, schema_sql: str):
    """Schema can be applied without errors."""
    import asyncmy

    host, port, user, password, database = connection_params
    conn = await asyncmy.connect(
        host=host, port=port, user=user, password=password,
        database=database, charset="utf8mb4",
    )

    statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
    errors: list[str] = []

    try:
        async with conn.cursor() as cur:
            for stmt in statements:
                match = re.search(
                    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\S+)",
                    stmt, re.IGNORECASE,
                )
                table_name = match.group(1) if match else "<unknown>"
                try:
                    await cur.execute(stmt)
                except Exception as exc:
                    errors.append(f"{table_name}: {exc}")
    finally:
        conn.close()

    assert not errors, "Schema application failed:\n" + "\n".join(errors)


@pytest.mark.asyncio
async def test_tables_exist(connection_params: tuple):
    """All expected tables exist after schema application."""
    import asyncmy

    host, port, user, password, database = connection_params
    conn = await asyncmy.connect(
        host=host, port=port, user=user, password=password,
        database=database, charset="utf8mb4",
    )

    try:
        async with conn.cursor() as cur:
            await cur.execute("SHOW TABLES")
            rows = await cur.fetchall()
            actual_tables = {row[0] for row in rows}
    finally:
        conn.close()

    missing = [t for t in EXPECTED_TABLES if t not in actual_tables]
    assert not missing, f"Missing tables: {missing}"
