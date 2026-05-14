from aptguide2.interaction.classifier import ClarifyingInteractionClassifier, LLMInteractionClassifier, apply_policy_corrections


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


def test_llm_classifier_uses_model_output_for_room_search():
    content = """
    {
      "raw_message": "有阳台的房间吗",
      "route": "rag",
      "rag_task": "room_search",
      "domain": "room",
      "action": "search",
      "needs_room_search": true,
      "hard_filters": {},
      "soft_preferences": ["有阳台"],
      "retrieval_queries": ["有阳台 房源"],
      "risk_level": "low",
      "response_mode": "normal_answer",
      "confidence": 0.92
    }
    """
    classifier = LLMInteractionClassifier(FakeClient(content=content), "fake-model", min_confidence=0.65)

    intent = classifier.classify("有阳台的房间吗")

    assert intent.route == "rag"
    assert intent.rag_task == "room_search"
    assert intent.soft_preferences == ["有阳台"]
    assert intent.retrieval_queries == ["有阳台 房源"]


def test_llm_classifier_failure_returns_clarification_not_keyword_guess():
    classifier = LLMInteractionClassifier(FakeClient(error=RuntimeError("timeout")), "fake-model", min_confidence=0.65)

    intent = classifier.classify("有阳台的房间吗")

    assert intent.route == "fallback"
    assert intent.action == "clarify"
    assert intent.response_mode == "ask_clarification"
    assert intent.clarification_needed is True


def test_llm_classifier_low_confidence_returns_clarification():
    content = """
    {
      "raw_message": "这个可以吗",
      "route": "rag",
      "rag_task": "kb_qa",
      "domain": "policy",
      "action": "ask_policy",
      "confidence": 0.3
    }
    """
    classifier = LLMInteractionClassifier(FakeClient(content=content), "fake-model", min_confidence=0.65)

    intent = classifier.classify("这个可以吗")

    assert intent.route == "fallback"
    assert intent.action == "clarify"


def test_clarifying_classifier_never_uses_keywords():
    intent = ClarifyingInteractionClassifier().classify("大学城附近1500以内安静房源")

    assert intent.route == "fallback"
    assert intent.action == "clarify"
    assert intent.response_mode == "ask_clarification"


def test_privacy_correction_still_refuses():
    intent = apply_policy_corrections(ClarifyingInteractionClassifier().classify("查一下室友手机号"))

    assert intent.route == "fallback"
    assert intent.risk_level == "high"
    assert intent.response_mode == "refuse"


def test_prompt_forbids_guessing_when_ambiguous():
    from aptguide2.interaction.prompts import INTERACTION_INTENT_SYSTEM_PROMPT

    assert "do not guess" in INTERACTION_INTENT_SYSTEM_PROMPT.lower()
    assert "clarification_needed" in INTERACTION_INTENT_SYSTEM_PROMPT
    assert "retrieval_queries" in INTERACTION_INTENT_SYSTEM_PROMPT
