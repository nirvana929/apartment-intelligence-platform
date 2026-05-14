from __future__ import annotations

from aptguide2.harness.tools.contracts import ToolDefinition
from aptguide2.harness.tools.registry import ToolRegistry

MVP_TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="lease.health",
        backend="lease",
        permission="public",
        input_schema="LeaseHealthInput",
        output_schema="LeaseHealthOutput",
        timeout_seconds=3.0,
        description="Check lease backend health.",
    ),
    ToolDefinition(
        name="room.search",
        backend="lease",
        permission="public",
        input_schema="RoomSearchInput",
        output_schema="RoomSearchOutput",
        timeout_seconds=5.0,
        description="Search rooms via lease backend.",
    ),
    ToolDefinition(
        name="room.detail",
        backend="lease",
        permission="public",
        input_schema="RoomDetailInput",
        output_schema="RoomDetailOutput",
        timeout_seconds=5.0,
        description="Get room detail by ID.",
    ),
    ToolDefinition(
        name="kb.search",
        backend="vector",
        permission="public",
        input_schema="KBSearchInput",
        output_schema="KBSearchOutput",
        timeout_seconds=5.0,
        description="Search knowledge base via vector adapter.",
    ),
    ToolDefinition(
        name="trace.record",
        backend="internal",
        permission="public",
        input_schema="TraceRecordInput",
        output_schema="TraceRecordOutput",
        timeout_seconds=1.0,
        description="Record a trace stage.",
    ),
    ToolDefinition(
        name="appointment.create",
        backend="lease",
        permission="user",
        input_schema="AppointmentCreateInput",
        output_schema="AppointmentCreateOutput",
        requires_user=True,
        requires_confirmation=True,
        timeout_seconds=10.0,
        description="Create a viewing appointment.",
    ),
    ToolDefinition(
        name="appointment.list_mine",
        backend="lease",
        permission="user",
        input_schema="AppointmentListMineInput",
        output_schema="AppointmentListMineOutput",
        requires_user=True,
        timeout_seconds=5.0,
        description="List user's appointments.",
    ),
    ToolDefinition(
        name="lease.list_mine",
        backend="lease",
        permission="user",
        input_schema="LeaseListMineInput",
        output_schema="LeaseListMineOutput",
        requires_user=True,
        timeout_seconds=5.0,
        description="List user's leases.",
    ),
    ToolDefinition(
        name="appointment.cancel",
        backend="lease",
        permission="user",
        input_schema="AppointmentCancelInput",
        output_schema="AppointmentCancelOutput",
        requires_user=True,
        requires_confirmation=True,
        timeout_seconds=10.0,
        description="Cancel one of the current user's viewing appointments.",
    ),
]


def build_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for definition in MVP_TOOL_DEFINITIONS:
        registry.register(definition)
    return registry
