from __future__ import annotations

from dataclasses import dataclass

from aptguide3.config import Settings


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    display_name: str = ""
    auth_mode: str = "dev"


class AuthResolver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def resolve(
        self,
        *,
        authorization: str | None,
        x_user_id: str | None,
        x_internal_token: str | None,
        requested_user_id: str | None,
    ) -> AuthContext:
        if self.settings.auth_mode == "dev":
            return AuthContext(
                user_id=requested_user_id or self.settings.dev_user_id,
                display_name=self.settings.dev_user_name,
                auth_mode="dev",
            )
        if self.settings.auth_mode != "internal_header":
            raise PermissionError(f"unsupported auth mode: {self.settings.auth_mode}")
        expected = self.settings.internal_token.get_secret_value()
        if self.settings.internal_token_required and x_internal_token != expected:
            raise PermissionError("invalid internal token")
        if not x_user_id:
            raise PermissionError("missing X-User-Id")
        return AuthContext(user_id=x_user_id, auth_mode="internal_header")
