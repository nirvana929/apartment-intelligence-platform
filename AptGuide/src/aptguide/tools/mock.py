from datetime import datetime


class MockToolClient:
    """Mock 工具客户端"""

    def __init__(self):
        self.appointments = {}
        self.appointment_counter = 1000

    async def create_appointment(
        self,
        room_id: int,
        appointment_time: str,
        user_id: str,
        remark: str | None = None,
    ) -> dict:
        """创建预约"""
        self.appointment_counter += 1
        appointment_id = f"A{datetime.now().strftime('%Y%m%d')}{self.appointment_counter}"

        room_titles = {
            3001: "天河公寓 302",
            3002: "科韵公寓 506",
            3003: "棠德公寓 412",
        }

        appointment = {
            "appointment_id": appointment_id,
            "room_id": room_id,
            "room_title": room_titles.get(room_id, f"房间 {room_id}"),
            "appointment_time": appointment_time,
            "status": "confirmed",
            "created_at": datetime.now().isoformat(),
            "user_id": user_id,
            "remark": remark,
        }

        self.appointments[appointment_id] = appointment
        return appointment

    async def query_appointments(self, user_id: str) -> dict:
        """查询用户预约"""
        user_appointments = [
            appt for appt in self.appointments.values() if appt["user_id"] == user_id
        ]

        if not user_appointments:
            user_appointments = [
                {
                    "appointment_id": "A20260501001",
                    "room_title": "天河公寓 302",
                    "appointment_time": "2026-05-05 14:00",
                    "status": "confirmed",
                }
            ]

        return {"appointments": user_appointments}

    async def query_leases(self, user_id: str) -> dict:
        """查询用户租约"""
        return {
            "leases": [
                {
                    "lease_id": "L20250801001",
                    "room_title": "科韵公寓 506",
                    "start_date": "2025-08-01",
                    "end_date": "2026-07-31",
                    "rent": 2950,
                    "status": "active",
                }
            ]
        }
