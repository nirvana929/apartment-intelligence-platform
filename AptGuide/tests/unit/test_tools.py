from aptguide.tools.schemas import (
    AppointmentCreateRequest,
    AppointmentCreateResponse,
    AppointmentQueryResponse,
)


def test_appointment_create_request():
    req = AppointmentCreateRequest(
        room_id=3001,
        appointment_time="2026-05-03 15:00",
        user_id="user-001",
    )
    assert req.room_id == 3001
    assert req.appointment_time == "2026-05-03 15:00"


def test_appointment_create_response():
    resp = AppointmentCreateResponse(
        appointment_id="A20260503302",
        room_id=3001,
        room_title="天河公寓 302",
        appointment_time="2026-05-03 15:00",
        status="confirmed",
    )
    assert resp.appointment_id == "A20260503302"
    assert resp.status == "confirmed"


def test_appointment_query_response():
    resp = AppointmentQueryResponse(
        appointments=[
            {
                "appointment_id": "A20260503302",
                "room_title": "天河公寓 302",
                "appointment_time": "2026-05-03 15:00",
                "status": "confirmed",
            }
        ]
    )
    assert len(resp.appointments) == 1
