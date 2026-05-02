# Apartment Intelligence Platform

这是一个单仓库多项目工程，用于集中管理公寓租赁系统相关项目。

## 项目结构

```text
.
├── AptInsight/       # 运营端智能分析助手（B 端，Text-to-SQL）
├── AptGuide/         # 用户端智能找房助手（C 端，Tool-calling + RAG）
├── lease/            # 公寓租赁后端服务项目
├── rentHouseAdmin/   # 管理后台前端项目
└── rentHouseH5/      # H5/移动端项目
```

## 项目说明

- `AptInsight`：面向运营人员，基于 Python FastAPI、LangGraph 和 Text-to-SQL 的智能运营分析助手。
- `AptGuide`：面向租客用户，基于 Python FastAPI、LangGraph、Milvus 和 Java 工具接口的智能找房助手；不直查 MySQL，所有业务数据通过 `lease` 内部接口获取。
- `lease`：公寓租赁业务后端服务（Spring Boot）。
- `rentHouseAdmin`：后台管理端前端项目。
- `rentHouseH5`：面向移动端或 H5 场景的前端项目。

各项目保留独立的依赖、配置、启动方式和 README。仓库根目录只维护整体结构说明和通用工程规则。

