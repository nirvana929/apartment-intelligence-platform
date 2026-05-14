# RAG v2 Eval Report

**Generated:** 2026-05-14 03:15:10
**Total cases:** 55

## Summary

| Metric | Value | Gate | Pass |
| --- | ---: | ---: | --- |
| KB source hit@3 | 48.6% | >= 90% | FAIL |
| KB source hit@5 | 51.4% | - | PASS |
| KB MRR | 0.458 | - | PASS |
| KB NDCG@5 | 0.440 | - | PASS |
| Room hit@5 | 40.0% | >= 85% | FAIL |
| Room MRR | 0.400 | - | PASS |
| Room NDCG@5 | 0.294 | - | PASS |
| High-risk fallback | 100.0% | >= 100% | PASS |
| Unvalidated rooms | 0 | = 0 | PASS |

**All gates passed:** NO

## KB Retrieval

- Total cases: 35
- Pass: 18
- Fail: 17

## Room Retrieval

- Total cases: 5
- Pass: 2
- Fail: 3

## Fallback Retrieval

- Total cases: 15
- Pass: 15
- Fail: 0

## Failed Cases (20)

- **kb-002** [kb_retrieval]: expected source not in top-5 (expected: ['KB-LEASE-006'], got: ['KB-LEASE-008', 'KB-LEASE-007', 'KB-LEASE-005', 'KB-LEASE-009', 'KB-LEASE-011'])
- **kb-005** [kb_retrieval]: no KB sources returned (expected: ['KB-PAY-002'], got: [])
- **kb-006** [kb_retrieval]: no KB sources returned (expected: ['KB-PAY-001', 'KB-PAY-003'], got: [])
- **kb-007** [kb_retrieval]: no KB sources returned (expected: ['KB-LEASE-012', 'KB-LIFE-001'], got: [])
- **kb-008** [kb_retrieval]: no KB sources returned (expected: ['KB-LIFE-001', 'KB-LIFE-002'], got: [])
- **kb-009** [kb_retrieval]: no KB sources returned (expected: ['KB-LIFE-005'], got: [])
- **kb-010** [kb_retrieval]: no KB sources returned (expected: ['KB-LIFE-009', 'KB-POLICY-009'], got: [])
- **kb-017** [kb_retrieval]: no KB sources returned (expected: ['KB-LEASE-002'], got: [])
- **kb-018** [kb_retrieval]: expected source not in top-5 (expected: ['KB-LIFE-003'], got: ['KB-LIFE-001', 'KB-LIFE-004', 'KB-POLICY-008', 'KB-APPT-002', 'KB-APPT-004'])
- **kb-019** [kb_retrieval]: expected source not in top-5 (expected: ['KB-LEASE-010', 'KB-POLICY-005'], got: ['KB-LEASE-009', 'KB-LEASE-012', 'KB-POLICY-008', 'KB-ACCT-003', 'KB-APPT-009'])
- **kb-020** [kb_retrieval]: no KB sources returned (expected: ['KB-PAY-005'], got: [])
- **kb-022** [kb_retrieval]: no KB sources returned (expected: ['KB-LEASE-008', 'KB-LEASE-009'], got: [])
- **kb-023** [kb_retrieval]: no KB sources returned (expected: ['KB-LIFE-003', 'KB-LIFE-006'], got: [])
- **kb-027** [kb_retrieval]: no KB sources returned (expected: ['KB-APPT-006'], got: [])
- **kb-030** [kb_retrieval]: expected source not in top-5 (expected: ['KB-POLICY-001', 'KB-POLICY-009'], got: ['KB-APPT-009', 'KB-ACCT-003', 'KB-LEASE-002', 'KB-LEASE-012', 'KB-LEASE-001'])
- **kb-034** [kb_retrieval]: no KB sources returned (expected: ['KB-APPT-004', 'KB-LEASE-010'], got: [])
- **kb-035** [kb_retrieval]: expected source not in top-5 (expected: ['KB-LEASE-006'], got: ['KB-LEASE-008', 'KB-LEASE-010', 'KB-LEASE-009', 'KB-LEASE-004', 'KB-LEASE-005'])
- **room-002** [room_retrieval]: no rooms returned (expected: [200013, 200014, 200025, 200026], got: [])
- **room-004** [room_retrieval]: no rooms returned (expected: [200098, 200105, 200106], got: [])
- **room-005** [room_retrieval]: expected room not in top-5 (expected: [200031, 200032, 200043], got: [200098, 200102, 200104, 200115, 200100])
