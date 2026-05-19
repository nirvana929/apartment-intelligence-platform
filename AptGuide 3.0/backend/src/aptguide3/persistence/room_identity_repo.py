from __future__ import annotations

from typing import Protocol

from aptguide3.rag.room_identity import RoomIdentity


class RoomIdentityRepository(Protocol):
    async def get_by_source(self, source_system: str, source_record_id: str) -> RoomIdentity | None:
        raise NotImplementedError

    async def upsert_mapping(self, identity: RoomIdentity) -> None:
        raise NotImplementedError


class InMemoryRoomIdentityRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], RoomIdentity] = {}

    async def get_by_source(self, source_system: str, source_record_id: str) -> RoomIdentity | None:
        return self._items.get((source_system, source_record_id))

    async def upsert_mapping(self, identity: RoomIdentity) -> None:
        self._items[(identity.source_system, identity.source_record_id)] = identity
