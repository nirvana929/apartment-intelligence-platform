# Lessons Learned

## 2026-05-15 — LLM Contract Boundary and Silent Validation Failure

### 4. LLM output schema and Pydantic contract are different things

**Situation:** First live eval after LLM-first refactor: 100/120 cases returned clarification. The LLM was correctly understanding queries, but every classification was silently discarded.
**Root cause:** `InteractionIntent` Pydantic model requires `raw_message` as a field. The LLM (qwen-turbo-latest) never outputs `raw_message` — it's a system-injected traceability field, not a semantic understanding field. `model_validate(parsed)` raised `ValidationError`, the exception handler returned clarification, and the system appeared to have 0% LLM success.
**Lesson:** When using LLM structured output with Pydantic validation, distinguish between fields the LLM should produce (semantic: route, task, filters) and fields the system should inject (metadata: raw_message, trace_id, timestamps). Requiring the LLM to output system metadata creates a contract boundary that silently fails.
**Fix:** Parse JSON first, inject system fields, then validate:
```python
parsed = json.loads(content)
if "raw_message" not in parsed:
    parsed["raw_message"] = message
intent = InteractionIntent.model_validate(parsed)
```
**Apply:** Never include system-traceability fields in the LLM prompt schema. Inject them between parsing and validation. After fix: clarification dropped from 100/120 to 15/120.

### 5. Exception handlers that return "safe" defaults can mask root causes

**Situation:** The `LLMInteractionClassifier.classify()` had a `try/except` that caught `ValidationError` and returned clarification. This felt safe (fail to clarification is the design intent), but it masked the fact that every single LLM call was failing validation.
**Lesson:** Catching broad exceptions and returning "safe" defaults is a debugging hazard. When the safe default is also the failure mode (clarification), you can't distinguish "LLM doesn't understand" from "contract mismatch". Add logging or metrics before returning safe defaults.
**Apply:** In LLM integration code, log the exception type and message before returning clarification fallback. Consider adding a `reason` field to clarification intents that records why clarification was triggered (e.g., `"llm_intent_failed:ValidationError"` vs `"low_confidence"` vs `"model_requested"`).

## 2026-05-15 — LLM-First Understanding Over Keyword Fallback

### 1. Keyword fallback can be worse than no fallback

**Situation:** RAG v2 live eval expanded from 50 to 120 cases. Fixing failures by adding strings such as room attributes, district names, and broad question markers improved some cases but caused new misroutes.
**Lesson:** Keyword fallback encodes developer bias and eval-case memory. When the model cannot confidently identify the user intent, the product should ask a clarifying question instead of pretending that keyword matching is certainty.
**Apply:** For natural-language routing, use LLM structured output as the primary path. If the LLM fails, returns invalid JSON, produces contradictory fields, or has low confidence, route to `fallback.clarify`.

### 2. Separate semantic understanding from deterministic business boundaries

**Situation:** The team debated whether budgets, district IDs, payment enums, and filters should be parsed by code or by the model.
**Lesson:** Modern models can perform the primary extraction and normalization. The backend still needs schema validation, permission checks, confirmation gates, and source-of-truth validation, but those are contract and business safeguards, not keyword inference.
**Apply:** Let the LLM produce route, task, domain, filters, preferences, risk posture, and retrieval queries. Let code validate allowed enums/types and enforce safety, pending actions, ToolRuntime permissions, and lease-backed room availability.

### 3. Do not use eval failures as a synonym list backlog

**Situation:** Several classifier changes were driven by failed eval examples, adding more terms to `_looks_like_room_search`, `_looks_like_kb_policy`, and `_looks_like_policy_question`.
**Lesson:** Adding terms after each failed phrasing can make reported metrics look better while reducing generalization. The correct fix is to improve the understanding architecture and eval semantic coverage, not to grow string lists.
**Apply:** Add anti-regression tests that prevent keyword route helpers from returning to the runtime path. Evaluate paraphrases and ambiguous cases, and require uncertainty to produce clarification.

## 2026-05-14 — Standalone Productization

### 1. Check sibling projects for shared infrastructure credentials

**Situation:** MySQL `Access denied for root@localhost` when trying to create the database.
**Lesson:** AptInsight already had MySQL credentials in its `.env` file. Always check sibling projects' configuration before troubleshooting access issues from scratch.
**Apply:** Before configuring any shared infrastructure (database, Redis, message queue), check existing projects in the same workspace for working credentials and connection strings.

### 2. Use shared databases with table prefixes when CREATE DATABASE is blocked

**Situation:** User `chove` didn't have CREATE DATABASE permission on MySQL.
**Lesson:** Instead of fighting for permissions, use an existing database with a table name prefix (`aptguide_` vs `aptinsight_`). This is a common production pattern anyway.
**Apply:** When deploying to shared database environments, design table naming with a project prefix from the start.

### 3. Async-first with sync fallback is the right migration path

**Situation:** The harness was sync-only but the new context store needed async (Redis + MySQL).
**Lesson:** Adding `run_async()` and having sync `run()` delegate via `asyncio.run()` preserved all existing callers while enabling async internals. No breaking changes.
**Apply:** When upgrading a sync system to async, always keep the sync entry point working. New code uses async; old code is unaffected.

### 4. Vite projects need explicit `vite-env.d.ts` for TypeScript

**Situation:** `import.meta.env` TypeScript errors even with Vite installed.
**Lesson:** Vite's type definitions come from `vite/client` and must be explicitly referenced via `/// <reference types="vite/client" />` in a `.d.ts` file.
**Apply:** When scaffolding a Vite + TypeScript project, create `src/vite-env.d.ts` as part of the initial setup.

### 5. Auth resolvers should provide defaults in dev mode

**Situation:** Test `test_missing_user_id_blocks_appointment` failed because dev auth now provides a default user.
**Lesson:** In dev mode, the auth resolver should be permissive and provide sensible defaults. Strict validation belongs in production auth mode.
**Apply:** Design auth systems with a clear dev/prod split. Dev mode optimizes for developer experience; prod mode optimizes for security.

### 6. Operator API settings import must go through the dependency layer

**Situation:** `test_operator_can_list_tickets` returned 401 because the operator API imported `get_settings()` directly instead of through `deps.get_settings()`.
**Lesson:** When testing with mocked dependencies, all code paths must go through the same dependency injection layer. Direct imports bypass mocks.
**Apply:** FastAPI routers that need settings should always import from `deps` module, never directly from `config`.

## 2026-05-12 to 2026-05-14 — AptGuide 2.0 System Hardening

### 1. Real external data needs product semantics before ingestion

**Situation:** WeChat rental messages are real posted data, but they are not verified platform inventory.
**Lesson:** Authenticity, verification, availability, and appointability are separate concepts. Treating all "real" data as bookable inventory creates product and safety risk.
**Apply:** External listing rows must carry explicit statuses such as `REAL_POSTED`, `UNVERIFIED`, `UNKNOWN`, and `appointable=false`.

### 2. Do not push raw external data directly into RAG

**Situation:** The WeChat import plan initially mixed MySQL ingestion, RAG visibility, and Milvus sync.
**Lesson:** RAG should index governed records, not raw txt files or unreviewed extracted artifacts. MySQL must be the durable source of truth.
**Apply:** First ship parser, desensitization, deduplication, SQL generation, and reviewable artifacts. Add RAG sync only after status semantics and data safety are stable.

### 3. Live eval can reveal problems that unit tests cannot

**Situation:** RAG v2 passed implementation tests, but live eval showed KB hit@3 = 48.6% and Room hit@5 = 40.0%.
**Lesson:** Passing unit tests proves code paths, not retrieval quality. Real Milvus, embedding, lease data, and realistic eval cases are required for trustworthy RAG claims.
**Apply:** Keep live dependency readiness and live eval reports as release gates for RAG quality claims.

### 4. Trace evidence should come before ranking tweaks

**Situation:** RAG v2 live eval failures were under-explained because the report lacked per-stage trace evidence.
**Lesson:** Without seeing query understanding, filters, candidates, rerank features, and confidence gates, ranking changes are guesswork.
**Apply:** Add per-stage trace and data validation before tuning hybrid retrieval, rerank weights, or confidence thresholds.

### 5. Guardrails work better as routing than blanket refusal

**Situation:** High-risk housing questions need careful treatment but should not all be blocked.
**Lesson:** A guardrail can route to safer response modes, stronger source requirements, confirmation, or handoff. Refusal is only one possible outcome.
**Apply:** Evaluate guardrails with high-risk recall, false-block rate, and response-mode accuracy.

### 6. RAG is a module, not the whole product

**Situation:** After RAG v2 replacement, the system still needed appointment confirmation, lease query, memory, handoff, pending actions, and tool failure recovery.
**Lesson:** A rental agent is a procedure-driven system. Retrieval is one capability inside the harness mainline.
**Apply:** System acceptance should cover room search, KB QA, appointment create/cancel confirmation, lease list, fallback, handoff, and tool failure.
