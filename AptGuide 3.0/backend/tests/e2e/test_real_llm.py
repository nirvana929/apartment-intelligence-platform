import os

import pytest
from fastapi.testclient import TestClient

from aptguide3.api.app import create_app

HAS_API_KEY = bool(os.environ.get("APTGUIDE3_LLM_API_KEY"))

pytestmark = pytest.mark.skipif(not HAS_API_KEY, reason="APTGUIDE3_LLM_API_KEY not set")


@pytest.fixture()
def client():
    return TestClient(create_app())


def test_room_search_intent(client):
    response = client.post("/chat", json={"message": "珠江新城3000以内有阳台的房间", "session_id": "e2e-search"})

    assert response.status_code == 200
    body = response.json()
    meta = body["metadata"]
    assert meta["route"] in ("rag", "clarify")
    assert meta["task"] in ("room_search", "clarify")


def test_ambiguous_returns_clarification(client):
    response = client.post("/chat", json={"message": "这个可以吗", "session_id": "e2e-clarify"})

    assert response.status_code == 200
    body = response.json()
    assert body["phase"] == "clarify"
    meta = body["metadata"]
    assert meta["route"] == "clarify"
    assert meta["task"] == "clarify"
