import pytest
import respx
import httpx
from httpx import Response

from aptguide2.api.auth import AuthContext, AuthResolver
from aptguide2.core.config import Settings


def test_dev_auth_uses_configured_dev_user_and_allows_display_name() -> None:
    settings = Settings(auth_mode="dev", dev_user_id="u-dev", dev_user_name="测试用户")
    resolver = AuthResolver(settings)

    ctx = resolver.resolve_sync(authorization=None, requested_user_id="forged-user")

    assert ctx == AuthContext(user_id="u-dev", display_name="测试用户", auth_mode="dev")


@respx.mock
@pytest.mark.asyncio
async def test_lease_token_auth_resolves_user_from_lease_backend() -> None:
    settings = Settings(
        auth_mode="lease_token",
        lease_base_url="http://lease.test",
        lease_userinfo_path="/app/info",
    )
    respx.get("http://lease.test/app/info").mock(
        return_value=Response(200, json={"code": 200, "data": {"id": 42, "nickname": "张三"}})
    )

    ctx = await AuthResolver(settings).resolve("Bearer token-abc", requested_user_id="999")

    assert ctx.user_id == "42"
    assert ctx.display_name == "张三"
    assert ctx.auth_mode == "lease_token"


@respx.mock
@pytest.mark.asyncio
async def test_lease_token_auth_ignores_requested_user_id() -> None:
    settings = Settings(
        auth_mode="lease_token",
        lease_base_url="http://lease.test",
        lease_userinfo_path="/app/info",
    )
    respx.get("http://lease.test/app/info").mock(
        return_value=Response(200, json={"code": 200, "data": {"id": 7, "nickname": "李四"}})
    )

    ctx = await AuthResolver(settings).resolve("Bearer legit-token", requested_user_id="forged-999")

    assert ctx.user_id == "7"
    assert ctx.display_name == "李四"


@pytest.mark.asyncio
async def test_lease_token_auth_rejects_missing_token() -> None:
    settings = Settings(auth_mode="lease_token")

    with pytest.raises(PermissionError, match="missing bearer token"):
        await AuthResolver(settings).resolve(None, requested_user_id=None)


@respx.mock
@pytest.mark.asyncio
async def test_lease_token_auth_converts_http_status_error() -> None:
    settings = Settings(
        auth_mode="lease_token",
        lease_base_url="http://lease.test",
        lease_userinfo_path="/app/info",
    )
    respx.get("http://lease.test/app/info").mock(return_value=Response(401, json={"error": "unauthorized"}))

    with pytest.raises(PermissionError, match="lease token rejected"):
        await AuthResolver(settings).resolve("Bearer bad-token", requested_user_id=None)


@respx.mock
@pytest.mark.asyncio
async def test_lease_token_auth_converts_connection_error() -> None:
    settings = Settings(
        auth_mode="lease_token",
        lease_base_url="http://lease.test",
        lease_userinfo_path="/app/info",
    )
    respx.get("http://lease.test/app/info").mock(side_effect=httpx.ConnectError("connection refused"))

    with pytest.raises(PermissionError, match="lease auth service unavailable"):
        await AuthResolver(settings).resolve("Bearer token-abc", requested_user_id=None)
