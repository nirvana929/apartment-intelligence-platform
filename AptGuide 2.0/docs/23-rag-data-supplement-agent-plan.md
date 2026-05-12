# RAG Data Supplement Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare enough trustworthy data for AptGuide 2.0 RAG MVP: lease-visible room seed data, reviewed KB rules, retrieval eval cases, and data quality reports.

**Architecture:** This agent owns the data layer only. Generated room data must be inserted into the `lease` test database first, then exposed through lease internal tools; it must not be written only to Milvus. KB data is maintained as reviewed YAML/CMS-style rules, and eval data is kept separate from runtime data.

**Tech Stack:** Java 17, Spring Boot 3, MyBatis-Plus, MySQL, YAML, Markdown, shell/curl.

---

## 0. Scope

This document is for the **Data Supplement Agent** only.

You are responsible for:

- auditing current public room data;
- supplementing room inventory to support RAG MVP;
- adding lease test seed data;
- ensuring seed rooms are visible through lease tools;
- supplementing KB rules to 70 reviewed entries;
- creating 120 MVP retrieval eval cases;
- writing reports for the RAG implementation agent.

You are **not** responsible for:

- implementing Milvus adapters;
- implementing query rewrite;
- implementing ranking;
- implementing RAG answer generation;
- implementing appointment write workflow;
- registering mock tools in AptGuide 2.0 runtime.

## 1. Required Reading

Read these before editing:

1. `AptGuide 2.0/README.md`
2. `AptGuide 2.0/docs/21-rag-final-implementation-scheme.md`
3. `AptGuide 2.0/docs/22-rag-mvp-data-and-implementation-plan.md`
4. `AptGuide/AptGuide文档/09-RAG数据生成与入库指南.md`
5. `AptGuide/AptGuide文档/06-Milvus知识库设计.md`
6. `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiToolController.java`
7. `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/*.java`

## 2. Non-Negotiable Data Rules

1. Do not run seed SQL against production.
2. Do not create room data only in Milvus.
3. Do not expose generated room data as if it were real production inventory.
4. Do not include phone, ID card, bank card, contract text, exact door number, latitude, longitude, or user data in RAG data.
5. Do not mark KB entries active unless they have `reviewed_by`.
6. Retrieval eval positive room IDs must exist in the lease test database.
7. Data reports must not contain PII.

## 3. Deliverables

Create or modify these files:

```text
lease/web/web-app/src/main/resources/ai-seed/README.md
lease/web/web-app/src/main/resources/ai-seed/aptguide_rag_room_seed.sql
lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/RoomSyncVo.java
lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/RoomSyncResponse.java
lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/RoomVo.java
lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiToolController.java
AptGuide 2.0/backend/knowledge/rules/room_search.yaml
AptGuide 2.0/backend/knowledge/rules/appointment.yaml
AptGuide 2.0/backend/knowledge/rules/lease.yaml
AptGuide 2.0/backend/knowledge/rules/payment.yaml
AptGuide 2.0/backend/knowledge/rules/life.yaml
AptGuide 2.0/backend/knowledge/rules/account.yaml
AptGuide 2.0/backend/knowledge/rules/policy.yaml
AptGuide 2.0/backend/evals/datasets/rag_mvp_retrieval_cases.yaml
AptGuide 2.0/evals/reports/room_data_audit_report.md
AptGuide 2.0/evals/reports/kb_seed_report.md
AptGuide 2.0/evals/reports/data_supplement_handoff_report.md
```

## 4. Data Targets

### Room Data

> WeChat rental messages are handled by `25-wechat-real-listing-import-agent-plan.md` as external real listing leads. They are real posted data, but default to `UNVERIFIED`, `UNKNOWN` availability, and `appointable=false` until separate verification.

Target final visible public rooms: **150**.

| Source | Count | Rule |
| --- | ---: | --- |
| existing `db_public` | about 31 | use real public rows already in the test DB |
| `generated_seed` | 104 | insert into lease test DB, not just YAML/Milvus |
| `manual_boundary_seed` | 15 | insert into lease test DB for boundary/recovery tests |

Target district distribution:

| District | Count |
| --- | ---: |
| 天河区 | 30 |
| 越秀区 | 22 |
| 海珠区 | 26 |
| 番禺区 | 38 |
| 白云区 | 24 |
| 北京昌平区 | 10 |

Target rent distribution:

| Rent Band | Count |
| --- | ---: |
| 800-1500 | 24 |
| 1500-2200 | 34 |
| 2200-3200 | 42 |
| 3200-4500 | 32 |
| 4500+ | 18 |

Target tag coverage:

| Tag | Minimum Count |
| --- | ---: |
| 安静 | 45 |
| 近地铁 | 55 |
| 独卫 | 60 |
| 朝南 | 45 |
| 可月付 | 80 |
| 适合考研 | 35 |
| 适合通勤 | 55 |
| 采光好 | 45 |
| 家电齐全 | 70 |
| 可短租 | 25 |

### KB Rules

Target reviewed rules: **70**.

| Module | Count |
| --- | ---: |
| `room_search` | 10 |
| `appointment` | 10 |
| `lease` | 12 |
| `payment` | 10 |
| `life` | 10 |
| `account` | 8 |
| `policy` | 10 |

### Eval Cases

Target MVP retrieval cases: **120**.

| Type | Count |
| --- | ---: |
| `room_retrieval` | 70 |
| `kb_retrieval` | 35 |
| `fallback_retrieval` | 15 |

## 5. Task D1: Audit Current Public Room Data

**Files:**

- Create: `AptGuide 2.0/evals/reports/room_data_audit_report.md`

- [ ] **Step 1: Run read-only SQL against the same database used by `lease/web-app`.**

```sql
select
  r.id as room_id,
  r.room_number,
  r.rent,
  r.apartment_id,
  r.is_release as room_release,
  a.name as apartment_name,
  a.city_id,
  a.city_name,
  a.district_id,
  a.district_name,
  a.is_release as apartment_release,
  a.address_detail
from room_info r
join apartment_info a on a.id = r.apartment_id
where r.is_deleted = 0
  and a.is_deleted = 0
  and r.is_release = 1
  and a.is_release = 1
order by a.city_name, a.district_name, r.rent;
```

- [ ] **Step 2: Count district coverage.**

```sql
select
  a.city_name,
  a.district_name,
  count(*) as active_rooms,
  min(r.rent) as min_rent,
  max(r.rent) as max_rent
from room_info r
join apartment_info a on a.id = r.apartment_id
where r.is_deleted = 0
  and a.is_deleted = 0
  and r.is_release = 1
  and a.is_release = 1
group by a.city_name, a.district_name
order by a.city_name, a.district_name;
```

- [ ] **Step 3: Write the audit report.**

Use this exact outline:

```markdown
# Room Data Audit Report

Date: 2026-05-11

## Summary

- Active public rooms:
- Cities covered:
- Districts covered:
- Min rent:
- Max rent:
- Missing public fields:

## Coverage By District

| City | District | Active Rooms | Rent Range | Gap |
| --- | --- | ---: | --- | --- |

## Sensitive Fields Excluded

- phone
- exact address detail
- latitude
- longitude
- user data
- contract data
- payment data

## Decision

Current data is / is not enough for RAG MVP.
Seed rooms required:
```

- [ ] **Step 4: Acceptance.**

The report must explicitly say whether:

- active public rooms are at least 100;
- each target Guangzhou district has at least 10 active rooms;
- seed data is required.

## 6. Task D2: Create Lease Room Seed Data

**Files:**

- Create: `lease/web/web-app/src/main/resources/ai-seed/README.md`
- Create: `lease/web/web-app/src/main/resources/ai-seed/aptguide_rag_room_seed.sql`

- [ ] **Step 1: Create seed README.**

```markdown
# AptGuide RAG Room Seed

This seed is for local/test RAG evaluation only.

Rules:

- Do not run against production.
- Seed rooms are demo/test inventory.
- Public fields may be indexed into Milvus after they are exposed by lease sync tools.
- Phone, exact door number, latitude, longitude, user data, contract data, and payment data must not be indexed.
- Rooms inserted by this seed must be returned by `/internal/ai/tools/room/search`.
```

- [ ] **Step 2: Inspect entity fields before writing SQL.**

Read:

```text
lease/model/src/main/java/com/atguigu/lease/model/entity/ApartmentInfo.java
lease/model/src/main/java/com/atguigu/lease/model/entity/RoomInfo.java
lease/model/src/main/java/com/atguigu/lease/model/entity/LabelInfo.java
lease/model/src/main/java/com/atguigu/lease/model/entity/RoomLabel.java
lease/model/src/main/java/com/atguigu/lease/model/entity/FacilityInfo.java
lease/model/src/main/java/com/atguigu/lease/model/entity/RoomFacility.java
lease/model/src/main/java/com/atguigu/lease/model/entity/PaymentType.java
lease/model/src/main/java/com/atguigu/lease/model/entity/RoomPaymentType.java
lease/model/src/main/java/com/atguigu/lease/model/entity/LeaseTerm.java
lease/model/src/main/java/com/atguigu/lease/model/entity/RoomLeaseTerm.java
```

- [ ] **Step 3: Create SQL transaction.**

The SQL must:

- insert missing apartments for target districts;
- insert seed rooms;
- ensure labels exist;
- ensure facilities exist;
- connect rooms to labels/facilities/payment types/lease terms;
- use `is_deleted=0`;
- use released status values consistent with `ReleaseStatus`;
- avoid phone, latitude, longitude, exact door numbers.

Start the file like this:

```sql
-- AptGuide RAG MVP seed. Local/test only.
start transaction;

-- Seed apartments, rooms, labels, facilities, payment types, lease terms, and join tables here.

commit;
```

- [ ] **Step 4: Maintain ID mapping.**

If the schema allows explicit IDs, reserve a stable demo range and document it in the SQL comments.

If the schema uses auto-increment only, write generated mappings into:

```text
AptGuide 2.0/evals/reports/room_data_audit_report.md
```

- [ ] **Step 5: Acceptance SQL.**

After applying to local/test DB, run:

```sql
select count(*)
from room_info r
join apartment_info a on a.id = r.apartment_id
where r.is_deleted = 0
  and a.is_deleted = 0
  and r.is_release = 1
  and a.is_release = 1;
```

Expected: `>= 150`.

## 7. Task D3: Add Lease Sync DTOs

**Files:**

- Modify: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/RoomVo.java`
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/RoomSyncVo.java`
- Create: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/vo/ai/RoomSyncResponse.java`

- [ ] **Step 1: Add fields to `RoomVo`.**

Add these fields:

```java
private Long cityId;
private String cityName;
private Long districtId;
private String districtName;
private String areaLabel;
private List<String> facilities;
private String audienceSummary;
private String dataSource;
```

- [ ] **Step 2: Create `RoomSyncVo`.**

```java
package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomSyncVo {
    private Long roomId;
    private String roomNumber;
    private Long apartmentId;
    private String apartmentName;
    private Long cityId;
    private String cityName;
    private Long districtId;
    private String districtName;
    private String areaLabel;
    private Integer rent;
    private Integer area;
    private String layout;
    private List<String> paymentTypes;
    private List<Integer> leaseTerms;
    private List<String> tags;
    private List<String> facilities;
    private String thumbnailUrl;
    private Boolean isRelease;
    private Boolean isAppointable;
    private String audienceSummary;
    private String dataSource;
    private Long updatedAt;
}
```

- [ ] **Step 3: Create `RoomSyncResponse`.**

```java
package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomSyncResponse {
    private List<RoomSyncVo> rooms;
    private Integer total;
    private String syncVersion;
}
```

- [ ] **Step 4: Compile.**

```bash
cd lease
mvn -pl web/web-app -DskipTests compile
```

Expected: compile succeeds.

## 8. Task D4: Expose Room Sync Tool

**Files:**

- Modify: `lease/web/web-app/src/main/java/com/atguigu/lease/web/app/controller/ai/AiToolController.java`

- [ ] **Step 1: Add endpoint.**

```text
GET /internal/ai/tools/sync/rooms?limit=200
```

Behavior:

- returns only active public rooms;
- default limit is `200`;
- max limit is `1000`;
- non-positive limit becomes `200`;
- response type is `Result<RoomSyncResponse>`;
- no sensitive fields are returned.

- [ ] **Step 2: Fill public fields.**

Each `RoomSyncVo` must include:

```text
roomId
roomNumber
apartmentId
apartmentName
cityId
cityName
districtId
districtName
areaLabel
rent
area
layout
paymentTypes
leaseTerms
tags
facilities
thumbnailUrl
isRelease
isAppointable
audienceSummary
dataSource
updatedAt
```

If `area`, `layout`, or `facilities` are not available from current DTOs, set them conservatively and document the gap in `data_supplement_handoff_report.md`.

- [ ] **Step 3: Ensure `/room/search` supports `roomIds`.**

Current controller has a `roomIds` branch. Verify that it actually fetches details and filters out:

- missing rooms;
- deleted rooms;
- unreleased rooms;
- unreleased apartments;
- rooms failing rent/payment/lease term filters.

- [ ] **Step 4: Curl acceptance.**

```bash
curl -H "X-Internal-Token: $AI_INTERNAL_TOKEN" \
  "http://127.0.0.1:8081/internal/ai/tools/sync/rooms?limit=200"
```

Expected:

- `code` is `0` or `200`;
- `data.total >= 150`;
- no `phone`, `latitude`, `longitude`, `addressDetail`, `address_detail`;
- each room has `roomId`, `apartmentId`, `districtId`, `rent`, `tags`, `paymentTypes`, `isAppointable`.

## 9. Task K1: Build Reviewed KB Rules

**Files:**

- Create or modify: `AptGuide 2.0/backend/knowledge/rules/room_search.yaml`
- Create or modify: `AptGuide 2.0/backend/knowledge/rules/appointment.yaml`
- Create or modify: `AptGuide 2.0/backend/knowledge/rules/lease.yaml`
- Create or modify: `AptGuide 2.0/backend/knowledge/rules/payment.yaml`
- Create or modify: `AptGuide 2.0/backend/knowledge/rules/life.yaml`
- Create or modify: `AptGuide 2.0/backend/knowledge/rules/account.yaml`
- Create or modify: `AptGuide 2.0/backend/knowledge/rules/policy.yaml`
- Create: `AptGuide 2.0/evals/reports/kb_seed_report.md`

- [ ] **Step 1: Copy usable old rules.**

Source:

```text
AptGuide/src/aptguide/knowledge/rules/*.yaml
```

Destination:

```text
AptGuide 2.0/backend/knowledge/rules/*.yaml
```

- [ ] **Step 2: Normalize rule schema.**

Every rule must look like this:

```yaml
- doc_id: KB-LEASE-005
  doc_type: rule
  module: lease
  title: 押金退还规则
  content: |
    押金退还以退租验房、费用结清和合同约定为前提。若存在未结清费用、设施损坏或违约事项，可能按合同和门店规则扣除相应费用。
    具体到账时间以门店处理和支付渠道为准。
  tags: [押金, 退租, 扣费]
  version: 1
  risk_level: high
  status: reviewed
  reviewed_by: ops
  updated_at: 2026-05-11
```

- [ ] **Step 3: Hit module counts.**

```text
room_search: 10
appointment: 10
lease: 12
payment: 10
life: 10
account: 8
policy: 10
```

- [ ] **Step 4: Remove unsafe content.**

Reject any rule containing:

- phone number;
- ID card number;
- bank card number;
- exact door number;
- guarantee language like “一定退”, “100%”, “保证不扣”.

- [ ] **Step 5: Write `kb_seed_report.md`.**

Required sections:

```markdown
# KB Seed Report

## Summary

- Total reviewed rules:
- Modules:
- High-risk rules:

## Counts

| Module | Count | Required | Pass |
| --- | ---: | ---: | --- |

## Rejected Entries

| Source | Reason |
| --- | --- |
```

## 10. Task E1: Create MVP Retrieval Eval Cases

**Files:**

- Create: `AptGuide 2.0/backend/evals/datasets/rag_mvp_retrieval_cases.yaml`

- [ ] **Step 1: Create 70 room retrieval cases.**

Distribution:

```text
budget: 15
area: 15
tag/preference: 20
combination: 15
boundary/recovery: 5
```

Case format:

```yaml
- id: room-panyu-quiet-1500-001
  task: room_retrieval
  query: 找大学城南亭附近1500以内安静点的房子
  positive_room_ids: [3001, 3005]
  hard_negative_room_ids: [3012]
  expected:
    hit_at_5: true
    must_validate_with_lease: true
    must_not_return_unvalidated_vector_room: true
```

- [ ] **Step 2: Create 35 KB retrieval cases.**

Case format:

```yaml
- id: kb-lease-deposit-001
  task: kb_retrieval
  query: 押金退还多久到账
  expected_sources: [KB-LEASE-005]
  risk_level: high
  expected:
    hit_at_3: true
    must_cite_source: true
```

- [ ] **Step 3: Create 15 fallback cases.**

Case format:

```yaml
- id: fallback-policy-no-source-001
  task: fallback_retrieval
  query: 你能保证我退租时押金一天到账吗
  expected:
    must_low_confidence_fallback: true
    must_not_make_unverified_commitment: true
```

- [ ] **Step 4: Validate references.**

Every `positive_room_ids` must exist in lease test DB after seed.

Every `expected_sources` must exist in KB YAML.

## 11. Task H1: Write Handoff Report For RAG Agent

**Files:**

- Create: `AptGuide 2.0/evals/reports/data_supplement_handoff_report.md`

- [ ] **Step 1: Write handoff report.**

Required content:

```markdown
# Data Supplement Handoff Report

## Room Data

- Active public rooms:
- Seed rooms inserted:
- District coverage:
- Rent coverage:
- Known field gaps:

## Lease Tool Readiness

- `/internal/ai/tools/room/search` supports roomIds:
- `/internal/ai/tools/sync/rooms` available:
- Sensitive fields excluded:

## KB Data

- Total reviewed rules:
- High-risk rules:
- Missing modules:

## Eval Data

- room_retrieval cases:
- kb_retrieval cases:
- fallback_retrieval cases:

## Blockers For RAG Agent

- None / list blockers
```

- [ ] **Step 2: Acceptance.**

The report must say either:

```text
RAG implementation agent may start room vector sync.
```

or:

```text
RAG implementation agent must not start room vector sync because ...
```

## 12. Definition Of Done

Data Supplement Agent is done when:

- `room_data_audit_report.md` exists and states the seed decision;
- lease test DB has at least 150 active public rooms;
- `/internal/ai/tools/sync/rooms` returns at least 150 rooms with no sensitive fields;
- `/internal/ai/tools/room/search` can validate candidate `roomIds`;
- KB YAML has exactly or at least 70 reviewed rules across required modules;
- `rag_mvp_retrieval_cases.yaml` has 120 cases;
- all room eval positive IDs exist in lease test data;
- all KB eval expected source IDs exist in KB YAML;
- `data_supplement_handoff_report.md` tells the RAG agent whether to proceed.
