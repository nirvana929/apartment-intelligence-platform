# 模型性能基准测试报告

测试日期：2026-05-02
测试目的：为 AptInsight 各节点选择最优模型（速度 + 质量）

## 测试环境

- 测试场景：意图识别、SQL 生成、答案生成
- 测试问题：「本月各公寓预约量排名」
- max_tokens：意图 200、SQL 500、答案 200
- temperature：0.1

---

## 第一轮：Qwen 2.5 / Grok 3 / MiMo 测试

### 测试的模型

| 平台 | 模型 | API 地址 |
|------|------|---------|
| 小米 MiMo | mimo-v2.5-pro | https://token-plan-cn.xiaomimimo.com/v1 |
| xAI Grok | grok-3-fast | https://api.x.ai/v1 |
| xAI Grok | grok-3-mini | https://api.x.ai/v1 |
| 阿里百炼 | qwen-turbo | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| 阿里百炼 | qwen-turbo-latest | 同上 |
| 阿里百炼 | qwen-plus | 同上 |
| 阿里百炼 | qwen-plus-latest | 同上 |
| 阿里百炼 | qwen-max | 同上 |
| 阿里百炼 | qwen-max-latest | 同上 |
| 阿里百炼 | qwen-long | 同上 |
| 阿里百炼 | qwen2.5-7b-instruct | 同上 |
| 阿里百炼 | qwen2.5-14b-instruct | 同上 |
| 阿里百炼 | qwen2.5-32b-instruct | 同上 |
| 阿里百炼 | qwen2.5-72b-instruct | 同上 |

## 第一轮测试结果

### 1. 意图识别（速度关键）

输入：判断「本月各公寓预约量排名」的意图类型

| 模型 | 耗时 | 判断正确 | JSON 格式 | 备注 |
|------|------|---------|----------|------|
| **qwen-turbo** | 1315ms | ✅ analysis | ✅ 干净 | 最快 |
| qwen-turbo-latest | 1509ms | ✅ analysis | ✅ 干净 | |
| qwen2.5-14b-instruct | 1913ms | ✅ analysis | ⚠️ 带```json | |
| qwen2.5-7b-instruct | 1944ms | ⚠️ analysis/request | ⚠️ 带```json | 输出格式不规范 |
| qwen2.5-32b-instruct | 2092ms | ✅ analysis | ✅ 干净 | |
| qwen2.5-72b-instruct | 2225ms | ✅ analysis | ⚠️ 带```json | |
| qwen-max | 2406ms | ✅ analysis | ⚠️ 带```json | |
| qwen-plus | 2625ms | ✅ analysis | ✅ 干净 | |
| qwen-long | 2731ms | ✅ analysis | ✅ 干净 | |
| qwen-plus-latest | 2878ms | ✅ analysis | ✅ 干净 | |
| qwen-max-latest | 3333ms | ✅ analysis | ⚠️ 带```json | |
| grok-3-fast | 3963ms | ✅ analysis | ✅ 干净 | |
| MiMo-Pro | 4567ms | ✅ analysis | ✅ 干净 | |
| grok-3-mini | 14219ms | ❌ out_of_scope | ✅ | 判断错误 |

### 2. SQL 生成（质量关键）

输入：根据问题生成 MySQL SQL，评分标准：SELECT/ GROUP BY/ is_deleted

| 模型 | 耗时 | SQL 质量 | 备注 |
|------|------|---------|------|
| **qwen-turbo** | 1981ms | 3/3 ✅ | 最快，质量完美 |
| qwen-turbo-latest | 2320ms | 3/3 ✅ | |
| qwen2.5-7b-instruct | 2338ms | 3/3 ✅ | |
| qwen2.5-14b-instruct | 3416ms | 3/3 ✅ | |
| qwen-plus | 4088ms | 3/3 ✅ | |
| qwen2.5-32b-instruct | 4055ms | 3/3 ✅ | |
| qwen-long | 4212ms | 3/3 ✅ | |
| qwen2.5-72b-instruct | 4734ms | 3/3 ✅ | |
| qwen-plus-latest | 4330ms | 3/3 ✅ | |
| qwen-max-latest | 7555ms | 3/3 ✅ | |
| qwen-max | 10285ms | 3/3 ✅ | 太慢 |
| MiMo-Pro | 10667ms | ❌ 空响应 | 偶尔返回空 |
| grok-3-fast | - | - | 429 限流 |

### 3. 答案生成（速度 + 质量）

输入：根据查询结果写 50 字总结

| 模型 | 耗时 | 质量 | 备注 |
|------|------|------|------|
| qwen-turbo-latest | 1218ms | ✅ 简洁准确 | 最快 |
| **qwen-turbo** | 1353ms | ✅ 简洁准确 | |
| qwen2.5-72b-instruct | 1874ms | ✅ | |
| qwen2.5-7b-instruct | 1906ms | ✅ | |
| qwen2.5-14b-instruct | 1930ms | ✅ | |
| qwen2.5-32b-instruct | 1958ms | ✅ | |
| qwen-plus | 2147ms | ✅ | |
| qwen-plus-latest | 2322ms | ✅ | |
| qwen-long | 2309ms | ✅ | |
| qwen-max-latest | 2862ms | ✅ 详细 | |
| qwen-max | 5295ms | ✅ | 太慢 |

### 4. 综合对比（意图 + SQL + 答案）

| 模型 | 意图 | SQL | 答案 | **总耗时** | SQL质量 | 推荐 |
|------|------|-----|------|-----------|---------|------|
| **qwen-turbo** | 1.3s | 2.0s | 1.4s | **4.7s** | 3/3 | ⭐ 最佳性价比 |
| **qwen-turbo-latest** | 1.5s | 2.3s | 1.2s | **5.0s** | 3/3 | ⭐ 推荐 |
| qwen2.5-7b-instruct | 1.9s | 2.3s | 1.9s | 6.1s | 3/3 | |
| qwen2.5-14b-instruct | 1.9s | 3.4s | 1.9s | 7.2s | 3/3 | |
| qwen-plus | 2.6s | 4.1s | 2.1s | 8.8s | 3/3 | |
| qwen2.5-32b-instruct | 2.1s | 4.1s | 2.0s | 8.2s | 3/3 | |
| qwen-max | 2.4s | 10.3s | 5.3s | 18.0s | 3/3 | 太慢 |
| MiMo-Pro | 4.6s | 10.7s | - | 15.3s+ | 偶尔空 | 当前方案 |

## 与 MiMo-Pro 对比

| 指标 | MiMo-Pro | qwen-turbo-latest | 提升 |
|------|----------|-------------------|------|
| 意图识别 | 4.6s | 1.5s | **3.1x 快** |
| SQL 生成 | 10.7s | 2.3s | **4.7x 快** |
| 答案生成 | - | 1.2s | - |
| 总耗时 | 15.3s+ | 5.0s | **3x 快** |
| SQL 质量 | 偶尔空响应 | 3/3 稳定 | 更稳定 |
| 输出格式 | 干净 | 干净 | 相当 |

## 结论

**推荐方案：全部节点使用 qwen-turbo-latest**

理由：
1. 速度最快（总耗时 5s vs MiMo-Pro 15s+）
2. SQL 质量稳定（3/3，无空响应问题）
3. 输出格式干净（不带 markdown 包裹）
4. 成本更低（turbo 级别定价）

备选方案：
- 意图/答案用 qwen-turbo-latest，SQL 用 qwen-plus（更稳但慢 2s）
- 全部用 qwen-turbo（比 latest 略快，质量相当）

---

## 第二轮：Qwen 3.6 / Grok 4.3 最新模型测试

### 测试的模型

| 平台 | 模型 | 定位 |
|------|------|------|
| 阿里百炼 | qwen3.6-flash | 便宜、快，性能接近 Plus |
| 阿里百炼 | qwen3.6-plus | 综合推荐，性能/成本平衡 |
| 阿里百炼 | qwen3.6-max-preview | 最强推理，预览版 |
| xAI | grok-4.3 | 当前 xAI 推荐主模型 |
| xAI | grok-4.3-fast | Grok 快速版（如存在） |
| 对比基线 | qwen-turbo-latest | 第一轮最优 |

### 测试结果

#### 意图识别

| 模型 | 耗时 | tokens | 判断正确 | 备注 |
|------|------|--------|---------|------|
| **qwen-turbo-latest (基线)** | **1489ms** | **83** | ✅ | 最快 |
| qwen3.6-flash | 8793ms | 1065 | ✅ | 深度思考模式，token 爆炸 |
| qwen3.6-plus | 11012ms | 585 | ✅ | 同上 |
| qwen3.6-max-preview | 16124ms | 558 | ✅ | 同上 |
| grok-4.3 | - | - | - | 429 限流 |
| grok-4.3-fast | - | - | - | 400 不可用 |

#### SQL 生成

| 模型 | 耗时 | tokens | SQL 质量 | 备注 |
|------|------|--------|---------|------|
| **qwen-turbo-latest (基线)** | **2269ms** | **219** | 3/3 ✅ | 最快 |
| qwen3.6-flash | 18283ms | 2575 | 3/3 ✅ | 思考模式，token 10x |
| qwen3.6-plus | 超时 | - | - | 60s 超时 |
| qwen3.6-max-preview | 53023ms | 2389 | 3/3 ✅ | 极慢 |
| grok-4.3 | - | - | - | 429 限流 |

#### 答案生成

| 模型 | 耗时 | tokens | 质量 | 备注 |
|------|------|--------|------|------|
| qwen3.6-flash | 10949ms | 1422 | ✅ | 思考模式 |
| qwen3.6-plus | 34666ms | 1915 | ✅ | 极慢 |
| qwen3.6-max-preview | 46430ms | 1977 | ✅ | 极慢 |

#### 尝试关闭思考模式

尝试了两种方式关闭 Qwen 3.6 的深度思考模式：

1. **prompt 后缀 `/no_think`** — 无效，仍生成 900-2500 tokens
2. **API 参数 `extra_body: {enable_thinking: false}`** — 无效，仍生成 1000-3000 tokens

结论：Qwen 3.6 系列目前无法通过 OpenAI 兼容 API 关闭思考模式。

### 第二轮结论

| 模型 | 意图 | SQL | 答案 | 总耗时 | 状态 |
|------|------|-----|------|--------|------|
| **qwen-turbo-latest** | 1.5s | 2.3s | 1.2s | **5.0s** | ⭐ 仍然最优 |
| qwen3.6-flash | 8.8s | 18.3s | 10.9s | 38.0s | 思考模式太慢 |
| qwen3.6-plus | 11.0s | 超时 | 34.7s | 超时 | 不可用 |
| qwen3.6-max-preview | 16.1s | 53.0s | 46.4s | 115.5s | 不可用 |
| grok-4.3 | 限流 | 限流 | 限流 | - | API 额度耗尽 |

**Qwen 3.6 系列不适合本项目的实时查询场景**——内置深度思考模式导致 token 消耗 10-30 倍，速度慢 5-20 倍。且无法通过 API 参数关闭。

**最终推荐不变：全部节点使用 qwen-turbo-latest。**
