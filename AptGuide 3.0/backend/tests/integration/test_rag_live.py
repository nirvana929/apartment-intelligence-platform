"""Skip-safe live integration tests for the RAG room_search and kb_qa procedures.

These tests exercise the full LLM-first RAG pipeline: LLM understanding ->
retrieval plan -> vector recall -> validation/reranking -> response composition.

All tests are skipped unless ALL of the following env vars are set and non-empty:
  - APTGUIDE3_LIVE_TESTS=1
  - APTGUIDE3_LLM_API_KEY
  - APTGUIDE3_EMBEDDING_API_KEY
  - APTGUIDE3_VECTOR_URI
  - APTGUIDE3_LEASE_BASE_URL

To run:
  APTGUIDE3_LIVE_TESTS=1 \
  APTGUIDE3_LLM_API_KEY=<key> \
  APTGUIDE3_EMBEDDING_API_KEY=<key> \
  APTGUIDE3_VECTOR_URI=http://127.0.0.1:19530 \
  APTGUIDE3_LEASE_BASE_URL=http://127.0.0.1:8081 \
  uv run pytest tests/integration/test_rag_live.py -v
"""

from __future__ import annotations

import os
import uuid

import pytest

# ---------------------------------------------------------------------------
# Skip logic: require all live-service env vars
# ---------------------------------------------------------------------------

_REQUIRED_ENV_VARS = [
    "APTGUIDE3_LIVE_TESTS",
    "APTGUIDE3_LLM_API_KEY",
    "APTGUIDE3_EMBEDDING_API_KEY",
    "APTGUIDE3_VECTOR_URI",
    "APTGUIDE3_LEASE_BASE_URL",
]


def _missing_env_reasons() -> list[str]:
    """Return a list of missing-or-empty env var descriptions."""
    reasons = []
    for var in _REQUIRED_ENV_VARS:
        val = os.environ.get(var, "")
        if var == "APTGUIDE3_LIVE_TESTS":
            if val != "1":
                reasons.append(f"{var} is not '1' (got {val!r})")
        else:
            if not val:
                reasons.append(f"{var} is not set or is empty")
    return reasons


_missing = _missing_env_reasons()

pytestmark = pytest.mark.skipif(
    bool(_missing),
    reason="RAG live tests skipped: " + "; ".join(_missing) if _missing else "all env vars present",
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fresh_caches():
    """Clear LRU caches so each test reads current env vars."""
    from aptguide3.api.deps import get_chat_service
    from aptguide3.config import get_settings

    get_settings.cache_clear()
    get_chat_service.cache_clear()
    yield
    get_settings.cache_clear()
    get_chat_service.cache_clear()


@pytest.fixture()
def chat_service():
    """Return a fully-wired ChatService with real LLM, vector, embedding, lease."""
    from aptguide3.api.deps import get_chat_service

    return get_chat_service()


@pytest.fixture()
def session_id():
    """Return a unique session ID for each test."""
    return f"rag-live-{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _send(chat_service, message: str, session_id: str):
    """Send a message through ChatService and return the ChatResponse."""
    from aptguide3.domain.conversation import ConversationFrame

    frame = ConversationFrame(message=message, session_id=session_id)
    return chat_service.run(frame)


def _has_room_cards(response) -> bool:
    """True if response contains at least one room_card with room_id > 0."""
    return any(
        c.get("type") == "room_card" and c.get("room_id", 0) > 0
        for c in response.cards
    )


def _has_source_cards(response) -> bool:
    """True if response contains at least one kb_source card."""
    return any(c.get("type") == "kb_source" for c in response.cards)


def _all_room_ids_valid(response) -> bool:
    """Every room_card in the response must have room_id > 0."""
    for card in response.cards:
        if card.get("type") == "room_card":
            room_id = card.get("room_id", 0)
            if not isinstance(room_id, int) or room_id <= 0:
                return False
    return True


# ---------------------------------------------------------------------------
# Tests -- room_search
# ---------------------------------------------------------------------------


class TestRoomSearchLive:
    """RAG room_search end-to-end through ChatService."""

    def test_room_search_returns_valid_response(self, chat_service, session_id):
        """Room search returns either room cards or a conservative fallback message.

        In a live environment the LLM should route to room_search.  Whether
        the vector/lease pipeline returns rooms depends on data availability,
        so we accept both outcomes: real cards (room_id > 0) or a helpful
        fallback message.
        """
        resp = _send(chat_service, "帮我找一间朝阳区的单间", session_id)

        assert resp.message, "response message must not be empty"
        assert resp.phase, "response phase must not be empty"

        if _has_room_cards(resp):
            assert _all_room_ids_valid(resp), (
                "room cards present but some have invalid room_id"
            )

    def test_room_search_no_unvalidated_cards(self, chat_service, session_id):
        """Every room_card in the response must have room_id > 0.

        This guards against the anti-regression requirement: no room card
        should ever reach the user without a validated room_id from the
        lease client.
        """
        resp = _send(chat_service, "有没有朝阳区的房子，预算3000", session_id)
        assert _all_room_ids_valid(resp), (
            "found room_card with room_id <= 0; "
            "this indicates an unvalidated card leaked through the pipeline"
        )

    def test_room_search_cards_have_required_fields(self, chat_service, session_id):
        """If room cards are present, they must contain the expected fields."""
        resp = _send(chat_service, "帮我找海淀区的整租", session_id)

        for card in resp.cards:
            if card.get("type") == "room_card":
                assert "room_id" in card, "room_card missing room_id"
                assert "apartment_name" in card, "room_card missing apartment_name"
                assert "rent" in card, "room_card missing rent"
                assert "final_score" in card, "room_card missing final_score"


# ---------------------------------------------------------------------------
# Tests -- kb_qa
# ---------------------------------------------------------------------------


class TestKbQaLive:
    """RAG kb_qa end-to-end through ChatService."""

    def test_kb_qa_returns_valid_response(self, chat_service, session_id):
        """KB question returns either source cards or a confidence fallback.

        The LLM should route to kb_qa for knowledge questions.  Depending on
        confidence gate results, the response may contain source cards or a
        conservative fallback message.
        """
        resp = _send(chat_service, "租房需要注意哪些法律问题？", session_id)

        assert resp.message, "response message must not be empty"
        assert resp.phase, "response phase must not be empty"

        # Either we get source cards or a fallback -- both are valid outcomes
        if _has_source_cards(resp):
            for card in resp.cards:
                if card.get("type") == "kb_source":
                    assert "chunk_id" in card, "kb_source missing chunk_id"
                    assert "content_snippet" in card, "kb_source missing content_snippet"

    def test_kb_qa_source_cards_have_fields(self, chat_service, session_id):
        """If source cards are present, they must contain expected fields."""
        resp = _send(chat_service, "退租的流程是什么？", session_id)

        for card in resp.cards:
            if card.get("type") == "kb_source":
                assert "chunk_id" in card
                assert "doc_id" in card
                assert "title" in card
                assert "content_snippet" in card
                assert "score" in card
