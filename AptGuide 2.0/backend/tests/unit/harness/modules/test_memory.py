from aptguide2.harness.contracts import ConversationFrame, RouteDecision
from aptguide2.harness.memory_repository import MemoryRepository
from aptguide2.harness.modules.memory import MemoryProcedure


def decision() -> RouteDecision:
    return RouteDecision(task="memory", procedure="memory.profile", confidence=0.9)


async def test_show_profile_requires_user() -> None:
    proc = MemoryProcedure(MemoryRepository())
    frame = ConversationFrame(request_id="r1", session_id="s1", message="我的偏好")

    result = await proc.run_async(frame, decision())

    assert result.phase == "memory_auth_required"


async def test_remember_preference_creates_confirmation_card() -> None:
    repo = MemoryRepository()
    proc = MemoryProcedure(repo)
    frame = ConversationFrame(request_id="r1", session_id="s1", user_id="u1", message="记住我喜欢安静近地铁")

    result = await proc.run_async(frame, decision())

    assert result.phase == "memory_confirmation_required"
    assert result.pending_action["type"] == "memory.profile_update"
    assert result.cards[0]["type"] == "memory_confirmation"


async def test_show_profile_returns_profile() -> None:
    repo = MemoryRepository()
    await repo.upsert_profile("u1", {"preferences": ["安静"]})
    proc = MemoryProcedure(repo)
    frame = ConversationFrame(request_id="r1", session_id="s1", user_id="u1", message="我的偏好")

    result = await proc.run_async(frame, decision())

    assert result.phase == "memory_profile"
    assert result.cards[0]["profile"] == {"preferences": ["安静"]}
