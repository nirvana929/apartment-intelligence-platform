# Room Search 评测方法修正计划

## 背景

当前 room search 使用 Hit@5 精确匹配评测：预定义 `expected_room_ids`，检查返回结果是否命中。
这种方法不适用于语义搜索场景——LLM 每次生成不同的语义查询，Milvus 召回结果天然非确定性。
Hit@5 永远是 False，不是搜索质量差，而是评测方法错误。

## 修正方案

**放弃 room search 的 Hit@5/MRR/nDCG 精确匹配评测。**
改用 criteria-based 评测——衡量搜索结果是否满足用户的实际需求。

## 新的评测指标

### Room Search 指标（criteria-based）

| 指标 | 定义 | 通过条件 |
|------|------|----------|
| `response_not_empty` | 搜索是否返回了结果 | cards > 0 |
| `district_match` | 返回的房间是否在用户指定的区域 | 返回房间的 district 字段匹配查询中的区域（允许 fallback 放宽） |
| `price_in_range` | 返回的房间价格是否在用户指定的范围 | 返回房间的租金在查询指定的范围内 |
| `amenity_match` | 返回的房间是否包含用户要求的设施 | 返回房间的 amenity 字段匹配查询中的设施要求 |
| `lease_validated` | 房间是否通过 lease API 验证 | 所有 room_card 的 lease_validation_status=passed（当前 wechat 数据跳过此项） |
| `understanding_correct` | 理解层是否正确路由 | parsed_route=rag, parsed_task=room_search, confidence>=0.8 |
| `latency_ok` | 响应时间是否合理 | latency < 15000ms |

### KB QA 指标（保持不变）

| 指标 | 定义 | 通过条件 |
|------|------|----------|
| `hit_at_3` | 预期文档是否在返回结果前3 | expected_doc_ids 中至少1个出现在 returned_doc_ids 前3 |
| `must_cite_source` | 高风险回答是否引用了来源 | source_cards > 0 或 confidence_gate 正确拦截 |
| `must_not_make_unverified_commitment` | 是否做出了无依据的承诺 | 有来源时不做无依据承诺 |

## 实现任务

### Task 1: 修改 eval dataset 格式

**文件:** `backend/evals/datasets/rag_retrieval_cases.yaml`

- Room search cases: 移除 `expected_room_ids`，改为 `expected_criteria` 块
- 新增字段：
  - `expected_district`: 期望的区域（如 "番禺区"）
  - `expected_price_max`: 最高价格（如 1500）
  - `expected_amenities`: 期望的设施列表（如 ["空调"]）
  - `expected`: 保留 `must_validate_with_lease` 等布尔条件

示例：
```yaml
- id: room-panyu-quiet-001
  task: room_search
  query: 找番禺1500以内安静一点的房子
  expected_district: 番禺区
  expected_price_max: 1500
  expected:
    must_validate_with_lease: true
    response_not_empty: true
    understanding_correct: true
```

### Task 2: 修改 eval runner

**文件:** `backend/evals/runners/run_rag_eval.py`

- `_check_criteria`: 新增 room search criteria 检查逻辑
  - `response_not_empty`: 检查 cards > 0
  - `district_match`: 从返回的 room_card 元数据中提取 district，与 expected_district 比对
  - `price_in_range`: 从 room_card 元数据中提取 price，与 expected_price_max 比对
  - `amenity_match`: 从 room_card 元数据中提取 amenities，与 expected_amenities 比对
- `_compute_hit_metrics`: room search 不再调用此函数（或返回 N/A）
- `run_live_eval`: room search case 的 metrics 改为 criteria 结果汇总
- `classify_failure_owner`: 更新逻辑，不再依赖 Hit@5 结果
- 报告渲染: room search 部分改为显示 criteria 通过率

### Task 3: 更新 room_card 元数据

**需要确认:** `room_retrieval.py` 返回的 room_card 是否包含 district、price、amenities 字段。
如果缺失，需要在 `rag/room_retrieval.py` 或 `rag/room_ranking.py` 中补充这些字段到 card metadata。

### Task 4: 更新报告格式

**文件:** `backend/evals/runners/run_rag_eval.py` (render_report)

Room search 报告改为：
```
| Metric | Value |
|--------|-------|
| Response not empty | 5/5 (100%) |
| District match | 4/5 (80%) |
| Price in range | 3/5 (60%) |
| Understanding correct | 5/5 (100%) |
| Latency ok | 5/5 (100%) |
```

### Task 5: 更新 unit tests

**文件:** `backend/tests/unit/evals/test_rag_eval_runner.py`

- 更新 room search 相关测试用例以匹配新 criteria 格式
- 新增 district_match、price_in_range、amenity_match 的测试

### Task 6: 更新 plan docs

- `docs/plans/current-plan.md`: 移除 P0 dataset_gap，更新 findings
- `docs/plans/known-issues.md`: 标注 Hit@5 不适用于 room search
- `docs/plans/next-steps.md`: 更新下一步
- `docs/tests/evaluation-report.md`: 记录方法修正

## 验收标准

1. Room search eval case 不再需要 `expected_room_ids`
2. Room search 评测使用 criteria-based 指标（response_not_empty, district_match, price_in_range 等）
3. KB QA 评测保持 Hit@3 不变
4. 报告正确显示 room search criteria 通过率
5. `uv run pytest tests/unit/evals/ -q` 全部通过
6. `uv run ruff check src tests` clean
7. Live eval 能正确运行并输出新格式报告

## 风险

- room_card 元数据可能缺少 district/price/amenities 字段 → 需要先检查再决定是否补充
- district 匹配需要考虑实体解析（如 "番禺" vs "番禺区"）→ 可复用 entity_resolution 模块
- wechat 数据可能没有标准的 price/amenities 字段 → 需要检查数据结构
