# CODEX.md

Codex 应遵循 `AGENTS.md` 中的项目指引。

对于此仓库：

- 将 `/home/chove/桌面/apartment-intelligence-platform/AptInsight` 视为项目根目录。
- 与用户交流时默认使用中文。仅在代码、命令、日志、标识符、依赖名称、文件名、API 名称、精确错误信息中使用英文，或用户明确要求英文时使用英文。
- 保持 Python AptInsight Agent 独立于现有的 `least` Java/Vue 项目。
- 遵循 `AptInsight文档/` 中记录的 MVP 架构。
- 使用 `src/aptinsight/` 放置服务代码，`evals/` 放置 Agent 评测，`tests/` 放置自动化测试。
- 除非 SQL 守卫已批准，否则绝不执行模型生成的 SQL。
- 只允许对只读 MySQL 账号执行只读 `SELECT` 查询。

完整规则见 `AGENTS.md`。
