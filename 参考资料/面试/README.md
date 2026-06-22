# 面试训练资料入口

> **AI Agent 入口**：新 Agent 应先阅读 [AGENTS.md](./AGENTS.md)，了解全局背景、当前训练进展和下一步任务。

## 用途

本目录是吴超文进行 AI 应用开发、Java 后端、大模型应用开发、Agent / RAG / Text-to-SQL 方向面试准备的统一入口。

新的 AI 对话窗口应先阅读本目录资料，再扮演面试官开展问答训练。资料不足以回答具体技术事实时，应回查仓库中的项目文档或代码，不要自行补全经历或生产成果。

## 推荐阅读顺序

| 顺序 | 文档 | 作用 |
| --- | --- | --- |
| 1 | [面试经验.md](./面试经验.md) | 字节面试要求、表达原则、通用答题方法 |
| 2 | [候选人背景与面试定位.md](./候选人背景与面试定位.md) | 候选人形象、目标岗位、真实能力边界 |
| 3 | [AptGuide3.0项目面试手册.md](./AptGuide3.0项目面试手册.md) | 重点项目：租客侧找房 Agent |
| 4 | [AptInsight项目面试手册.md](./AptInsight项目面试手册.md) | 运营侧 Text-to-SQL 分析 Agent |
| 5 | [租赁业务平台项目面试手册.md](./租赁业务平台项目面试手册.md) | lease、租客 H5、管理后台与集成边界 |
| 6 | [AI-Coding面试表达手册.md](./AI-Coding面试表达手册.md) | 如何真实说明 AI 辅助开发经历 |
| 7 | [真实开发案例与三代迭代复盘.md](./真实开发案例与三代迭代复盘.md) | 三代演进、已记录 Bug、评测根因和可讲答案 |
| 8 | [STAR案例库.md](./STAR案例库.md) | 项目难点与行为面试素材 |
| 9 | [模拟面试官使用说明.md](./模拟面试官使用说明.md) | 新窗口启动提示、追问规则和纠错方式 |

## 当前训练稿

| 文档 | 状态 | 说明 |
| --- | --- | --- |
| [自我介绍.md](./自我介绍.md) | active | 按时间保存第一版和当前第二版；第二版为 90 秒口述训练稿 |

## 重点准备主线

主讲项目是 **AptGuide 3.0**。它是面向租客的智能找房助手，覆盖自然语言找房、租赁规则问答、预约确认、租约查询、偏好记忆与人工转接。

辅助项目是 **AptInsight**。它是面向运营人员的数据分析助手，覆盖自然语言经营分析、Text-to-SQL、SQL 安全校验、只读查询、表格图表与总结。

业务底座是 **Apartment Intelligence Platform / lease**。它说明 AI 服务不是孤立 Demo，而是围绕房源、预约、租约等租赁事实接入的应用探索。

## 统一事实边界

- 可以说：项目完成了独立开发、关键功能实现与验证/评测探索。
- 可以说：在设计中采用确认式写操作、只读 SQL、安全校验和业务事实源边界。
- 不要说：项目已经生产上线或经历大规模真实用户验证。
- 不要说：发生过没有证据支撑的线上误操作、事故或业务收益。
- 不要把设计目标、后续规划表述为已经完成的成果。

## 回查项目入口

| 主题 | 首选事实来源 |
| --- | --- |
| 平台总体架构与系统边界 | [../../README.md](../../README.md) |
| AptGuide 3.0 状态与能力 | [../../AptGuide 3.0/README.md](../../AptGuide%203.0/README.md) |
| AptGuide 3.0 架构边界 | [../../AptGuide 3.0/docs/architecture.md](../../AptGuide%203.0/docs/architecture.md) |
| AptGuide 3.0 评测事实 | [../../AptGuide 3.0/docs/tests/evaluation-report.md](../../AptGuide%203.0/docs/tests/evaluation-report.md) |
| AptGuide 初版开发 Bug | [../../AptGuide/docs/development-log.md](../../AptGuide/docs/development-log.md) |
| AptGuide 2.0 成果与经验 | [../../AptGuide 2.0/docs/outcomes/achievements.md](../../AptGuide%202.0/docs/outcomes/achievements.md)、[../../AptGuide 2.0/docs/outcomes/lessons-learned.md](../../AptGuide%202.0/docs/outcomes/lessons-learned.md) |
| AptInsight 状态与评测基线 | [../../AptInsight/README.md](../../AptInsight/README.md) |
| AptInsight 业务定位 | [../../AptInsight/AptInsight文档/01-助手总体设计.md](../../AptInsight/AptInsight文档/01-助手总体设计.md) |
| AptInsight 安全约束 | [../../AptInsight/SECURITY.md](../../AptInsight/SECURITY.md) |
| lease 租客端与 AI 工具 API | [../../docs/api/lease-web-app.md](../../docs/api/lease-web-app.md) |
