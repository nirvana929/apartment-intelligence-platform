from __future__ import annotations

from typing import Any

import httpx

from aptguide3.config import Settings


async def build_readiness_report(settings: Settings, *, live: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = [
        {"name": "mysql_config", "ok": bool(settings.mysql_dsn), "required": True},
        {"name": "redis_config", "ok": bool(settings.redis_url), "required": True},
        {"name": "lease_config", "ok": bool(settings.lease_base_url), "required": True},
        {"name": "vector_config", "ok": bool(settings.vector_uri), "required": True},
        {
            "name": "llm_config",
            "ok": bool(settings.llm_api_key.get_secret_value()),
            "required": False,
        },
        {
            "name": "embedding_config",
            "ok": bool(settings.embedding_api_key.get_secret_value()),
            "required": False,
        },
    ]

    if live:
        await _probe_connectivity(settings, checks)

    required_ok = all(c["ok"] for c in checks if c["required"])
    return {"ready": required_ok, "checks": checks}


async def _probe_connectivity(settings: Settings, checks: list[dict[str, Any]]) -> None:
    """Add live connectivity probes to checks.

    Each probe is wrapped in its own try/except so one failure cannot
    cascade into another.  On failure the check's ``ok`` flag is flipped
    to ``False`` and a ``probe`` key describes the error; on success the
    ``probe`` key is set to ``"ok"``.
    """
    check_map: dict[str, dict[str, Any]] = {c["name"]: c for c in checks}

    # MySQL probe
    if settings.mysql_dsn:
        try:
            from sqlalchemy import text

            from aptguide3.database.database import build_sessionmaker

            sm = build_sessionmaker(settings.mysql_dsn)
            async with sm() as session:
                await session.execute(text("SELECT 1"))
            check_map["mysql_config"]["probe"] = "ok"
        except Exception as exc:  # noqa: BLE001
            check_map["mysql_config"]["probe"] = f"error: {exc}"
            check_map["mysql_config"]["ok"] = False

    # Redis probe
    if settings.redis_url:
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.redis_url)
            await r.ping()
            await r.aclose()
            check_map["redis_config"]["probe"] = "ok"
        except Exception as exc:  # noqa: BLE001
            check_map["redis_config"]["probe"] = f"error: {exc}"
            check_map["redis_config"]["ok"] = False

    # Lease service probe
    if settings.lease_base_url:
        try:
            headers: dict[str, str] = {}
            token = settings.internal_token.get_secret_value()
            if token:
                headers["X-Internal-Token"] = token
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    f"{settings.lease_base_url}/internal/ai/tools/health",
                    headers=headers,
                )
                resp.raise_for_status()
            check_map["lease_config"]["probe"] = "ok"
        except Exception as exc:  # noqa: BLE001
            check_map["lease_config"]["probe"] = f"error: {exc}"
            check_map["lease_config"]["ok"] = False

    # Milvus probe
    if settings.vector_uri:
        try:
            from pymilvus import MilvusClient

            mc = MilvusClient(uri=settings.vector_uri)
            mc.list_collections()
            mc.close()
            check_map["vector_config"]["probe"] = "ok"
        except Exception as exc:  # noqa: BLE001
            check_map["vector_config"]["probe"] = f"error: {exc}"
            check_map["vector_config"]["ok"] = False
