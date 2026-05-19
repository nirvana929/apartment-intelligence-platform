from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel


class RoomCard(BaseModel):
    room_id: int
    rent: float = 0.0
    payment_types: list[str] = []
    tags: list[str] = []
    facilities: list[str] = []


class LeaseClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8081",
        timeout: float = 5.0,
        internal_token: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._headers: dict[str, str] = {}
        if internal_token:
            self._headers["X-Internal-Token"] = internal_token

    async def get_room(self, room_id: int) -> dict | None:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            try:
                resp = await client.get(
                    f"/internal/ai/tools/room/{room_id}",
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("data") if isinstance(data.get("data"), dict) else None
            except (httpx.HTTPError, Exception):
                return None

    async def validate_rooms(self, room_ids: list[int], filters: dict[str, Any]) -> list[dict[str, Any]]:
        if not room_ids:
            return []
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            try:
                payload = {"roomIds": room_ids, **_to_camel_filters(filters)}
                resp = await client.post(
                    "/internal/ai/tools/room/search",
                    json=payload,
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()
                rooms = data.get("data", {})
                if isinstance(rooms, dict):
                    rooms = rooms.get("rooms", [])
                if not isinstance(rooms, list):
                    return []
                return [_to_snake_dict(r) for r in rooms if _matches_filters(r, filters)]
            except (httpx.HTTPError, Exception):
                return []

    async def create_appointment(
        self,
        user_id: int,
        apartment_id: int,
        appointment_time: str,
        remark: str = "",
    ) -> dict[str, Any]:
        """Create an appointment. Returns ``{"ok": True, "data": ...}`` or ``{"ok": False, "error": "..."}``."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            try:
                resp = await client.post(
                    "/internal/ai/tools/appointment/create",
                    json={"apartmentId": apartment_id, "appointmentTime": appointment_time, "remark": remark},
                    headers={**self._headers, "X-User-Id": str(user_id)},
                )
                resp.raise_for_status()
                body = resp.json()
                if body.get("code") == 0:
                    return {"ok": True, "data": _to_snake_dict(body.get("data"))}
                return {"ok": False, "error": body.get("message", "unknown error")}
            except (httpx.HTTPError, Exception) as exc:
                return {"ok": False, "error": str(exc)}

    async def list_appointments(self, user_id: int) -> list[dict[str, Any]]:
        """List appointments for the given user. Returns a list of dicts, or ``[]`` on failure."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            try:
                resp = await client.get(
                    "/internal/ai/tools/appointment/list-mine",
                    headers={**self._headers, "X-User-Id": str(user_id)},
                )
                resp.raise_for_status()
                body = resp.json()
                if body.get("code") == 0:
                    data = body.get("data", [])
                    if isinstance(data, list):
                        return [_to_snake_dict(r) for r in data]
                return []
            except (httpx.HTTPError, Exception):
                return []

    async def list_leases(self, user_id: int) -> list[dict[str, Any]]:
        """List leases for the given user. Returns a list of dicts, or ``[]`` on failure."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            try:
                resp = await client.get(
                    "/internal/ai/tools/lease/list-mine",
                    headers={**self._headers, "X-User-Id": str(user_id)},
                )
                resp.raise_for_status()
                body = resp.json()
                if body.get("code") == 0:
                    data = body.get("data", [])
                    if isinstance(data, list):
                        return [_to_snake_dict(r) for r in data]
                return []
            except (httpx.HTTPError, Exception):
                return []


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _to_camel_filters(filters: dict[str, Any]) -> dict[str, Any]:
    return {_to_camel(k): v for k, v in filters.items()}


def _to_snake(s: str) -> str:
    import re
    return re.sub(r"([A-Z])", r"_\1", s).lower().lstrip("_")


def _to_snake_dict(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {_to_snake(k): _to_snake_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_snake_dict(i) for i in obj]
    return obj


def _matches_filters(room: dict[str, Any], filters: dict[str, Any]) -> bool:
    snake_room = _to_snake_dict(room)
    max_rent = filters.get("max_rent")
    if max_rent is not None:
        rent = snake_room.get("rent", 0)
        if isinstance(rent, (int, float)) and rent > max_rent:
            return False
    payment_type = filters.get("payment_type")
    if payment_type is not None:
        room_types = snake_room.get("payment_types", [])
        if isinstance(payment_type, str) and payment_type not in room_types:
            return False
    return True
