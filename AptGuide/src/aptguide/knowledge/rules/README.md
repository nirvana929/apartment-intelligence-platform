# 租房知识库原材料

本目录存放 `apt_rental_kb` Milvus Collection 的**原材料**。`scripts/seed_kb.py` 会读取这些 YAML 文件，生成 embedding 后写入 Milvus。

> ⚠️ 这里的内容会直接被 RAG 流程检索并送入 LLM 上下文，所以**所有文案都必须经过运营审核**，不允许直接放未校对的 LLM 生成内容、营销话术、内部口径。

## 目录结构

```text
src/aptguide/knowledge/rules/
├── README.md           本文档：维护规范
├── _schema.yaml        条目 schema 与枚举值
├── room_search.yaml    找房 / 筛选 / 标签 / 历史
├── appointment.yaml    看房预约
├── lease.yaml          签约 / 续约 / 退租 / 租约查看
├── payment.yaml        支付方式 / 押金 / 缴费 / 发票
├── life.yaml           入住 / 钥匙 / 报修 / 公共设施
├── account.yaml        注册 / 实名 / 信息修改 / 注销
└── policy.yaml         同住人 / 宠物 / 装修 / 安全 / 清算
```

## 条目 schema

每个 YAML 文件是一个数组，数组元素遵循以下结构（详见 `_schema.yaml`）：

```yaml
- doc_id: KB-APT-001            # 必填，全局唯一，前缀按模块固定
  doc_type: faq                 # 必填，枚举：faq | rule | guide | policy | flow
  module: appointment           # 必填，枚举：见下表
  title: 怎么预约看房            # 必填，≤ 30 字
  content: |                    # 必填，≤ 600 字
    （正文）
  tags: [预约, 看房, 入门]       # 选填，便于人工检索
  version: 1                    # 必填，每次更新自增
  updated_at: 2026-05-01        # 必填，YYYY-MM-DD
  reviewed_by: ops              # 必填，审核人标识
```

### `doc_id` 前缀对照

| 模块 | 前缀 | 示例 |
|------|------|------|
| room_search | `KB-RS-` | `KB-RS-001` |
| appointment | `KB-APT-` | `KB-APT-001` |
| lease | `KB-LS-` | `KB-LS-001` |
| payment | `KB-PAY-` | `KB-PAY-001` |
| life | `KB-LIFE-` | `KB-LIFE-001` |
| account | `KB-ACCT-` | `KB-ACCT-001` |
| policy | `KB-POL-` | `KB-POL-001` |

### `doc_type` 枚举

| 值 | 含义 |
|----|------|
| `faq` | 常见问答（Q&A 风格）|
| `rule` | 业务规则（条件、上下限、时效）|
| `guide` | 用户使用指引 |
| `policy` | 平台 / 公寓政策 |
| `flow` | 流程说明（多步骤）|

### `module` 枚举

`room_search` `appointment` `lease` `payment` `life` `account` `policy`

## 写作要求

1. **正文 ≤ 600 字**：超长请拆分为多条（同一 doc_id 不允许有多条记录）。
2. **不出现敏感字段**：手机号、身份证、合同全文、银行卡、内部表名、密钥等，**禁止**出现在 content 里。
3. **避免承诺式措辞**："一定"、"保证"、"绝对"、"包退"等词不允许使用；用"按合同约定"、"以门店实际为准"等中性表达。
4. **金额、时间窗、比例必须有明确数字**或写成"以合同约定为准"，不要用"通常"、"大概"、"差不多"。
5. **时态中性**：写规则不要用"我刚刚"、"这次"等时间相对词。
6. **风格简洁**：使用短句，分点列出步骤。可读性重于优雅。
7. **必要时给指引**：例如 FAQ 末尾可以指向相关 doc_id（"另见 KB-LS-007"）。

## 维护流程

1. 在对应 YAML 文件中新增 / 修改条目。
2. 自检：是否符合上面的 schema 与写作要求。
3. 提 PR，CI 跑 `scripts/validate_kb.py`（schema 校验 + 唯一性 + 长度）。
4. 运营评审通过后合并。
5. 合并后由部署流水线触发 `make seed-kb`，全量重写 `apt_rental_kb` Collection。

> ⚠️ `seed-kb` 默认采用"按 doc_id 全量替换"策略：删除旧版本、写入新版本。删除前请确认条目不需要保留历史。如需保留历史版本，请提交到独立的 `archive/` 目录。

## 与代码的关系

- `vector/kb_search.py` 仅负责**检索**，不修改条目。
- `scripts/seed_kb.py` 是**唯一**写入 `apt_rental_kb` 的入口；不允许在请求链路中向该 Collection 写入。
- 应用代码不要硬编码 `doc_id`；如需引用，通过 `module + title` 检索后使用。

## 与产品文档的关系

- 这里的条目是 **运营 / 客服口径**的简化版，不是法律文本；具体条款以租客签订的合同为准。
- 与 `AptGuide文档/02-产品需求文档.md` 中的对话样例保持一致，避免 FAQ 答案与产品对话样例口径冲突。
