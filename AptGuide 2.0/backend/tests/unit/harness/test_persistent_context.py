from aptguide2.harness.context_persistent import PersistentContextStore
from aptguide2.harness.contracts import AptGuideRequest, ConversationFrame


class FakeRedisStore:
    def __init__(self) -> None:
        self.sessions = {}

    async def load_session(self, session_id):
        return self.sessions.get(session_id)

    async def save_session(self, session_id, payload):
        self.sessions[session_id] = payload

    async def save_pending_action(self, confirmation_id, payload):
        pass


class FakeSessionRepository:
    def __init__(self) -> None:
        self.frames = {}

    async def load_frame(self, session_id):
        return self.frames.get(session_id)

    async def save_frame(self, frame):
        self.frames[frame.session_id] = frame.model_dump()


def test_new_request_creates_frame_when_no_session_exists() -> None:
    store = PersistentContextStore(redis_store=FakeRedisStore(), session_repository=FakeSessionRepository())

    frame = store.load(AptGuideRequest(request_id="r1", session_id="s1", user_id="u1", message="找房"))

    assert frame.session_id == "s1"
    assert frame.user_id == "u1"
    assert frame.message == "找房"


def test_save_and_load_round_trip() -> None:
    store = PersistentContextStore(redis_store=FakeRedisStore(), session_repository=FakeSessionRepository())
    frame = ConversationFrame(session_id="s1", request_id="r1", user_id="u1", message="找房", phase="idle")

    store.save(frame)
    loaded = store.load(AptGuideRequest(request_id="r2", session_id="s1", user_id="u1", message="我的预约"))

    assert loaded.request_id == "r2"
    assert loaded.message == "我的预约"
    assert loaded.user_id == "u1"
