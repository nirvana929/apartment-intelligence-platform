# RAG v2 Eval Report

**Generated:** 2026-05-14 23:27:07
**Total cases:** 120

## Summary

| Metric | Value | Gate | Pass |
| --- | ---: | ---: | --- |
| KB source hit@3 | 94.3% | >= 90% | PASS |
| KB source hit@5 | 94.3% | - | PASS |
| KB MRR | 0.848 | - | PASS |
| KB NDCG@5 | 0.872 | - | PASS |
| Room hit@5 | 10.0% | >= 85% | FAIL |
| Room MRR | 0.010 | - | PASS |
| Room NDCG@5 | 0.007 | - | PASS |
| High-risk fallback | 40.0% | >= 100% | FAIL |
| Unvalidated rooms | 0 | = 0 | PASS |

**All gates passed:** NO

## KB Retrieval

- Total cases: 35
- Pass: 33
- Fail: 2

## Room Retrieval

- Total cases: 70
- Pass: 7
- Fail: 63

## Fallback Retrieval

- Total cases: 15
- Pass: 6
- Fail: 9

## Failed Cases (74)

- **kb-pay-cycle-002** [kb_retrieval]: no KB sources returned (expected: ['KB-PAY-002'], got: [])
  - diagnostics: route=fallback, rag_task=none, domain=unknown, action=unknown, parsed_task=fallback, risk_level=low, response_mode=normal_answer, fallback_reason=out_of_scope
- **kb-life-noise-003** [kb_retrieval]: no KB sources returned (expected: ['KB-LIFE-004'], got: [])
  - diagnostics: route=fallback, rag_task=none, domain=unknown, action=unknown, parsed_task=fallback, risk_level=low, response_mode=normal_answer, fallback_reason=out_of_scope
  - soft_preferences: `['安静', '低噪音']`
- **room-budget-1000-001** [room_retrieval]: expected room not in top-5 (expected: [1, 3, 7], got: [200079, 200080, 200091])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 1000}`
  - retrieval_queries: `['1000以内 房源']`
- **room-budget-1500-002** [room_retrieval]: no rooms returned (expected: [2, 5, 8], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'max_rent': 1500}`
  - soft_preferences: `['低预算', '性价比高']`
  - retrieval_queries: `['1500以内 低预算 性价比高 房源', '适合 低预算 性价比高 公寓']`
- **room-budget-2000-003** [room_retrieval]: no rooms returned (expected: [10, 14, 18], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 2000}`
- **room-budget-800-004** [room_retrieval]: no rooms returned (expected: [1, 4], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 4, 'area_text': '番禺'}`
- **room-budget-3000-005** [room_retrieval]: expected room not in top-5 (expected: [20, 22, 28], got: [200080, 200079, 51, 200032, 200031])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 3000}`
  - retrieval_queries: `['3000以内 房源']`
- **room-budget-cheapest-006** [room_retrieval]: no rooms returned (expected: [1, 3, 4], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - soft_preferences: `['低预算', '性价比高']`
  - retrieval_queries: `['低预算 性价比高 房源', '适合 低预算 性价比高 公寓']`
- **room-budget-1200-007** [room_retrieval]: no rooms returned (expected: [5, 9, 11], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 1200}`
  - soft_preferences: `['独立卫浴', '独卫']`
- **room-budget-2500-008** [room_retrieval]: expected room not in top-5 (expected: [25, 32, 36], got: [200094, 200083, 200080, 44, 50])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 2500}`
  - retrieval_queries: `['2500以内 房源']`
- **room-budget-500-009** [room_retrieval]: no rooms returned (expected: [3, 7], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['合租', '单间']`
- **room-budget-1800-010** [room_retrieval]: no rooms returned (expected: [12, 16, 19], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
- **room-budget-seed-low-011** [room_retrieval]: no rooms returned (expected: [200001, 200005], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - soft_preferences: `['低预算', '性价比高']`
  - retrieval_queries: `['低预算 性价比高 房源', '适合 低预算 性价比高 公寓']`
- **room-budget-seed-mid-012** [room_retrieval]: no rooms returned (expected: [200010, 200020, 200030], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 1500}`
- **room-budget-seed-high-013** [room_retrieval]: expected room not in top-5 (expected: [200040, 200050, 200060], got: [44, 200096, 50, 200095, 49])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 3000}`
  - retrieval_queries: `['3000以内 房源']`
- **room-budget-range-014** [room_retrieval]: no rooms returned (expected: [8, 12, 16, 200015], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'max_rent': 1000}`
  - retrieval_queries: `['1000以内 房源']`
- **room-area-panyu-001** [room_retrieval]: no rooms returned (expected: [1, 5, 10, 15], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 4, 'area_text': '番禺'}`
- **room-area-tianhe-002** [room_retrieval]: expected room not in top-5 (expected: [20, 25, 30], got: [200011, 200009, 200010, 200012, 200007])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 1, 'area_text': '天河'}`
  - retrieval_queries: `['天河附近 房源', '天河 单间']`
- **room-area-haizhu-003** [room_retrieval]: no rooms returned (expected: [35, 38, 42], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'district_id': 3, 'area_text': '海珠'}`
  - soft_preferences: `['海珠附近']`
  - retrieval_queries: `['海珠附近 海珠附近 房源', '海珠 海珠附近 单间', '适合 海珠附近 公寓']`
- **room-area-yuexiu-004** [room_retrieval]: no rooms returned (expected: [44, 46, 48], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 2, 'area_text': '越秀'}`
- **room-area-metro-near-005** [room_retrieval]: no rooms returned (expected: [8, 14, 22, 200008], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
- **room-area-university-006** [room_retrieval]: no rooms returned (expected: [1, 5, 10], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 4, 'area_text': '大学城'}`
- **room-area-nanting-007** [room_retrieval]: expected room not in top-5 (expected: [3, 7, 11], got: [200086, 200087, 200090, 200088, 200089])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 4, 'area_text': '南亭'}`
  - soft_preferences: `['南亭附近']`
  - retrieval_queries: `['南亭附近 南亭附近 房源', '南亭 南亭附近 单间', '适合 南亭附近 公寓']`
- **room-area-baiyun-008** [room_retrieval]: no rooms returned (expected: [200020, 200025, 200030], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 5, 'area_text': '白云'}`
  - soft_preferences: `['低预算', '性价比高']`
- **room-area-panyu-street-009** [room_retrieval]: no rooms returned (expected: [12, 18, 22], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'district_id': 4, 'area_text': '番禺'}`
  - soft_preferences: `['番禺附近']`
  - retrieval_queries: `['番禺附近 番禺附近 房源', '番禺 番禺附近 单间', '适合 番禺附近 公寓']`
- **room-area-seed-panyu-010** [room_retrieval]: expected room not in top-5 (expected: [200001, 200005, 200010], got: [200094, 200082, 200092, 200096, 200088])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 4, 'area_text': '番禺'}`
  - retrieval_queries: `['番禺附近 房源', '番禺 单间']`
- **room-area-seed-tianhe-011** [room_retrieval]: no rooms returned (expected: [200040, 200045, 200050], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 1, 'area_text': '天河'}`
- **room-area-commute-012** [room_retrieval]: no rooms returned (expected: [20, 25, 28, 30], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'district_id': 1, 'area_text': '珠江新城'}`
  - soft_preferences: `['通勤方便', '近地铁', '交通便利']`
  - retrieval_queries: `['珠江新城附近 通勤方便 近地铁 交通便利 房源', '珠江新城 通勤方便 单间', '适合白领通勤 通勤方便 近地铁 公寓']`
- **room-area-wide-013** [room_retrieval]: expected room not in top-5 (expected: [1, 20, 35, 44, 200001], got: [200070, 200073, 200022, 200029, 200018])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - retrieval_queries: `['房源']`
- **room-area-near-work-014** [room_retrieval]: no rooms returned (expected: [20, 22, 25, 28], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'district_id': 1, 'area_text': '科韵路'}`
- **room-tag-quiet-001** [room_retrieval]: no rooms returned (expected: [5, 11, 15, 200003], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - soft_preferences: `['安静', '适合学习', '低噪音']`
  - retrieval_queries: `['安静 适合学习 低噪音 房源', '适合考研学生 安静 适合学习 公寓']`
- **room-tag-bright-002** [room_retrieval]: no rooms returned (expected: [8, 14, 20, 200012], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['采光好', '朝南']`
- **room-tag-south-003** [room_retrieval]: expected room not in top-5 (expected: [10, 16, 22, 200015], got: [200109, 200097, 200052, 200061, 200049])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['朝南', '采光好']`
  - retrieval_queries: `['朝南 采光好 房源', '适合 朝南 采光好 公寓']`
- **room-tag-pet-friendly-004** [room_retrieval]: no rooms returned (expected: [7, 13, 200020], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=life, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['可养宠物', '宠物友好']`
- **room-tag-balcony-005** [room_retrieval]: no rooms returned (expected: [12, 18, 24, 200025], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - soft_preferences: `['有阳台', '带阳台']`
  - retrieval_queries: `['有阳台 带阳台 房源', '适合 有阳台 带阳台 公寓']`
- **room-tag-separate-bath-006** [room_retrieval]: expected room not in top-5 (expected: [5, 9, 11, 200008], got: [200048, 200102, 200104, 200096, 200060])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['独立卫浴', '独卫']`
  - retrieval_queries: `['独立卫浴 独卫 房源', '适合 独立卫浴 独卫 公寓']`
- **room-tag-kitchen-007** [room_retrieval]: no rooms returned (expected: [15, 20, 25, 200030], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - soft_preferences: `['有厨房', '可做饭']`
  - retrieval_queries: `['有厨房 可做饭 房源', '适合 有厨房 可做饭 公寓']`
- **room-tag-wifi-008** [room_retrieval]: expected room not in top-5 (expected: [3, 8, 14, 200010], got: [200065, 200016, 200083, 200025, 200020])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['有WiFi', '有网络']`
  - retrieval_queries: `['有WiFi 有网络 房源', '适合 有WiFi 有网络 公寓']`
- **room-tag-aircon-009** [room_retrieval]: no rooms returned (expected: [6, 12, 18, 200014], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - soft_preferences: `['有空调', '空调房']`
  - retrieval_queries: `['有空调 空调房 房源', '适合 有空调 空调房 公寓']`
- **room-tag-washer-010** [room_retrieval]: expected room not in top-5 (expected: [9, 15, 21, 200018], got: [200087, 200024, 200111, 200104, 200118])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['有洗衣机']`
  - retrieval_queries: `['有洗衣机 房源', '适合 有洗衣机 公寓']`
- **room-tag-newly-decorated-011** [room_retrieval]: no rooms returned (expected: [18, 24, 200035], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['新装修', '精装修']`
- **room-tag-elevator-012** [room_retrieval]: no rooms returned (expected: [20, 25, 30, 200040], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['有电梯', '电梯房']`
- **room-tag-high-floor-013** [room_retrieval]: no rooms returned (expected: [22, 28, 34, 200045], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - soft_preferences: `['高楼层', '视野好']`
  - retrieval_queries: `['高楼层 视野好 房源', '适合 高楼层 视野好 公寓']`
- **room-tag-ensuite-014** [room_retrieval]: expected room not in top-5 (expected: [15, 20, 25, 30], got: [200112, 200033, 200014, 200065, 200117])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['整租', '独立空间', '合租', '单间']`
  - retrieval_queries: `['整租 独立空间 合租 房源', '适合 整租 独立空间 公寓']`
- **room-tag-share-015** [room_retrieval]: no rooms returned (expected: [3, 7, 200002], got: [])
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['合租', '单间']`
- **room-tag-large-area-016** [room_retrieval]: no rooms returned (expected: [25, 30, 35, 200050], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - retrieval_queries: `['房源']`
- **room-tag-compact-017** [room_retrieval]: no rooms returned (expected: [1, 4, 6, 200003], got: [])
  - diagnostics: route=fallback, rag_task=none, domain=unknown, action=unknown, parsed_task=fallback, risk_level=low, response_mode=normal_answer, fallback_reason=out_of_scope
  - soft_preferences: `['温馨', '小而美']`
- **room-tag-seed-quiet-018** [room_retrieval]: expected room not in top-5 (expected: [200005, 200015, 200025], got: [200091, 200083, 200079, 200072, 200098])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['安静', '适合学习', '低噪音']`
  - retrieval_queries: `['安静 适合学习 低噪音 房源', '适合考研学生 安静 适合学习 公寓']`
- **room-tag-seed-bright-019** [room_retrieval]: no rooms returned (expected: [200010, 200020, 200030], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - soft_preferences: `['采光好', '朝南']`
  - retrieval_queries: `['采光好 朝南 房源', '适合 采光好 朝南 公寓']`
- **room-combo-panyu-1500-quiet-001** [room_retrieval]: no rooms returned (expected: [5, 10], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'max_rent': 1500, 'district_id': 4, 'area_text': '番禺'}`
  - soft_preferences: `['安静', '适合学习', '低噪音']`
  - retrieval_queries: `['番禺附近 1500以内 安静 适合学习 低噪音 房源', '番禺 低预算 安静 单间', '适合考研学生 安静 适合学习 公寓']`
- **room-combo-tianhe-2000-bright-002** [room_retrieval]: expected room not in top-5 (expected: [22, 26], got: [200025, 200013, 200026, 200014, 200027])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 2000, 'district_id': 1, 'area_text': '天河'}`
  - soft_preferences: `['采光好', '朝南']`
  - retrieval_queries: `['天河附近 2000以内 采光好 朝南 房源', '天河 低预算 采光好 单间', '适合 采光好 朝南 公寓']`
- **room-combo-budget-pet-003** [room_retrieval]: no rooms returned (expected: [13, 17, 200020], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'max_rent': 1800}`
  - soft_preferences: `['可养宠物', '宠物友好']`
  - retrieval_queries: `['1800以内 可养宠物 宠物友好 房源', '适合 可养宠物 宠物友好 公寓']`
- **room-combo-area-kitchen-004** [room_retrieval]: expected room not in top-5 (expected: [36, 40], got: [200060, 200059, 200076, 200061])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 2000, 'district_id': 3, 'area_text': '海珠'}`
  - soft_preferences: `['有厨房', '可做饭']`
  - retrieval_queries: `['海珠附近 2000以内 有厨房 可做饭 房源', '海珠 低预算 有厨房 单间', '适合 有厨房 可做饭 公寓']`
- **room-combo-metro-budget-005** [room_retrieval]: no rooms returned (expected: [3, 8], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'max_rent': 1000}`
  - soft_preferences: `['合租', '单间', '地铁附近']`
  - retrieval_queries: `['1000以内 合租 单间 地铁附近 房源', '适合 合租 单间 公寓']`
- **room-combo-area-type-007** [room_retrieval]: no rooms returned (expected: [10, 15], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'district_id': 4, 'area_text': '大学城'}`
  - soft_preferences: `['大学城附近']`
  - retrieval_queries: `['大学城附近 大学城附近 房源', '大学城 大学城附近 单间', '适合 大学城附近 公寓']`
- **room-combo-budget-area-008** [room_retrieval]: expected room not in top-5 (expected: [200020, 200025], got: [200105])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 1500, 'district_id': 5, 'area_text': '白云'}`
  - retrieval_queries: `['白云附近 1500以内 房源', '白云 低预算 单间']`
- **room-combo-bath-wifi-009** [room_retrieval]: no rooms returned (expected: [5, 9], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'max_rent': 1200}`
  - soft_preferences: `['独立卫浴', '独卫']`
  - retrieval_queries: `['1200以内 独立卫浴 独卫 房源', '适合 独立卫浴 独卫 公寓']`
- **room-combo-area-budget-pet-010** [room_retrieval]: expected room not in top-5 (expected: [20, 25], got: [200025, 200026, 200013, 200027, 200014])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 2000, 'district_id': 1, 'area_text': '天河'}`
  - soft_preferences: `['可养宠物', '宠物友好']`
  - retrieval_queries: `['天河附近 2000以内 可养宠物 宠物友好 房源', '天河 低预算 可养宠物 单间', '适合 可养宠物 宠物友好 公寓']`
- **room-combo-elevator-south-011** [room_retrieval]: no rooms returned (expected: [22, 28, 200040], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'max_rent': 2500}`
  - soft_preferences: `['朝南', '采光好', '有电梯', '电梯房']`
  - retrieval_queries: `['2500以内 朝南 采光好 有电梯 房源', '适合 朝南 采光好 公寓']`
- **room-combo-seed-panyu-budget-012** [room_retrieval]: expected room not in top-5 (expected: [200001, 200005], got: [200079, 200080, 200091])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 1000, 'district_id': 4, 'area_text': '番禺'}`
  - retrieval_queries: `['番禺附近 1000以内 房源', '番禺 低预算 单间']`
- **room-combo-whole-rent-budget-013** [room_retrieval]: no rooms returned (expected: [15, 20], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'max_rent': 2000}`
  - soft_preferences: `['有厨房', '可做饭', '整租', '独立空间']`
  - retrieval_queries: `['2000以内 有厨房 可做饭 整租 房源', '适合 有厨房 可做饭 公寓']`
- **room-combo-type-area-budget-014** [room_retrieval]: expected room not in top-5 (expected: [30, 35], got: [200026, 200027, 200025, 200013, 200014])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - hard_filters: `{'max_rent': 3000, 'district_id': 1, 'area_text': '天河'}`
  - retrieval_queries: `['天河附近 3000以内 房源', '天河 低预算 单间']`
- **room-combo-decorated-bright-015** [room_retrieval]: no rooms returned (expected: [18, 24], got: [])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer, fallback_reason=lease_validation_empty
  - hard_filters: `{'max_rent': 1800}`
  - soft_preferences: `['采光好', '朝南', '新装修', '精装修']`
  - retrieval_queries: `['1800以内 采光好 朝南 新装修 房源', '适合 采光好 朝南 公寓']`
- **room-boundary-ambiguous-002** [room_retrieval]: expected room not in top-5 (expected: [1, 5, 10, 20, 200001], got: [200079, 200032, 200109, 200107, 200031])
  - diagnostics: route=rag, rag_task=room_search, domain=room, action=search, parsed_task=room_search, risk_level=low, response_mode=normal_answer
  - retrieval_queries: `['房源']`
- **room-boundary-vague-004** [room_retrieval]: no rooms returned (expected: [1, 5, 10, 15], got: [])
  - diagnostics: route=fallback, rag_task=none, domain=unknown, action=unknown, parsed_task=fallback, risk_level=low, response_mode=normal_answer, fallback_reason=out_of_scope
- **fallback-deposit-guarantee-001** [fallback_retrieval]: task=kb_qa, is_confident=True, expected fallback/low-conf
  - diagnostics: route=rag, rag_task=kb_qa, domain=lease, action=ask_policy, parsed_task=kb_qa, risk_level=medium, response_mode=kb_grounded_answer
- **fallback-room-quality-003** [fallback_retrieval]: task=kb_qa, is_confident=True, expected fallback/low-conf
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
- **fallback-neighbors-004** [fallback_retrieval]: task=kb_qa, is_confident=True, expected fallback/low-conf
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
  - soft_preferences: `['安静', '低噪音']`
- **fallback-no-rent-increase-005** [fallback_retrieval]: task=kb_qa, is_confident=True, expected fallback/low-conf
  - diagnostics: route=rag, rag_task=kb_qa, domain=lease, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
- **fallback-legal-advice-008** [fallback_retrieval]: task=kb_qa, is_confident=True, expected fallback/low-conf
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
- **fallback-future-policy-010** [fallback_retrieval]: task=kb_qa, is_confident=True, expected fallback/low-conf
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
- **fallback-room-interior-011** [fallback_retrieval]: task=kb_qa, is_confident=True, expected fallback/low-conf
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
- **fallback-investment-013** [fallback_retrieval]: task=kb_qa, is_confident=True, expected fallback/low-conf
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
- **fallback-illegal-request-014** [fallback_retrieval]: task=kb_qa, is_confident=True, expected fallback/low-conf
  - diagnostics: route=rag, rag_task=kb_qa, domain=policy, action=ask_policy, parsed_task=kb_qa, risk_level=low, response_mode=normal_answer
