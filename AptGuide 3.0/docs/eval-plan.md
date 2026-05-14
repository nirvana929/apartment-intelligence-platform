# Evaluation Plan

## First Gates

1. Understanding contract tests
   - valid room search output passes;
   - valid KB QA output passes;
   - ambiguous output becomes clarification;
   - invalid JSON becomes clarification;
   - low confidence becomes clarification;
   - keyword fallback source scan passes.

2. Procedure routing tests
   - each route dispatches to the expected procedure;
   - non-RAG routes keep retrieval off;
   - pending action has priority over new LLM interpretation.

3. API smoke tests
   - `/health` returns service status;
   - `/chat` returns a typed response for clarification;
   - `/chat` returns a typed response for stubbed room search.

## Later Gates

- live LLM understanding eval;
- live Milvus and embedding eval;
- lease-backed room validation eval;
- RAG quality gates after the clean architecture is stable.
