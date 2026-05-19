"""Apply AptGuide 3.0 database schema to a live MySQL instance.

Reads APTGUIDE3_MYSQL_DSN from environment (falls back to individual
MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE vars).

Usage:
    python scripts/apply_schema.py
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


def _resolve_dsn() -> tuple[str, int, str, str, str]:
    """Return (host, port, user, password, database) from env."""
    raw_dsn = os.getenv("APTGUIDE3_MYSQL_DSN", "")
    if raw_dsn:
        # Handle mysql+asyncmy:// or mysql+pymysql:// prefix
        dsn = re.sub(r"^mysql\+\w+://", "mysql://", raw_dsn)
        parsed = urlparse(dsn)
        host = parsed.hostname or "localhost"
        port = parsed.port or 3306
        user = unquote(parsed.username or "root")
        password = unquote(parsed.password or "")
        database = (parsed.path or "/aptguide3").lstrip("/")
        return host, port, user, password, database

    # Fallback to individual env vars
    return (
        os.getenv("MYSQL_HOST", "localhost"),
        int(os.getenv("MYSQL_PORT", "3306")),
        os.getenv("MYSQL_USER", "root"),
        os.getenv("MYSQL_PASSWORD", os.getenv("MYSQL_ROOT_PASSWORD", "")),
        os.getenv("MYSQL_DATABASE", "aptguide3"),
    )


async def main() -> int:
    try:
        import asyncmy
    except ImportError:
        print("ERROR: asyncmy is not installed. Run: pip install asyncmy")
        return 1

    host, port, user, password, database = _resolve_dsn()

    schema_path = (
        Path(__file__).resolve().parent.parent
        / "src" / "aptguide3" / "database" / "schema.sql"
    )
    if not schema_path.exists():
        print(f"ERROR: schema file not found at {schema_path}")
        return 1

    raw_sql = schema_path.read_text(encoding="utf-8")
    statements = [s.strip() for s in raw_sql.split(";") if s.strip()]

    if not statements:
        print("WARNING: no SQL statements found in schema.sql")
        return 0

    print(f"Connecting to MySQL at {host}:{port} (database={database}) ...")
    try:
        conn = await asyncmy.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
        )
    except Exception as exc:
        print(f"ERROR: failed to connect to MySQL: {exc}")
        return 1

    success = 0
    failed = 0

    try:
        async with conn.cursor() as cur:
            for stmt in statements:
                # Extract table name from CREATE TABLE statement
                match = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\S+)", stmt, re.IGNORECASE)
                table_name = match.group(1) if match else "<unknown>"

                try:
                    await cur.execute(stmt)
                    print(f"  OK  {table_name}")
                    success += 1
                except Exception as exc:
                    print(f"  FAIL {table_name}: {exc}")
                    failed += 1
    finally:
        conn.close()

    print(f"\nDone: {success} succeeded, {failed} failed out of {len(statements)} statements.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
