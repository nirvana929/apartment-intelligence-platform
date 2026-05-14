"""Lease adapter — bridges AptGuide 2.0 to the lease Java backend internal tools."""

from __future__ import annotations

import re
from typing import Any

import httpx

from aptguide2.core.config import Settings


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    s = re.sub(r"([A-Z])", r"_\1", name).lower()
    return s.lstrip("_")


def convert_keys_to_camel(obj: Any) -> Any:
    """Recursively convert dict keys from snake_case to camelCase."""
    if isinstance(obj, dict):
        return {_snake_to_camel(k): convert_keys_to_camel(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_keys_to_camel(item) for item in obj]
    return obj


def convert_keys_to_snake(obj: Any) -> Any:
    """Recursively convert dict keys from camelCase to snake_case."""
    if isinstance(obj, dict):
        return {_camel_to_snake(k): convert_keys_to_snake(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_keys_to_snake(item) for item in obj]
    return obj


class LeaseAdapterError(Exception):
    """Raised when the lease backend returns an error."""

    def __init__(self, code: str, message: str, recoverable: bool = True):
        self.code = code
        self.message = message
        self.recoverable = recoverable
        super().__init__(f"[{code}] {message}")


class LeaseAdapter:
    """Adapter for calling lease internal tools endpoints."""

    def __init__(self, settings: Settings | None = None, base_url: str | None = None, timeout: float | None = None, internal_token: str = ""):
        if settings:
            self.base_url = settings.lease_base_url.rstrip("/")
            self.timeout = settings.lease_timeout_seconds
            self.internal_token = settings.lease_internal_token
        else:
            self.base_url = (base_url or "http://localhost:8081").rstrip("/")
            self.timeout = timeout or 5.0
            self.internal_token = internal_token
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.internal_token:
                headers["X-Internal-Token"] = self.internal_token
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _handle_response(self, resp: httpx.Response, tool_name: str) -> dict:
        """Check lease Java response envelope and raise on error."""
        resp.raise_for_status()
        data = resp.json()
        code = data.get("code", 0)
        if code not in (0, 200):
            raise LeaseAdapterError(
                code=data.get("errorCode", "LEASE_ERROR"),
                message=data.get("message", data.get("msg", f"lease {tool_name} failed")),
            )
        return data

    async def health(self) -> bool:
        """Check lease backend health."""
        client = await self._get_client()
        try:
            resp = await client.get("/internal/ai/tools/health")
            data = self._handle_response(resp, "health")
            return data.get("data", {}).get("healthy", False) if isinstance(data.get("data"), dict) else bool(data.get("data"))
        except (httpx.HTTPError, LeaseAdapterError):
            return False

    async def sync_rooms(self, limit: int = 200) -> list[dict]:
        """Fetch room sync DTOs from lease.

        Returns list of room dicts in snake_case.
        """
        client = await self._get_client()
        resp = await client.get("/internal/ai/tools/sync/rooms", params={"limit": limit})
        data = self._handle_response(resp, "sync_rooms")
        rooms_data = data.get("data", [])
        # Handle both list and dict with "rooms" key
        if isinstance(rooms_data, dict):
            rooms = rooms_data.get("rooms", [])
        elif isinstance(rooms_data, list):
            rooms = rooms_data
        else:
            rooms = []
        return [convert_keys_to_snake(r) for r in rooms]

    async def search_rooms(self, payload: dict) -> dict:
        """Search rooms through lease.

        Input payload uses snake_case keys; automatically converted to camelCase
        for the Java backend. Response is converted back to snake_case.
        """
        client = await self._get_client()
        camel_payload = convert_keys_to_camel(payload)
        resp = await client.post("/internal/ai/tools/room/search", json=camel_payload)
        data = self._handle_response(resp, "room.search")
        result = data.get("data", {})
        return convert_keys_to_snake(result) if isinstance(result, dict) else {}

    async def get_room_detail(self, room_id: int) -> dict:
        """Get room detail from lease.

        Returns room detail dict in snake_case.
        """
        client = await self._get_client()
        resp = await client.get(f"/internal/ai/tools/room/{room_id}")
        data = self._handle_response(resp, "room.detail")
        result = data.get("data", {})
        return convert_keys_to_snake(result) if isinstance(result, dict) else {}

    async def create_appointment(self, payload: dict) -> dict:
        """Create a viewing appointment through lease.

        Input payload uses snake_case keys; automatically converted to camelCase
        for the Java backend. Response is converted back to snake_case.
        """
        client = await self._get_client()
        camel_payload = convert_keys_to_camel(payload)
        resp = await client.post("/internal/ai/tools/appointment/create", json=camel_payload)
        data = self._handle_response(resp, "appointment.create")
        result = data.get("data", {})
        return convert_keys_to_snake(result) if isinstance(result, dict) else {}

    async def list_appointments(self, payload: dict) -> dict:
        """List user's appointments through lease.

        Input payload uses snake_case keys; automatically converted to camelCase
        for the Java backend. Response is converted back to snake_case.
        """
        client = await self._get_client()
        camel_payload = convert_keys_to_camel(payload)
        resp = await client.post("/internal/ai/tools/appointment/list", json=camel_payload)
        data = self._handle_response(resp, "appointment.list")
        result = data.get("data", {})
        return convert_keys_to_snake(result) if isinstance(result, dict) else {}

    async def cancel_appointment(self, payload: dict) -> dict:
        """Cancel a viewing appointment through lease."""
        client = await self._get_client()
        camel_payload = convert_keys_to_camel(payload)
        resp = await client.post("/internal/ai/tools/appointment/cancel", json=camel_payload)
        data = self._handle_response(resp, "appointment.cancel")
        result = data.get("data", {})
        return convert_keys_to_snake(result) if isinstance(result, dict) else {}

    async def list_leases(self, payload: dict) -> dict:
        """List user's leases through lease."""
        client = await self._get_client()
        camel_payload = convert_keys_to_camel(payload)
        resp = await client.post("/internal/ai/tools/lease/list", json=camel_payload)
        data = self._handle_response(resp, "lease.list")
        result = data.get("data", {})
        return convert_keys_to_snake(result) if isinstance(result, dict) else {}
