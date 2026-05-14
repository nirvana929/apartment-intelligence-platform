from __future__ import annotations

from dataclasses import dataclass

import httpx

from aptguide2.core.config import Settings


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    display_name: str = ""
    auth_mode: str = "dev"


class AuthResolver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def resolve_sync(self, authorization: str | None, requested_user_id: str | None) -> AuthContext:
        if self.settings.auth_mode == "dev":
            return AuthContext(
                user_id=self.settings.dev_user_id or requested_user_id or "dev-user-001",
                display_name=self.settings.dev_user_name,
                auth_mode="dev",
            )
        raise RuntimeError("lease_token auth requires async resolution")

    async def resolve(self, authorization: str | None, requested_user_id: str | None) -> AuthContext:
        if self.settings.auth_mode == "dev":
            return self.resolve_sync(authorization, requested_user_id)
        if self.settings.auth_mode != "lease_token":
            raise PermissionError(f"unsupported auth mode: {self.settings.auth_mode}")
        if not authorization or not authorization.lower().startswith("bearer "):
            raise PermissionError("missing bearer token")

        token = authorization.split(" ", 1)[1].strip()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.lease_base_url.rstrip("/"),
                timeout=self.settings.lease_timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.get(self.settings.lease_userinfo_path)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError:
            raise PermissionError("lease token rejected")
        except httpx.HTTPError:
            raise PermissionError("lease auth service unavailable")

        data = payload.get("data", payload)
        user_id = data.get("id") or data.get("user_id") or data.get("userId")
        if user_id is None:
            raise PermissionError("lease token did not resolve user")
        return AuthContext(
            user_id=str(user_id),
            display_name=str(data.get("nickname") or data.get("name") or ""),
            auth_mode="lease_token",
        )
