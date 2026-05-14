from aptguide3.understanding.llm_understanding import LLMUnderstanding


class FakeMessage:
    def __init__(self, content: str):
        self.content = content


class FakeChoice:
    def __init__(self, content: str):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content: str):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, content: str | None = None, error: Exception | None = None):
        self.content = content
        self.error = error

    def create(self, **kwargs):
        if self.error is not None:
            raise self.error
        return FakeResponse(self.content or "{}")


class FakeChat:
    def __init__(self, completions: FakeCompletions):
        self.completions = completions


class FakeClient:
    def __init__(self, content: str | None = None, error: Exception | None = None):
        self.chat = FakeChat(FakeCompletions(content=content, error=error))


def test_llm_understanding_returns_valid_model_output():
    content = """
    {
      "raw_message": "有阳台的房间吗",
      "route": "rag",
      "task": "room_search",
      "domain": "room",
      "action": "search",
      "confidence": 0.92,
      "hard_filters": {},
      "soft_preferences": ["有阳台"],
      "retrieval_queries": ["有阳台 房源"],
      "risk": {"level": "low", "response_mode": "normal_answer"},
      "clarification": {"needed": false, "question": ""},
      "reason": "User wants room search."
    }
    """

    understanding = LLMUnderstanding(FakeClient(content=content), model="fake-model", min_confidence=0.65)

    result = understanding.understand("有阳台的房间吗")

    assert result.route == "rag"
    assert result.task == "room_search"
    assert result.soft_preferences == ["有阳台"]


def test_llm_understanding_error_returns_clarification():
    understanding = LLMUnderstanding(FakeClient(error=RuntimeError("timeout")), model="fake-model", min_confidence=0.65)

    result = understanding.understand("有阳台的房间吗")

    assert result.route == "clarify"
    assert result.task == "clarify"
    assert result.clarification.needed is True


def test_llm_understanding_invalid_json_returns_clarification():
    understanding = LLMUnderstanding(FakeClient(content="not json"), model="fake-model", min_confidence=0.65)

    result = understanding.understand("有阳台的房间吗")

    assert result.route == "clarify"
