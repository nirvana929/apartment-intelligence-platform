# 评测系统全面改造计划

## 背景

当前 AptGuide 3.0 评测系统有 4 类问题，阻塞了全面质量度量：

| # | 问题 | 影响 |
|---|------|------|
| 1 | T1 KB QA 30 case，26 个 `expected_doc_ids` 为空 | 只有 4/30 可测检索质量 |
| 2 | T1 Room Search 用 Hit@5 exact-match | 语义搜索天然非确定性，全 FAIL，评测方法错 |
| 3 | T2 Understanding 有 free-text 断言 + 缺 risk_level 字段 | 部分 case 无法自动验证 |
| 4 | T3 Procedures multi-turn 无法工作 + 9 个 free-text 断言 | multi-turn 全 FAIL，部分 case 无结构化断言 |

## 总体目标

将评测系统从"4/9 passed"提升到"60+ KB QA + criteria-based room search + T2/T3 全部可自动验证"。

---

## 工作流

### Wave 1 — 数据集改造（3 个并行工作流）

#### Workstream 1A: T1 数据集 (`rag_retrieval_cases.yaml`)

**Room Search（30 case → 保持不变，改格式）：**

- 移除所有 `expected_room_ids` 字段
- 新增 criteria 字段：
  - `expected_district`：期望区域（如 "番禺区"），不强制时留空
  - `expected_price_max`：最高价格，无价格要求时留空
  - `expected_amenities`：设施列表，无要求时留空
- `expected` 块新增：`response_not_empty: true`、`latency_ok: true`
- 30 个 case 的 `expected_district`/`expected_price_max` 从现有 query 中提取

**KB QA（30 → 60 case，全填 expected_doc_ids）：**

扩充维度（在现有 6 模块 × 5 = 30 基础上扩展）：

| 模块 | 现有 | 新增 | 总计 | 新增覆盖点 |
|------|------|------|------|-----------|
| lease | 6 | 4 | 10 | 转租纠纷、续约涨价、租赁期限、合同解除 |
| payment | 5 | 5 | 10 | 逾期罚金、租金涨价、缴费方式变更、退款流程、押金利息 |
| account | 5 | 5 | 10 | 实名认证、账号冻结、注销后数据、设备绑定、登录异常 |
| appointment | 5 | 5 | 10 | 改期流程、取消退费、预约提醒、带看流程、线上签约 |
| policy | 5 | 5 | 10 | 装修规定、噪音投诉、垃圾分类、快递代收、访客登记 |
| life | 4 | 6 | 10 | 周边配套、交通指引、维修报修、水电缴费、搬家流程、邻里纠纷 |

所有 60 个 case 的 `expected_doc_ids` 初始化策略：
- 已知 4 个保留现有值
- 56 个新 case：先用 KB 文档 ID 模式推断（如 lease 模块用 KB-LS-xxx，payment 用 KB-PAY-xxx），标记为 `# TODO: verify with live discovery`
- 后续 live discovery 跑一遍确认

#### Workstream 1B: T2 数据集 (`understanding_route_cases.yaml`)

修复 3 个问题：

1. **补 `expected_risk_level`**（10 个 risk classification case）：
   ```
   risk-high-lease-001 → expected_risk_level: high
   risk-high-payment-001 → expected_risk_level: high
   risk-high-account-001 → expected_risk_level: high
   risk-medium-appointment-001 → expected_risk_level: medium
   risk-medium-policy-001 → expected_risk_level: medium
   risk-low-life-001 → expected_risk_level: low
   risk-low-policy-001 → expected_risk_level: low
   risk-high-deposit-001 → expected_risk_level: high
   risk-high-sublet-001 → expected_risk_level: high
   risk-medium-visitor-001 → expected_risk_level: medium
   ```

2. **修 free-text 断言**（2 个 case）：
   ```
   ambiguous-room-or-kb-001:
     expected: either room_search or kb_qa acceptable
     → expected_route: rag  (放宽为只测 route)
   
   ambiguous-multi-intent-001:
     expected: should handle primary intent (room_search)
     → expected_route: rag, expected_task: room_search
   ```

3. **加 entity 解析验证**（12 个 entity case 新增字段）：
   - `expected_resolved_district`: 期望解析后的区域名（如 "天河区"）
   - `expected_resolved_room_type`: 期望解析后的房型
   - `expected_resolved_payment_type`: 期望解析后的付款方式

#### Workstream 1C: T3 数据集 (`procedure_cases.yaml`)

修复 2 个问题：

1. **修 9 个 free-text 断言 → 结构化**：
   ```
   appt-no-apartment-001 → expected_phase: clarify
   appt-no-time-001 → expected: {has_clarification_question: true}
   appt-past-time-001 → expected: {handles_past_time: true}
   appt-multiple-rooms-001 → expected_phase: appointment
   memory-empty-001 → expected_phase: clarify
   handoff-not-satisfied-001 → expected_phase: handoff
   handoff-escalate-001 → expected_phase: handoff
   lease-no-user-001 → expected_phase: clarify
   ```

2. **修 multi-turn（数据集 + runner 联动）**：
   - 数据集不变（保留 context 字段作为文档）
   - 修复在 runner 端

3. **修 lease user_id**：
   - runner 端透传 `user_id` 字段而非硬编码

---

### Wave 2 — Runner 改造（串行，依赖 Wave 1 完成）

**文件：** `backend/evals/runners/run_rag_eval.py`

**Task 2.1: Room search criteria 检查**

`_check_criteria()` 新增：
```python
# Room search criteria
if expected.get("response_not_empty"):
    has_cards = len(cards) > 0
    results["response_not_empty"] = {"pass": has_cards, "detail": f"cards={len(cards)}"}

if expected.get("district_match"):
    expected_district = case.get("expected_district")
    if expected_district:
        room_cards = [c for c in cards if c.get("type") == "room_card"]
        district_ok = any(
            c.get("district_name", "") == expected_district
            for c in room_cards
        ) if room_cards else True
        results["district_match"] = {"pass": district_ok, "detail": f"expected={expected_district}"}

if expected.get("price_in_range"):
    expected_price_max = case.get("expected_price_max")
    if expected_price_max:
        room_cards = [c for c in cards if c.get("type") == "room_card"]
        price_ok = all(
            c.get("rent", 0) <= expected_price_max
            for c in room_cards
        ) if room_cards else True
        results["price_in_range"] = {"pass": price_ok, "detail": f"max={expected_price_max}"}

if expected.get("amenity_match"):
    expected_amenities = case.get("expected_amenities", [])
    if expected_amenities:
        room_cards = [c for c in cards if c.get("type") == "room_card"]
        amenity_ok = all(
            any(a in c.get("facilities", "") or a in c.get("tags", "")
                for a in expected_amenities)
            for c in room_cards
        ) if room_cards else True
        results["amenity_match"] = {"pass": amenity_ok, "detail": f"expected={expected_amenities}"}

if expected.get("latency_ok"):
    # Set in run_live_eval per-case from latency_ms
    max_latency = expected.get("latency_max_ms", 15000)
    # latency checked at call site, injected via extra kwarg
```

**Task 2.2: Multi-turn 支持**

```python
# run_live_eval 中新增 multi-turn session 管理
def run_live_eval(..., multi_turn_enabled=True):
    ...
    sessions: dict[str, str] = {}  # context_key -> session_id
    
    for case in all_cases:
        context_key = case.get("context", "") or case.get("id")
        if case.get("context") and context_key in sessions:
            session_id = sessions[context_key]  # 复用 session
        else:
            session_id = f"eval-{case_id}-{uuid.uuid4().hex[:8]}"
            sessions[context_key] = session_id
```

**Task 2.3: user_id 透传**

```python
# _send_live 中：
user_id = case.get("user_id", "eval-runner")
frame = ConversationFrame(message=query, session_id=session_id, user_id=user_id)
```

**Task 2.4: latency_ok 检查**

在 per-case 循环中：
```python
latency_ok = latency_ms <= case.get("expected", {}).get("latency_max_ms", 15000)
```

**Task 2.5: T2 risk_level 验证**

`_check_understanding_criteria` 已有 `expected_risk` 检查（第 381 行），数据集补了 `expected_risk_level` 后自动生效。

**Task 2.6: T2 entity 解析验证**

新增 `_check_entity_resolution_criteria()`：
```python
def _check_entity_resolution_criteria(response, case, diagnostic):
    results = {}
    edr = case.get("expected") or {}
    # 从 diagnostic 中提取 resolved entities
    resolved = diagnostic.get("resolved_entities", {})
    
    if edr.get("expected_resolved_district"):
        actual = resolved.get("district", "")
        results["resolved_district"] = {
            "pass": actual == edr["expected_resolved_district"],
            "detail": f"expected={edr['expected_resolved_district']}, actual={actual}"
        }
    # 同理 room_type, payment_type
    return results
```

**Task 2.7: 报告格式更新**

- Room search 报告改为 criteria 汇总表
- T2/T3 报告显示 per-case criteria 详情
- 新增 "实体解析验证" 章节

---

### Wave 3 — Unit Tests（串行，依赖 Wave 2）

**文件：** `backend/tests/unit/evals/test_rag_eval_runner.py`

1. 新增 room search criteria 测试（response_not_empty, district_match, price_in_range, amenity_match, latency_ok）
2. 新增 multi-turn session 复用测试
3. 新增 entity resolution criteria 测试
4. 更新现有测试以匹配新数据格式

---

### Wave 4 — 文档 + 验证（串行）

1. `uv run pytest tests/unit/evals/ -q` 全部通过
2. `uv run ruff check src tests` clean
3. 更新 `docs/plans/current-plan.md`
4. 更新 `docs/plans/known-issues.md`
5. 更新 `docs/tests/evaluation-report.md`
6. Checkpoint

---

## 并行执行指导

```
Wave 1 (3 工作流并行):
  ┌─ 1A: T1 rag_retrieval_cases.yaml ──────────────┐
  ├─ 1B: T2 understanding_route_cases.yaml ─────────┤  → 无文件冲突
  └─ 1C: T3 procedure_cases.yaml ──────────────────┘

Wave 2 (串行):
  └─ run_rag_eval.py — 整合所有 3 层改动

Wave 3 (串行):
  └─ test_rag_eval_runner.py

Wave 4 (串行):
  └─ Docs + verification
```

- Wave 1 三个工作流操作不同的 YAML 文件，零冲突，完全并行
- Wave 2 runner 改动需要 Wave 1 的数据结构确定后才能做
- Wave 3 测试需要 Wave 2 的函数签名确定后才能写

## 验收标准

1. T1 KB QA：60 case，全部有 `expected_doc_ids`（人工推断 + 标记待 live 验证）
2. T1 Room Search：30 case 全部改为 criteria 格式，不依赖 expected_room_ids
3. T2：55 case 全部可自动验证，无 free-text 断言，10 个 risk case 有 `expected_risk_level`
4. T3：55 case 全部有结构化断言，multi-turn 可工作，user_id 正确透传
5. `uv run pytest tests/unit/evals/ -q` 全部通过
6. `uv run ruff check src tests` clean
7. Smoke mode eval 正常运行并输出新格式报告

## 风险

- KB QA `expected_doc_ids` 推断可能不准确 → 标记 `# TODO: verify with live discovery`，后续 live 跑校准
- entity resolution criteria 需要 diagnostic 中有 `resolved_entities` 字段 → 检查 `understanding/diagnostics.py` 是否有此字段，没有则需补充
- multi-turn session 复用依赖 runner 改造正确性 → 先 smoke 后 live 验证
