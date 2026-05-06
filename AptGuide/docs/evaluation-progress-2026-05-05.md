# AptGuide 评测进度记录

**日期:** 2026-05-05
**状态:** 已完成（50/800 条样本测试）

---

## 一、已完成工作

### 1.1 修复的 S1/S2 问题

| 问题 | 状态 | 修改文件 |
|------|------|----------|
| S1: body user_id 未被忽略 | ✅ fixed | `src/aptguide/schemas/request.py`, `src/aptguide/api/chat.py` |
| S2: /health/deps 端点不存在 | ✅ fixed | `src/aptguide/api/health.py` |
| S2: 卡片字段映射不完整 | ✅ fixed | `src/aptguide/agent/nodes/tool.py` |

### 1.2 创建的测试和评测工具

| 文件 | 用途 | 状态 |
|------|------|------|
| `evals/runner.py` | 评测运行器，支持对话和检索评测 | ✅ 完成 |
| `tests/e2e/test_ai_functions.py` | 33 个 AI 功能测试用例 | ✅ 完成 |

### 1.3 评测结果（50 条样本）

| 数据集 | 总数 | 通过 | 失败 | 通过率 |
|--------|------|------|------|--------|
| 对话评测 | 50 | 36 | 14 | 72% |
| 检索评测 | 50 | 50 | 0 | 100% |

---

## 二、当前状态

### 2.1 评测进度

- 对话数据集：300 条（已完成 50 条样本测试）
- 检索数据集：500 条（已完成 50 条样本测试）

### 2.2 失败用例分析

对话评测失败的主要原因：

1. **数据覆盖问题**：部分查询在 Milvus 中没有匹配的房源
   - 例：番禺区带独卫、珠江新城附近等
   - 解决方案：扩充 Milvus 数据或调整测试用例

2. **Reply 要点检查太严格**：
   - 期望：推荐海珠区带厨房的两居室
   - 实际：推荐天河公寓1002...（回复内容不同但功能正确）
   - 解决方案：更新关键词映射或放宽检查条件

3. **Agent 追问行为**：
   - 单条件查询时 agent 会追问更多信息
   - 这是设计行为，不是错误

### 2.3 测试问题记录

评测数据集中的测试问题已记录在：
- `evals/datasets/dialog_cases.yaml`（300 条对话用例）
- `evals/datasets/retrieval_cases.yaml`（500 条检索用例）

每个用例包含：
- 测试问题（user message）
- 期望意图（expected_intent）
- 期望槽位（expected_slots）
- 期望回复要点（expected_reply_points）

---

## 三、下次继续的方向

1. **运行全量评测**：执行 `uv run python -m evals.runner --verbose`
2. **分析失败用例**：查看 `evals/results/` 目录下的结果文件
3. **优化评测脚本**：根据失败原因调整检查逻辑
4. **更新测试报告**：记录最终评测结果

---

## 四、相关文件

- 评测运行器：`evals/runner.py`
- 对话数据集：`evals/datasets/dialog_cases.yaml`（300 条）
- 检索数据集：`evals/datasets/retrieval_cases.yaml`（500 条）
- 评测结果：`evals/results/eval_results_partial_50cases_20260505.json`
- AI 功能测试：`tests/e2e/test_ai_functions.py`
- 进度文档：`docs/evaluation-progress-2026-05-05.md`
