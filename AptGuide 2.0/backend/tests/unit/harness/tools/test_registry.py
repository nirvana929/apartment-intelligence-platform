import pytest

from aptguide2.harness.tools.contracts import ToolDefinition
from aptguide2.harness.tools.errors import ToolAlreadyRegisteredError, ToolNotFoundError
from aptguide2.harness.tools.registry import ToolRegistry


def _make_definition(name: str, **kwargs) -> ToolDefinition:
    defaults = dict(
        name=name,
        backend="lease",
        permission="public",
        input_schema="Input",
        output_schema="Output",
    )
    defaults.update(kwargs)
    return ToolDefinition(**defaults)


def test_register_and_get():
    registry = ToolRegistry()
    d = _make_definition("room.search")
    registry.register(d)
    assert registry.get("room.search") is d


def test_duplicate_raises():
    registry = ToolRegistry()
    registry.register(_make_definition("room.search"))
    with pytest.raises(ToolAlreadyRegisteredError):
        registry.register(_make_definition("room.search"))


def test_missing_raises():
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError):
        registry.get("missing")


def test_names_sorted():
    registry = ToolRegistry()
    registry.register(_make_definition("b.tool"))
    registry.register(_make_definition("a.tool"))
    assert registry.names() == ["a.tool", "b.tool"]


def test_by_backend():
    registry = ToolRegistry()
    registry.register(_make_definition("a", backend="lease"))
    registry.register(_make_definition("b", backend="vector"))
    registry.register(_make_definition("c", backend="lease"))
    assert [d.name for d in registry.by_backend("lease")] == ["a", "c"]


def test_requires_confirmation():
    registry = ToolRegistry()
    registry.register(_make_definition("a"))
    registry.register(_make_definition("b", requires_confirmation=True))
    registry.register(_make_definition("c", requires_confirmation=True))
    assert [d.name for d in registry.requires_confirmation()] == ["b", "c"]
