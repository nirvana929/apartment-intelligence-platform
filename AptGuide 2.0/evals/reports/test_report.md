# AptGuide 2.0 Test Report

**Date:** 2026-05-12
**Status:** All tests passing

## Summary

| Test Type | Count | Status |
|-----------|------:|--------|
| Unit Tests | 133 | ✅ PASSED |
| E2E Tests | 16 | ✅ PASSED |
| **Total** | **149** | **✅ 100%** |

## Unit Tests (133)

### RAG Module (tests/unit/rag/)

| File | Tests | Coverage |
|------|------:|----------|
| test_query_understanding.py | 28 | 预算、区域、偏好、任务检测、指代解析、风险等级 |
| test_chunking.py | 12 | KB chunk 构建、房源向量文本、content_hash |
| test_room_retrieval.py | 8 | 多路召回、过滤构建、候选补全 |
| test_kb_retrieval.py | 10 | KB 检索、source rerank、step_back query |
| test_ranking.py | 9 | 多维排序、权重计算、标签匹配 |
| test_schemas.py | 8 | Pydantic 模型验证、默认值 |

### Tools Module (tests/unit/tools/)

| File | Tests | Coverage |
|------|------:|----------|
| test_vector_adapter.py | 6 | Milvus collection 名称、结果规范化、初始化 |
| test_lease_adapter.py | 12 | lease 对接、key 转换、错误处理、健康检查 |

### Trace Module (tests/unit/trace/)

| File | Tests | Coverage |
|------|------:|----------|
| test_retrieval_events.py | 12 | PII 检测、事件构建、trace ID 生成 |

### Data Import Module (tests/unit/data_import/)

| File | Tests | Coverage |
|------|------:|----------|
| test_wechat_parser.py | 28 | 微信数据解析、字段映射、错误处理 |

## E2E Tests (16)

### API Tests (tests/e2e/test_api.py)

| Test | Description | Status |
|------|-------------|--------|
| test_health_ok | /health 返回 ok + Milvus 连接 | ✅ |
| test_room_search_returns_rooms | /chat 房源搜索返回结果 | ✅ |
| test_room_search_with_budget | 带预算的房源搜索 | ✅ |
| test_kb_qa_confident | KB 问答高置信度 | ✅ |
| test_kb_qa_low_confidence | KB 问答低置信度 | ✅ |
| test_fallback_out_of_scope | 超范围问题 fallback | ✅ |
| test_fallback_guarantee | 保证性承诺 fallback | ✅ |

### Pipeline Tests (tests/e2e/test_pipeline.py)

| Test | Description | Status |
|------|-------------|--------|
| test_room_search_returns_ranked_rooms | Pipeline 房源搜索 | ✅ |
| test_room_search_with_budget_filter | Pipeline 预算过滤 | ✅ |
| test_room_search_no_results | Pipeline 无结果处理 | ✅ |
| test_kb_qa_confident | Pipeline KB 问答 | ✅ |
| test_kb_qa_low_confidence_returns_fallback | Pipeline 低置信 fallback | ✅ |
| test_kb_qa_no_sources | Pipeline 无来源处理 | ✅ |
| test_fallback_out_of_scope | Pipeline 超范围 | ✅ |
| test_fallback_guarantee_request | Pipeline 保证性承诺 | ✅ |
| test_fallback_random_question | Pipeline 随机问题 | ✅ |

## Test Commands

```bash
# Run all tests
cd "AptGuide 2.0/backend"
.venv/bin/python -m pytest tests/ -v

# Run unit tests only
.venv/bin/python -m pytest tests/unit/ -v

# Run E2E tests only
.venv/bin/python -m pytest tests/e2e/ -v

# Run with coverage
.venv/bin/python -m pytest tests/ --cov=src/aptguide2 --cov-report=html
```

## Recent Fixes

### 2026-05-12

1. **District ID mapping** - Updated query_understanding.py to use lease backend IDs (1-11, 110114)
2. **KB duplicate doc_id** - Fixed sync_kb_vectors.py to deduplicate by doc_id
3. **Lease auth header** - Changed from `Authorization: Bearer` to `X-Internal-Token`
4. **Lease response code** - Accept both 0 and 200 as success codes
5. **facilities None handling** - Added `or []` default for tags/facilities
6. **LangSmith config** - Removed conflicting `LANGCHAIN_*` env vars

## Continuous Integration

To run tests in CI:

```bash
# Install dependencies
cd "AptGuide 2.0/backend"
uv sync

# Run tests
uv run pytest tests/ -v --tb=short

# Generate JUnit XML for CI
uv run pytest tests/ --junitxml=test-results.xml
```
