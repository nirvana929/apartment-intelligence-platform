from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """健康检查。"""
    return {"status": "ok"}


@router.get("/health/deps")
async def health_deps():
    """依赖健康检查。"""
    import httpx
    from pymilvus import connections

    deps = {}

    # 检查 Milvus
    try:
        connections.connect("default", uri="http://milvus:19530")
        connections.disconnect("default")
        deps["milvus"] = "ok"
    except Exception as e:
        deps["milvus"] = f"error: {e!s}"

    # 检查 lease 后端
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "http://lease-web-app:8081/internal/ai/tools/health",
                headers={"X-Internal-Token": "aptguide-internal-token-2026"},
                timeout=5,
            )
            deps["lease"] = "ok" if resp.status_code == 200 else f"status: {resp.status_code}"
    except Exception as e:
        deps["lease"] = f"error: {e!s}"

    # 检查 Redis
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("redis", 6379))
        sock.close()
        deps["redis"] = "ok" if result == 0 else f"error: connection refused"
    except Exception as e:
        deps["redis"] = f"error: {e!s}"

    all_ok = all(v == "ok" for v in deps.values())
    return {"status": "ok" if all_ok else "degraded", "deps": deps}
