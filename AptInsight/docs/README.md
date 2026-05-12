# AptInsight 文档中心

AptInsight 是面向运营人员的智能分析助手。本文档中心只负责 AptInsight 项目内部文档索引，旧文档暂不迁移，通过链接纳入索引。

当前文档重点覆盖 Text-to-SQL、SQL Guard、Agent Eval Harness、模型评测、失败定位和面试成果复盘。

## 推荐阅读顺序

1. [助手总体设计](../AptInsight文档/01-助手总体设计.md)
2. [技术架构与模块设计](../AptInsight文档/03-技术架构与模块设计.md)
3. [Agent 设计与提示词规范](../AptInsight文档/04-Agent设计与提示词规范.md)
4. [数据库字典与指标口径](../AptInsight文档/05-数据库字典与指标口径.md)
5. [接口契约与集成方案](../AptInsight文档/06-接口契约与集成方案.md)
6. [最终版系统测试测评方案](../AptInsight文档/11-最终版系统测试测评方案.md)

## 文档分类

| 类型 | 用途 | 入口 |
| --- | --- | --- |
| 系统文档 | 架构、模块、接口、数据、指标、Agent 流程 | [system](./system/README.md) |
| 计划文档 | 给 Agent 执行的实施计划、任务拆解、验收标准 | [plans](./plans/README.md) |
| 测试文档 | 测试策略、Eval Harness、测试报告、失败分析 | [tests](./tests/README.md) |
| 成果文档 | 面试和简历视角的成果、踩坑、方案复盘 | [outcomes](./outcomes/README.md) |

## 现有资料位置

| 位置 | 说明 |
| --- | --- |
| [AptInsight文档](../AptInsight文档/README.md) | 产品、架构、Agent、接口、测试和集成文档 |
| [docs](./) | 当前补充文档、排障、模型评测和经验总结 |
| [evals/reports](../evals/reports/) | Agent Eval Harness 生成报告 |
| [根目录 Agent 评测资料](../../docs/README.md) | 平台级 Agent Eval、简历和作品集资料入口 |

## 维护规则

- 新增正式文档写入 `docs/system`、`docs/plans`、`docs/tests` 或 `docs/outcomes`。
- 旧文档先保留原路径，本索引负责指向和归类。
- 新增或调整文档后，同步更新对应分类目录的 `README.md`。
