# Architecture Spine — Adversary Review (Round 2)

- **Spine under review:** `architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` (v2 with AD-16…AD-25 added)
- **Driving PRD:** `_bmad-output/planning-artifacts/prd.md` (v2.0, 2026-07-24)
- **Paradigm:** Modular Monolith + Hexagonal Core, 25 ADs.
- **Previous review:** `architecture-costmgr-2026-07-24/review-adversary.md` — flagged AD-16…AD-25 candidates as critical/high; this round re-checks whether they were *closed* and finds *new* divergence.
- **Lens:** construct two units one level down that each obey every AD to the letter yet still build incompatibly. Prioritize AD-9, AD-14 (region + stack pin) and the previously Critical/High AD-16…AD-25.

## Verdict

**has-gaps** — The v2 spine closes the *named* candidates AD-16…AD-25 at the *shape* level: snapshot row shape, promotion port signature, single product identity, single calc endpoint, state machine names, CCR formula, reversal link columns, one settings aggregate, typed period keys, cache key tuple are all present. But a follow-on class of divergence has opened at the *enum, unit, identifier, and ownership* layer. Two engineers — one building M3/M5/M11 around the snapshot row, one building M9/M6 around verification — can each literally obey every AD-1…AD-25 yet produce code that does not reconcile: `engine_type` enum values differ, `result_hash` algorithms differ, `segment_id` ≠ `department_id` is left implicit, the `DEPARTMENT` table is missing from the ERD, the `state='reversed'` row-write path is undecidable, the V-row "skip inapplicable" rule for ② tenants contradicts V1's allocation-completeness invariant, the AI extraction port has two owning modules, CI enforcement tooling is not named, and the Anthropic model snapshot is explicitly deferred. AD-9 is structurally sound (Singapore compute + Seoul storage) but the trace-payload, Vercel-feature, and Supabase-Storage-CDN boundaries are not pinned. AD-14 has tightened but is missing uvicorn/starlette and the JS package manager.

**Counts:** 6 Critical, 12 High, 8 Medium.

## Re-check of previously Critical/High

### AD-16 (Fiscal snapshot contract) — *partially closed*

Closed:
- Unique key `(tenant_id, period_key, segment_id, engine_type)` is named.
- Normalized columns (`material_cost`, `labor_cost`, `overhead_cost`, `manufacturing_cost`, `inventory_adjustment`) are enumerated.
- "Opaque result JSON is forbidden" prevents JSON-blob divergence.
- M3-only-writer / M5·M11-read-only rule is concrete.

Still open (closed in shape, ambiguous in value):
- `engine_type` is named as a key field but no value set is pinned. M3's engineer reads it as `'trad' | 'abc'`; M9's engineer reads `'traditional' | 'activity_based' | 'hybrid'`; M5's engineer reads `'manufacturing' | 'service'`. Joins across `fiscal_period_snapshots` for the "전통 vs ABC 비교" report (PRD §9 #20) fail under any pair.
- `segment_id` has no entity definition. The ERD has no `SEGMENT` table. The capability map has no segment-owning module. PRD §4.2 calls `제조 부문` a `segment`, but the spine uses `segment_id` (AD-16) and `department_id` (AD-21) as if they were different. Two engineers pick different definitions.
- `result_hash` algorithm is not pinned. AD-25 keys the M10 cache on `calculation_result_hash`. blake2b-256 vs sha3-256 vs sha256 produce different hashes; the same engine output yields different cache keys; cache invalidation silently fails.
- The "deterministic `result_hash`" invariant contradicts AD-5 only if the hash is computed inside the engine (forbidden). So the hash must be computed by the `services` layer; the hash is the *adapter's* identity of the engine result, not the engine's. The spine is silent on which layer computes the hash. (See finding 3 below.)
- PRD §11 V4 mandates a 4-element decomposition. The snapshot row has only `inventory_adjustment`. The 4 elements (수량차·배부차·단가차·재고조정) need 4 columns or a child table. The spine says "Opaque result JSON is forbidden" but the 4 elements aren't enumerated as columns. (See finding 6 below.)

### AD-17 (AI draft → confirmed input promotion) — *closed*

Closed:
- Single port `InputPromoter.promote(tenant_id, period_key, draft_ids) -> MonthlyInput`.
- Idempotency key `(tenant_id, period_key, source_draft_id)` named.
- Draft row retained with `state='promoted'`.
- Audit row with actor + draft hash required.
- M10 forbidden from confirmed-input writes.

Minor open:
- Idempotent return value on the *second* call is not specified. M2's "재확인" flow may call promote twice; what does the second call return? The original `MonthlyInput`? An error? A merged `MonthlyInput`? M2's engineer builds one semantics, M3's another. (Medium — not blocking.)
- `MonthlyInput` shape is referenced ("produces `MonthlyInput`") but never enumerated. The PRD's 6 input streams (주문·생산·판매·구매·경비·인원) need explicit fields. M2's adapter and M3's engine can disagree on shape. (Medium.)

### AD-18 (Single product identity across costing methods) — *partially closed*

Closed:
- `PRODUCT(product_id)` as sole identity.
- `product_role: trad_only | abc_only | both` enum.

Still open:
- The ERD says `PRODUCT ||--o{ BOM : defines` — every product has a BOM. But `abc_only` products (services) don't have BOMs in the PRD's cost model. Two engineers: (a) make BOM optional via `is_required` flag; (b) require BOM and store a sentinel; (c) make BOM a typed sub-table (`product_bom` joined only for `product_role IN ('trad_only', 'both')`). The acceptance criterion M1(b) "품목 유형을 변경할 때 BOM·수불 참조가 0건임 검증" only guards *change*, not *creation*. (See finding 12 below.)
- PRD §8.1 M1 says "품목 통합(제품/반제품/원자재/상품/서비스)" — 5 product kinds. AD-18's `product_role` is 3-valued. The 5-kinds-to-3-roles mapping is not specified. A 반제품 (semi-finished) is `trad_only`? `both`? A 원자재 (raw material) is `trad_only`? A 상품 (merchandise) is `trad_only`? A service is `abc_only`? M1's engineer maps one way, M3's another, and the BOM/CCR/ledger semantics diverge. (Medium — see finding 25.)

### AD-19 (One calculation entry point) — *partially closed*

Closed:
- `POST /api/v1/calc` named.
- M3-only-writer of the endpoint.
- M9 has no public calculation endpoint.

Still open:
- "M3 dispatches traditional and/or M9 ABC ports by tenant kind inside one AD-4 transaction" — but the *dispatch matrix* is not enumerated. PRD §4.1 has 4 tenant kinds (① 제조 / ② 서비스 / ③ 제조+서비스 / ④ 제조+서비스+기타). ② runs "only ABC"; ③ runs traditional + ABC; ④ adds an "격리 버킷." The matrix is: ①→traditional, ②→ABC, ③→(trad,abc) sequential, ④→(trad,abc,isolation_bucket). "격리 버킷" has no engine. Two engineers can implement ③ as "parallel writes" vs "sequential writes" — different `engine_type` semantics in the snapshot row. (See finding 9 below.)
- M7 (CVP/BEP) is a *calculation* that uses `cost_engine` ports (PRD §8.1 M7: "1초 이내로 재계산"). AD-19 says M3 is the sole public calc endpoint. Is M7 routed through `/api/v1/calc` with a `simulation=true` flag, or is there a separate `/api/v1/simulate`? The exception is not enumerated. (See finding 8 below.)
- "Tenant upgrade flow migrates ABC state into M3's orchestration" is named but the migration logic is not pinned. ②→③ upgrade: the existing ABC results (written by M9) need to be moved into M3's AD-4 transaction boundary. Two engineers can build different migration paths.

### AD-20 (Calculation result state machine) — *partially closed*

Closed:
- States `draft → verified → committed → reversed` named.
- `verification_status ∈ {pending, passed, failed}` named.
- `draft` and `verified` transaction-internal.
- Only `committed` feeds M5.

Still open:
- The state machine has no `failed` state. AD-12 says "A failed check aborts later checks and rolls back." AD-20 says "attempts are captured in audit telemetry outside the result table." The "attempts" table is not enumerated. SM-3a "계산 결과 변경 시도 = 0건" requires counting attempts. M3's engineer writes attempts to a `calculation_attempts` table; M6's verifier writes attempts to `audit_logs` (security); M5's engineer looks for the "last failed" in the result table (where it never lands). (See finding 5 below.)
- "Reversed is represented by an append-only AD-22 event and never by mutating the committed row." But AD-16 names `state` as a column on the snapshot row with `reversed` as a value. So is `state='reversed'` set on the snapshot row by a trigger when an AD-22 event is inserted? Or is `state='reversed'` only a *computed* property that M5 must derive? Two engineers build different query semantics; M5's `WHERE state='committed'` returns different rows depending on interpretation. (See finding 6 below.)

### AD-21 (Single CCR definition) — *partially closed*

Closed:
- Formula `CCR = department_indirect_cost / practical_capacity_hours` is named.
- Excludes direct labor and direct material via M1 account tags.
- `CCRPort.compute(tenant_id, period_key, department_id) -> Decimal` is the only definition.

Still open:
- `practical_capacity_hours` is unitless in the formula. The PRD says "이론 능력 × 80% 기본" but does not pin the unit (hours per month? hours per year? hours per shift?). M9's engineer writes hours/month; M3's reads hours/year. The CCR is off by 12×. (See finding 14 below.)
- "Department_indirect_cost" is "the pre-allocation department total after direct labor and direct material are excluded by M1 account tags." But who computes "pre-allocation"? M3 owns allocation. M9 owns CCR. There is a chicken-and-egg: M3 needs CCR to allocate, M9 needs M3's allocation to compute CCR. The fix is "practical capacity is pre-determined, not derived from allocation." But the spine is silent on the source of "pre-allocation" totals — M1's account tags, M2's `exp` input, or M3's pre-pass? Two engineers can build different pre-pass logic. (See finding 14 below.)
- The ERD has no `DEPARTMENT` table. AD-21 references `department_id` as a CCR key, but the entity doesn't exist in the schema. The previous review's AD-27 candidate ("one department entity") is deferred to "Resolve with the owning Epic before its first Story" — not yet resolved. (See finding 4 below.)

### AD-22 (Reversal construction and ownership) — *partially closed*

Closed:
- Reversal row construction sequence (1 reversal + optional correction, both sharing `correction_group_id`).
- `reverses_event_id` and `reversal_of_period_key` columns.
- `request_reversal(event_id, reason)` port.
- Only M11 authorizes.

Still open:
- Reversal-of-reversal: if a reversal row itself needs correction, the next reversal's `reverses_event_id` points to the previous reversal. The `correction_group_id` chain extends. The spine is silent on whether `correction_group_id` is a *flat* identifier (all rows in the chain share one ID) or a *linear* chain (each new correction gets a new group). Two engineers build different chains. (See finding 20 below.)
- M4 owns inventory ledger. The `request_reversal` port is called by M4. But the PRD §8.1 M4 says "기초재고 입력 후 자동 이월 체인 개시, 이후 수동 입력은 차단." So manual reversals are M4's job, but the *authorization* is M11's. Is there a `pending_reversals` table between M4's request and M11's authorization? An event queue? Two engineers can build different M4↔M11 wiring. (Medium.)
- "Only M11 authorizes and writes the sequence." M11 itself runs operator-driven reversals. Does M11 call `request_reversal` first, then authorize (a self-loop)? Or does M11 bypass the port? Two engineers implement M11's internal logic differently. (Medium.)

### AD-23 (One tenant settings aggregate) — *partially closed*

Closed:
- One `tenant_settings` row per tenant.
- `settings_version` column.
- JSONB namespaces `onboarding`, `baseline`, `abc`, `ai`.
- Each module writes only its namespace through a version-checked service.
- "Parallel settings tables are forbidden."

Still open:
- "Version-checked" is ambiguous. Two readings: (a) optimistic concurrency on `settings_version` (a single integer, monotonic); (b) per-namespace version (4 integers, one per namespace). M0's engineer picks (a) for simplicity; M1's engineer picks (b) for fine-grained locking. The behavior diverges when a baseline change and an onboarding change happen concurrently. (See finding 23 below.)
- "Schema-validated JSONB" — which library? Pydantic v2 generates JSON Schema from the `MonthlyInput`-style dataclasses. The TS side needs `ajv` or a `zod`-to-JSON-Schema bridge. Two engineers pick different validators; the same JSON may validate in one and fail in another. (Medium.)
- Onboarding partial state: a new tenant has `tenant_settings.onboarding` written multiple times during the wizard. The "each module writes only its namespace" rule says M0 owns `onboarding`. But during onboarding, the tenant isn't yet "active." Is the row in `tenant_settings` from the first keystroke, or only after the wizard completes? Two engineers: (a) write the row on the first keystroke; (b) write the row only on wizard completion (then partial state lives in a session store). The (a) choice creates many partial writes that the version-checked service must handle. (Medium.)

### AD-24 (Typed period-key namespaces) — *closed*

Closed:
- `YYYY-MM` for fiscal, `YYYY-MM#B<n>` for virtual budget.
- M8 mints virtual.
- M5 YTD defaults to fiscal.
- M11 closes only fiscal.

Minor open:
- The "explicit join" between virtual and fiscal is named but the join *predicate* is not. `LEFT(period_key, 7) = '2026-07'` is correct; `period_key LIKE '2026-07%'` is also correct; `period_key ~ '^2026-07($|#)'` is the most precise (anchored). Two SQL dialects can differ. M5's engineer picks one; M8's another. (See finding 15 below.)
- Virtual period lifecycle: virtual periods accumulate over years. PRD §10 says "회계연도당 예산 시나리오 1개" — so at most 1 per fiscal year. But what happens at year-end? Are virtual periods archived? Frozen? The spine says M11 cannot close virtuals — but doesn't say who freezes them. (Low.)

### AD-25 (AI insight cache invalidation) — *closed*

Closed:
- Cache key `(tenant_id, period_key, calculation_result_hash)`.
- Triggers: AD-4 commit, AD-22 reversal, M11 reopen.
- DB notification (not polling).

Minor open:
- "DB notification" mechanism not pinned. Supabase Realtime channels vs Postgres `LISTEN/NOTIFY` vs webhook. Two engineers pick different mechanisms. (Low.)
- M11 reopen trigger is independent of AD-22 reversal. But M11's reopen may be implemented *as* an AD-22 reversal + a status change. Duplication or split? (Low.)

### AD-9 (KR residency) — *partially closed*

Closed:
- Region pin corrected: Supabase Seoul (`ap-northeast-2`) for storage; Railway Singapore (`asia-southeast1-eqsg3a`) for compute. Previous review's "Railway Seoul doesn't exist" finding is closed.
- PIPA pre-pilot checklist is a process gate, not an AD guarantee.
- "Vercel may cache static assets globally but never tenant data" is named.

Still open:
- **Trace payload bounds:** OTel is "traces only in MVP." But spans flow through Singapore→Seoul. If a span includes the request body (which can be an AI-extracted `MonthlyInput`), the trace payload leaks tenant data outside Seoul. The spine is silent on which fields are in the span. (See finding 17 below.)
- **Vercel feature whitelist:** the spine says "static assets only." But Next.js 16 has ISR, Server Actions, fetch cache, Edge Middleware, and Data Cache. Server Actions *write* tenant data; ISR may cache rendered tenant pages; fetch cache may cache API responses. The spine is silent on which Vercel features are off-limits. Two engineers enable different features. (See finding 21 below.)
- **Supabase Storage CDN:** Supabase Storage uses a CDN. If a tenant uploads a receipt photo to M0 onboarding, the photo CDN-caches at the edge. Is the CDN edge in Seoul? The spine says "Storage + backups live in Supabase Seoul" but doesn't bound the CDN. (Medium.)
- **Railway logs scope:** "tenant payload logging … on Railway are forbidden." But what about *non-payload* logs (request metadata, user IDs, request paths)? A `request_path=/api/v1/calc?tenant_id=…` log line is a tenant identification log. The spine doesn't bound log content. (Medium.)

### AD-14 (Web-verified stack pin) — *partially closed*

Closed:
- Specific version pins for Node, Next, React, TypeScript, Tailwind, FastAPI, Pydantic, SQLAlchemy, Alembic, pytest, Supabase, Stripe, Recharts, structlog, uv, OTel.
- Banned infrastructure: Celery, Kafka, Redis-as-queue.
- CI runs V8 before dependency changes.

Still open:
- **Anthropic model snapshot deferred:** "exact model snapshot belongs to M10 config." Two M10 engineers can pick `claude-sonnet-4-5-20250929` vs `claude-sonnet-4-6-20260115`. Cost and behavior differ. The PRD §12 lists Vision, insight, and fixed/variable estimation as 3 AI features; whether each uses a different snapshot is not pinned. (See finding 22 below.)
- **uvicorn + starlette not pinned:** FastAPI 0.139.2 is named, but its ASGI server (uvicorn) and ASGI framework (starlette) are not pinned. They have independent version cadences. (See finding 23 below.)
- **Package manager not pinned:** pnpm vs npm vs yarn vs bun. The lockfile format differs. CI's "owns lockfiles" doesn't say which. (Medium.)
- **OpenTelemetry signal scope:** "traces only in MVP." Spans, baggage, links — all traces, but different shapes. The instrumentation library is pinned (`1.44.0`) but the *export surface* (which fields per span) is not. (Medium.)

## New Critical/High Divergences

### Critical

1. **[critical] `engine_type` enum value set not pinned (AD-16, AD-18, AD-19)** — AD-16 says `engine_type` is part of the unique key; AD-19 says M3 dispatches "traditional and/or M9 ABC ports." The *value set* (`'trad'`, `'abc'`, `'hybrid'`, `'manufacturing'`, `'service'`, …) is not pinned. M3 writes one set, M9 another, M5 reads a third. The "전통 vs ABC 비교" report (PRD §9 #20) joins on `engine_type`; the join returns zero rows under any pair. *Fix:* pin the enum to `{'traditional', 'activity_based'}` in AD-16; document the per-tenant-kind write pattern in AD-19's dispatch matrix.

2. **[critical] `result_hash` algorithm not pinned (AD-16, AD-25)** — AD-16 says the snapshot row carries a "deterministic `result_hash`." AD-25 says M10's cache key is `(tenant_id, period_key, calculation_result_hash)`. blake2b-256 vs sha3-256 vs sha256 vs xxh3 produce different hashes for the same engine output. The cache miss/hit ratio diverges. The "1원 단위 대조" (PRD §6.1) requires bitwise identity. *Fix:* pin blake2b-256 (or sha3-256) in AD-16; pin the serializer (engine-output JSON encoding) in AD-16; pin the hash computation point in the `services` layer (not engine — AD-5 forbids it).

3. **[critical] `segment_id` definition ambiguous vs `department_id` (AD-16, AD-21, PRD §4.2)** — AD-16 keys snapshots by `segment_id`; AD-21 keys CCR by `department_id`. PRD §4.2 names "제조 부문" and "서비스 부문" as *segments*. The spine uses `segment_id` and `department_id` as if they were different, but PRD §4.2 has no "department" entity (only "부문" / "segment"). Two engineers: (a) treat `segment_id` as `department_id` (one entity, two names — name drift per AD-15); (b) treat `segment_id` as business-unit, `department_id` as the cost-center within — two entities; (c) invent a third entity. The "전통 vs ABC 비교" report joins on the segment. The CCR uses the department. The cross-engine reconciliation breaks. *Fix:* in AD-16, replace `segment_id` with the PRD-aligned term "segment" (one entity); drop `department_id` from AD-21 or rename to `cost_center_id`; add a `DEPARTMENT`/`COST_CENTER` table to the ERD.

4. **[critical] Department entity absent from ERD (AD-21)** — AD-21 references `department_id` as a CCR key. The ERD lists `TENANT`, `USER`, `TENANT_SETTINGS`, `FISCAL_PERIOD`, `PRODUCT`, `BOM`, `MONTHLY_INPUT`, `INVENTORY_LEDGER`, `FISCAL_PERIOD_SNAPSHOT`, `AUDIT_LOG` — no `DEPARTMENT` or `COST_CENTER`. M1 owns "기준정보" per the capability map but the capability map doesn't list departments. The previous review's AD-27 candidate ("one department entity") is deferred to "Resolve with the owning Epic before its first Story" — not yet resolved. Two engineers each create their own `departments` table (M1's with `name, manager_user_id, is_active`; M9's with `name, capacity_hours, is_abc_eligible`); the two diverge; AD-21's CCR semantics collapse. *Fix:* add a `DEPARTMENT` table to the ERD, owned by M1, with columns sufficient for both M3's allocation and M9's CCR. Promote the AD-27 candidate to an adopted AD.

5. **[critical] Failed verification row visibility (AD-12, AD-20, SM-3a)** — AD-12 says "A failed check aborts later checks and rolls back." AD-20 says "Failed rows roll back; attempts are captured in audit telemetry outside the result table." The "attempts" table is not enumerated. M3's engineer writes attempts to a `calculation_attempts` table; M6's verifier writes attempts to `audit_logs` (which AD-3 defines as security-only); M5's engineer looks for `state='failed'` in `fiscal_period_snapshots` (which never lands). SM-3a "계산 결과 변경 시도 = 0건" requires counting failed attempts. Three writers, three tables, three query paths. *Fix:* add an `AD-26` defining a single `calculation_attempts` table (or a dedicated schema within `audit_logs`) with the columns SM-3a needs: `{attempt_id, tenant_id, period_key, segment_id, attempt_at, v_row, verification_status, error_code, actor_user_id, trace_id}`.

6. **[critical] Reversed state write semantics (AD-20, AD-22)** — AD-20 says "reversed is represented by an append-only AD-22 event and never by mutating the committed row." AD-22 says "a correction inserts (1) one sign-negating reversal row with `reverses_event_id` and `reversal_of_period_key`, then (2) an optional corrected business row sharing `correction_group_id`." The spine does not say whether the *original* `fiscal_period_snapshots` row is updated to `state='reversed'` by a trigger. AD-16 names `state` as a column with `reversed` as a value. If the row is not mutated (per AD-20 + AD-2), then the `state='reversed'` value is not set on the row — but AD-16's column-shape says it can be. M5's engineer writes `WHERE state IN ('committed', 'reversed')` to find reports-to-render. M11's engineer writes `WHERE state='committed'` only. The two diverge. *Fix:* state explicitly: `state='reversed'` is *not* stored on `fiscal_period_snapshots`; it is a *computed* property derived from the existence of an AD-22 reversal row for `(tenant_id, period_key, segment_id, engine_type)`. AD-16's `state` column enum excludes `reversed`; the *effective* state is `committed ∧ ∃ reversal_event → reversed`.

### High

7. **[high] M7 simulation endpoint ambiguity (AD-19)** — AD-19 says `POST /api/v1/calc` is the only public calculation endpoint. But M7 (CVP/BEP, 차월 추정) is also a *calculation* that uses engine ports (PRD §8.1 M7: "1초 이내로 재계산"). Is M7 routed through `/api/v1/calc` with a `simulation=true` flag (a violation of the "only one button per period" intent — simulations have no `period_key`)? Or is there a separate `/api/v1/simulate` endpoint (a violation of the "only one calculation endpoint" letter)? Two engineers route M7 differently. *Fix:* in AD-19, name M7's exception: `POST /api/v1/simulate` is a separate endpoint because M7 is non-authoritative (results are not persisted, not snapshotted, not closed); document this in AD-19's "Rule" body.

8. **[high] Tenant kind → dispatch matrix not enumerated (AD-19)** — "M3 dispatches traditional and/or M9 ABC ports by tenant kind" — but the *matrix* is not in the spine. PRD §4.1 has 4 tenant kinds. The matrix must specify: ①→traditional, ②→activity_based, ③→(traditional, activity_based) sequential in one AD-4 transaction, ④→(traditional, activity_based, isolation_bucket) with isolation_bucket = excluded. The isolation_bucket ("기타") has no engine — its costs are parked. M3's engineer implements ③ as "parallel writes" (two snapshot rows in one transaction); M9's engineer implements ③ as "sequential writes" (M3 traditional, then M9 ABC, then merge). The `engine_type` semantics differ; M5's "전통 vs ABC 비교" reads different rows. *Fix:* add a dispatch table to AD-19's body with 4 rows, 1 per tenant kind.

9. **[high] V-row skip rule for ② tenants contradicts V1 (AD-12)** — AD-12 says "Service-only tenants skip inapplicable V1/V4 but still run V7/V8." But V1 is "완전배부 — 각 배부 단계 합계 = 원금액 (1원 단위) [A6]" (PRD §11). V1's invariant applies to *both* engines: ABC §7.1 says "각 단계 배부합계 = 원금액 [A6]." So V1 *is* applicable to ② tenants. AD-12 contradicts the PRD. Two engineers: (a) skip V1 (literal AD-12), V1's invariant is unenforced for ② — a 1원 mismatch slips through; (b) run V1 as a "ABC allocation completeness" check (named differently), V1's invariant is preserved; (c) keep V1 and skip V4 only (the genuine "inapplicable" case). *Fix:* rewrite AD-12: ② tenants run *V1 (ABC variant) and V7 and V8*; only V4 (traditional-only reconciliation) is skipped. Document the V-row per-tenant-kind skip table.

10. **[high] AI extraction port ownership overlap (M0 vs M10, AD-1, AD-7)** — Capability map: M0 = "Onboarding/settings/AI extraction"; M10 = "AI extraction/insight/estimation." Both list "AI extraction." The spine names `DocumentExtractionPort` (in the previous review's AD-34 candidate, not adopted). M0's engineer creates `claude_vision` adapter under `m0_onboarding`; M10's engineer creates `claude_vision` adapter under `m10_ai`. Both write to `input_drafts`. Two writers, one logical store, no shared schema enforcement. *Fix:* in AD-1 or a new AD, name a single `DocumentExtractionPort` in `packages/cost_engine/ports/` and a single `claude_vision` adapter in `packages/cost_engine/adapters/ai/`; M0 and M10 both call the same port; no module may create a parallel extraction adapter.

11. **[high] CI enforcement tooling not named (AD-11, AD-14)** — "Engine-to-adapter/service/UI imports... forbidden and checked in CI." "CI owns lockfiles and runs V8 before dependency changes." The CI toolchain is not named. Possible choices: `import-linter` (Python), `pyright`, `ruff`, `eslint-plugin-boundaries` (TS). Two engineers can pick different linters; one may pass when another would fail. The "version-checked settings service" (AD-23) is also a runtime invariant — not enforceable by a static linter. *Fix:* in AD-11, name `import-linter` for Python layer rules and `eslint-plugin-boundaries` for TS layer rules; in AD-14, name the CI provider (GitHub Actions is implied but unstated) and the lockfile format (`uv.lock` + `pnpm-lock.yaml`); name a separate runtime check (e.g., a `pydantic` validator on `tenant_settings`) for AD-23.

12. **[high] BOM existence for `abc_only` products (AD-18, M1 acceptance)** — ERD: `PRODUCT ||--o{ BOM : defines`. Every product has a BOM. But `abc_only` products (services) don't have BOMs in the PRD's cost model. The M1 acceptance criterion M1(b) "품목 유형을 변경할 때 BOM·수불 참조가 0건임을 검증" only guards *change*, not *creation*. Two engineers: (a) make BOM optional via `is_required` flag on `PRODUCT` or `BOM`; (b) require BOM and store a sentinel/empty BOM for services; (c) split `product_bom` as a sub-table joined only for `product_role IN ('trad_only', 'both')` and add a CHECK constraint. (c) is the cleanest but not in the spine. *Fix:* in AD-18, add: "`abc_only` products may have zero BOM rows; M1's `product_bom` table is joined only for `product_role IN ('trad_only', 'both')`; the ERD's `||--o{` is conditional."

13. **[high] M5 PDF template + tenant currency change invalidation (AD-8, AD-23)** — AD-23 says one settings table with `currency` in the `onboarding` namespace. AD-8 says display is per currency. M5's engineer caches PDF templates by `(tenant_id, period_key, template_version)`. The currency change should invalidate the cache. The "version-checked settings service" applies to writes, not reads. Two engineers: (a) read settings per request (no cache); (b) cache and invalidate on settings change. If the change isn't propagated to the cache, reports show wrong currency. The previous review's AD-33 candidate ("templates re-rendered on every request") is deferred to "Resolve with the owning Epic." *Fix:* in AD-23, add: "M5 does not cache rendered PDFs; if caching is introduced, the cache key is `(tenant_id, period_key, template_version, currency, language)` and is invalidated on any write to `tenant_settings`." Or promote AD-33 to an adopted AD.

14. **[high] `practical_capacity_hours` unit and pre-allocation source (AD-21)** — The CCR formula `CCR = department_indirect_cost / practical_capacity_hours` is unitless. The PRD says "이론 능력 × 80% 기본" but does not pin the unit. Hours per month vs hours per year vs hours per shift produces 12× / 5× / shift-count divergence. M9's engineer writes hours/month (the natural M10 timescale); M3's reads hours/year (the natural cost-period timescale). Also: "department_indirect_cost is the pre-allocation department total after direct labor and direct material are excluded by M1 account tags." But "pre-allocation" needs a pre-pass: who reads M1's account tags, totals by department, subtracts direct labor/material? M3 has not yet run allocation; M9 cannot read M3's allocated numbers. *Fix:* in AD-21, add: "`practical_capacity_hours` is hours per fiscal month; the value is stored in `DEPARTMENT.default_capacity_hours` (set by M1) and may be overridden per period by M9." And: "`department_indirect_cost` is computed by M3's pre-pass (a pure-function read of M1's account tags grouped by `department_id`, excluding `direct_labor` and `direct_material` tags), invoked inside the AD-4 transaction before CCR computation."

15. **[high] Period prefix join SQL (AD-24)** — "budget-vs-actual explicitly joins virtual and fiscal rows by `YYYY-MM` prefix." The join predicate is not specified. `LEFT(period_key, 7) = '2026-07'`, `period_key LIKE '2026-07%'`, `period_key ~ '^2026-07($|#)'` all match the same rows for valid keys, but diverge if a key like `2026-07x` exists (defensive coding). The "explicit join" should be a stored expression or a SQL function. *Fix:* in AD-24, add: "The `period_key_prefix(p)` SQL function returns `LEFT(p, 7)`; all virtual↔fiscal joins use `period_key_prefix(virtual.period_key) = fiscal.period_key`."

16. **[high] `service_role` audit row schema (AD-3)** — "Every `service_role` bypass writes a typed audit row before the privileged action." "Typed" is vague. The previous review's AD-28 candidate (`{bypass_id, tenant_id, requested_action, reason, actor_user_id, scope_tables[], expires_at}`) is deferred. M12's operator console and M11's operator-driven reversal both invoke `service_role`. M5's read-only consultant-proxy may also need a service_role read. Two engineers write different audit shapes; SM-3a counting breaks. *Fix:* promote AD-28 to an adopted AD, or pin the schema in AD-3's body.

17. **[high] Trace payload bounds (AD-5, AD-9)** — OTel is "traces only in MVP." The engine is pure (no I/O) per AD-5. So traces must be emitted from the `services` layer. But the `services` layer reads `MonthlyInput` (which may contain AI-extracted fields), `fiscal_period_snapshots` (with monetary values), and `audit_logs`. If a span includes the request body, the trace payload leaks tenant data through Singapore→Seoul. The spine is silent on which fields are in the span. *Fix:* in AD-9 or a new AD, add: "OTel span attributes are bounded to `{trace_id, span_id, parent_span_id, tenant_id, route, http_status, latency_ms, error_code}`. Span events may include `verification_status` and `engine_type` but not monetary values, not input field values, not AI extraction output."

18. **[high] M3/M9 result collision on ③·④ tenants (AD-16, AD-19)** — For ③ tenants, both M3 (traditional) and M9 (ABC) write snapshots. AD-16's key is `(tenant_id, period_key, segment_id, engine_type)`. For ③: 2 segments (제조, 서비스) × 2 engines (traditional for 제조, ABC for 서비스) = 4 rows per period. PRD §4.2 says "제조 부문 → 전통 / 서비스 부문 → ABC" — so the engine is determined by the segment, not by tenant kind. But the AD-16 key is `(segment_id, engine_type)` — a tuple that's over-specified if engine is fully determined by segment. Two engineers: (a) drop `engine_type` from the key (engine implied by segment); (b) keep `engine_type` for generality (some segment may have both engines in 2차); (c) keep `engine_type` and add a CHECK constraint that `engine_type` matches `segment.engine_default`. *Fix:* in AD-16, document the per-segment default engine and the M3 dispatch matrix together (link to AD-19); add a CHECK constraint that `(segment_id, engine_type)` is allowed.

19. **[high] M3 dispatch into M9 for ② tenants (AD-19)** — "Service-only tenants use the same endpoint with only the applicable ABC path." M3 owns the endpoint, M9 owns the engine. So ② tenants call `POST /api/v1/calc`, M3 dispatches to M9's engine port, and only ABC runs. M3 is "원가계산 엔진" (traditional) by capability map. M9 is "ABC 엔진." M3's engineer writes an M9 dispatcher; M9's engineer refuses to be called from M3 for ② tenants (because M3 is a different module). Two integration patterns: (a) M3 directly imports M9's port (forbidden by AD-11 — adapter-layer violation); (b) M3 calls a service-level orchestration that calls M9. The capability map shows M3 governs M3 + M9's internal ports; but AD-11 forbids cross-module imports. *Fix:* in AD-19, name the dispatch mechanism: M3 owns `m3_calculate.orchestrator` which uses `CCRPort` and `abc_calc.compute` (both internal engine ports from `packages/cost_engine/ports/`); M3's `m3_calculate` module has no direct dependency on `m9_abc`'s code; M9's engine ports are imported by M3 through the engine's public port surface.

20. **[high] Reversal-of-reversal chain (AD-22)** — The spine's "one sign-negating reversal row … then (2) an optional corrected business row sharing `correction_group_id`" works for a single correction. But a reversal itself may need correction: e.g., the user reverses a closure, then realizes the reversal was wrong, then reverses the reversal. AD-2's "INSERT-only" rule says the new reversal inserts with `reverses_event_id` pointing to the first reversal. The `correction_group_id` is shared or extended? Two engineers: (a) all rows in the chain share one `correction_group_id`; (b) each new correction gets a new `correction_group_id`, with the chain recorded via `reverses_event_id`. The reporting layer (M5) needs to "unwind" the chain to find the latest state. *Fix:* in AD-22, add: "`correction_group_id` is a single UUID per logical correction episode, shared by all sign-flipping and replacement rows in the chain; the `reverses_event_id` forms a linear chain within the group; M5's reversal-aware reads traverse the chain to the latest row."

21. **[high] Vercel tenant-data cache boundary (AD-9)** — "Vercel may cache static assets globally but never tenant data." Vercel has ISR, Server Actions, Edge Middleware, Data Cache, and fetch cache. The spine names "static assets" as the only cacheable. But Server Actions *write* tenant data (e.g., M2's input write); ISR may cache rendered tenant pages if the page is dynamic-but-cached; fetch cache may cache API responses with `revalidate`. The spine is silent on which Vercel features are off-limits. Two engineers enable different features. *Fix:* in AD-9, add a blacklist: "Vercel `revalidate` policies, ISR, Data Cache, and Server Actions are not used for tenant-data routes. Only static asset paths (e.g., `/_next/static`, `/public/*`) and a CDN for the marketing site are cached. Authenticated routes are `cache: 'no-store'`."

22. **[high] Anthropic model snapshot deferred (AD-14)** — "Anthropic Claude API | PRD-selected model family; exact model snapshot belongs to M10 config." Two M10 engineers can pick `claude-sonnet-4-5-20250929` vs `claude-sonnet-4-6-20260115` (or whatever is current at M10 implementation time). Cost differs; behavior differs (Vision quality, JSON-mode reliability, prompt-caching semantics). M10's three features (PRD §12: 문서추출, 인사이트, 고정·변동 추정) may need different snapshots. The spine defers this. *Fix:* in AD-14, name the M0 cut-off for snapshot selection; require a M10 ADR that locks the snapshot before M10's first story, with a re-verification against https://docs.anthropic.com/en/docs/about-claude/models.

23. **[high] uvicorn + starlette not pinned; package manager not pinned (AD-14)** — FastAPI 0.139.2 is pinned, but uvicorn and starlette are not. They have independent version cadences. CI's "owns lockfiles" doesn't say which lockfile. pnpm vs npm vs bun vs yarn. Two engineers pick different combinations; lockfile drift; one stack resolves while another doesn't. *Fix:* in the Stack table, add `uvicorn: <minor>` and `starlette: <minor>`; add `Package manager: pnpm` (with lockfile `pnpm-lock.yaml`); for Python, `uv` already pinned.

### Medium (selected — for follow-up)

24. **[medium] settings_version semantics (AD-23)** — "version-checked" reads as either (a) one integer `settings_version` for optimistic concurrency, or (b) four per-namespace integers. M0's engineer picks (a); M1's picks (b). Concurrent onboarding + baseline change behavior diverges. *Fix:* in AD-23, name the choice: "settings_version is a single integer; concurrent writes use `WHERE settings_version = :expected`; the loser retries with a re-read."

25. **[medium] 5 product kinds vs 3 product roles (AD-18)** — PRD §8.1 M1 names 5 kinds (제품/반제품/원자재/상품/서비스); AD-18 names 3 roles (`trad_only | abc_only | both`). The 5→3 mapping is not specified. A 반제품 (semi-finished) is `trad_only` (used in BOM)? `both` (also a saleable)? A 원자재 is `trad_only`? A 상품 is `trad_only`? A service is `abc_only`? M1's engineer maps one way; M3's another; BOM construction breaks.

26. **[medium] V8 regression in CI vs V8 in M3 calc (AD-14, M6)** — "V8 is run before dependency changes" in CI. M3's `POST /api/v1/calc` runs V8 inside the AD-4 transaction (M6 acceptance criterion M6(a)). Two V8 invocations: CI's is a static test against the `cost_engine` package; M3's is an integration test against the full stack. Different fixtures, different pass conditions, different latency. *Fix:* in M6's governing ADs, name CI's V8 as `packages/cost_engine/tests/regression_v8/` (pure engine, fixtures in `tests/regression_v8/`) and M3's V8 as `m3_calculate.verifier.v8` (integration, against DB).

27. **[medium] OpenTelemetry span emission point (AD-5)** — Engine is pure; traces must be emitted from `services`. But `services` runs in the FastAPI process on Railway Singapore. The `cost_engine` package's pure functions are called from `services`. The span boundary is `service.process_request` → `engine.compute_*`. The spine says "traces only" but doesn't name the span boundary. *Fix:* in AD-5 or a new AD, name the span boundary: "Engine functions do not import OTel. The `services` layer wraps each engine call in a span `{op: 'engine.compute_*, tenant_id, period_key, segment_id, engine_type, latency_ms, error_code}`."

28. **[medium] M0 onboarding partial state (AD-23)** — During the onboarding wizard, partial `tenant_settings.onboarding` writes happen. The "each module writes only its namespace" rule says M0 owns `onboarding`. But partial writes may be many. *Fix:* name a "wizard session" store (e.g., `onboarding_sessions` table) that holds partial state; `tenant_settings.onboarding` is written atomically only on wizard completion.

29. **[medium] M8 budget scenario vs AD-18 product_role (AD-18, AD-24)** — M8 creates virtual period `2026-07#B1` for budget. M5's budget-vs-actual report joins virtual to fiscal. But the budget scenario's products must match the fiscal's products. If a tenant adds a product in M1 between fiscal close and budget creation, the join misses. *Fix:* in M8's ADs, name a "scenario product list" snapshot taken at scenario creation; the join is on the snapshot, not the live product list.

30. **[medium] M11 close — virtual period lifecycle (AD-24)** — M11 cannot close virtuals. But virtual periods accumulate over years. What freezes them? *Fix:* add: "Virtual periods are auto-archived 13 months after their fiscal year ends; M8 owns the archive; M5 reads active and archived virtuals."

31. **[medium] `consultant_proxy` API surface (AD-10)** — The role is named; the read-only API surface is not. M5, M11, M12 each have their own proxy implementation. *Fix:* in AD-10, add: "consultant_proxy has read access to M5 only; cannot reverse (M11), cannot change settings (M0/M1/M9), cannot see consultant-proxy access in `audit_logs` (M12's proxy invocation row is mandatory)."

## What Holds Up

- **AD-1 (paradigm)** — engine purity + import-linter enforcement is the spine's strongest pillar.
- **AD-2 (append-only)** — trigger-level INSERT-only is concrete.
- **AD-3 (RLS)** — `tenant_id` derivation from JWT is correct; the audit-row shape gap is now flagged as finding 16.
- **AD-4 (calculation atomicity)** — REPEATABLE READ + in-tx verifications is concrete; the gap (AD-20) is the state machine, now partially closed and flagged as finding 5/6.
- **AD-5 (engine purity)** — `f(inputs) -> outputs` is unambiguous; the OTel-span-emission-point gap is now finding 27.
- **AD-6 (fiscal close lock)** — trigger on `status='closed'` is concrete.
- **AD-7 (AI non-authoritative)** — `input_drafts` boundary is real; the gap is the port-ownership overlap (finding 10).
- **AD-8 (monetary types)** — `BIGINT`/`NUMERIC(18,2)` + `Decimal` is unambiguous; the PDF-cache gap is finding 13.
- **AD-9 (residency)** — Singapore-compute / Seoul-storage is a deliberate cross-border design with a PIPA process gate; the observability/Vercel/Storage-CDN gaps are findings 17/21/medium.
- **AD-10 (identity & roles)** — four roles + JWT claims; the consultant_proxy surface is finding 31.
- **AD-11 (dependency direction)** — `ui → api → services → ports → engine` is correct; the enforcement-tool gap is finding 11.
- **AD-14 (stack pin)** — most pins specific; the model-snapshot, uvicorn/starlette, package-manager gaps are findings 22/23.
- **AD-15 (conventions)** — naming/date/ID/error/log/money are explicit.
- **AD-24 (typed period keys)** — closed; the join-predicate gap is finding 15.

## Summary

The 25 ADs form a sound substrate for *module-internal* contracts and for the *named* cross-module shapes (snapshots, promotion, products, calc endpoint, state machine, CCR, reversals, settings, period keys, cache key). The v2 spine closes 19 of 25 ADs completely and partially closes the remaining 6 (AD-16, AD-18, AD-19, AD-20, AD-21, AD-22, AD-23). The new divergence class is at the *value, unit, identifier, ownership, and toolchain* layer — not at the shape layer. The most dangerous gaps are:

1. **Snapshot enum/algorithm/identifier ambiguity** (findings 1, 2, 3) — every module touches this; missing enums are the highest-leverage hole.
2. **Failed/reversed state visibility** (findings 5, 6) — SM-3a and M5 reads depend on these; without them, the state machine is half-pinned.
3. **Department entity + AD-21 semantics** (findings 4, 14) — without a single entity and unit spec, CCR breaks.
4. **Cross-engine dispatch for ②·③·④ tenants** (findings 8, 9, 18, 19) — without a matrix and a clear M3↔M9 wiring, the calc endpoint rule is half-pinned.
5. **AI extraction port ownership** (finding 10) — two modules with overlapping "AI extraction" capability is the canonical "two owners of one entity" failure.

Closing the 6 Critical and 12 High findings (AD-26…AD-37 candidates) would bring the spine from "has-gaps" to "tight."

## File paths

- **Spine:** `C:\Users\c8rom\desktop\costmgr\_bmad-output\planning-artifacts\architecture\architecture-costmgr-2026-07-24\ARCHITECTURE-SPINE.md`
- **PRD:** `C:\Users\c8rom\desktop\costmgr\_bmad-output\planning-artifacts\prd.md`
- **Validation report:** `C:\Users\c8rom\desktop\costmgr\_bmad-output\planning-artifacts\validation-report.md`
- **Previous adversary review:** `C:\Users\c8rom\desktop\costmgr\_bmad-output\planning-artifacts\architecture\architecture-costmgr-2026-07-24\review-adversary.md`
- **Previous verifier review:** `C:\Users\c8rom\desktop\costmgr\_bmad-output\planning-artifacts\architecture\architecture-costmgr-2026-07-24\review-verifier.md`
- **This review:** `C:\Users\c8rom\desktop\costmgr\_bmad-output\planning-artifacts\architecture\architecture-costmgr-2026-07-24\reviews\review-adversary.md`
