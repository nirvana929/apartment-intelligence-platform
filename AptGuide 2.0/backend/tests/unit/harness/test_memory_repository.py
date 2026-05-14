from aptguide2.harness.memory_repository import MemoryCandidate, MemoryRepository


class FakeMemoryRepository(MemoryRepository):
    def __init__(self) -> None:
        super().__init__()


async def test_profile_update_and_delete_contract() -> None:
    repo = FakeMemoryRepository()

    await repo.upsert_profile("u1", {"budget_max": 2500, "preferences": ["安静"]})
    assert await repo.get_profile("u1") == {"budget_max": 2500, "preferences": ["安静"]}

    await repo.delete_profile_key("u1", "budget_max", session_id="s1")
    assert await repo.get_profile("u1") == {"preferences": ["安静"]}
    assert repo.audit[-1]["event_type"] == "memory.profile_delete"


async def test_candidate_confirmation_contract() -> None:
    repo = FakeMemoryRepository()
    candidate = await repo.create_candidate(
        user_id="u1",
        session_id="s1",
        kind="preference",
        payload={"preferences": ["近地铁"]},
    )

    assert isinstance(candidate, MemoryCandidate)
    assert candidate.status == "pending"

    await repo.confirm_candidate(candidate.candidate_id)
    assert repo.candidates[candidate.candidate_id]["status"] == "confirmed"


async def test_get_empty_profile() -> None:
    repo = FakeMemoryRepository()
    assert await repo.get_profile("nonexistent") == {}
