# AptGuide 文档中心

AptGuide 是面向租客的智能找房助手。本文档中心只负责旧版 AptGuide 项目内部文档索引，旧文档暂不迁移，通过链接纳入索引。

如果要阅读新一代 Agent 方案，请进入 [AptGuide 2.0 文档中心](../../AptGuide%202.0/docs/README.md)。

## 推荐阅读顺序

1. [助手总体设计](../AptGuide文档/01-助手总体设计.md)
2. [技术架构与模块设计](../AptGuide文档/03-技术架构与模块设计.md)
3. [Agent 设计与提示词规范](../AptGuide文档/04-Agent设计与提示词规范.md)
4. [Java 工具接口契约](../AptGuide文档/05-Java工具接口契约.md)
5. [测试验收方案](../AptGuide文档/07-测试验收方案.md)
6. [RAG MVP 成果报告](../../AptGuide%202.0/docs/28-rag-mvp-achievement-report.md)

## 文档分类

| 类型 | 用途 | 入口 |
| --- | --- | --- |
| 系统文档 | 架构、模块、接口、RAG、Agent 流程、集成边界 | [system](./system/README.md) |
| 计划文档 | 给 Agent 执行的实施计划、任务拆解、验收标准 | [plans](./plans/README.md) |
| 测试文档 | 测试策略、评测方法、测试报告、覆盖率总结 | [tests](./tests/README.md) |
| 成果文档 | 面试和简历视角的成果、踩坑、方案复盘 | [outcomes](./outcomes/README.md) |

## 现有资料位置

| 位置 | 说明 |
| --- | --- |
| [AptGuide文档](../AptGuide文档/README.md) | 早期产品、架构、接口、测试和集成文档 |
| [docs](./) | 当前补充文档、测试报告、排障和评测资料 |
| [evals/reports](../evals/reports/) | 评测和数据导入相关生成报告 |
| [AptGuide 2.0 docs](../../AptGuide%202.0/docs/README.md) | AptGuide 2.0 设计、计划、RAG、评测和成果资料 |

## 与 AptGuide 2.0 的边界

- 本文档中心记录旧版 AptGuide 的 LangGraph 工作流、工具接口、Milvus 知识库和测试经验。
- AptGuide 2.0 文档中心记录新框架、领域边界、RAG 检索 MVP、工具注册、记忆状态和成果复盘。
- 旧版测试失败、接口契约和集成经验可以作为 2.0 的输入，但新增 2.0 文档应写入 `AptGuide 2.0/docs/`。

## 维护规则

- 新增正式文档写入 `docs/system`、`docs/plans`、`docs/tests` 或 `docs/outcomes`。
- 旧文档先保留原路径，本索引负责指向和归类。
- 新增或调整文档后，同步更新对应分类目录的 `README.md`。
