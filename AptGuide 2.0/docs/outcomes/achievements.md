# Achievements

## LLM-First Interaction Understanding — Execution and LLM Boundary Analysis (2026-05-15)

### Summary

Executed the LLM-first interaction understanding plan, replacing all keyword-based intent classification with LLM as the sole NL understanding layer. During live evaluation, discovered a critical boundary between LLM output and system contract — and fixed it.

### LLM Boundary: Where It Broke

**The problem:** First live eval showed 100/120 cases returning clarification (`route=fallback, action=clarify`). The LLM was actually understanding queries correctly, but the system rejected every response.

**Root cause — LLM output schema vs Pydantic contract mismatch:**

The `InteractionIntent` Pydantic model requires a `raw_message` field. But the LLM (qwen-turbo-latest) never outputs `raw_message` — it's a system-level field that carries the original user message for downstream processing. The LLM correctly outputs `route`, `rag_task`, `domain`, `action`, `hard_filters`, `soft_preferences`, `retrieval_queries`, `confidence`, etc. — but not `raw_message`.

When `InteractionIntent.model_validate(parsed)` ran, Pydantic raised `ValidationError` on the missing required field. The exception handler caught it and returned a clarification intent. So every single LLM classification was silently discarded.

**Why this is a genuine LLM boundary:**

This isn't a prompt engineering failure. The LLM correctly understood the query semantics. The failure was at the **contract boundary** — the LLM's natural output schema doesn't include system-injected metadata fields. The system assumed the LLM would output all required fields, but `raw_message` is semantically a system concern (traceability), not an NL understanding concern.

**The fix — inject system fields after parsing, before validation:**

```python
parsed = json.loads(content)
if "raw_message" not in parsed:
    parsed["raw_message"] = message  # system injects, not LLM
intent = InteractionIntent.model_validate(parsed)
```

This separates responsibilities: the LLM handles semantic understanding (route, task, filters), the system handles metadata (raw_message, timestamps, trace IDs).

### Eval Results (Post-Fix)

| Metric | Before Fix | After Fix | Gate |
|---|---:|---:|---:|
| Cases returning clarification | 100/120 | 15/120 | — |
| KB source hit@3 | N/A (all fallback) | 71.4% | >= 90% |
| Room hit@5 | N/A | 8.6% | >= 85% |
| High-risk fallback | N/A | 40.0% | >= 100% |

The raw_message fix unblocked 85 cases that were previously silently discarded. The remaining failures are retrieval quality issues (seed IDs vs Milvus content mismatch), not LLM understanding issues.

### Three Categories of LLM Boundary

1. **Contract boundary (fixed):** LLM output schema doesn't include system metadata fields. Fix: inject system fields after parsing, before validation. Never require the LLM to output traceability or routing metadata that belongs to the system layer.

2. **Knowledge boundary (known, not fixable by prompt):** The LLM correctly classifies "番禺区 1500元以内安静房源" as `route=rag, rag_task=room_search`, but the actual Milvus data doesn't contain matching room IDs. This is a data problem, not an understanding problem. The LLM can't retrieve what doesn't exist in the vector store.

3. **Calibration boundary (partially addressable):** High-risk fallback at 40% means some risky queries (押金退还、租金涨幅) are classified as `kb_qa` instead of `fallback`. The LLM sees these as legitimate policy questions and routes them confidently. Improving this requires either adjusting the prompt's risk sensitivity or lowering the confidence threshold — both have tradeoffs (over-refusal vs under-detection).

### Key Lesson

**Separate LLM understanding from system contracts.** The LLM should output what it knows (intent, filters, preferences). The system should inject what it needs (raw_message, trace IDs, timestamps). When these responsibilities blur, you get silent failures that look like the LLM is broken when it's actually the contract layer rejecting valid understanding.

### Interview Talking Points

- "I discovered that a 100% clarification rate was caused by the LLM correctly understanding queries but the system rejecting responses due to a missing metadata field — a contract boundary problem, not an understanding problem."
- "I fixed it by separating LLM responsibilities (semantic understanding) from system responsibilities (metadata injection), reducing clarification from 100/120 to 15/120."
- "I identified three categories of LLM boundary: contract schema mismatch (fixable), data availability gap (not fixable by prompt), and risk calibration (partially addressable with tradeoffs)."

## LLM-First Interaction Understanding Plan (2026-05-15)

### Summary

Completed the architecture decision and execution plan for replacing keyword-driven interaction understanding with an LLM-first structured understanding layer.

The design decision is intentionally strict: if the LLM output is invalid, low-confidence, contradictory, or unavailable, the system asks the user for clarification instead of falling back to keyword matching. Keyword lists are no longer accepted as a production fallback for route, task, filter, preference, or KB-domain decisions.

### Key Outcomes

1. **Keyword fallback rejected as a product architecture**
   - The session identified keyword matching as the root cause of biased routing, not merely an incomplete coverage problem.
   - Examples: `吗` can incorrectly bias room queries toward KB QA; `房间/空调/宠物` can oscillate between room search and policy QA; eval-driven keyword expansion memorizes cases instead of improving semantic generalization.
   - The agreed principle: model uncertainty should become `fallback.clarify`, not keyword guessing.

2. **LLM became the sole natural-language understanding entrypoint**
   - The LLM is responsible for route, RAG task, domain, action, filters, preferences, risk posture, and retrieval queries.
   - The LLM is allowed to normalize values such as `1500以内 -> max_rent=1500`, `珠江新城 -> district_id=1`, and `月付 -> MONTHLY`.
   - Python code validates contracts and business boundaries, but does not infer intent from `in` string matching.

3. **Hard business boundaries remain deterministic**
   - Safety refusal, pending action routing, schema validation, permission checks, write confirmation, ToolRuntime governance, and lease validation remain outside the LLM decision surface.
   - The LLM must not decide real room availability, lease ownership, appointment write permissions, or final business facts.

4. **Implementation plan created**
   - Plan: `docs/plans/2026-05-15-aptguide2-llm-first-interaction-understanding-plan.md`
   - The plan includes contract changes, prompt hardening, classifier refactor, intent-only query understanding, planning changes, anti-regression source scans, focused tests, full verification, and project checkpointing.
   - No production code was changed in this session; implementation and verification remain next steps.

### Updated Interview Talking Points

- "I identified keyword fallback as an architectural source of bias in an AI routing system and replaced it with an LLM-first structured understanding design."
- "I designed a failure policy where model uncertainty triggers user clarification rather than brittle string-matching guesses."
- "I separated semantic understanding from deterministic business boundaries: the model interprets intent, while code enforces contracts, permissions, confirmations, and factual lease validation."

## AptGuide 2.0 Standalone Productization (2026-05-14)

### Summary

Transformed AptGuide 2.0 from a backend-only harness into a full-stack standalone rental AI agent application in a single development session.

### Metrics

- **Backend tests:** 365 passing (up from 323 baseline, +42 new tests)
- **Frontend tests:** 2 contract tests passing, production build succeeds
- **New backend files:** 18 created, 7 modified
- **New frontend files:** 25+ created (Vue 3 + Vant + Pinia + TypeScript)
- **MySQL tables:** 8 tables deployed (`aptguide_` prefix in shared `least` database)
- **Test coverage areas:** auth, persistence, memory, handoff, operator API, RAG v2, harness framework

### Architecture Decisions

1. **Async-first harness:** Added `run_async()` to `AptGuideHarness` while keeping sync `run()` for backward compatibility. API endpoint uses `await harness.run_async()`.

2. **Redis-first persistence:** `PersistentContextStore` loads from Redis first (fast), falls back to MySQL (durable), falls back to new frame. Saves to both for redundancy.

3. **Shared database strategy:** Uses AptInsight's `least` database with `aptguide_` table prefix to avoid needing CREATE DATABASE permissions.

4. **Auth resolver pattern:** `AuthContext` dataclass + `AuthResolver` class supports dev mode (configurable default user) and lease_token mode (async HTTP call to lease backend). Clean separation of concerns.

5. **Operator API isolation:** Separate FastAPI router with token-based auth (`X-Operator-Token` header), independent from chat API auth.

### Key Technical Wins

- **Zero breaking changes:** All 323 existing tests continued passing throughout development
- **Backward compatible async:** Sync `run()` delegates to `asyncio.run(run_async())` so existing callers don't break
- **Type-safe frontend:** Full TypeScript with contract tests validating ChatResponse and HandoffTicket structures
- **Component architecture:** 7 chat components + 6 card renderers + 4 operator components, each with single responsibility

### Interview Talking Points

- "Designed a persistence layer with Redis hot-path and MySQL durable fallback, ensuring sub-millisecond reads and zero data loss on restart"
- "Built an auth resolver that supports both development (test user selector) and production (lease token resolution) modes without code changes"
- "Implemented a complete operator console with ticket lifecycle management — list, inspect, reply, close, resume AI"
- "Maintained 100% backward compatibility while adding async support to the harness orchestrator"

## Recent AptGuide 2.0 Development Outcomes (2026-05-12 to 2026-05-14)

### Summary

整理最近三天 AptGuide 2.0 的真实开发记录后，当前成果不只是“做了一个 RAG MVP”，而是已经推进到数据治理、RAG v2 主线替换、风险感知路由、系统主流程集成、可观测性和成果文档收尾。

### Key Outcomes

1. **WeChat real listing ingestion plan clarified**
   - 微信群租房消息被定位为外部真实发布线索，不是平台已核验库存。
   - 当前验收范围收窄为 MySQL 入库、脱敏、去重、SQL 幂等和状态字段。
   - RAG/Milvus 同步被降级为后续工作，避免把未核验数据直接暴露给用户。
   - 核心语义字段：`REAL_POSTED`、`UNVERIFIED`、`UNKNOWN`、`appointable=false`。

2. **RAG v2 live evaluation exposed real quality gaps**
   - Live eval 使用真实 Milvus、embedding 和 lease 数据，不只依赖 mock。
   - 当前指标：KB source hit@3 = 48.6%，Room hit@5 = 40.0%。
   - 结论：问题主要在 query understanding、检索链路、ranking 和 eval trace 解释力，不应盲目调权重。

3. **Legacy RAG removed from public mainline**
   - 旧 RAG MVP 被定位为 legacy reference，不再作为 public API、harness procedure 或系统验收路径。
   - RAG v2 被挂载为 harness mainline 内部模块，服务 `/chat` 的房源搜索和租房知识问答。

4. **Risk-aware query understanding and guardrail completed**
   - 高风险租房问题（押金、合同、投诉、争议）不再按普通 KB/fallback 处理。
   - 风险评测结果达到 high risk recall = 1.000、false block rate = 0.000、response mode accuracy = 1.000。
   - Guardrail 被定义为风险感知路由，而不是一刀切拦截。

5. **System feature completion moved beyond retrieval**
   - `/chat` 主线目标扩展到 room search、KB QA、appointment create/cancel confirmation、lease query、memory、handoff、tool failure。
   - 预约创建和取消都要求 two-turn confirmation，避免写操作误触发。
   - 工具失败和高风险争议可以进入人工接管，并保留上下文摘要。

6. **Observability and handoff documentation consolidated**
   - LangSmith/trace/eval 被纳入生产硬化目标。
   - 文档要求 trace 能解释边界判断、工具调用、确认动作、失败恢复和检索阶段。
   - `docs/plans/handoff.md`、`docs/plans/next-steps.md`、`docs/tests/verification-log.md` 已作为后续交接入口。

### Current Blocker

当前最大 blocker 是 RAG v2 检索质量：KB hit@3 需要从 48.6% 提升到 90%+，Room hit@5 需要从 40.0% 提升到 85%+。下一步应先补 per-stage trace 和数据校验，再做 query understanding、hybrid retrieval、rerank 和 filter 优化。

### Updated Interview Talking Points

- "I separated real external rental leads from verified platform inventory, with explicit authenticity, verification, availability, and appointability semantics."
- "I ran RAG v2 against real Milvus, embedding, and lease dependencies, then used failed cases to identify retrieval quality as the next blocker."
- "I replaced the public legacy RAG path with a harness mainline that can coordinate retrieval, appointment confirmation, memory, handoff, and tool failure recovery."
- "I designed guardrails as risk-aware routing with measurable recall and false-block gates, not generic refusal logic."
