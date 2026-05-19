from __future__ import annotations

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.memory import MemoryProcedure


class StubMemoryRepo:
    """In-memory stub for MemoryRepositoryContract."""

    def __init__(self, stored: list[dict] | None = None) -> None:
        self._stored: list[dict] = stored if stored is not None else []
        self.upsert_calls: list[dict] = []

    async def list_memories(self, user_id: str) -> list[dict]:
        return [m for m in self._stored if m["user_id"] == user_id]

    async def upsert_memory(
        self, memory_id: str, user_id: str, kind: str, key_name: str, value_json: dict,
    ) -> None:
        self.upsert_calls.append({
            "memory_id": memory_id,
            "user_id": user_id,
            "kind": kind,
            "key_name": key_name,
            "value_json": value_json,
        })
        # Simulate upsert: replace existing or append
        self._stored = [m for m in self._stored if m["memory_id"] != memory_id]
        self._stored.append({
            "memory_id": memory_id,
            "user_id": user_id,
            "kind": kind,
            "key_name": key_name,
            "value_json": value_json,
        })


# -- fixtures --

def _frame(user_id: str | None = "u-1") -> ConversationFrame:
    return ConversationFrame(message="test", session_id="s-1", user_id=user_id)


def _understanding(action: str = "list", hard_filters: dict | None = None) -> UnderstandingResult:
    return UnderstandingResult(
        raw_message="test",
        route="memory",
        task="memory",
        action=action,
        hard_filters=hard_filters or {},
    )


# -- tests --

def test_no_memory_repo_returns_unavailable():
    proc = MemoryProcedure(memory_repo=None)

    result = proc.run(_frame(), _understanding())

    assert result.phase == "memory"
    assert "不可用" in result.message
    assert result.metadata["available"] is False


def test_no_user_id_returns_login_prompt():
    proc = MemoryProcedure(memory_repo=StubMemoryRepo())

    result = proc.run(_frame(user_id=None), _understanding())

    assert result.phase == "memory"
    assert "登录" in result.message
    assert result.metadata["needs_login"] is True


def test_save_preference_success():
    repo = StubMemoryRepo()
    proc = MemoryProcedure(memory_repo=repo)
    u = _understanding(
        action="update_preference",
        hard_filters={"preference_key": "朝向", "preference_value": "朝南"},
    )

    result = proc.run(_frame(), u)

    assert result.phase == "memory"
    assert "已记住" in result.message
    assert result.metadata["saved"] is True
    assert result.metadata["key"] == "朝向"
    assert len(repo.upsert_calls) == 1
    call = repo.upsert_calls[0]
    assert call["memory_id"] == "u-1:preference:朝向"
    assert call["kind"] == "preference"
    assert call["value_json"] == {"value": "朝南"}


def test_save_preference_missing_fields_returns_ask():
    proc = MemoryProcedure(memory_repo=StubMemoryRepo())
    u = _understanding(action="update_preference", hard_filters={})

    result = proc.run(_frame(), u)

    assert result.phase == "memory"
    assert "请告诉我" in result.message
    assert result.metadata["needs_fields"] is True


def test_save_preference_missing_value_returns_ask():
    proc = MemoryProcedure(memory_repo=StubMemoryRepo())
    u = _understanding(
        action="update_preference",
        hard_filters={"preference_key": "朝向"},
    )

    result = proc.run(_frame(), u)

    assert result.metadata["needs_fields"] is True


def test_list_memories_with_results():
    stored = [
        {
            "memory_id": "u-1:preference:朝向",
            "user_id": "u-1",
            "kind": "preference",
            "key_name": "朝向",
            "value_json": {"value": "朝南"},
        },
        {
            "memory_id": "u-1:preference:楼层",
            "user_id": "u-1",
            "kind": "preference",
            "key_name": "楼层",
            "value_json": {"value": "高楼层"},
        },
    ]
    proc = MemoryProcedure(memory_repo=StubMemoryRepo(stored=stored))

    result = proc.run(_frame(), _understanding(action="list"))

    assert result.phase == "memory"
    assert "朝向" in result.message
    assert "朝南" in result.message
    assert "楼层" in result.message
    assert result.metadata["memory_count"] == 2


def test_list_memories_empty():
    proc = MemoryProcedure(memory_repo=StubMemoryRepo())

    result = proc.run(_frame(), _understanding(action="list"))

    assert result.phase == "memory"
    assert "暂无" in result.message
    assert result.metadata["memory_count"] == 0


def test_delete_preference_returns_ack():
    proc = MemoryProcedure(memory_repo=StubMemoryRepo())

    result = proc.run(_frame(), _understanding(action="delete_preference"))

    assert result.phase == "memory"
    assert "已删除" in result.message
    assert result.metadata["deleted"] is True


def test_unknown_action_falls_back_to_list():
    proc = MemoryProcedure(memory_repo=StubMemoryRepo())

    result = proc.run(_frame(), _understanding(action="search"))

    assert result.phase == "memory"
    assert "暂无" in result.message
