"""Integration test: live LLM boundary verification.

Skipped unless APTGUIDE3_LLM_BASE_URL and APTGUIDE3_LLM_API_KEY are set.
Tests a single minimal chat completion to verify the external LLM endpoint responds.
"""
import os
import time

import pytest
from openai import OpenAI

_HAS_LLM_CREDS = bool(
    os.environ.get("APTGUIDE3_LLM_BASE_URL")
    and os.environ.get("APTGUIDE3_LLM_API_KEY")
)

pytestmark = pytest.mark.skipif(
    not _HAS_LLM_CREDS,
    reason="APTGUIDE3_LLM_BASE_URL / APTGUIDE3_LLM_API_KEY not set",
)


def test_llm_chat_completion_boundary():
    """Send one minimal structured-understanding request and verify response shape."""
    base_url = os.environ["APTGUIDE3_LLM_BASE_URL"]
    api_key = os.environ["APTGUIDE3_LLM_API_KEY"]
    model = os.environ.get("APTGUIDE3_LLM_MODEL", "qwen-turbo-latest")

    client = OpenAI(base_url=base_url, api_key=api_key)

    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "你好"}],
        max_tokens=32,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    # Boundary verification: response shape
    assert response.choices, "LLM response has no choices"
    assert response.choices[0].message.content, "LLM response content is empty"

    # Record metadata for diagnostics
    print(f"\n[LLM boundary] model={response.model} latency={latency_ms:.0f}ms")
