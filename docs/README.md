# Apartment Intelligence Platform 文档中心

本文档中心负责提供整个仓库的文档入口。各子项目继续维护自己的文档，根目录只做平台级索引与跨项目导航。

## 推荐阅读顺序

1. 阅读根项目 [README](../README.md)，了解平台整体组成。
2. 进入目标子项目的文档中心。
3. 按子项目 `docs/README.md` 中的推荐顺序阅读具体文档。

## 子项目文档入口

| 子项目 | 说明 | 文档入口 | 当前整理状态 |
| --- | --- | --- | --- |
| AptGuide | 面向租客的智能找房助手 | [AptGuide/docs](../AptGuide/docs/README.md) | 已建立四类索引 |
| AptGuide 2.0 | 面向租客找房场景的新一代 Agent 应用 | [AptGuide 2.0/docs](../AptGuide%202.0/docs/README.md) | 已建立四类索引 |
| AptInsight | 面向运营人员的智能分析助手 | [AptInsight/docs](../AptInsight/docs/README.md) | 已建立四类索引 |
| lease | Spring Boot 租赁业务后端 | [lease](../lease/) | 本阶段不整理 |
| rentHouseAdmin | Vue3 后台管理前端 | [rentHouseAdmin](../rentHouseAdmin/) | 本阶段不整理 |
| rentHouseH5 | Vue3 租客 H5 | [rentHouseH5](../rentHouseH5/) | 本阶段不整理 |

## 文档分类规则

每个已整理子项目在自己的 `docs/` 下维护四类正式索引：

| 分类 | 用途 |
| --- | --- |
| `system/` | 系统文档：架构、模块、接口、数据、Agent 流程、核心设计 |
| `plans/` | 计划文档：给 Agent 执行的任务计划、实施步骤、验收标准 |
| `tests/` | 测试文档：测试策略、测试记录、评测结果、失败分析、回归记录 |
| `outcomes/` | 成果文档：面试、简历、踩坑复盘、解决方案、成果指标 |

## 维护原则

- 正式文档优先写入所属子项目自己的 `docs/<type>/`。
- 根目录 `docs/` 只维护平台入口，不集中接管子项目文档。
- 新增文档后，更新最近一层分类索引；必要时更新项目级 `docs/README.md`。
- 自动生成的报告可以保留在原始输出目录，但应在 `tests/` 索引中链接和总结。
- `AptGuide` 与 `AptGuide 2.0` 分开维护索引：旧版保留旧链路与历史经验，2.0 维护新框架、新 RAG、新评测和 MVP 成果。
