from aptguide3.rag.preference_scorer import LLMPreferenceScorer
from aptguide3.rag.schemas import ValidatedRoom


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


FAKE_SCORES_JSON = (
    '{"scores":[{"room_id":1,"score":0.86,'
    '"matched_preferences":["安静"],'
    '"missing_preferences":["近地铁"],'
    '"reason":"房源标签显示安静，但未明确近地铁。"}]}'
)


class FakeCompletions:
    def create(self, **kwargs):
        return FakeResponse(FAKE_SCORES_JSON)


class FakeClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeCompletions()})()


def test_llm_preference_scorer_returns_structured_scores():
    scorer = LLMPreferenceScorer(FakeClient(), model="fake")
    rooms = [ValidatedRoom(room_id=1, rent=1500, tags=["安静"], facilities=["空调"])]

    scores = scorer.score("找安静近地铁的房子", ["安静", "近地铁"], rooms)

    assert scores[1].score == 0.86
    assert scores[1].matched_preferences == ["安静"]
    assert scores[1].missing_preferences == ["近地铁"]


def test_no_client_returns_neutral_scores():
    scorer = LLMPreferenceScorer(None, model="fake")
    rooms = [ValidatedRoom(room_id=1)]

    scores = scorer.score("test", ["安静"], rooms)

    assert scores[1].score == 0.5


def test_no_preferences_returns_neutral():
    scorer = LLMPreferenceScorer(FakeClient(), model="fake")
    rooms = [ValidatedRoom(room_id=1)]

    scores = scorer.score("test", [], rooms)

    assert scores[1].score == 0.5
