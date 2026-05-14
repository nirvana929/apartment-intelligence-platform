from fastapi.testclient import TestClient

from aptguide3.api.app import create_app


def test_health():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "aptguide3"


def test_chat_returns_typed_response():
    client = TestClient(create_app())

    response = client.post("/chat", json={"message": "这个可以吗", "session_id": "s-1"})

    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert "phase" in body
    assert "metadata" in body
