"""OpenAI-compatible LLM client for Xiaomi MiMo."""

from openai import AsyncOpenAI

from aptinsight.core.config import settings
from aptinsight.core.logging import get_logger

logger = get_logger(__name__)

client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    timeout=settings.llm_timeout_seconds,
)


async def generate(prompt: str, system: str = "") -> str:
    """Generate a text response from the LLM."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.1,
    )
    content = response.choices[0].message.content or ""
    logger.info("llm_generated", extra={"model": settings.llm_model, "tokens": response.usage})
    return content


async def generate_structured(prompt: str, system: str = "") -> str:
    """Generate a response expecting structured output (JSON)."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    logger.info("llm_structured_generated", extra={"model": settings.llm_model})
    return content
