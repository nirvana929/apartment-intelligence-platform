"""Tests for MemoryManager."""

import time

from aptguide2.harness.contracts import ConversationFrame
from aptguide2.harness.memory import MemoryManager


def _frame(**kwargs) -> ConversationFrame:
    defaults = {"request_id": "r-1", "message": "hello"}
    defaults.update(kwargs)
    return ConversationFrame(**defaults)


class TestUpdateRecentMessages:
    def test_appends_user_message(self):
        mm = MemoryManager()
        frame = _frame()
        mm.update_recent_messages(frame)
        assert len(frame.recent_messages) == 1
        assert frame.recent_messages[0]["role"] == "user"
        assert frame.recent_messages[0]["content"] == "hello"

    def test_appends_user_and_assistant(self):
        mm = MemoryManager()
        frame = _frame()
        mm.update_recent_messages(frame, assistant_reply="hi there")
        assert len(frame.recent_messages) == 2
        assert frame.recent_messages[0]["role"] == "user"
        assert frame.recent_messages[1]["role"] == "assistant"
        assert frame.recent_messages[1]["content"] == "hi there"

    def test_trims_to_max(self):
        mm = MemoryManager()
        frame = _frame()
        for i in range(15):
            frame.message = f"msg-{i}"
            mm.update_recent_messages(frame, assistant_reply=f"reply-{i}")
        assert len(frame.recent_messages) == mm.MAX_RECENT_MESSAGES

    def test_preserves_existing_messages(self):
        mm = MemoryManager()
        frame = _frame(recent_messages=[{"role": "user", "content": "old", "request_id": "r-0", "timestamp": 0}])
        mm.update_recent_messages(frame)
        assert len(frame.recent_messages) == 2
        assert frame.recent_messages[0]["content"] == "old"


class TestPendingAction:
    def test_create_pending_action(self):
        mm = MemoryManager()
        frame = _frame()
        pending = mm.create_pending_action(frame, "appointment.create", {"room_id": 101})
        assert pending["type"] == "appointment.create"
        assert pending["status"] == "pending"
        assert pending["payload"] == {"room_id": 101}
        assert frame.pending_action is pending

    def test_confirm_pending_action(self):
        mm = MemoryManager()
        frame = _frame()
        pending = mm.create_pending_action(frame, "appointment.create", {"room_id": 101}, confirmation_id="abc123")
        payload = mm.confirm_pending_action(frame, "abc123")
        assert payload == {"room_id": 101}
        assert frame.pending_action is None

    def test_confirm_wrong_id_returns_none(self):
        mm = MemoryManager()
        frame = _frame()
        mm.create_pending_action(frame, "appointment.create", {"room_id": 101}, confirmation_id="abc123")
        assert mm.confirm_pending_action(frame, "wrong") is None

    def test_confirm_no_pending_returns_none(self):
        mm = MemoryManager()
        frame = _frame()
        assert mm.confirm_pending_action(frame, "abc123") is None

    def test_confirm_expired_returns_none(self):
        mm = MemoryManager()
        frame = _frame()
        mm.create_pending_action(frame, "appointment.create", {"room_id": 101}, confirmation_id="abc123", expires_in_seconds=0)
        time.sleep(0.01)
        assert mm.confirm_pending_action(frame, "abc123") is None
        assert frame.pending_action is None

    def test_cancel_pending_action(self):
        mm = MemoryManager()
        frame = _frame()
        mm.create_pending_action(frame, "appointment.create", {"room_id": 101})
        mm.cancel_pending_action(frame)
        assert frame.pending_action is None

    def test_is_pending_action_expired(self):
        mm = MemoryManager()
        frame = _frame()
        mm.create_pending_action(frame, "test", {}, expires_in_seconds=0)
        time.sleep(0.01)
        assert mm.is_pending_action_expired(frame) is True

    def test_is_pending_action_not_expired(self):
        mm = MemoryManager()
        frame = _frame()
        mm.create_pending_action(frame, "test", {}, expires_in_seconds=300)
        assert mm.is_pending_action_expired(frame) is False

    def test_check_pending_action_expiry_cleans_up(self):
        mm = MemoryManager()
        frame = _frame()
        mm.create_pending_action(frame, "test", {}, expires_in_seconds=0)
        time.sleep(0.01)
        assert mm.check_pending_action_expiry(frame) is True
        assert frame.pending_action is None

    def test_check_pending_action_expiry_no_action(self):
        mm = MemoryManager()
        frame = _frame()
        assert mm.check_pending_action_expiry(frame) is False


class TestToolObservations:
    def test_update_tool_observations(self):
        mm = MemoryManager()
        frame = _frame()
        obs = {"tool": "room.search", "success": True}
        mm.update_tool_observations(frame, obs)
        assert len(frame.tool_observations) == 1
        assert frame.tool_observations[0] == obs

    def test_tool_observations_trim_to_10(self):
        mm = MemoryManager()
        frame = _frame()
        for i in range(15):
            mm.update_tool_observations(frame, {"tool": f"tool-{i}", "success": True})
        assert len(frame.tool_observations) == 10
        assert frame.tool_observations[0]["tool"] == "tool-5"

    def test_consecutive_tool_failures(self):
        mm = MemoryManager()
        frame = _frame()
        mm.update_tool_observations(frame, {"tool": "t1", "success": True})
        mm.update_tool_observations(frame, {"tool": "t2", "success": False})
        mm.update_tool_observations(frame, {"tool": "t3", "success": False})
        assert mm.get_consecutive_tool_failures(frame) == 2

    def test_consecutive_failures_resets_on_success(self):
        mm = MemoryManager()
        frame = _frame()
        mm.update_tool_observations(frame, {"tool": "t1", "success": False})
        mm.update_tool_observations(frame, {"tool": "t2", "success": True})
        mm.update_tool_observations(frame, {"tool": "t3", "success": False})
        assert mm.get_consecutive_tool_failures(frame) == 1

    def test_consecutive_failures_no_observations(self):
        mm = MemoryManager()
        frame = _frame()
        assert mm.get_consecutive_tool_failures(frame) == 0
