"""Dependency injection for the API."""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from aptguide2.core.config import Settings
from aptguide2.tools.vector_adapter import VectorAdapter


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_vector_adapter() -> VectorAdapter:
    s = get_settings()
    return VectorAdapter(
        uri=s.milvus_uri,
        token=s.milvus_token,
        dim=s.embedding_dim,
    )


def get_embed_fn():
    """Return a sync embed function for the current settings."""
    s = get_settings()
    client = OpenAI(
        api_key=s.embedding_api_key.get_secret_value(),
        base_url=s.embedding_base_url,
    )

    def embed(text: str) -> list[float]:
        resp = client.embeddings.create(model=s.embedding_model, input=[text])
        return resp.data[0].embedding

    return embed


def get_llm_client() -> OpenAI:
    """Return an OpenAI-compatible LLM client."""
    s = get_settings()
    return OpenAI(
        api_key=s.llm_api_key.get_secret_value(),
        base_url=s.llm_base_url,
    )
