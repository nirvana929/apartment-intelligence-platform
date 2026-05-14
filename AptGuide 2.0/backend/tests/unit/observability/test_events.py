from __future__ import annotations

from aptguide2.observability.events import emit_event


def test_emit_event_returns_structured_payload():
    result = emit_event("chat.received", request_id="r-abc", session_id="s-1", message_len=42)
    assert result["event"] == "chat.received"
    assert result["request_id"] == "r-abc"
    assert result["session_id"] == "s-1"
    assert result["message_len"] == 42


def test_emit_event_without_extra_fields():
    result = emit_event("ping")
    assert result == {"event": "ping"}
