"""E2E tests for the FastAPI /chat and /health endpoints."""

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


class TestChatRoomSearch:
    def test_room_search_returns_rooms(self):
        with patch("aptguide2.api.app.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.app.get_embed_fn", return_value=_fake_embed):
            from aptguide2.api.app import app
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "番禺区1500以内的房子"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "room_search"
            assert len(data["rooms"]) > 0
            assert data["rooms"][0]["room_id"] in (1, 2)

    def test_room_search_with_budget(self):
        with patch("aptguide2.api.app.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.app.get_embed_fn", return_value=_fake_embed):
            from aptguide2.api.app import app
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "找房2000以内"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "room_search"


class TestChatKBQA:
    def test_kb_qa_confident(self):
        with patch("aptguide2.api.app.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.app.get_embed_fn", return_value=_fake_embed), \
             patch("aptguide2.api.app.get_llm_client") as mock_llm:
            # Mock LLM response
            mock_choice = type("Choice", (), {"message": type("Msg", (), {"content": "押金在退租后15个工作日内退还。"})()})()
            mock_resp = type("Resp", (), {"choices": [mock_choice]})()
            mock_llm.return_value = type("Client", (), {
                "chat": type("Chat", (), {
                    "completions": type("Comp", (), {"create": lambda *a, **kw: mock_resp})()
                })()
            })()

            from aptguide2.api.app import app
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "押金什么时候退"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "kb_qa"
            assert data["is_confident"] is True
            assert len(data["kb_sources"]) > 0

    def test_kb_qa_low_confidence(self):
        # Override mock to return low-score KB results
        low_score_results = [
            {"chunk_id": "kb-lease-01#01", "doc_id": "kb-lease-01", "title": "押金退还规则",
             "module": "lease", "content": "押金相关。",
             "distance": 0.3, "risk_level": "high", "_recall_source": "original", "_matched_query": "押金"},
        ]

        class LowScoreAdapter(MockVectorAdapter):
            def search_kb(self, vector, filters=None, top_k=10):
                return low_score_results

        with patch("aptguide2.api.app.get_vector_adapter", return_value=LowScoreAdapter()), \
             patch("aptguide2.api.app.get_embed_fn", return_value=_fake_embed):
            from aptguide2.api.app import app
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "押金什么时候退"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "kb_qa"
            assert data["is_confident"] is False
            assert data["message"]  # should have fallback message


class TestChatFallback:
    def test_fallback_out_of_scope(self):
        with patch("aptguide2.api.app.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.app.get_embed_fn", return_value=_fake_embed):
            from aptguide2.api.app import app
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "帮我写代码"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "fallback"
            assert "超出" in data["message"] or "服务范围" in data["message"]

    def test_fallback_guarantee(self):
        with patch("aptguide2.api.app.get_vector_adapter", return_value=MockVectorAdapter()), \
             patch("aptguide2.api.app.get_embed_fn", return_value=_fake_embed):
            from aptguide2.api.app import app
            client = TestClient(app)
            resp = client.post("/chat", json={"message": "你保证没问题"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "fallback"
