# AptGuide 3.0 RAG Evidence, Trace, and Evaluation Roadmap Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement each linked plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the remaining AptGuide 3.0 RAG work into independently verifiable plans so room search, KB QA, risk handling, LangSmith observability, and full evaluation can reach production-grade evidence standards.

**Architecture:** Treat Milvus as recall index, lease/database as business truth, LangSmith as end-to-end observability, and eval datasets as the acceptance gate. Do not optimize ranking or prompts before the evidence contract and ID alignment are explicit.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, Milvus, MySQL, Redis, lease internal API, OpenAI-compatible DashScope client, LangSmith, pytest, existing AptGuide 3.0 eval runner.

---

## Current Project State

- Project: AptGuide 3.0.
- Current branch: `codex/update-project-readme`.
- M0-M6 are complete.
- Latest checkpoint shows expanded live RAG eval can pass `9/9`, but project harness state still contains older Milvus failure notes.
- Room search currently uses `wechat_room_index` and builds room cards from vector metadata; lease validation is bypassed for wechat data because there is no confirmed `wechat_room_id -> lease_room_id` mapping in the retrieval path.
- Plan 1 data/evidence contract is complete.
- Plan 4 LangSmith final-output tracing is complete.
- Critical finding after Plan 1/4: `room_retrieval.py` uses hash-generated synthetic room IDs and drops the original `wechat_room_id`; a formal room identity mapping layer is required before Plan 2, Plan 3, or Plan 5.
- KB QA returns `kb_source` cards with source IDs, but the user-facing answer still needs grounded generation with citations in Plan 3.

## Plan Package

Execute these plans in order:

1. `docs/plans/2026-05-15-aptguide3-data-evidence-contract-plan.md` — completed
2. `docs/plans/2026-05-15-aptguide3-langsmith-chat-output-tracing-plan.md` — completed
3. `docs/plans/2026-05-15-aptguide3-room-identity-map-prerequisite-plan.md` — active prerequisite
4. `docs/plans/2026-05-15-aptguide3-room-lease-id-alignment-plan.md`
5. `docs/plans/2026-05-15-aptguide3-grounded-risk-answer-plan.md`
6. `docs/plans/2026-05-15-aptguide3-comprehensive-rag-evaluation-plan.md`

## Phase Gates

- Do not start Plan 2 until the room identity map prerequisite preserves source IDs and distinguishes `vector_only`, `mapped_candidate`, and `mapped_verified`.
- Do not claim room search is business-valid until Plan 2 restores lease validation for returned room cards.
- Do not claim medium/high-risk answers are grounded until Plan 3 verifies that final answer text cites concrete evidence.
- Do not allow Plan 3 room answers to cite synthetic room IDs as evidence.
- Do not run Plan 5 formal full RAG quality evaluation until identity mapping, Plan 2, and Plan 3 are complete; before that, only smoke/live-chain eval is meaningful.

## Shared Non-Negotiables

- Keep LLM-first understanding; no keyword fallback for route, task, risk, filters, preferences, or retrieval queries.
- Do not let vector recall override lease/database hard validation.
- Do not let the LLM invent room IDs, lease IDs, source IDs, availability, price validity, appointment ability, refund promises, or policy commitments.
- Every medium/high-risk final answer must be traceable to source cards, room evidence, lease validation, or conservative fallback.
- Every eval report must distinguish data gap, retrieval failure, ranking issue, confidence gate issue, answer grounding issue, and trace visibility issue.

## Final Acceptance

- Room search cards include real business identity and lease validation evidence.
- KB QA produces final grounded answer text with citations and source cards.
- Medium/high-risk answers either cite adequate evidence or return a conservative fallback / handoff path.
- LangSmith displays user input, understanding result, retrieval evidence, final answer, cards, and metadata in one trace.
- Full RAG eval includes retrieval, grounding, risk, trace, latency, and product-safety metrics.
