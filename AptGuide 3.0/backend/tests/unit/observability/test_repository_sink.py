"""Unit tests for RepositoryTraceSink.

Verifies that the sink delegates to the trace repository's
``append_trace_event`` method with the correct arguments.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from aptguide3.observability.events import TraceEvent
from aptguide3.observability.repository_sink import RepositoryTraceSink


class RecordingTraceRepo:
    """Synchronous stand-in for TraceRepository used in simple tests."""

    def __init__(self):
        self.events = []

    async def append_trace_event(self, trace_id, request_id, session_id, event_name, payload):
        self.events.append((trace_id, request_id, session_id, event_name, payload))


# ---------------------------------------------------------------------------
# AsyncMock-based tests (preferred for protocol-accurate repos)
# ---------------------------------------------------------------------------


def test_repository_trace_sink_calls_repo_append_trace_event():
    """Sink must call repo.append_trace_event with correct field mapping."""
    repo = MagicMock()
    repo.append_trace_event = AsyncMock()
    sink = RepositoryTraceSink(repo)

    event = TraceEvent(event_type="chat_started", session_id="s1", data={"key": "value"})

    with patch("aptguide3.observability.repository_sink.asyncio") as mock_asyncio:
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        mock_asyncio.get_running_loop.return_value = mock_loop
        sink.write(event)

    repo.append_trace_event.assert_called_once_with(
        trace_id="s1",
        request_id="",
        session_id="s1",
        event_name="chat_started",
        payload={"key": "value"},
    )
    mock_loop.create_task.assert_called_once()


def test_repository_trace_sink_falls_back_to_asyncio_run():
    """When no event loop is running, sink uses asyncio.run()."""
    repo = MagicMock()
    repo.append_trace_event = AsyncMock()
    sink = RepositoryTraceSink(repo)

    event = TraceEvent(event_type="turn_complete", session_id="s2", data={})

    with patch("aptguide3.observability.repository_sink.asyncio") as mock_asyncio:
        mock_asyncio.get_running_loop.side_effect = RuntimeError("no loop")
        sink.write(event)

    repo.append_trace_event.assert_called_once_with(
        trace_id="s2",
        request_id="",
        session_id="s2",
        event_name="turn_complete",
        payload={},
    )
    mock_asyncio.run.assert_called_once()


def test_repository_trace_sink_handles_loop_not_running():
    """When a loop exists but is not running, sink uses asyncio.run()."""
    repo = MagicMock()
    repo.append_trace_event = AsyncMock()
    sink = RepositoryTraceSink(repo)

    event = TraceEvent(event_type="error", session_id="s3", data={"msg": "oops"})

    with patch("aptguide3.observability.repository_sink.asyncio") as mock_asyncio:
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = False
        mock_asyncio.get_running_loop.return_value = mock_loop
        sink.write(event)

    repo.append_trace_event.assert_called_once()
    mock_asyncio.run.assert_called_once()


# ---------------------------------------------------------------------------
# Synchronous recording repo tests (simpler, no mock patching needed)
# ---------------------------------------------------------------------------


def test_repository_trace_sink_records_event():
    repo = RecordingTraceRepo()
    sink = RepositoryTraceSink(repo)
    sink.write(TraceEvent(event_type="chat_started", session_id="s1", data={"key": "value"}))
    assert len(repo.events) == 1
    assert repo.events[0][0] == "s1"  # trace_id
    assert repo.events[0][3] == "chat_started"  # event_name
    assert repo.events[0][4] == {"key": "value"}  # payload


def test_repository_trace_sink_handles_multiple_events():
    repo = RecordingTraceRepo()
    sink = RepositoryTraceSink(repo)
    sink.write(TraceEvent(event_type="event1", session_id="s1", data={}))
    sink.write(TraceEvent(event_type="event2", session_id="s1", data={"a": 1}))
    assert len(repo.events) == 2
    assert repo.events[0][3] == "event1"
    assert repo.events[1][3] == "event2"
