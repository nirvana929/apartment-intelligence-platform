import pytest

from aptguide3.persistence.room_identity_repo import InMemoryRoomIdentityRepository
from aptguide3.rag.room_identity import RoomIdentity


@pytest.fixture
def repo() -> InMemoryRoomIdentityRepository:
    return InMemoryRoomIdentityRepository()


@pytest.mark.asyncio
async def test_get_by_source_returns_none_when_empty(repo: InMemoryRoomIdentityRepository) -> None:
    result = await repo.get_by_source("wechat", "wx-1")
    assert result is None


@pytest.mark.asyncio
async def test_upsert_and_get_by_source(repo: InMemoryRoomIdentityRepository) -> None:
    identity = RoomIdentity(
        source_system="wechat",
        source_record_id="wx-1",
        canonical_room_id="room-canon-1",
        business_room_id="101",
        verification_status="verified",
        match_method="direct_id",
        match_confidence=1.0,
    )
    await repo.upsert_mapping(identity)
    result = await repo.get_by_source("wechat", "wx-1")
    assert result is not None
    assert result.source_record_id == "wx-1"
    assert result.business_room_id == "101"
    assert result.verification_status == "verified"


@pytest.mark.asyncio
async def test_upsert_overwrites_existing(repo: InMemoryRoomIdentityRepository) -> None:
    identity_v1 = RoomIdentity(
        source_system="wechat",
        source_record_id="wx-2",
        verification_status="unmapped",
    )
    await repo.upsert_mapping(identity_v1)

    identity_v2 = RoomIdentity(
        source_system="wechat",
        source_record_id="wx-2",
        verification_status="candidate",
        match_method="field_similarity",
        match_confidence=0.8,
    )
    await repo.upsert_mapping(identity_v2)

    result = await repo.get_by_source("wechat", "wx-2")
    assert result is not None
    assert result.verification_status == "candidate"
    assert result.match_confidence == 0.8


@pytest.mark.asyncio
async def test_get_by_source_different_system_returns_none(repo: InMemoryRoomIdentityRepository) -> None:
    identity = RoomIdentity(source_system="wechat", source_record_id="wx-3")
    await repo.upsert_mapping(identity)
    result = await repo.get_by_source("other_system", "wx-3")
    assert result is None


@pytest.mark.asyncio
async def test_multiple_identities_stored_independently(repo: InMemoryRoomIdentityRepository) -> None:
    for i in range(5):
        await repo.upsert_mapping(
            RoomIdentity(source_system="wechat", source_record_id=f"wx-{i}")
        )
    assert len(repo._items) == 5
    for i in range(5):
        result = await repo.get_by_source("wechat", f"wx-{i}")
        assert result is not None
        assert result.source_record_id == f"wx-{i}"
