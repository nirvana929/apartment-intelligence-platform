from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aptguide3.persistence.handoff_repo import InMemoryHandoffRepo
from aptguide3.persistence.memory_repo import InMemoryMemoryRepo
from aptguide3.persistence.pending_action_repo import InMemoryPendingActionRepo


@pytest.mark.asyncio
async def test_memory_repo_upsert_and_list():
    repo = InMemoryMemoryRepo()
    await repo.upsert_memory("m1", "u1", "preference", "color", {"value": "blue"})
    await repo.upsert_memory("m2", "u1", "fact", "name", {"value": "Alice"})
    await repo.upsert_memory("m3", "u2", "preference", "lang", {"value": "zh"})

    u1_memories = await repo.list_memories("u1")
    assert len(u1_memories) == 2
    keys = {m["key_name"] for m in u1_memories}
    assert keys == {"color", "name"}
    assert all(m["kind"] in ("preference", "fact") for m in u1_memories)

    u2_memories = await repo.list_memories("u2")
    assert len(u2_memories) == 1
    assert u2_memories[0]["memory_id"] == "m3"
    assert u2_memories[0]["value_json"] == {"value": "zh"}


@pytest.mark.asyncio
async def test_memory_repo_upsert_overwrites():
    repo = InMemoryMemoryRepo()
    await repo.upsert_memory("m1", "u1", "preference", "color", {"value": "blue"})
    await repo.upsert_memory("m1", "u1", "preference", "color", {"value": "red"})

    memories = await repo.list_memories("u1")
    assert len(memories) == 1
    assert memories[0]["value_json"] == {"value": "red"}


@pytest.mark.asyncio
async def test_handoff_repo_create_ticket_and_list():
    repo = InMemoryHandoffRepo()
    await repo.create_ticket("t1", "s1", "u1", "escalation", {"text": "help"})
    await repo.create_ticket("t2", "s2", "u2", "timeout", {"text": "slow"})

    open_tickets = await repo.list_tickets()
    assert len(open_tickets) == 2
    ids = {t["ticket_id"] for t in open_tickets}
    assert ids == {"t1", "t2"}


@pytest.mark.asyncio
async def test_handoff_repo_list_tickets_filtered_by_status():
    repo = InMemoryHandoffRepo()
    await repo.create_ticket("t1", "s1", "u1", "escalation", {"text": "help"})
    await repo.create_ticket("t2", "s2", "u2", "timeout", {"text": "slow"})

    # Resolve one ticket via the legacy sync method
    repo._store["t1"]["status"] = "resolved"

    open_tickets = await repo.list_tickets(status="open")
    assert len(open_tickets) == 1
    assert open_tickets[0]["ticket_id"] == "t2"

    resolved = await repo.list_tickets(status="resolved")
    assert len(resolved) == 1
    assert resolved[0]["ticket_id"] == "t1"


@pytest.mark.asyncio
async def test_pending_action_save_load_mark_completed():
    repo = InMemoryPendingActionRepo()
    expires = datetime(2026, 6, 1, tzinfo=UTC)

    await repo.save_pending_action("pa1", "s1", "u1", "approval", {"item": "x"}, expires)
    loaded = await repo.load_pending_action("pa1")
    assert loaded is not None
    assert loaded["pending_action_id"] == "pa1"
    assert loaded["action_type"] == "approval"
    assert loaded["status"] == "pending"
    assert "2026-06-01" in loaded["expires_at"]

    await repo.mark_completed("pa1")
    loaded = await repo.load_pending_action("pa1")
    assert loaded["status"] == "completed"


@pytest.mark.asyncio
async def test_pending_action_load_nonexistent_returns_none():
    repo = InMemoryPendingActionRepo()
    result = await repo.load_pending_action("nonexistent")
    assert result is None
