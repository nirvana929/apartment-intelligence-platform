from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.understanding import UnderstandingResult
from aptguide3.procedures.appointment import AppointmentProcedure


def _frame(**overrides: Any) -> ConversationFrame:
    defaults = dict(message="我要预约看房", session_id="s-1", user_id="u-1")
    defaults.update(overrides)
    return ConversationFrame(**defaults)


def _understanding(**overrides: Any) -> UnderstandingResult:
    defaults = dict(
        raw_message="我要预约看房",
        route="appointment",
        task="appointment",
        domain="appointment",
        action="create",
        confidence=0.9,
        hard_filters={},
        soft_preferences=[],
    )
    defaults.update(overrides)
    return UnderstandingResult(**defaults)


# ---- 1. Missing fields returns clarification ----


def test_missing_fields_returns_clarification():
    proc = AppointmentProcedure()
    result = proc.run(_frame(), _understanding())

    assert result.phase == "appointment"
    assert "请提供房间号和预约时间" in result.message
    assert result.metadata.get("needs_fields") is True
    assert len(result.actions) == 1
    assert result.actions[0]["type"] == "ask_fields"


def test_missing_apartment_id_returns_clarification():
    proc = AppointmentProcedure()
    result = proc.run(_frame(), _understanding(hard_filters={"appointment_time": "2026-05-20 10:00"}))

    assert result.metadata.get("needs_fields") is True


def test_missing_appointment_time_returns_clarification():
    proc = AppointmentProcedure()
    result = proc.run(_frame(), _understanding(hard_filters={"apartment_id": 101}))

    assert result.metadata.get("needs_fields") is True


# ---- 2. Valid fields returns confirmation card with pending_action ----


def test_valid_fields_returns_confirmation_card():
    proc = AppointmentProcedure()
    result = proc.run(
        _frame(),
        _understanding(hard_filters={"apartment_id": 101, "appointment_time": "2026-05-20 10:00"}),
    )

    assert result.phase == "appointment"
    assert "确认预约看房" in result.message
    assert "101" in result.message
    assert "2026-05-20 10:00" in result.message
    assert result.pending_action is not None
    assert result.pending_action["type"] == "appointment"
    assert len(result.actions) == 1
    assert result.actions[0]["type"] == "confirm"
    assert "pending_action_id" in result.actions[0]
    assert result.metadata.get("pending_action_id") is not None


def test_valid_fields_saves_pending_action():
    mock_repo = AsyncMock()
    proc = AppointmentProcedure(pending_action_repo=mock_repo)
    result = proc.run(
        _frame(),
        _understanding(hard_filters={"apartment_id": 202, "appointment_time": "2026-05-21 14:00"}),
    )

    pending_id = result.metadata["pending_action_id"]
    mock_repo.save_pending_action.assert_called_once()
    call_args = mock_repo.save_pending_action.call_args
    assert call_args[0][0] == pending_id  # pending_action_id
    assert call_args[0][1] == "s-1"  # session_id
    assert call_args[0][2] == "u-1"  # user_id
    assert call_args[0][3] == "appointment"  # action_type
    payload = call_args[0][4]
    assert payload["apartment_id"] == 202
    assert payload["appointment_time"] == "2026-05-21 14:00"


# ---- 3. Confirmation success ----


def test_confirmation_success():
    mock_pending = AsyncMock()
    mock_pending.load_pending_action.return_value = {
        "status": "pending",
        "payload": {
            "apartment_id": 101,
            "appointment_time": "2026-05-20 10:00",
            "remark": "我要预约看房",
        },
    }
    mock_lease = AsyncMock()
    mock_lease.create_appointment.return_value = {"ok": True, "data": {"id": 42}}
    mock_audit = AsyncMock()

    proc = AppointmentProcedure(
        pending_action_repo=mock_pending,
        lease_client=mock_lease,
        audit_repo=mock_audit,
    )

    frame = _frame(pending_action={"id": "abc123", "type": "appointment"})
    result = proc.run(frame, _understanding())

    assert result.phase == "appointment"
    assert "预约成功" in result.message
    assert result.metadata["appointment_created"] is True

    mock_pending.load_pending_action.assert_called_once_with("abc123")
    mock_lease.create_appointment.assert_called_once()
    lease_call = mock_lease.create_appointment.call_args
    assert lease_call[1]["apartment_id"] == 101
    assert lease_call[1]["appointment_time"] == "2026-05-20 10:00"
    mock_pending.mark_completed.assert_called_once_with("abc123")
    mock_audit.append_audit_event.assert_called_once()


# ---- 4. Confirmation with expired pending action ----


def test_confirmation_expired_pending_action():
    mock_pending = AsyncMock()
    mock_pending.load_pending_action.return_value = None
    mock_lease = AsyncMock()

    proc = AppointmentProcedure(pending_action_repo=mock_pending, lease_client=mock_lease)

    frame = _frame(pending_action={"id": "expired-id", "type": "appointment"})
    result = proc.run(frame, _understanding())

    assert result.phase == "appointment"
    assert "过期" in result.message
    mock_lease.create_appointment.assert_not_called()
    mock_pending.mark_completed.assert_not_called()


def test_confirmation_already_completed():
    mock_pending = AsyncMock()
    mock_pending.load_pending_action.return_value = {
        "status": "completed",
        "payload": {"apartment_id": 101, "appointment_time": "2026-05-20 10:00"},
    }
    mock_lease = AsyncMock()

    proc = AppointmentProcedure(pending_action_repo=mock_pending, lease_client=mock_lease)

    frame = _frame(pending_action={"id": "done-id", "type": "appointment"})
    result = proc.run(frame, _understanding())

    assert result.phase == "appointment"
    assert "已完成" in result.message
    mock_lease.create_appointment.assert_not_called()


# ---- 5. Confirmation with lease failure ----


def test_confirmation_lease_failure():
    mock_pending = AsyncMock()
    mock_pending.load_pending_action.return_value = {
        "status": "pending",
        "payload": {
            "apartment_id": 101,
            "appointment_time": "2026-05-20 10:00",
            "remark": "test",
        },
    }
    mock_lease = AsyncMock()
    mock_lease.create_appointment.return_value = {"ok": False, "error": "时间冲突"}

    proc = AppointmentProcedure(pending_action_repo=mock_pending, lease_client=mock_lease)

    frame = _frame(pending_action={"id": "fail-id", "type": "appointment"})
    result = proc.run(frame, _understanding())

    assert result.phase == "appointment"
    assert "预约失败" in result.message
    assert "时间冲突" in result.message
    mock_pending.mark_completed.assert_called_once_with("fail-id")


def test_confirmation_lease_exception():
    mock_pending = AsyncMock()
    mock_pending.load_pending_action.return_value = {
        "status": "pending",
        "payload": {"apartment_id": 101, "appointment_time": "2026-05-20 10:00", "remark": "test"},
    }
    mock_lease = AsyncMock()
    mock_lease.create_appointment.side_effect = ConnectionError("network down")

    proc = AppointmentProcedure(pending_action_repo=mock_pending, lease_client=mock_lease)

    frame = _frame(pending_action={"id": "err-id", "type": "appointment"})
    result = proc.run(frame, _understanding())

    assert result.phase == "appointment"
    assert "预约失败" in result.message
    mock_pending.mark_completed.assert_called_once()


# ---- 6. No repos (graceful degradation) ----


def test_no_repos_confirmation_degrades_gracefully():
    proc = AppointmentProcedure()

    frame = _frame(pending_action={"id": "x", "type": "appointment"})
    result = proc.run(frame, _understanding())

    assert result.phase == "appointment"
    assert "不可用" in result.message


def test_no_pending_repo_skips_save():
    """When pending_action_repo is None, confirmation card is still returned."""
    proc = AppointmentProcedure(pending_action_repo=None)
    result = proc.run(
        _frame(),
        _understanding(hard_filters={"apartment_id": 101, "appointment_time": "2026-05-20 10:00"}),
    )

    assert "确认预约看房" in result.message
    assert result.pending_action is not None


def test_no_audit_repo_skips_audit():
    """When audit_repo is None, confirmation flow still works."""
    mock_pending = AsyncMock()
    mock_pending.load_pending_action.return_value = {
        "status": "pending",
        "payload": {"apartment_id": 101, "appointment_time": "2026-05-20 10:00", "remark": "test"},
    }
    mock_lease = AsyncMock()
    mock_lease.create_appointment.return_value = {"ok": True, "data": {}}

    proc = AppointmentProcedure(
        pending_action_repo=mock_pending,
        lease_client=mock_lease,
        audit_repo=None,
    )

    frame = _frame(pending_action={"id": "no-audit", "type": "appointment"})
    result = proc.run(frame, _understanding())

    assert "预约成功" in result.message
