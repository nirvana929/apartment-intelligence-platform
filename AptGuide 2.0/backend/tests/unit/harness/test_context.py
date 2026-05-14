from aptguide2.harness.context import InMemoryContextStore
from aptguide2.harness.contracts import AptGuideRequest


def test_load_creates_frame_from_request():
    store = InMemoryContextStore()
    req = AptGuideRequest(request_id="r-1", session_id="s-1", message="找房")
    frame = store.load(req)
    assert frame.session_id == "s-1"
    assert frame.request_id == "r-1"
    assert frame.message == "找房"


def test_save_and_reload_preserves_last_recommendations():
    store = InMemoryContextStore()
    req = AptGuideRequest(request_id="r-1", session_id="s-1", message="找房")
    frame = store.load(req)
    frame.last_recommendations = [{"room_id": 100}]
    store.save(frame)

    req2 = AptGuideRequest(request_id="r-2", session_id="s-1", message="第一个")
    frame2 = store.load(req2)
    assert frame2.request_id == "r-2"
    assert frame2.message == "第一个"
    assert frame2.last_recommendations == [{"room_id": 100}]
