from __future__ import annotations

from typing import Any

from aptguide3.domain.conversation import ConversationFrame
from aptguide3.domain.procedures import ProcedureResult
from aptguide3.domain.understanding import UnderstandingResult


class RoomSearchProcedure:
    name = "room_search"

    def __init__(self, lease_client: Any = None):
        self._lease_client = lease_client

    def run(self, frame: ConversationFrame, understanding: UnderstandingResult) -> ProcedureResult:
        if self._lease_client is not None:
            import asyncio

            filters = understanding.hard_filters
            room_ids = filters.pop("room_ids", [])
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            try:
                if loop and loop.is_running():
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        rooms = pool.submit(asyncio.run, self._lease_client.validate_rooms(room_ids, filters)).result()
                else:
                    rooms = asyncio.run(self._lease_client.validate_rooms(room_ids, filters))
            except Exception:
                rooms = []

            if rooms:
                cards = [_room_card(r) for r in rooms[:10]]
                return ProcedureResult(
                    message=f"找到 {len(rooms)} 间符合条件的房源",
                    phase="room_search",
                    cards=cards,
                    metadata={"route": understanding.route, "task": understanding.task, "room_count": len(rooms)},
                )

        return ProcedureResult(
            message="已理解您的找房需求。房源检索将在接入 lease 和 vector 后返回可验证结果。",
            phase="room_search",
            metadata={
                "route": understanding.route,
                "task": understanding.task,
                "hard_filters": understanding.hard_filters,
                "soft_preferences": understanding.soft_preferences,
            },
        )


def _room_card(room: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "room",
        "room_id": room.get("room_id", 0),
        "rent": room.get("rent", 0),
        "payment_types": room.get("payment_types", []),
        "tags": room.get("tags", []),
        "facilities": room.get("facilities", []),
    }
