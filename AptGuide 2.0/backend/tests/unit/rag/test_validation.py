from aptguide2.rag.schemas import RoomCandidate
from aptguide2.rag.validation import validate_room_candidates


class FakeLeaseValidator:
    def __init__(self, rooms):
        self.rooms = rooms
        self.called_with = None

    def search_rooms(self, payload):
        self.called_with = payload
        return {"rooms": self.rooms}


def test_validation_keeps_only_lease_returned_rooms():
    validator = FakeLeaseValidator([
        {"room_id": 101, "apartment_id": 1, "apartment_name": "南亭寓", "rent": 1500, "is_appointable": True}
    ])
    candidates = [
        RoomCandidate(room_id=101, semantic_score=0.9, matched_query="安静"),
        RoomCandidate(room_id=999, semantic_score=0.95, matched_query="安静"),
    ]

    validated = validate_room_candidates(candidates, {"max_rent": 1600}, validator)

    assert [room["room_id"] for room in validated] == [101]
    assert validated[0]["semantic_score"] == 0.9
    assert validator.called_with["room_ids"] == [101, 999]


def test_validation_returns_empty_when_lease_returns_no_rooms():
    validator = FakeLeaseValidator([])
    candidates = [RoomCandidate(room_id=999, semantic_score=0.95)]

    validated = validate_room_candidates(candidates, {}, validator)

    assert validated == []


from aptguide2.rag.tool_validation import ToolRuntimeRoomValidator


class FakeToolRuntime:
    def execute(self, request):
        assert request.tool == "room.search"
        return type("Result", (), {
            "ok": True,
            "data": {"rooms": [{"room_id": 101, "apartment_id": 1, "rent": 1500}]},
        })()


def test_tool_runtime_room_validator_calls_room_search():
    validator = ToolRuntimeRoomValidator(FakeToolRuntime())

    result = validator.search_rooms({"room_ids": [101]})

    assert result["rooms"][0]["room_id"] == 101
