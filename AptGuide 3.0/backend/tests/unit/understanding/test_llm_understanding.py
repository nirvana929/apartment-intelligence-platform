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


def test_llm_understanding_records_low_confidence_diagnostic():
    content = """{
      "raw_message": "找番禺1500以内安静一点的房子",
      "route": "rag",
      "task": "room_search",
      "domain": "room",
      "action": "search",
      "confidence": 0.5,
      "hard_filters": {"district_name": "番禺", "max_rent": 1500},
      "soft_preferences": ["安静"],
      "retrieval_queries": ["番禺 1500以内 安静 房子"],
      "risk": {"level": "low", "response_mode": "normal_answer", "reason": ""},
      "clarification": {"needed": false, "question": ""},
      "reason": ""
    }"""
    understanding = LLMUnderstanding(FakeClient(content=content), model="fake-model", min_confidence=0.65)

    result = understanding.understand("找番禺1500以内安静一点的房子")

    assert result.route == "clarify"
    assert understanding.last_diagnostic is not None
    assert understanding.last_diagnostic.parsed_route == "rag"
    assert understanding.last_diagnostic.parsed_task == "room_search"
    assert understanding.last_diagnostic.parsed_confidence == 0.5
    assert understanding.last_diagnostic.validator_reason == "low_confidence"
    assert understanding.last_diagnostic.final_route == "clarify"


def test_llm_understanding_records_model_requested_clarification_diagnostic():
    content = """{
      "raw_message": "我想租房",
      "route": "clarify",
      "task": "clarify",
      "domain": "unknown",
      "action": "ask_clarification",
      "confidence": 0.8,
      "hard_filters": {},
      "soft_preferences": [],
      "retrieval_queries": [],
      "risk": {"level": "low", "response_mode": "ask_clarification", "reason": ""},
      "clarification": {"needed": true, "question": "预算是多少？"},
      "reason": "missing_budget"
    }"""
    understanding = LLMUnderstanding(FakeClient(content=content), model="fake-model", min_confidence=0.65)

    result = understanding.understand("我想租房")

    assert result.route == "clarify"
    assert understanding.last_diagnostic is not None
    assert understanding.last_diagnostic.parsed_route == "clarify"
    assert understanding.last_diagnostic.validator_reason == "missing_budget"
    assert understanding.last_diagnostic.final_route == "clarify"


def test_llm_understanding_error_records_diagnostic():
    understanding = LLMUnderstanding(FakeClient(error=RuntimeError("timeout")), model="fake-model", min_confidence=0.65)

    result = understanding.understand("有阳台的房间吗")

    assert result.route == "clarify"
    assert understanding.last_diagnostic is not None
    assert understanding.last_diagnostic.parse_error == "RuntimeError"
    assert understanding.last_diagnostic.final_route == "clarify"
