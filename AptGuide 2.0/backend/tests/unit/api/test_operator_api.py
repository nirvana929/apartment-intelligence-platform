from unittest.mock import patch

from fastapi.testclient import TestClient


def _fake_settings():
    from aptguide2.core.config import Settings
    return Settings(
        operator_console_enabled=True,
        operator_dev_token="test-token",
    )


def test_operator_requires_token():
    from aptguide2.api.app import app

    with patch("aptguide2.api.deps.get_settings", return_value=_fake_settings()):
        client = TestClient(app)
        response = client.get("/operator/tickets")
        assert response.status_code == 401


def test_operator_can_list_tickets():
    from aptguide2.api.app import app

    with patch("aptguide2.api.deps.get_settings", return_value=_fake_settings()):
        client = TestClient(app)
        response = client.get("/operator/tickets", headers={"X-Operator-Token": "test-token"})
        assert response.status_code == 200
        assert "tickets" in response.json()


def test_operator_can_create_and_close_ticket():
    from aptguide2.api.app import app
    from aptguide2.api.operator import get_handoff_repository

    with patch("aptguide2.api.deps.get_settings", return_value=_fake_settings()):
        client = TestClient(app)
        repo = get_handoff_repository()

        # Create a ticket
        import asyncio
        ticket = asyncio.run(repo.create_ticket("u1", "s1", "user_initiated", {}))

        # List tickets
        response = client.get("/operator/tickets", headers={"X-Operator-Token": "test-token"})
        assert response.status_code == 200
        tickets = response.json()["tickets"]
        assert any(t["ticket_id"] == ticket.ticket_id for t in tickets)

        # Close ticket
        response = client.post(f"/operator/tickets/{ticket.ticket_id}/close", headers={"X-Operator-Token": "test-token"})
        assert response.status_code == 200
        assert response.json()["ok"] is True


def test_operator_console_disabled_returns_403():
    from aptguide2.api.app import app
    from aptguide2.core.config import Settings

    disabled_settings = Settings(
        operator_console_enabled=False,
        operator_dev_token="test-token",
    )

    with patch("aptguide2.api.deps.get_settings", return_value=disabled_settings):
        client = TestClient(app)
        response = client.get("/operator/tickets", headers={"X-Operator-Token": "test-token"})
        assert response.status_code == 403
        assert response.json()["detail"] == "operator console disabled"


def test_operator_console_rejects_default_token_in_staging():
    from aptguide2.api.app import app
    from aptguide2.core.config import Settings

    staging_settings = Settings(
        environment="staging",
        operator_console_enabled=True,
        operator_dev_token="operator-dev-token",
    )

    with patch("aptguide2.api.deps.get_settings", return_value=staging_settings):
        client = TestClient(app)
        response = client.get("/operator/tickets", headers={"X-Operator-Token": "operator-dev-token"})
        assert response.status_code == 500
        assert response.json()["detail"] == "operator token is not configured"
