from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def build_engine(mysql_dsn: str):
    # ChatService is currently synchronous and bridges async repositories with
    # asyncio.run(). Avoid reusing async DB connections across those short-lived
    # event loops until the API/application path is fully async.
    return create_async_engine(mysql_dsn, pool_pre_ping=True, poolclass=NullPool)


def build_sessionmaker(mysql_dsn: str) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(build_engine(mysql_dsn), expire_on_commit=False)


async def iter_session(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        yield session
