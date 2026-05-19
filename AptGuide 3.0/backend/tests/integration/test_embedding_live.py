"""Integration test: live embedding boundary verification.

Skipped unless APTGUIDE3_EMBEDDING_BASE_URL and APTGUIDE3_EMBEDDING_API_KEY are set.
Tests a single embedding call to verify the external endpoint responds with expected shape.
"""
import os
import time

import pytest

_HAS_EMBEDDING_CREDS = bool(
    os.environ.get("APTGUIDE3_EMBEDDING_BASE_URL")
    and os.environ.get("APTGUIDE3_EMBEDDING_API_KEY")
)

pytestmark = pytest.mark.skipif(
    not _HAS_EMBEDDING_CREDS,
    reason="APTGUIDE3_EMBEDDING_BASE_URL / APTGUIDE3_EMBEDDING_API_KEY not set",
)


def test_embedding_boundary():
    """Send one embedding request and verify response is a list of floats."""
    from aptguide3.integrations.embedding_client import EmbeddingClient

    base_url = os.environ["APTGUIDE3_EMBEDDING_BASE_URL"]
    api_key = os.environ["APTGUIDE3_EMBEDDING_API_KEY"]
    model = os.environ.get("APTGUIDE3_EMBEDDING_MODEL", "text-embedding-3-small")

    client = EmbeddingClient(base_url=base_url, api_key=api_key, model=model)

    start = time.perf_counter()
    result = client.embed("测试向量嵌入")
    latency_ms = (time.perf_counter() - start) * 1000

    # Boundary verification: response is a list of floats
    assert isinstance(result, list), f"Expected list, got {type(result)}"
    assert len(result) > 0, "Embedding returned empty list"
    assert all(isinstance(v, (int, float)) for v in result), "Embedding contains non-numeric values"

    # Record metadata for diagnostics
    print(f"\n[Embedding boundary] model={model} dim={len(result)} latency={latency_ms:.0f}ms")
