"""System mainline e2e tests.

These tests validate that /chat goes through harness mainline
and returns a consistent response shape for all covered flows.
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from aptguide2.interaction.classifier import ClarifyingInteractionClassifier
from aptguide2.interaction.contracts import InteractionIntent


class MockVectorAdapter:
    def __init__(self, **kwargs):
        pass

    def _ensure_client(self):
        m = type("C", (), {"has_collection": lambda s, n: True})()
        return m

    def search_rooms(self, vector, filters=None, top_k=30):
        return []

    def search_kb(self, vector, filters=None, top_k=10):
        return []

    def get_room_by_ids(self, room_ids):
        return []


def _fake_embed(text: str) -> list[float]:
    return [0.1] * 1024


def _fake_settings(**overrides):
    from aptguide2.core.config import Settings
    defaults = dict(
        milvus_uri="http://localhost:19530",
        embedding_api_key="sk-test",
        embedding_base_url="https://example.com/v1",
        embedding_model="test",
        embedding_dim=1024,
        llm_api_key="sk-test",
        llm_base_url="https://example.com/v1",
        llm_model="test",
        pipeline_version="harness_v1",
        harness_include_trace=False,
        intent_classifier_mode="clarify_only",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def assert_system_response_shape(data: dict) -> None:
    """Assert the response has all required system fields."""
    assert isinstance(data["task"], str)
    assert isinstance(data["message"], str)
    assert "phase" in data
    assert isinstance(data["cards"], list)
    assert isinstance(data["actions"], list)
    assert "pending_action" in data
    assert isinstance(data["metadata"], dict)
    assert isinstance(data["rooms"], list)
    assert isinstance(data["kb_sources"], list)


class TestSystemResponseShape:
    def test_capability_response_shape(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            response = client.post("/chat", json={"message": "你能做什么", "session_id": "s-mainline"})
            assert response.status_code == 200
            assert_system_response_shape(response.json())

    def test_handoff_response_shape(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            response = client.post("/chat", json={"message": "转人工", "session_id": "s-handoff"})
            assert response.status_code == 200
            assert_system_response_shape(response.json())

    def test_fallback_response_shape(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            response = client.post("/chat", json={"message": "帮我写代码", "session_id": "s-fb"})
            assert response.status_code == 200
            assert_system_response_shape(response.json())


class TestMainlineAcceptance:
    def test_appointment_create_returns_pending_action(self):
        from aptguide2.api.app import app
        settings = _fake_settings()

        class AppointmentClassifier:
            def classify(self, message):
                return InteractionIntent(
                    raw_message=message,
                    route="appointment",
                    domain="appointment",
                    action="create",
                    needs_tool=True,
                    needs_confirmation=True,
                    confidence=0.82,
                )

        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed), \
             patch("aptguide2.api.deps.get_interaction_classifier", return_value=AppointmentClassifier()):
            client = TestClient(app)
            response = client.post(
                "/chat",
                json={"message": "预约200013号房明天下午3点", "session_id": "s-appt", "user_id": "u-1"},
            )
            data = response.json()

            assert response.status_code == 200
            assert data["task"] == "appointment"
            assert data["pending_action"]["type"] == "appointment.create"
            assert data["actions"][0]["type"] == "confirm"

    def test_dev_auth_provides_default_user_for_appointment(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        settings.auth_mode = "dev"
        settings.dev_user_id = "dev-user-001"

        class AppointmentClassifier:
            def classify(self, message):
                return InteractionIntent(
                    raw_message=message,
                    route="appointment",
                    domain="appointment",
                    action="create",
                    needs_tool=True,
                    needs_confirmation=True,
                    confidence=0.82,
                )

        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed), \
             patch("aptguide2.api.deps.get_interaction_classifier", return_value=AppointmentClassifier()):
            client = TestClient(app)
            response = client.post(
                "/chat",
                json={"message": "预约200013号房明天下午3点", "session_id": "s-auth"},
            )
            data = response.json()

            assert response.status_code == 200
            assert data["task"] == "appointment"
            assert data["pending_action"] is not None
            assert data["pending_action"]["type"] == "appointment.create"

    def test_default_runtime_is_harness(self):
        from aptguide2.core.config import Settings
        assert Settings().pipeline_version == "harness_v1"

    def test_chat_response_includes_request_and_trace_ids(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.deps.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.deps.get_embed_fn", return_value=_fake_embed):
            client = TestClient(app)
            response = client.post("/chat", json={"message": "你能做什么", "session_id": "s-ids"})
            data = response.json()
            assert response.status_code == 200
            assert isinstance(data["request_id"], str) and data["request_id"].startswith("r-")
            assert isinstance(data["trace_id"], str) and len(data["trace_id"]) > 0


class TestReadinessEndpoint:
    def test_ready_endpoint_returns_required_dependency_report(self):
        from aptguide2.api.app import app
        settings = _fake_settings()
        with patch("aptguide2.api.deps.get_settings", return_value=settings), \
             patch("aptguide2.api.app.get_settings", return_value=settings):
            client = TestClient(app)
            response = client.get("/ready")
            assert response.status_code == 200
            data = response.json()
            assert "ready" in data
            assert isinstance(data["ready"], bool)
            assert isinstance(data["checks"], list)
            check_names = [c["name"] for c in data["checks"]]
            assert "pipeline" in check_names
            assert "auth_mode" in check_names
            assert "mysql_config" in check_names
            assert "redis_config" in check_names
            assert "lease_config" in check_names
            assert "milvus_config" in check_names
            assert "embedding_config" in check_names
