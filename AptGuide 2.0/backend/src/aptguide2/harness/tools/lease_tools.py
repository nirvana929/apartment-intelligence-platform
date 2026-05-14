"""Lease tool executors that wrap the existing LeaseAdapter."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from aptguide2.harness.tools.contracts import ToolCallRequest, ToolCallResult

BACKEND = "lease"


def _run_awaitable(value: Any) -> Any:
    """Run an awaitable if no event loop is running; otherwise signal not-implemented."""
    if not asyncio.iscoroutine(value):
        return value
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(value)
    # An event loop is already running -- cannot asyncio.run inside it.
    return _NOT_IMPLEMENTED_SENTINEL


# Sentinel for "adapter method exists but cannot be called synchronously".
_NOT_IMPLEMENTED_SENTINEL = object()


def _error_from_exception(tool: str, exc: Exception) -> ToolCallResult:
    """Map well-known exception types to ToolError codes."""
    if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
        return ToolCallResult.error_result(
            tool=tool,
            code="TOOL_TIMEOUT",
            message=str(exc) or "tool timed out",
            recoverable=True,
            backend=BACKEND,
        )
    return ToolCallResult.error_result(
        tool=tool,
        code="UNKNOWN_TOOL_ERROR",
        message=f"{type(exc).__name__}: {exc}",
        backend=BACKEND,
    )


def _not_implemented(tool: str) -> ToolCallResult:
    return ToolCallResult.error_result(
        tool=tool,
        code="TOOL_NOT_IMPLEMENTED",
        message=f"Adapter does not support {tool}",
        backend=BACKEND,
    )


# ---------------------------------------------------------------------------
# Executors
# ---------------------------------------------------------------------------


class LeaseHealthExecutor:
    """Calls adapter.health() and returns ok/error."""

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        try:
            result = _run_awaitable(self._adapter.health())
            if result is _NOT_IMPLEMENTED_SENTINEL:
                return _not_implemented(request.tool)
            return ToolCallResult.ok_result(
                tool=request.tool,
                data={"healthy": bool(result)},
                backend=BACKEND,
            )
        except Exception as exc:
            return _error_from_exception(request.tool, exc)


class RoomSearchExecutor:
    """Calls adapter.search_rooms(payload) and maps result to ToolCallResult."""

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        try:
            result = _run_awaitable(self._adapter.search_rooms(request.payload))
            if result is _NOT_IMPLEMENTED_SENTINEL:
                return _not_implemented(request.tool)
            if not isinstance(result, dict):
                result = {}
            rooms = result.get("rooms", result.get("data", []))
            if isinstance(rooms, list):
                return ToolCallResult.ok_result(
                    tool=request.tool,
                    data={"rooms": rooms},
                    backend=BACKEND,
                    metadata={"result_count": len(rooms)},
                )
            return ToolCallResult.ok_result(
                tool=request.tool,
                data=result,
                backend=BACKEND,
            )
        except Exception as exc:
            return _error_from_exception(request.tool, exc)


class RoomDetailExecutor:
    """Calls adapter.get_room_detail(room_id) and returns room data."""

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        try:
            room_id = request.payload.get("room_id")
            if room_id is None:
                return ToolCallResult.error_result(
                    tool=request.tool,
                    code="INVALID_PAYLOAD",
                    message="room_id is required",
                    backend=BACKEND,
                )
            result = _run_awaitable(self._adapter.get_room_detail(room_id))
            if result is _NOT_IMPLEMENTED_SENTINEL:
                return _not_implemented(request.tool)
            return ToolCallResult.ok_result(
                tool=request.tool,
                data={"room": result} if isinstance(result, dict) else {"room": result},
                backend=BACKEND,
            )
        except Exception as exc:
            return _error_from_exception(request.tool, exc)


class AppointmentCreateExecutor:
    """Calls adapter.create_appointment(payload) if available."""

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        method = getattr(self._adapter, "create_appointment", None)
        if method is None:
            return _not_implemented(request.tool)
        try:
            result = _run_awaitable(method(request.payload))
            if result is _NOT_IMPLEMENTED_SENTINEL:
                return _not_implemented(request.tool)
            data = result if isinstance(result, dict) else {"appointment_id": str(result)}
            return ToolCallResult.ok_result(
                tool=request.tool,
                data=data,
                backend=BACKEND,
            )
        except Exception as exc:
            return _error_from_exception(request.tool, exc)


class AppointmentListMineExecutor:
    """Calls adapter.list_appointments(payload) if available."""

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        method = getattr(self._adapter, "list_appointments", None)
        if method is None:
            return _not_implemented(request.tool)
        try:
            result = _run_awaitable(method(request.payload))
            if result is _NOT_IMPLEMENTED_SENTINEL:
                return _not_implemented(request.tool)
            data = result if isinstance(result, dict) else {"appointments": result}
            return ToolCallResult.ok_result(
                tool=request.tool,
                data=data,
                backend=BACKEND,
            )
        except Exception as exc:
            return _error_from_exception(request.tool, exc)


class LeaseListMineExecutor:
    """Calls adapter.list_leases(payload) if available."""

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        method = getattr(self._adapter, "list_leases", None)
        if method is None:
            return _not_implemented(request.tool)
        try:
            result = _run_awaitable(method(request.payload))
            if result is _NOT_IMPLEMENTED_SENTINEL:
                return _not_implemented(request.tool)
            data = result if isinstance(result, dict) else {"leases": result}
            return ToolCallResult.ok_result(
                tool=request.tool,
                data=data,
                backend=BACKEND,
            )
        except Exception as exc:
            return _error_from_exception(request.tool, exc)


class AppointmentCancelExecutor:
    """Calls adapter.cancel_appointment(payload) if available."""

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        method = getattr(self._adapter, "cancel_appointment", None)
        if method is None:
            return _not_implemented(request.tool)
        try:
            result = _run_awaitable(method(request.payload))
            if result is _NOT_IMPLEMENTED_SENTINEL:
                return _not_implemented(request.tool)
            data = result if isinstance(result, dict) else {"appointment_id": str(result)}
            return ToolCallResult.ok_result(
                tool=request.tool,
                data=data,
                backend=BACKEND,
            )
        except Exception as exc:
            return _error_from_exception(request.tool, exc)
