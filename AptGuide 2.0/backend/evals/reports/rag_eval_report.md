# RAG Eval Report

**Generated:** 2026-05-12 01:56:17
**Total cases:** 120

## Summary

| Category | Total | Pass | Fail | Pass Rate | Gate | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Room | 70 | 50 | 20 | 71.4% | >= 70% | PASS |
| KB | 35 | 35 | 0 | 100.0% | >= 80% | PASS |
| Fallback | 15 | 15 | 0 | 100.0% | >= 80% | PASS |

**Overall pass rate:** 83.3%
**All gates passed:** YES

## Failed Cases (20)

- **room-budget-2000-003** [room_retrieval]: no positive room in top-10 (expected: [10, 18, 14], got: [1, 2, 200003, 34, 11, 44, 13, 15, 17, 19])
- **room-budget-3000-005** [room_retrieval]: no positive room in top-10 (expected: [20, 28, 22], got: [1, 2, 38, 9, 12, 13, 17, 18, 19, 30])
- **room-budget-1800-010** [room_retrieval]: no positive room in top-10 (expected: [16, 19, 12], got: [32, 1, 34, 6, 42, 28, 17, 18, 200020, 200060])
- **room-budget-seed-low-011** [room_retrieval]: no positive room in top-10 (expected: [200001, 200005], got: [1, 34, 35, 2, 6, 9, 11, 13, 15, 17])
- **room-budget-range-014** [room_retrieval]: no positive room in top-10 (expected: [8, 16, 12, 200015], got: [1, 2, 200035, 36, 38, 44, 13, 15, 17, 22])
- **room-area-tianhe-002** [room_retrieval]: no positive room in top-10 (expected: [25, 20, 30], got: [32, 200040, 200010, 200012, 200045, 200020, 24, 26, 28, 200030])
- **room-area-baiyun-008** [room_retrieval]: no positive room in top-10 (expected: [200025, 200020, 200030], got: [17, 13])
- **room-area-panyu-street-009** [room_retrieval]: no positive room in top-10 (expected: [18, 12, 22], got: [2, 200002, 4, 5, 200005, 6, 8, 200008, 14, 15])
- **room-tag-bright-002** [room_retrieval]: no positive room in top-10 (expected: [8, 20, 14, 200012], got: [35, 42, 10, 12, 200045, 200015, 16, 48, 22, 200028])
- **room-tag-pet-friendly-004** [room_retrieval]: no positive room in top-10 (expected: [200020, 13, 7], got: [32, 200002, 2, 36, 5, 46, 48, 19, 25, 28])
- **room-tag-wifi-008** [room_retrieval]: no positive room in top-10 (expected: [8, 200010, 3, 14], got: [1, 35, 36, 38, 40, 42, 13, 200050, 19, 200060])
- **room-tag-washer-010** [room_retrieval]: no positive room in top-10 (expected: [9, 200018, 21, 15], got: [32, 36, 38, 40, 42, 13, 17, 200050, 19, 200060])
- **room-tag-ensuite-014** [room_retrieval]: no positive room in top-10 (expected: [25, 20, 30, 15], got: [1, 34, 35, 200003, 3, 7, 9, 11, 18, 200060])
- **room-tag-large-area-016** [room_retrieval]: no positive room in top-10 (expected: [25, 200050, 35, 30], got: [200001, 1, 2, 40, 9, 42, 12, 13, 18, 19])
- **room-tag-seed-bright-019** [room_retrieval]: no positive room in top-10 (expected: [200010, 200020, 200030], got: [200001, 200002, 200003, 12, 200045, 200015, 200050, 200028, 200025, 200060])
- **room-combo-tianhe-2000-bright-002** [room_retrieval]: no positive room in top-10 (expected: [26, 22], got: [200035, 200010, 200012, 200018, 200020, 200030])
- **room-combo-south-balcony-006** [room_retrieval]: no positive room in top-10 (expected: [24, 200025, 18], got: [35, 40, 42, 10, 12, 200015, 16, 48, 19, 200028])
- **room-combo-budget-area-008** [room_retrieval]: no positive room in top-10 (expected: [200025, 200020], got: [17, 13])
- **room-combo-area-budget-pet-010** [room_retrieval]: no positive room in top-10 (expected: [25, 20], got: [200035, 200010, 200012, 200018, 200020, 200030])
- **room-combo-elevator-south-011** [room_retrieval]: no positive room in top-10 (expected: [200040, 28, 22], got: [2, 40, 9, 10, 42, 12, 200015, 16, 19, 200028])
