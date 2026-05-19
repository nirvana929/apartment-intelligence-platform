"""Integration test: live Milvus vector store boundary verification.

Skipped unless APTGUIDE3_VECTOR_URI is set.
Tests a connection to Milvus and lists collections to verify the endpoint is reachable.
"""
import os
import time

import pytest

_HAS_VECTOR_URI = bool(os.environ.get("APTGUIDE3_VECTOR_URI"))

pytestmark = pytest.mark.skipif(
    not _HAS_VECTOR_URI,
    reason="APTGUIDE3_VECTOR_URI not set",
)


def test_vector_connection_boundary():
    """Connect to Milvus and list collections to verify the endpoint is reachable."""
    try:
        from pymilvus import MilvusClient
    except ImportError:
        pytest.skip("pymilvus not installed")

    uri = os.environ["APTGUIDE3_VECTOR_URI"]

    start = time.perf_counter()
    client = MilvusClient(uri=uri)
    collections = client.list_collections()
    latency_ms = (time.perf_counter() - start) * 1000

    # Boundary verification: connection succeeded, response is iterable
    assert isinstance(collections, list), f"Expected list, got {type(collections)}"

    # Record metadata for diagnostics
    collection_names = ", ".join(collections) if collections else "(none)"
    print(f"\n[Vector boundary] uri={uri} collections=[{collection_names}] latency={latency_ms:.0f}ms")
