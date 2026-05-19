# External AI Services -- AptGuide 3.0

## LLM (Chat / Understanding)

| Property | Value |
|---|---|
| Provider | DashScope (Alibaba Cloud) |
| Model | `qwen-turbo-latest` |
| Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| SDK | `openai.OpenAI` (OpenAI-compatible) |
| Config key | `llm_base_url`, `llm_model` |
| API key config | `llm_api_key` (SecretStr; value never documented) |

### Usage

- Intent understanding (`LLMUnderstanding`) -- classifies user messages into tasks
- Preference scoring (`LLMPreferenceScorer`) -- ranks room search results by user preference
- Wrapped with LangSmith tracing when `langsmith_tracing=true`

---

## Embeddings

| Property | Value |
|---|---|
| Provider | OpenAI-compatible endpoint |
| Model | `text-embedding-3-small` |
| Base URL | `https://api.openai.com/v1` |
| SDK | Custom `EmbeddingClient` |
| Config key | `embedding_base_url`, `embedding_model` |
| API key config | `embedding_api_key` (SecretStr; value never documented) |

### Usage

- Generates vector embeddings for room text and KB chunks
- Vectors are stored in Milvus collections (`apt_room_vector`, `apt_rental_kb`)
- Query-time embedding for semantic search

---

## LangSmith (Observability)

| Property | Value |
|---|---|
| Provider | LangChain |
| Endpoint | `https://api.smith.langchain.com` |
| Project | `langsmith_project` (default `aptguide3-local`) |
| Config key | `langsmith_tracing`, `langsmith_project`, `langsmith_endpoint` |

### Usage

- Optional tracing layer for LLM calls
- Receives trace spans from the OpenAI client wrapper
- Does not store business data independently
- Enabled/disabled via `langsmith_tracing` (default `false`)

---

## API Keys

**No API keys, tokens, or secrets are documented in this file or anywhere in the data-inventory folder.** All credential values are stored in environment variables or `.env` files and accessed via `pydantic.SecretStr`.
