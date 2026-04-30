# AptInsight

AptInsight 是面向尚庭公寓后台的智能运营分析助手。当前工程用于第一阶段独立验证：通过 FastAPI 暴露 Agent 服务，接入只读 MySQL，完成自然语言问题到 SQL 查询、表格、图表和运营总结的链路。

## 目录结构

```text
.
├── AptInsight文档/          # 项目设计、需求、测试和集成文档
├── docs/                   # 工程级 API、架构、安全补充文档
├── evals/                  # Agent Eval Harness 数据集、执行器、报告
├── src/aptinsight/         # Python 服务源码
├── tests/                  # 单元测试与接口契约测试
├── scripts/                # 本地开发脚本
├── pyproject.toml
├── .env.example
└── SECURITY.md
```

## 本地开发

```bash
uv sync
cp .env.example .env
uv run uvicorn aptinsight.main:app --reload
```

## 常用命令

```bash
make run
make test
make lint
make eval
```

