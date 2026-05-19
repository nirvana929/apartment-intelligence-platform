"""Safe metadata-only data inventory generator.

Collects structural metadata from MySQL, Redis, Milvus, and config
WITHOUT dumping actual data values, secrets, PII, or embeddings.

Usage:
    uv run python scripts/generate_data_inventory.py --output ../docs/system/data-inventory/generated --no-values
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import re
from datetime import datetime, timezone
from typing import Any

SENSITIVE_KEY_PATTERNS = {
    "api_key", "apikey", "secret", "token", "password",
    "mysql_dsn", "dsn", "credential", "auth",
}


def _is_sensitive(key: str) -> bool:
    key_lower = key.lower()
    return any(p in key_lower for p in SENSITIVE_KEY_PATTERNS)


def _redact_value(key: str, value: Any) -> Any:
    if _is_sensitive(key):
        return "<redacted>"
    return value


def _sanitize_config(settings: Any) -> dict[str, Any]:
    """Extract config presence and model names without secrets."""
    result = {}
    for field_name in [
        "environment", "service_name", "llm_base_url", "llm_model",
        "embedding_base_url", "embedding_model", "lease_base_url",
        "vector_uri", "auth_mode", "persistence_mode", "redis_url",
        "langsmith_tracing", "langsmith_project", "understanding_diagnostics_enabled",
    ]:
        value = getattr(settings, field_name, None)
        if _is_sensitive(field_name):
            result[field_name] = "<redacted>"
        elif field_name in ("redis_url",) and value:
            result[field_name] = "<set>"
        else:
            result[field_name] = value
    return result


async def _collect_mysql_metadata(dsn: str) -> dict[str, Any]:
    """Collect MySQL schema metadata without row data."""
    try:
        import asyncmy
        # Parse database name from DSN
        db_match = re.search(r"/([^?]+)", dsn)
        db_name = db_match.group(1) if db_match else "unknown"

        # Redact password from DSN
        safe_dsn = re.sub(r"://([^:]+):([^@]+)@", r"://\1:<redacted>@", dsn)

        conn = await asyncmy.connect(
            host=re.search(r"@([^:/]+)", dsn).group(1) if re.search(r"@([^:/]+)", dsn) else "localhost",
            port=int(re.search(r":(\d+)/", dsn).group(1)) if re.search(r":(\d+)/", dsn) else 3306,
            user=re.search(r"://([^:]+)", dsn).group(1) if re.search(r"://([^:]+)", dsn) else "root",
            password=re.search(r":([^@]+)@", dsn).group(1) if re.search(r":([^@]+)@", dsn) else "",
            database=db_name,
        )
        async with conn.cursor() as cur:
            # Get tables
            await cur.execute(
                "SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH "
                "FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s",
                (db_name,),
            )
            tables = []
            for row in await cur.fetchall():
                tables.append({
                    "table_name": row[0],
                    "estimated_rows": row[1],
                    "data_bytes": row[2],
                    "index_bytes": row[3],
                })

            # Get columns per table
            await cur.execute(
                "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY "
                "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME, ORDINAL_POSITION",
                (db_name,),
            )
            columns: dict[str, list[dict]] = {}
            for row in await cur.fetchall():
                table = row[0]
                if table not in columns:
                    columns[table] = []
                columns[table].append({
                    "column": row[1],
                    "type": row[2],
                    "nullable": row[3],
                    "key": row[4],
                })

        conn.close()
        return {
            "status": "ok",
            "dsn": safe_dsn,
            "database": db_name,
            "tables": tables,
            "columns": columns,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


async def _collect_redis_metadata(redis_url: str) -> dict[str, Any]:
    """Collect Redis key pattern metadata without values."""
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(redis_url)
        # SCAN for key patterns
        key_types: dict[str, int] = {}
        key_count = 0
        cursor = 0
        sample_keys: list[str] = []
        for _ in range(100):  # max 100 iterations
            cursor, keys = await client.scan(cursor, count=100)
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else str(key)
                key_count += 1
                if len(sample_keys) < 20:
                    sample_keys.append(key_str)
                try:
                    ktype = await client.type(key)
                    ktype_str = ktype.decode() if isinstance(ktype, bytes) else str(ktype)
                    key_types[ktype_str] = key_types.get(ktype_str, 0) + 1
                except Exception:
                    pass
            if cursor == 0:
                break
        await client.aclose()
        return {
            "status": "ok",
            "total_keys": key_count,
            "key_types": key_types,
            "sample_keys": sample_keys[:20],
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _collect_milvus_metadata(vector_uri: str) -> dict[str, Any]:
    """Collect Milvus collection metadata without vectors or content."""
    try:
        from pymilvus import MilvusClient
        client = MilvusClient(uri=vector_uri)
        collections = client.list_collections()
        result = {}
        for coll_name in collections:
            try:
                desc = client.describe_collection(coll_name)
                stats = client.get_collection_stats(coll_name)
                result[coll_name] = {
                    "description": desc.get("description", ""),
                    "num_entities": stats.get("row_count", "unknown"),
                    "fields": [
                        {"name": f.get("name", ""), "type": str(f.get("type", ""))}
                        for f in desc.get("fields", [])
                    ],
                }
            except Exception as exc:
                result[coll_name] = {"error": str(exc)}
        return {"status": "ok", "collections": result}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def generate_inventory(output_dir: pathlib.Path, no_values: bool = True) -> dict[str, Any]:
    """Generate metadata-only inventory."""
    from aptguide3.config import get_settings
    get_settings.cache_clear()
    settings = get_settings()

    inventory: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "metadata-only" if no_values else "full",
        "config": _sanitize_config(settings),
    }

    # MySQL
    dsn = settings.mysql_dsn
    if dsn and dsn != "mysql+asyncmy://root:change-me@localhost:3306/aptguide3":
        inventory["mysql"] = asyncio.run(_collect_mysql_metadata(dsn))
    else:
        inventory["mysql"] = {"status": "skipped", "reason": "default DSN not configured"}

    # Redis
    if settings.redis_url:
        inventory["redis"] = asyncio.run(_collect_redis_metadata(settings.redis_url))
    else:
        inventory["redis"] = {"status": "skipped", "reason": "redis_url not set"}

    # Milvus
    if settings.vector_uri:
        inventory["milvus"] = _collect_milvus_metadata(settings.vector_uri)
    else:
        inventory["milvus"] = {"status": "skipped", "reason": "vector_uri not set"}

    return inventory


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate safe data inventory")
    parser.add_argument("--output", type=str, default="../docs/system/data-inventory/generated")
    parser.add_argument("--no-values", action="store_true", default=True, help="Exclude actual data values")
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory = generate_inventory(output_dir, no_values=args.no_values)

    # Write JSON
    json_path = output_dir / "inventory.json"
    json_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    # Write Markdown summary
    md_lines = ["# Data Inventory (Auto-Generated)", ""]
    md_lines.append(f"Generated: {inventory['generated_at']}")
    md_lines.append(f"Mode: {inventory['mode']}")
    md_lines.append("")

    # Config
    md_lines.append("## Configuration")
    md_lines.append("")
    for k, v in inventory.get("config", {}).items():
        md_lines.append(f"- `{k}`: {v}")
    md_lines.append("")

    # MySQL
    mysql = inventory.get("mysql", {})
    md_lines.append("## MySQL")
    md_lines.append("")
    if mysql.get("status") == "ok":
        md_lines.append(f"- Database: `{mysql.get('database', '?')}`")
        md_lines.append(f"- Tables: {len(mysql.get('tables', []))}")
        for t in mysql.get("tables", []):
            md_lines.append(f"  - `{t['table_name']}`: ~{t.get('estimated_rows', '?')} rows")
    else:
        md_lines.append(f"- Status: {mysql.get('status')} — {mysql.get('error', mysql.get('reason', ''))}")
    md_lines.append("")

    # Redis
    redis = inventory.get("redis", {})
    md_lines.append("## Redis")
    md_lines.append("")
    if redis.get("status") == "ok":
        md_lines.append(f"- Total keys: {redis.get('total_keys', 0)}")
        for ktype, count in redis.get("key_types", {}).items():
            md_lines.append(f"  - {ktype}: {count}")
    else:
        md_lines.append(f"- Status: {redis.get('status')} — {redis.get('error', redis.get('reason', ''))}")
    md_lines.append("")

    # Milvus
    milvus = inventory.get("milvus", {})
    md_lines.append("## Milvus")
    md_lines.append("")
    if milvus.get("status") == "ok":
        for coll_name, coll_info in milvus.get("collections", {}).items():
            md_lines.append(f"- `{coll_name}`: {coll_info.get('num_entities', '?')} entities")
            for f in coll_info.get("fields", []):
                md_lines.append(f"  - {f['name']}: {f['type']}")
    else:
        md_lines.append(f"- Status: {milvus.get('status')} — {milvus.get('error', milvus.get('reason', ''))}")
    md_lines.append("")

    md_path = output_dir / "inventory.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Inventory written to {output_dir}")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


if __name__ == "__main__":
    main()
