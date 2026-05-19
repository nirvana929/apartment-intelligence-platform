import pytest

from aptguide3.api.auth import AuthResolver
from aptguide3.config import Settings


@pytest.mark.asyncio
async def test_dev_auth_uses_requested_user_when_allowed():
    settings = Settings(auth_mode="dev", dev_user_id="dev-user-001")
    auth = await AuthResolver(settings).resolve(
        authorization=None,
        x_user_id=None,
        x_internal_token=None,
        requested_user_id="demo-user",
    )
    assert auth.user_id == "demo-user"
    assert auth.auth_mode == "dev"


@pytest.mark.asyncio
async def test_internal_header_auth_ignores_requested_user():
    settings = Settings(
        auth_mode="internal_header",
        internal_token="secret",
        internal_token_required=True,
    )
    auth = await AuthResolver(settings).resolve(
        authorization=None,
        x_user_id="lease-user-1",
        x_internal_token="secret",
        requested_user_id="spoofed-user",
    )
    assert auth.user_id == "lease-user-1"
    assert auth.auth_mode == "internal_header"


@pytest.mark.asyncio
async def test_internal_header_auth_rejects_bad_token():
    settings = Settings(
        auth_mode="internal_header",
        internal_token="secret",
        internal_token_required=True,
    )
    with pytest.raises(PermissionError):
        await AuthResolver(settings).resolve(
            authorization=None,
            x_user_id="lease-user-1",
            x_internal_token="wrong",
            requested_user_id=None,
        )
