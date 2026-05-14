# RAG v2 Diagnostic Report

## Baseline After Semantic Interaction Routing

| Metric | Value |
| --- | ---: |
| KB source hit@3 | 57.1% |
| KB source hit@5 | 62.9% |
| Room hit@5 | 20.0% |
| High-risk fallback | 93.3% |
| Unvalidated rooms | 0 |

## Failure Classification

| Case | Type | Layer | Evidence | Next action |
| --- | --- | --- | --- | --- |
| kb-004 | KB | interaction_intent | "预约看房怎么取消" → route=appointment, parsed_task=fallback | Fix classifier: appointment policy questions → kb_qa |
| kb-013 | KB | interaction_intent | "预约看房要提前多久" → route=appointment, parsed_task=fallback | Fix classifier: appointment policy questions → kb_qa |
| kb-018 | KB | interaction_intent | "晚上十点以后能报修吗" → route=memory, parsed_task=fallback | Fix classifier: "报修" not a memory action |
| kb-023 | KB | interaction_intent | "公共区域卫生谁打扫" → route=fallback | Fix classifier: life/policy question detection |
| kb-026 | KB | interaction_intent | "租期到了不续约会怎样" → route=fallback | Fix classifier: lease policy question detection |
| kb-027 | KB | interaction_intent | "预约后迟到怎么办" → route=appointment, parsed_task=fallback | Fix classifier: appointment policy questions → kb_qa |
| kb-033 | KB | interaction_intent | "安全注意事项有哪些" → route=fallback | Fix classifier: policy question detection |
| room-003 | Room | interaction_intent | "海珠区近地铁通勤方便" → route=fallback | Fix classifier: room search without explicit "找房" |
| kb-002 | KB | kb_raw_recall | "提前退租会扣多少钱" expected KB-LEASE-006, not in top-5 | Improve query expansion for lease penalty |
| kb-010 | KB | kb_raw_recall | "合租可以带朋友住吗" expected KB-LIFE-009+KB-POLICY-009 | Improve query expansion for guest policy |
| kb-019 | KB | kb_raw_recall | "房间可以自己换锁吗" expected KB-POLICY-005+KB-LEASE-010 | Improve query expansion for lock policy |
| kb-030 | KB | kb_raw_recall | "同住人需要登记吗" expected KB-POLICY-001+KB-POLICY-009 | Improve query expansion for cohabitation |
| kb-034 | KB | kb_raw_recall | "换房间可以吗" expected KB-LEASE-010+KB-APPT-004 | Improve query expansion for room change |
| kb-035 | KB | kb_raw_recall | "违约金怎么算" expected KB-LEASE-006, not in top-5 | Improve query expansion for penalty calculation |
| room-002 | Room | lease_validation | "天河区3000以内可月付" → lease_validation_empty | Data consistency: rooms may not have MONTHLY payment |
| room-005 | Room | lease_validation | "白云区大面积低预算" → lease_validation_empty | Data consistency: rooms may not exist in district 2 |
| room-004 | Room | room_ranking | "番禺区2000以内适合考研" expected rooms not in top-5 | Ranking may need preference-aware scoring |
| fb-001 | Fallback | confidence_gate | "今天天气怎么样" → kb_qa, is_confident=True | Classifier correctly routes to fallback but pipeline returns kb_qa |

## Key Findings

### 1. Intent Misroute is the #1 Problem (8/18 failures = 44%)

The heuristic classifier has keyword collision issues:
- "预约" triggers appointment(create) even for policy questions like "预约看房怎么取消"
- "记" / "报修" can trigger memory when the user is asking a policy question
- General questions without clear domain keywords fall to fallback instead of being recognized as KB policy questions
- Room search queries without "找房" or "房源" keywords fall to fallback

### 2. Raw Recall is the #2 Problem (6/18 failures = 33%)

Even with correct intent, the retrieval doesn't find expected docs. This suggests:
- Query expansion may be too narrow
- Expected docs may not have good embedding matches for the query phrasing
- Module_intent filtering may be too restrictive

### 3. Room Validation Gaps (2/18 = 11%)

Two room cases return empty after lease validation, suggesting data consistency issues (expected rooms may not match the hard_filters in the eval cases).

### 4. Confidence Gate False Positive (1/18 = 6%)

"今天天气怎么样" is correctly classified as fallback by the classifier but the pipeline still returns kb_qa with is_confident=True. This suggests the pipeline's fallback detection may not align with the classifier's routing.
