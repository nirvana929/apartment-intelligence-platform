"""Unit tests for MySqlRoomIdentityRepository."""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from aptguide3.database.models import Base
from aptguide3.persistence.mysql_repos import MySqlRoomIdentityRepository
from aptguide3.rag.room_identity import RoomIdentity


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def sessionmaker(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_upsert_and_get(sessionmaker):
    repo = MySqlRoomIdentityRepository(sessionmaker)
    identity = RoomIdentity(
        source_system="wechat",
        source_record_id="WR001",
        canonical_room_id="C001",
        business_system="lease",
        business_room_id="L001",
        verification_status="verified",
        match_method="manual",
        match_confidence=0.95,
    )
    await repo.upsert_mapping(identity)
    result = await repo.get_by_source("wechat", "WR001")
    assert result is not None
    assert result.business_room_id == "L001"
    assert result.verification_status == "verified"


@pytest.mark.asyncio
async def test_get_missing_returns_none(sessionmaker):
    repo = MySqlRoomIdentityRepository(sessionmaker)
    result = await repo.get_by_source("wechat", "NONEXISTENT")
    assert result is None


@pytest.mark.asyncio
async def test_upsert_overwrites(sessionmaker):
    repo = MySqlRoomIdentityRepository(sessionmaker)
    await repo.upsert_mapping(RoomIdentity(
        source_system="wechat", source_record_id="WR002",
        verification_status="candidate",
    ))
    await repo.upsert_mapping(RoomIdentity(
        source_system="wechat", source_record_id="WR002",
        business_room_id="L002", verification_status="verified",
    ))
    result = await repo.get_by_source("wechat", "WR002")
    assert result is not None
    assert result.business_room_id == "L002"
    assert result.verification_status == "verified"
