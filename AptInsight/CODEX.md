# CODEX.md

Codex should follow the project instructions in `AGENTS.md`.

For this repository:

- Treat `/home/chove/桌面/尚庭公寓（练习版）/AptInsight` as the project root.
- Use Chinese by default when chatting with the user. Use English only for code, commands, logs, identifiers, dependency names, file names, API names, exact errors, or when the user explicitly asks for English.
- Keep the Python AptInsight Agent independent from the existing `least` Java/Vue project.
- Follow the MVP architecture documented in `AptInsight文档/`.
- Use `src/aptinsight/` for service code, `evals/` for Agent evaluation, and `tests/` for automated tests.
- Never execute model-generated SQL unless the SQL Guard has approved it.
- Only allow read-only `SELECT` queries against a read-only MySQL account.

See `AGENTS.md` for the full rules.
