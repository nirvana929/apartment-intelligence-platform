"""Real Playwright E2E tests for the AptGuide 3.0 frontend chat flow.

Requires the backend to be running at http://127.0.0.1:8100.
Tests are skipped automatically when the server is unreachable.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8100"
SCREENSHOT_DIR = Path(__file__).resolve().parents[2] / "evals" / "reports" / "frontend-e2e"


def _server_reachable() -> bool:
    """Return True if the backend is accepting TCP connections."""
    try:
        with socket.create_connection(("127.0.0.1", 8100), timeout=2):
            return True
    except OSError:
        return False


skip_if_down = pytest.mark.skipif(not _server_reachable(), reason="Backend not running at :8100")


def _screenshot_on_failure(page: Page, test_name: str) -> None:
    """Save a screenshot when a test fails."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{test_name}.png"
    page.screenshot(path=str(path), full_page=True)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@skip_if_down
def test_frontend_loads_without_console_errors(page: Page) -> None:
    """The page loads cleanly: title, input, and submit button are visible; no console errors."""
    errors: list[str] = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

    try:
        page.goto(BASE_URL, wait_until="networkidle")

        # Title visible
        expect(page.locator("h1")).to_contain_text("AptGuide")

        # Chat input visible
        input_el = page.locator('input[type="text"]')
        expect(input_el).to_be_visible()

        # Submit button visible
        btn = page.locator('button[type="submit"]')
        expect(btn).to_be_visible()

        # No console errors (ignore network noise like favicon)
        real_errors = [e for e in errors if "favicon" not in e.lower()]
        assert not real_errors, f"Console errors: {real_errors}"

    except Exception:
        _screenshot_on_failure(page, "test_frontend_loads_without_console_errors")
        raise


@skip_if_down
def test_frontend_sends_message_and_renders_reply(page: Page) -> None:
    """Send a message and verify both user and assistant bubbles appear with text."""
    try:
        page.goto(BASE_URL, wait_until="networkidle")

        input_el = page.locator('input[type="text"]')
        btn = page.locator('button[type="submit"]')

        input_el.fill("你好")
        btn.click()

        # User bubble appears
        user_bubble = page.locator(".message.user .bubble .text").first
        expect(user_bubble).to_be_visible(timeout=5000)
        expect(user_bubble).to_have_text("你好")

        # Wait for assistant bubble (typing indicator disappears)
        page.locator(".bubble.typing").wait_for(state="hidden", timeout=30000)

        assistant_bubble = page.locator(".message.assistant .bubble .text").first
        expect(assistant_bubble).to_be_visible(timeout=5000)
        text_content = assistant_bubble.text_content()
        assert text_content and len(text_content.strip()) > 0, "Assistant reply is empty"

    except Exception:
        _screenshot_on_failure(page, "test_frontend_sends_message_and_renders_reply")
        raise


@skip_if_down
def test_frontend_posts_to_chat_endpoint(page: Page) -> None:
    """Verify the frontend sends a POST to /chat and receives a response."""
    post_requests: list[dict] = []

    def on_request(request) -> None:
        if request.method == "POST" and "/chat" in request.url:
            post_requests.append({"url": request.url, "data": request.post_data})

    page.on("request", on_request)

    try:
        page.goto(BASE_URL, wait_until="networkidle")

        input_el = page.locator('input[type="text"]')
        btn = page.locator('button[type="submit"]')

        input_el.fill("找番禺1500以内安静一点的房子")
        btn.click()

        # Wait for assistant response
        page.locator(".bubble.typing").wait_for(state="hidden", timeout=30000)
        assistant_bubble = page.locator(".message.assistant .bubble .text").first
        expect(assistant_bubble).to_be_visible(timeout=5000)

        # Verify at least one POST to /chat was made
        assert len(post_requests) >= 1, f"Expected POST to /chat, got {len(post_requests)} requests"
        assert "/chat" in post_requests[0]["url"]

    except Exception:
        _screenshot_on_failure(page, "test_frontend_posts_to_chat_endpoint")
        raise
