from aptguide2.harness.tools.builtins import build_default_tool_registry

EXPECTED_NAMES = {
    "lease.health",
    "room.search",
    "room.detail",
    "kb.search",
    "trace.record",
    "appointment.create",
    "appointment.list_mine",
    "lease.list_mine",
    "appointment.cancel",
}


def test_default_registry_has_all_mvp_tools():
    registry = build_default_tool_registry()
    assert set(registry.names()) == EXPECTED_NAMES


def test_default_registry_confirmed_tools():
    registry = build_default_tool_registry()
    confirmed = registry.requires_confirmation()
    confirmed_names = {c.name for c in confirmed}
    assert "appointment.create" in confirmed_names
    assert "appointment.cancel" in confirmed_names


def test_default_registry_lease_tools():
    registry = build_default_tool_registry()
    lease_tools = registry.by_backend("lease")
    lease_names = {d.name for d in lease_tools}
    assert "room.search" in lease_names
    assert "lease.health" in lease_names
