"""E2E tests for the FastAPI /chat and /health endpoints.

All /chat requests now go through the harness mainline.
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

MOCK_ROOM_RESULTS = [
    {"room_id": 1, "apartment_id": 10, "distance": 0.9},
    {"room_id": 2, "apartment_id": 10, "distance": 0.8},
]

MOCK_KB_RESULTS = [
    {"chunk_id": "kb-lease-01#01", "doc_id": "kb-lease-01", "title": "押金退还规则",
     "module": "lease", "content": "押金在退租后15个工作日内退还。",
     "distance": 0.85, "risk_level": "high", "_recall_source": "original", "_matched_query": "押金"},
]

MOCK_ROOM_ENRICHED = [
    {"room_id": 1, "apartment_id": 10, "district_id": 1005, "district_name": "番禺区",
     "rent": 1500, "payment_types": ["月付"], "lease_terms": [6, 12],
     "tags": ["近地铁", "安静"], "facilities": ["空调", "WiFi"], "semantic_score": 0.9, "matched_query": "番禺"},
    {"room_id": 2, "apartment_id": 10, "district_id": 1005, "district_name": "番禺区",
     "rent": 1800, "payment_types": ["季付"], "lease_terms": [12],
     "tags": ["采光好"], "facilities": ["洗衣机"], "semantic_score": 0.8, "matched_query": "番禺"},
]


class MockVectorAdapter:
    def __init__(self, **kwargs):
        pass

    def _ensure_client(self):
        m = type("C", (), {"has_collection": lambda s, n: True})()
        return m

    def search_rooms(self, vector, filters=None, top_k=30):
        return MOCK_ROOM_RESULTS

    def search_kb(self, vector, filters=None, top_k=10):
        return MOCK_KB_RESULTS

    def get_room_by_ids(self, room_ids):
        return MOCK_ROOM_ENRICHED


def _fake_embed(text: str) -> list[float]:
    return [0.1] * 1024


def _fake_settings():
    from aptguide2.core.config import Settings
    return Settings(
        milvus_uri="http://localhost:19530",
        embedding_api_key="sk-test",
        embedding_base_url="https://example.com/v1",
        embedding_model="test",
        embedding_dim=1024,
        llm_api_key="sk-test",
        llm_base_url="https://example.com/v1",
        llm_model="test",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_ok(self):
        with patch("aptguide2.api.app.get_vector_adapter", return_value=MockVectorAdapter()):
            from aptguide2.api.app import app
            client = TestClient(app)
            resp = client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"


class TestChatMainline:
    """All /chat requests go through harness mainline."""

    def test_capability(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        settings.pipeline_version = "harness_v1"
        settings.harness_include_trace = False
        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "你能做什么", "session_id": "s-cap"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "capability"
            assert "phase" in data
            assert isinstance(data["actions"], list)
            assert isinstance(data["metadata"], dict)

    def test_room_search(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        settings.pipeline_version = "harness_v1"
        settings.harness_include_trace = False
        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "番禺区1500以内的房子", "session_id": "s-room"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "room_search"

    def test_fallback_out_of_scope(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        settings.pipeline_version = "harness_v1"
        settings.harness_include_trace = False
        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "帮我写代码", "session_id": "s-fb"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "fallback"

    def test_handoff(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        settings.pipeline_version = "harness_v1"
        settings.harness_include_trace = False
        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "转人工", "session_id": "s-handoff"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "handoff"


class TestHarnessAppointmentAPI:
    def test_harness_chat_exposes_pending_action_and_actions(self):
        from aptguide2.api.app import app

        settings = _fake_settings()
        settings.pipeline_version = "harness_v1"
        settings.harness_include_trace = False

        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            resp = client.post(
                "/chat",
                json={
                    "session_id": "s-api-confirm-1",
                    "user_id": "u-1",
                    "message": "预约101号房明天下午3点",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "appointment"
            assert data["pending_action"]["type"] == "appointment.create"
            assert data["actions"]
            assert data["metadata"]["procedure"] == "appointment.workflow"

    def test_harness_chat_accepts_action_for_pending_confirmation(self):
        from aptguide2.api.app import app

        settings = _fake_settings()
        settings.pipeline_version = "harness_v1"
        settings.harness_include_trace = False

        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            first = client.post(
                "/chat",
                json={
                    "session_id": "s-api-confirm-2",
                    "user_id": "u-1",
                    "message": "预约101号房明天下午3点",
                },
            ).json()

            resp = client.post(
                "/chat",
                json={
                    "session_id": "s-api-confirm-2",
                    "user_id": "u-1",
                    "message": "确认",
                    "action": {
                        "type": "confirm",
                        "confirmation_id": first["pending_action"]["confirmation_id"],
                    },
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "appointment"
            assert data["phase"] in {"appointment_created", "appointment_failed"}
