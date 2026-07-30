---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/validation-report.md
---

# bizup — Epic Breakdown (CE Step 1: Requirements Inventory)

## Overview

This document is the **requirements inventory** for bizup's Epic Breakdown. It is the seed for Epic design (step-02) and Story creation (step-03). Source documents: PRD v2.0 (final, 768 lines, 2026-07-25 Excellent), Architecture spine (final, 2026-07-24, 25 ADs), Validation report (Excellent, 19/20 ✅). UX design contract does not exist yet (skipped — runs in `bmad-ux` after CE).

**FR numbering**. PRD §8.1 ships M-level acceptance criteria (M0~M12, ~30 bullets). This document derives F-module.N FR-level IDs from the acceptance criteria and adjacent PRD sections (§6.1 engine, §7.1 ABC, §9 reports, §10 budget, §11 verifications, §12 AI). Coverage map at the bottom traces each FR to its acceptance criteria, validation IDs (§11 V-row), and architecture ADs.

**Non-Goals excluded** (per §14.B Non-Goals 10 items, 1차 명시 미구현): 제조부문ABC, 복수예산, A×B×C×D 엔진, CPA 정밀, 다국어환산, 멀티에이전트, 환경원가, 모바일앱, 부채자금, ERP동기화 — Epic 범위에서 제외.

## Requirements Inventory

### Functional Requirements

#### M0 — Onboarding / Settings (3 FRs)

- **F0.1** 업종 4지선다(제조·제조+유통·서비스·겸영) 선택 시 후속 메뉴(§4.1) 자동 토글
- **F0.2** 회계연도 시작월 / 통화 / 언어 / 배부기준 3종 미완료 시 [계산] 진입 차단
- **F0.3** AI 문서추출 신뢰도 < 70% 항목 빨강 배지 표시 + 사용자 확정 강제

#### M1 — Baseline / BOM / Accounts (2 FRs)

- **F1.1** BOM 매트릭스에서 비중 합 != 100% 상태 [계산] 진입 차단
- **F1.2** 품목 유형(제품/반제품/원자재/상품/서비스) 변경 시 BOM·수불 참조 0건 검증 후만 허용

#### M2 — Monthly Input (6 streams, 3 FRs)

- **F2.1** 월합계 기본 모드에서 일자별 그리드 필드 비노출 (E4)
- **F2.2** 일용직 FTE 환산 입력 완료 시 자동 계산 (환산 인원·환산 임금 표시)
- **F2.3** 음수재고 / 조업도 초과 발생 시 입력 완료 즉시 경고 + 마감 시 차단

#### M3 — Calculation Engine (2 FRs)

- **F3.1** [계산] 클릭 시 §6.1 산식 체인 전체 단일 트랜잭션 + 도중 실패 시 전체 롤백
- **F3.2** 계산 완료 시 §11 V1·V4·V7·V8 자동 발동 + 위반 1건이라도 "검증 실패" 잠금

#### M4 — Inventory Ledger (2 FRs)

- **F4.1** 기초재고 입력 후 자동 이월 체인 개시 + 이후 수동 입력 차단
- **F4.2** 음수 기말 감지 즉시 경고 + 사용자 확인 없이 마감 진입 차단

#### M5 — Reports (3 FRs; +§9 21 reports surfaced)

- **F5.1** §9 21종 보고서 "종합 / 제품별 / 판매지역별" 뷰 토글
- **F5.2** KRW/USD 동시 표시 + 환율 표시 + USD 소수 2자리 강제
- **F5.3** PDF 내보내기 A4 인쇄 최적화

#### M6 — Auto Verification (2 FRs)

- **F6.1** §11 V1~V8을 마감 진입 + 계산 시점 두 곳에서 자동 발동
- **F6.2** V8 회귀 테스트 스위트 실패 시 CI 빌드 차단

#### M7 — Simulation (2 FRs)

- **F7.1** 슬라이더 변경 시 BEP 수량·목표이익을 1초 이내 재계산
- **F7.2** 차월 추정 시 차입금·이자율·상승률·세율 4종 파라미터 사용자 입력 강제

#### M8 — Budget Scenario (2 FRs)

- **F8.1** 1차 시나리오 1개만 허용 + 2개 이상 생성 시도 차단
- **F8.2** 예산-실적 대조 시 모든 차이 행 + A×B×C×D 미구현 회색 배지

#### M9 — ABC Engine (2 FRs)

- **F9.1** 원가풀 행 합 != 100% / 활동 열 합 != 100% / 동인 합 != 100% [계산] 차단
- **F9.2** TDABC CCR 부서 원가 ÷ 실제적 조업능력 1원 단위 계산 + 미사용능력 별도 표시

#### M10 — AI Support (2 FRs)

- **F10.1** 인사이트 질문 3개 캐시 정책: 마감 완료 시점~다음 마감 시작 시점 보존, 마감 데이터 변경 시 폐기
- **F10.2** AI 의견 "자동 분석(고정 템플릿)" vs "AI 참고(구분 배지)" 분리 표시

#### M11 — Close / History (2 FRs)

- **F11.1** 부문분할 → 제조 → ABC → 공동 순서 강제 + 부분 마감 불허
- **F11.2** 마감 완료 시 계산 결과 전체 스냅샷 고정 + 이후 입력·변경은 역분개(A8)로만

#### M12 — Account / Operations (3 FRs)

- **F12.1** 2FA 미설정 시 M2 진입 차단
- **F12.2** 일 1회 자동 백업 + 셀프 다운로드(JSON)
- **F12.3** 해지 요청 시 보관일수 + 삭제 동의 문구 강제 표시

### NonFunctional Requirements

#### NFR — Availability / Recovery (4)

- **NFR1** 가용성 99.5% (월 4h 다운 허용) — 1차 목표, 2차 99.9%
- **NFR2** RPO 24h (일 1회 백업) — 2차 1h
- **NFR3** RTO 4h (1인 운영자 수동 복구) — 2차 1h
- **NFR4** 백업 보관 30일(자동) + 1년(분기) — 2차 1년(자동)

#### NFR — Security / Compliance (4)

- **NFR5** 전송 TLS 1.3, cert 검증
- **NFR6** 저장 AES-256 at rest + KMS 관리
- **NFR7** 인증 2FA 강제 (Supabase Auth), 역할 owner/member/viewer/consultant_proxy
- **NFR8** 감사로그 5년 append-only [A8] — RLS tenant_id 강제

#### NFR — Performance (3)

- **NFR9** 단일 테넌트 월 계산 P95 ≤ 5초
- **NFR10** 보고서 조회 P95 ≤ 3초
- **NFR11** AI 추출 응답 P95 ≤ 30초

#### NFR — Capacity / Volume (4)

- **NFR12** 동시 사용자 ≤ 10/테넌트 (2차 50)
- **NFR13** 테넌트 ≤ 100 (1차), 데이터: 제품 500, 자재 2,000, 월 50K 트랜잭션
- **NFR14** Vercel 글로벌 edge 캐시 = 정적 자산만, 테넌트 데이터 캐시 금지 (AD-9)
- **NFR15** Railway Singapore transient processing only — payload logging/persistent disk/response caching 금지 (AD-9)

#### NFR — Determinism / Quality (2)

- **NFR16** 원가엔진 순수성 (no I/O, no DB, no clock, no randomness outside tests) — V8 1원 단위 회귀 가능
- **NFR17** monetary types: BIGINT (KRW) / NUMERIC(18,2) (USD), Python decimal.Decimal

#### NFR — Localization (1)

- **NFR18** 1차 ko-KR 단일 — 다국어 인프라만 준비, 콘텐츠는 추후 (2차)

#### NFR — Billing (1)

- **NFR19** Stripe 단일 티어 (OQ-2 해결 전까지) — 1만원 월 구독

#### NFR — Platform (1)

- **NFR20** 모바일 네이티브 앱 없음 — 반응형 웹만 (1차)

### Additional Requirements (Architecture-derived, 25 ADs)

#### AD-1 Modular Monolith + Hexagonal Core paradigm

- `packages/cost_engine/` imports only stdlib + approved math; no DB/web/clock/random; SaaS modules invoke engine through ports.
- Dependency direction: `ui → api → services → ports → engine`; adapters implement ports.
- CI enforces engine isolation.

#### AD-2 Append-only ledger

- `inventory_ledger` and `audit_logs` are INSERT-only; PostgreSQL `BEFORE UPDATE OR DELETE` row-level triggers raise `append-only violation`.
- Corrections use AD-22 reversal sequence; originals never change.

#### AD-3 Multi-tenant isolation via Supabase RLS

- Every business table has `tenant_id UUID NOT NULL` and RLS policy.
- Backend derives tenant identity from JWT, never from request data.
- `service_role` bypass writes a typed audit row before the privileged action.

#### AD-4 Calculation transaction atomicity

- AD-19 entry point (`POST /api/v1/calc`) runs one `REPEATABLE READ` DB transaction.
- Verification runs inside it. Any violation rolls back the whole transaction.
- Only `committed` results are authoritative.

#### AD-5 Cost-engine purity

- Engine functions are pure `f(inputs: dataclass) -> dataclass`.
- I/O, DB, clock, randomness, global state, snapshot writes, and logs remain outside engine in services/adapters.

#### AD-6 Fiscal-period close lock

- Rows bounded by `fiscal_periods.status='closed'` reject business-data INSERTs except AD-22 reversal events.
- Reopen requires operator action, reason, audit row, and triggers AD-25 invalidation.

#### AD-7 AI non-authoritative

- AI output is stored only as `input_drafts`. It reaches confirmed inputs exclusively through AD-17.
- AI commentary labeled `ai_reference`; deterministic template analysis labeled `auto_analysis`.
- M10 attempts to write confirmed-input tables are denied and counted (target zero).

#### AD-8 Monetary types

- Storage: `BIGINT` for KRW integer, `NUMERIC(18,2)` for USD.
- Python: `decimal.Decimal`; `float` is forbidden on cost paths.
- UI: KRW integer display, USD two decimals.

#### AD-9 Seoul storage, Singapore compute

- Tenant data at rest, Auth, Storage, backups in Supabase `ap-northeast-2` Seoul.
- FastAPI in Railway `asia-southeast1-eqsg3a` Singapore — transient processing only; no payload logging, persistent disk writes, response caching, or backups on Railway.
- Vercel may cache static assets globally but never tenant data.
- Cross-region DB replication disabled.
- Before pilot launch: PIPA cross-border notice/consent + processor-contract review.

#### AD-10 Identity & roles

- Supabase Auth uses email + mandatory 2FA.
- Roles: `owner`, `member`, `viewer`, consent-bound read-only `consultant_proxy`.
- JWT carries `tenant_id` and `role`; backend middleware enforces role per endpoint.

#### AD-11 Dependency direction

- `ui → api → services → ports → engine`.
- Adapters implement ports.
- Engine-to-adapter/service/UI imports forbidden; direct adapter-to-engine imports forbidden; CI-checked.

#### AD-12 Verification-first calculation flow

- M3: input validation → engine calculation → V1→V4→V7→V8 in order → verified → snapshot persistence → committed.
- Failed check aborts later checks and rolls back.
- Service-only tenants skip V1/V4 but still run V7/V8.

#### AD-13 Input-collection adapter

- `MonthInputAdapter` is the only caller of engine input ports.
- Normalizes six streams across daily/monthly modes, applies FTE conversion + conditional machine-time exposure.
- UI calls the adapter, never the engine.

#### AD-14 Web-verified stack pin

- Stack table is the 2026-07-24 cold-start pin. Lockfiles must resolve these versions exactly.
- Changes require CI + V8 regression.
- Banned: Celery, Kafka, Redis as persistent queue, unmanaged components.

#### AD-15 Cross-language conventions

- DB/Python `snake_case`; Next.js routes `kebab-case`; React/TS types `PascalCase`.
- Store ISO-8601 UTC `TIMESTAMPTZ`, display KST.
- Period keys follow AD-24. IDs are UUID v7; `tenant_id` is ULID.
- Errors: `{code, message_ko, details, trace_id}`.
- Logs: structlog JSON with `trace_id`. Money follows AD-8.

#### AD-16 Fiscal snapshot contract

- `fiscal_period_snapshots` uniquely keyed by `(tenant_id, period_key, segment_id, engine_type)`.
- Stores normalized `material_cost`, `labor_cost`, `overhead_cost`, `manufacturing_cost`, `inventory_adjustment`, `state`, deterministic `result_hash`.
- Opaque result JSON forbidden. M3 is the only writer; M5 and M11 are read-only consumers.

#### AD-17 AI draft promotion port

- Only M2 may call `InputPromoter.promote(tenant_id, period_key, draft_ids) -> MonthlyInput`.
- Idempotent on `(tenant_id, period_key, source_draft_id)`.
- Promotion retains draft with `state='promoted'`, records actor + draft hash in `audit_logs`, writes canonical confirmed-input shape.
- M10 never writes confirmed inputs.

#### AD-18 Single product identity across costing methods

- `PRODUCT(product_id)` is the sole product / cost-object identity.
- `product_role` is `trad_only | abc_only | both`.
- Traditional and ABC attributes extend the same entity.
- Engine results, inventory ledger, reports join only on `product_id`.
- M9 may not mint a parallel cost-object identifier.

#### AD-19 One calculation entry point and owner

- `POST /api/v1/calc` owned by M3 is the only public calculation endpoint.
- UI shows one calculation action per period.
- M3 dispatches traditional and/or M9 ABC ports by tenant kind inside one AD-4 transaction.
- Service-only tenants use the same endpoint with only the ABC path.
- M9 exposes no separate public calculation endpoint.

#### AD-20 Calculation result state machine

- States: `draft → verified → committed → reversed`.
- `verification_status`: `pending | passed | failed`.
- `draft` and `verified` are transaction-internal.
- Only `committed` rows feed M5 or authoritative APIs.
- `reversed` represented by append-only AD-22 event, never by mutating committed row.
- Failed rows roll back; attempts captured in audit telemetry outside result table.

#### AD-21 Single CCR definition

- `CCR = department_indirect_cost / practical_capacity_hours`.
- `department_indirect_cost` is pre-allocation department total after direct labor and direct material are excluded by M1 account tags.
- M9 owns `CCRPort.compute(tenant_id, period_key, department_id) -> Decimal`.
- M3 consumes the result and never recomputes it.

#### AD-22 Reversal construction and ownership

- Correction inserts (1) one sign-negating reversal row with `reverses_event_id` and `reversal_of_period_key`, then (2) optional corrected business row sharing `correction_group_id`.
- Original never changes.
- `(tenant_id, reverses_event_id)` is unique.
- M4 calls `request_reversal(event_id, reason)`; only M11 authorizes and writes the sequence.

#### AD-23 One tenant settings aggregate

- Exactly one `tenant_settings` row per tenant contains `settings_version` + schema-validated JSONB namespaces `onboarding`, `baseline`, `abc`, `ai`.
- Each module writes only its namespace through a version-checked settings service.
- Parallel settings tables forbidden.

#### AD-24 Typed period-key namespaces

- Real fiscal keys: `YYYY-MM`. Virtual budget keys: `YYYY-MM#B<n>`.
- M8 alone mints virtual keys.
- M5 YTD defaults to fiscal keys; budget-vs-actual explicitly joins virtual and fiscal rows by `YYYY-MM` prefix.
- M11 may close only fiscal keys.

#### AD-25 AI insight cache invalidation

- M10 cache key: `(tenant_id, period_key, calculation_result_hash)`.
- New AD-4 commit, AD-22 reversal insert, or M11 reopen emits one DB notification.
- M10 adapter consumes it and invalidates matching entries.
- Application polling and input-write-only invalidation forbidden.

#### Cold-start Stack Pin (AD-14)

| Name | Version |
|------|---------|
| Node.js | 24.18.0 LTS |
| Next.js | 16.2.11 (App Router) |
| React | 19.2.8 |
| TypeScript | 7.0.2 |
| Tailwind CSS | 4.3.3 |
| shadcn CLI | 4.14.1 |
| TanStack React Table | 8.21.3 |
| next-intl | 4.13.4 |
| Recharts | 3.10.0 |
| Python | 3.12.x |
| FastAPI | 0.139.2 |
| Pydantic | 2.13.4 |
| SQLAlchemy | 2.0.51 async |
| Alembic | 1.18.5 |
| pytest | 9.1.1 |
| PostgreSQL | 17 on Supabase |
| Supabase | `ap-northeast-2` Seoul |
| Stripe API | `2026-06-24.dahlia` |
| Vercel | managed frontend |
| Railway | `asia-southeast1-eqsg3a` Singapore |
| structlog | 26.1.0 |
| uv | 0.11.32 |
| OpenTelemetry API | 1.44.0 (traces only MVP) |

#### Deferred / Open Items (Architecture 2차·3차 + AD-26 candidates)

- **PIPA cross-border processing review** — before pilot launch (AD-9 enforcement)
- **AD-26 candidates** (adversary Medium findings to resolve before IR): split `source` from `is_estimated`; define one department entity; type `service_role` bypass audit; decide whether non-authoritative preview port exists; persist daily-input granularity; fix verifier-row skip/order details beyond AD-12
- **A×B×C×D budgeting engine** — 2차 (formula retained, UI placeholder only)
- **Multiple budget scenarios** — 2차 (M8 enforces one in MVP)
- **Mixed classic/TDABC override** — 2차 (schema extension only)
- **Manufacturing ABC parallel view** — 3차
- **Additional locales** — 2차 (infrastructure exists; ko-KR only MVP)
- **Multi-agent cost-analysis committee** — 3차
- **Quantified SLO after pilot** — set from first pilot measurements
- **OpenTelemetry backend** — traces instrumented; exporter selected before production observability
- **Connection pool** — introduce after 20 concurrent tenants
- **Stripe tiered pricing** — 1 tier in MVP until OQ-2 closes
- **Native mobile app** — responsive web only

### UX Design Requirements

> UX design contract does not exist yet (no `ux-designs/` run folder). Skipped per step-01 §6. To be produced in `bmad-ux` after CE.
> 
> Carried UX-side items from PRD/Architecture (Epic-level hooks, not yet actionable requirements):
> - Design tokens (≥1024px PC / <1024px 폼, 12-col 8px base, WCAG AA, Pretendard fallback) — §13.1 — Medium #6
> - Next.js App Router modular pages per M0~M12 — AD-1
> - Recharts-based report visualizations (21 reports) — NFR9·10
> - Accessibility (WCAG AA) — §13.1
> - 2FA 화면 + 4종 역할 권한별 UI — AD-10
> - Calculated results visualization (3-element breakdown from V4) — AD-16

### FR Coverage Map

| FR | §8.1 source | §11 V-row | AD binds | UJ / SM refs |
|----|-------------|-----------|----------|--------------|
| F0.1 | M0 (a) | — | AD-3, AD-7, AD-23 | UJ-4 step 1 |
| F0.2 | M0 (b) | — | AD-3, AD-23 | UJ-4 step 2 |
| F0.3 | M0 (c) | — | AD-7, AD-17 | UJ-4 step 3 |
| F1.1 | M1 (a) | V1 | AD-6, AD-18, AD-23 | UJ-1 step 1 |
| F1.2 | M1 (b) | — | AD-6, AD-18 | UJ-1 step 1 |
| F2.1 | M2 (a) | — | AD-13 | UJ-1 step 2 |
| F2.2 | M2 (b) | — | AD-13 | UJ-1 step 2 |
| F2.3 | M2 (c) | V3, V5 | AD-11, AD-13 | UJ-1 step 2 |
| F3.1 | M3 (a) | — | AD-4, AD-5, AD-12, AD-19, AD-20 | UJ-1 step 3 |
| F3.2 | M3 (b) | V1, V4, V7, V8 | AD-4, AD-12, AD-19, AD-20 | UJ-1 step 3 |
| F4.1 | M4 (a) | — | AD-2, AD-6, AD-18, AD-22 | UJ-1 step 4 |
| F4.2 | M4 (b) | V3 | AD-2, AD-6, AD-22 | UJ-1 step 4 |
| F5.1 | M5 (a) | — | AD-8, AD-16, AD-18, AD-20, AD-24 | UJ-1 step 5 |
| F5.2 | M5 (b) | — | AD-8, AD-15 | UJ-1 step 5 |
| F5.3 | M5 (c) | — | AD-8 | UJ-1 step 5 |
| F6.1 | M6 (a) | V1~V8 | AD-4, AD-5, AD-12 | UJ-1 step 3 |
| F6.2 | M6 (b) | V8 | AD-4, AD-5 | UJ-1 step 3 |
| F7.1 | M7 (a) | — | AD-5 | UJ-2 step 4 |
| F7.2 | M7 (b) | — | AD-5 | UJ-2 step 4 |
| F8.1 | M8 (a) | — | AD-24 | UJ-2 step 3 |
| F8.2 | M8 (b) | — | AD-24 | UJ-2 step 3 |
| F9.1 | M9 (a) | V7 | AD-18, AD-19, AD-21 | UJ-3 step 2 |
| F9.2 | M9 (b) | — | AD-18, AD-19, AD-21 | UJ-3 step 2 |
| F10.1 | M10 (a) | — | AD-7, AD-17, AD-25 | UJ-1 step 5 |
| F10.2 | M10 (b) | — | AD-7, AD-17 | UJ-1 step 5 |
| F11.1 | M11 (a) | — | AD-6, AD-16, AD-20, AD-22, AD-25 | UJ-1 step 5 |
| F11.2 | M11 (b) | — | AD-2, AD-6, AD-20, AD-22 | UJ-1 step 5 |
| F12.1 | M12 (a) | — | AD-3, AD-10 | UJ-4 step 4 |
| F12.2 | M12 (b) | — | AD-3, AD-10 | UJ-4 step 5 |
| F12.3 | M12 (c) | — | AD-3, AD-10 | UJ-4 step 5 |

## Epic List

> **13 Epic 설계**: Epic 0 (Platform Foundation) + Epic 1~12 (M0~M12 1:1). MVP critical path = Epic 0 → 1 → 2 → 3 → 4 → 5 → 6 → 11 (월 마감 E2E). 7·8·9·10·12는 supplementary.

### Epic 0: Platform Foundation & Multi-Tenancy

Platform 빌드블록을 세우는 Epic. **사용자 가치 없음**(operator-facing). 모든 후속 Epic이 의존하는 토대. PRD §13.2 + Architecture AD-1·3·14·15·23.
- **FRs covered**: (직접 FR 없음 — AD/NFR 전용)
- **NFRs covered**: NFR5·6·7·8 (보안), NFR14·15 (지역 분리), NFR16·17 (엔진 순수성 + monetary types)
- **Architecture binds**: AD-1 paradigm, AD-3 RLS, AD-8 monetary types, AD-9 Seoul/Singapore, AD-10 identity+2FA, AD-11 dependency direction, AD-14 stack pin, AD-15 cross-language conventions, AD-23 one tenant settings aggregate
- **Implementation notes**: `apps/web` (Next.js 16), `apps/api` (FastAPI), `packages/cost_engine/` (pure Python), `supabase/migrations/` + `policies/` (RLS) bootstrap. Stack pin locked. Singleton `tenant_settings` enforced. CI lockfile + V8 regression.

### Epic 1: User Onboarding & Settings

신규 회원이 업종 4지선다 → 회사 기본정보 → 배부기준 3종을 완료해 계산 가능 상태에 도달. **사용자 가치**: "처음 와서 10분 안에 우리 회사 셋업 끝". UJ-4가 이 Epic의 주인공.
- **FRs covered**: F0.1, F0.2, F0.3
- **NFRs covered**: NFR18 (ko-KR)
- **Architecture binds**: AD-3, AD-7, AD-23
- **Implementation notes**: `m0_onboarding/` module. AI 문서추출(E5) 신뢰도 70% 임계값. 배부기준 3종 미완료 시 [계산] 차단. tenant_settings aggregate 첫 등록.

### Epic 2: Master Data & BOM

회원이 제품·반제품·원자재·상품·서비스를 등록하고 BOM·계정과목·부서·판매지역·거래처를 잡음. **사용자 가치**: "우리 회사 카탈로그가 시스템 안에 들어옴". UJ-1 step 1 + UJ-3.
- **FRs covered**: F1.1, F1.2
- **NFRs covered**: NFR13 (vol)
- **Architecture binds**: AD-6, AD-18, AD-23
- **Implementation notes**: `m1_baseline/` module. BOM 100% 검증 + 품목유형 변경 무결성. 제품 = 단일 product_id (AD-18). 계정 태그 (직접/간접, 고정/변동) — CCR 정의용.

### Epic 3: Monthly Input Capture

회원이 6종 데이터(주문·생산·판매·구매·경비·인원인건비)를 월합계/일자별로 입력. **사용자 가치**: "엑셀에서 옮겨오는 작업이 1시간 컷". UJ-1 step 2의 전부.
- **FRs covered**: F2.1, F2.2, F2.3
- **NFRs covered**: NFR9 (입력 응답성)
- **Architecture binds**: AD-13 (MonthInputAdapter)
- **Implementation notes**: `m2_input/` module. FTE 환산 자동. 음수재고·조업도 초과 즉시 경고. 월합계 기본 + 일자별 선택.

### Epic 4: Cost Calculation & Verification

회원이 [계산] 한 번에 §6.1 산식 체인 전체가 단일 트랜잭션으로 돌고 V1·V4·V7·V8 통과. **사용자 가치**: "틀린 계산은 불가능, 쓴 입력은 빨강으로 표시". UJ-1 step 3의 핵심.
- **FRs covered**: F3.1, F3.2, F6.1, F6.2
- **NFRs covered**: NFR9 (P95 ≤ 5s), NFR16 (determinism), NFR17 (monetary types)
- **Architecture binds**: AD-4 (atomicity), AD-5 (purity), AD-12 (verify-first), AD-16 (snapshot contract), AD-19 (single endpoint), AD-20 (state machine), AD-21 (single CCR)
- **Implementation notes**: `m3_calculate/` + `m6_verification/` modules — 동일 컴포넌트(calc engine)에서 calc + verify가 함께 동작. POST /api/v1/calc 단일 진입. AD-22 reversal event는 Epic 11에서. CI V8 차단.

### Epic 5: Inventory & Stock Control

원부재료·제품 수불이 자동으로 흐르고 음수 기말은 즉시 차단. **사용자 가치**: "재고가 음수가 되는 일이 시스템적으로 안 일어남". UJ-1 step 4.
- **FRs covered**: F4.1, F4.2
- **NFRs covered**: NFR13 (vol)
- **Architecture binds**: AD-2 (append-only), AD-6 (close lock), AD-18 (single product_id), AD-22 (reversal)
- **Implementation notes**: `m4_inventory/` module. 기초재고 후 자동 이월 체인. 음수 기말 = 마감 진입 차단. 수불부 append-only.

### Epic 6: Reporting & Export

회원이 §9 21종 보고서를 종합/제품별/판매지역별로 토글하고 PDF/A4로 내보냄. **사용자 가치**: "모든 보고서를 한 페이지에서 모아봄". UJ-1 step 5.
- **FRs covered**: F5.1, F5.2, F5.3
- **NFRs covered**: NFR10 (P95 ≤ 3s), NFR17 (KRW/USD)
- **Architecture binds**: AD-8 (monetary), AD-16 (snapshot reader), AD-18 (single product_id), AD-20 (committed-only), AD-24 (typed period keys)
- **Implementation notes**: `m5_reports/` module. 21 보고서 모두 M5 FR F5.1에 묶임. Read-only — M3 + M11만 writer. PDF A4 + KRW 정수 + USD 소수 2자리.

### Epic 7: CVP/BEP Simulation

회원이 슬라이더로 단가/원가/조업도를 흔들며 BEP와 목표이익을 1초 안에 봄. **사용자 가치**: "가격 인상 전 손익분기점 미리 확인". UJ-2 step 4.
- **FRs covered**: F7.1, F7.2
- **NFRs covered**: NFR9 (1초 응답)
- **Architecture binds**: AD-5 (engine purity)
- **Implementation notes**: `m7_simulation/` module. 순수 엔진 함수 — DB/시계 없음. 차월 추정 4종 파라미터 강제.

### Epic 8: Budget vs Actual

회원이 가상 기간으로 예산을 입력해 사전 표준원가계산 + 실적 대조를 봄. **사용자 가치**: "예산을 미리 짜보고 실적이 어디서 어긋났는지 보임". UJ-2 step 3.
- **FRs covered**: F8.1, F8.2
- **NFRs covered**: NFR24 (typed period keys)
- **Architecture binds**: AD-24 (virtual keys)
- **Implementation notes**: `m8_budget/` module. 1차 시나리오 1개만 (Non-Goal #2). A×B×C×D 편성 엔진 미구현 (Non-Goal #3) — 회색 배지. M8 alone mints virtual keys.

### Epic 9: ABC / TDABC Engine (Service Business)

서비스 업종 회사가 원가풀 → 활동 → 동인 → 원가대상으로 배부. **사용자 가치**: "여행상품·물류 서비스의 원가가 어떻게 구성됐는지 보임". UJ-3 step 2.
- **FRs covered**: F9.1, F9.2
- **NFRs covered**: NFR16 (CCR 1원)
- **Architecture binds**: AD-18 (single product_id), AD-19 (no public calc endpoint), AD-21 (CCRPort)
- **Implementation notes**: `m9_abc/` module. **No public calc endpoint** — M3이 호출하는 internal port. CCRPort.compute 단일 소유. Non-Goal #1: 제조부문 ABC 미구현.

### Epic 10: AI Assistance

회원이 AI 문서추출 + 인사이트 3개 + 고정/변동 3단계 추정을 받음. **사용자 가치**: "엑셀 업로드를 AI가 먼저 읽어줌". UJ-4 step 3 + UJ-1 step 5.
- **FRs covered**: F10.1, F10.2
- **NFRs covered**: NFR11 (AI P95 ≤ 30s)
- **Architecture binds**: AD-7 (AI non-authoritative), AD-17 (promotion port), AD-25 (cache invalidation)
- **Implementation notes**: `m10_ai/` module. **Never writes confirmed inputs** — only input_drafts. Cache key = (tenant_id, period_key, calculation_result_hash). 캐시 무효화는 DB notification (AD-25). SM-3a: 계산 결과 변경 시도 = 0건 별도 추적.

### Epic 11: Monthly Close & Audit

회원이 마감 완료 → 이후 수정은 역분개라서 원본이 안 바뀜. **사용자 가치**: "감사 받을 수 있는 마감 본이 만들어짐". UJ-1 step 5.
- **FRs covered**: F11.1, F11.2
- **NFRs covered**: NFR5 (감사로그 5년)
- **Architecture binds**: AD-2 (append-only), AD-6 (close lock), AD-16 (snapshot), AD-20 (state machine), AD-22 (reversal), AD-25 (cache invalidation)
- **Implementation notes**: `m11_close/` module. 부문분할→제조→ABC→공동 순서 강제. closed 기간 INSERT 차단 (AD-6). Reversal은 (1) 부호 반전 row + (2) corrected row (AD-22). M11만 authorize.

### Epic 12: Account & Security Operations

회원이 2FA·역할 권한·백업·해지·대리접속을 관리. **사용자 가치**: "내 회사 데이터가 안전하고, 새벽에 혼자 복구 가능". UJ-4 step 4-5.
- **FRs covered**: F12.1, F12.2, F12.3
- **NFRs covered**: NFR1 (99.5%), NFR2·3 (RPO/RTO), NFR4 (백업), NFR5 (TLS), NFR6 (AES-256), NFR7 (2FA)
- **Architecture binds**: AD-3 (RLS), AD-9 (Seoul), AD-10 (identity+roles)
- **Implementation notes**: `m12_account/` module. 2FA 강제 (M2 진입 차단). 일 1회 자동 백업 + JSON 다운로드. 4역할 owner/member/viewer/consultant_proxy. 대리접속(컨설턴트) = consent-bound read-only.

### FR Coverage Map

```
Epic 0 (Platform):       (FR 없음 — AD/NFR 토대)
Epic 1 (Onboarding):     F0.1, F0.2, F0.3
Epic 2 (Master Data):    F1.1, F1.2
Epic 3 (Input):          F2.1, F2.2, F2.3
Epic 4 (Calc+Verify):    F3.1, F3.2, F6.1, F6.2
Epic 5 (Inventory):      F4.1, F4.2
Epic 6 (Reports):        F5.1, F5.2, F5.3
Epic 7 (Simulate):       F7.1, F7.2
Epic 8 (Budget):         F8.1, F8.2
Epic 9 (ABC):            F9.1, F9.2
Epic 10 (AI):            F10.1, F10.2
Epic 11 (Close):         F11.1, F11.2
Epic 12 (Account):       F12.1, F12.2, F12.3
```

**Coverage 검증**: 30 FR → 13 Epic, 100% mapped. Non-Goal 10개 (§14.B)는 Epic 범위에서 의도적으로 제외.

### Epic Dependencies (참고)

```
Epic 0 ──→ Epic 1 ──→ Epic 2 ──→ Epic 3 ──→ Epic 4 ──→ Epic 5 ──→ Epic 11
                                              │            │
                                              ├─→ Epic 6 ──┤
                                              ├─→ Epic 7
                                              ├─→ Epic 8
                                              ├─→ Epic 9
                                              │
                                              └─→ Epic 10 (AI inputs from Epic 1·3, cache tied to Epic 4·11)

Epic 0 ──→ Epic 12 (auth needs RLS)
Epic 1 ──→ Epic 10 (AI defaults from settings)
Epic 3 ──→ Epic 9 (ABC needs inputs)
Epic 4 ──→ Epic 9 (M3 dispatches M9)
Epic 4 ──→ Epic 6 (M5 reads snapshot)
Epic 4 ──→ Epic 10 (AI cache tied to calc result hash)
Epic 5 ──→ Epic 11 (close sequence inventory)
```

**MVP critical path** (E2E 월 마감): 0 → 1 → 2 → 3 → 4 → 5 → 6 → 11
**Supplementary** (parallel 가능): 7 (sim), 8 (budget), 9 (ABC), 10 (AI), 12 (account ops)

---

## Epic Details & Stories

### Epic 0: Platform Foundation & Multi-Tenancy

**Epic goal**: 모든 후속 Epic이 의존하는 토대를 세운다. Multi-tenant 격리, stack pin, 결정론성 인프라, 엔진 격리가 동시에 갖춰져야 후속 모듈이 안전하게 출시될 수 있다.

**FRs covered**: (직접 FR 없음 — AD/NFR 토대)
**Architecture binds**: AD-1·3·8·9·10·11·14·15·23
**NFRs touched**: NFR5·6·7·8·14·15·16·17

---

#### Story 0.1: Modular Monolith + Hexagonal Core Skeleton

As a **platform engineer**, I want **the monorepo to enforce the `ui → api → services → ports → engine` dependency direction from day one**, so that **no module accidentally imports `packages/cost_engine/`'s DB, web, clock, or randomness**.

**Acceptance Criteria:**

- **Given** the monorepo is initialized
**When** I scaffold `apps/web/`, `apps/api/`, `packages/cost_engine/`, `packages/services/`, `packages/ports/`
**Then** each directory has its own `pyproject.toml` or `package.json` with explicit, restricted `imports` constraints
**And** `packages/cost_engine/` declares only stdlib + `decimal` + `numpy` (read-only) in `pyproject.toml`
**And** a CI lint step (`dependency-cruiser` for TS, `import-linter` for Python) fails the build if engine imports DB/web/clock/randomness
**And** `apps/api/` may only call `packages/ports/` interfaces, never engine internals

#### Story 0.2: Supabase Multi-Tenancy Schema + RLS Policies

As a **platform engineer**, I want **every business table to carry `tenant_id UUID` and a row-level security policy**, so that **two tenants can never see each other's data even with a leaked JWT**.

**Acceptance Criteria:**

- **Given** Supabase is provisioned in `ap-northeast-2` Seoul
**When** I write the initial Alembic migration for `tenants`, `users`, `tenant_memberships`, plus the `tenant_settings` placeholder
**Then** every table has `tenant_id UUID NOT NULL` and a FK to `tenants(id)`
**And** an RLS policy reads `tenant_id` from `auth.jwt() -> 'app_metadata' ->> 'tenant_id'` and filters all SELECT/INSERT/UPDATE/DELETE
**And** a fixture test runs as tenant A and asserts zero rows visible when reading tenant B's data
**And** `service_role` bypass exists only for backfill jobs and writes a typed `audit_logs` row before the privileged action

#### Story 0.3: Stack Pin Lockfile + Build Pipeline

As a **platform engineer**, I want **the cold-start stack pin (AD-14) enforced by lockfile and CI**, so that **no engineer can upgrade Next.js, FastAPI, or PostgreSQL without tripping the build**.

**Acceptance Criteria:**

- **Given** the stack pin table (Node 24.18 LTS, Next.js 16.2.11, React 19.2.8, TypeScript 7.0.2, Tailwind 4.3.3, FastAPI 0.139.2, Python 3.12, PostgreSQL 17, structlog 26.1, uv 0.11.32, OpenTelemetry 1.44) is locked
**When** I commit `package.json` + `uv.lock` + Dockerfile pinning all versions
**Then** CI rejects any PR that bumps a pinned version without an explicit `[STACK BUMP]` commit tag
**And** a weekly dependabot runs but is gated behind the same bump policy
**And** `package.json` script `pnpm dep:check` returns non-zero if any version drifts

#### Story 0.4: Cross-Language Conventions + Monetary Types Foundation

As a **platform engineer**, I want **all DB columns, Python types, and TS types to follow the shared conventions (AD-15, AD-8)**, so that **developers never guess the casing, time zone, money unit, or ID type**.

**Acceptance Criteria:**

- **Given** the conventions doc (`docs/conventions.md`) is published with `snake_case` SQL/Python, `kebab-case` Next.js routes, `PascalCase` React/TS types, ISO-8601 UTC `TIMESTAMPTZ` (KST display), UUID v7 IDs, ULID `tenant_id`, structured `{code, message_ko, details, trace_id}` errors
**When** I add a linter config (`ruff` for Python, `eslint` rules for TS) and a money-type validator
**Then** the linter fails builds that introduce `camelCase` DB columns or `float` money variables
**And** all monetary fields use `BIGINT` for KRW (integer) and `NUMERIC(18,2)` for USD in Postgres; `Decimal` in Python; `bigint` + `decimal.js` in TS
**And** a `make lint-conventions` script runs in CI

---

### Epic 1: User Onboarding & Settings

**Epic goal**: 신규 회원이 업종 4지선다 → 회사 기본정보 → 배부기준 3종을 10분 안에 완료하고, 회계연도 시작월·통화·언어·배부기준이 모두 채워질 때까지 [계산] 진입을 막는다.

**FRs covered**: F0.1, F0.2, F0.3
**NFRs touched**: NFR18 (ko-KR)
**Architecture binds**: AD-3, AD-7, AD-23

---

#### Story 1.1: Industry Selector + Menu Auto-Toggle

As a **신규 가입 사장님**, I want **업종 4지선다(제조·제조+유통·서비스·겸영)를 고르면 후속 메뉴가 자동으로 토글되는 것**, so that **내가 하는 일에 안 쓰는 화면은 안 보이게**.

**Acceptance Criteria:**

- **Given** 나는 신규 가입 후 첫 로그인
**When** 4지선다 중 "서비스"를 선택
**Then** 좌측 메뉴에서 "BOM", "기초재고", "수불부"가 숨겨지고 "원가풀", "활동", "동인" 메뉴가 노출됨
**And** "제조+유통" 선택 시 "BOM" + "기초재고" + "원가풀" 모두 노출
**And** 업종 선택은 `tenant_settings.onboarding.industry`에 한 번만 기록되고 이후 메뉴 토글의 단일 소스

#### Story 1.2: Settings Wizard with Calculation Block

As a **신규 사장님**, I want **[계산] 버튼이 회계연도 시작월·통화·언어·배부기준 3종이 다 채워질 때까지 회색으로 잠겨 있는 것**, so that **빠뜨리고 계산하는 사고를 시스템이 막아줌**.

**Acceptance Criteria:**

- **Given** 나는 [계산] 버튼을 누르려 한다
**When** 4개 필드 중 하나라도 미완료
**Then** 버튼은 disabled 상태이고 hover 시 "회계연도 시작월/통화/언어/배부기준 3종을 모두 완료해 주세요" 툴팁이 표시됨
**And** 4개 모두 채우면 버튼이 활성화됨
**And** 배부기준 3종 = "직접/간접 계정 분류", "고정/변동 분류", "동인 정의"이며 각각 최소 1행 이상 등록되어야 통과

#### Story 1.3: AI Document Extraction with Confidence Badge

As a **사장님**, I want **AI가 업로드한 PDF·Excel에서 회사 정보를 추출할 때 신뢰도 70% 미만이면 빨강 배지가 붙는 것**, so that **내가 모르고 AI가 틀린 값을 그대로 쓰는 일을 막음**.

**Acceptance Criteria:**

- **Given** 나는 PDF 1장(회사 소개서)을 업로드한다
**When** AI가 추출한 필드 중 "사업자등록번호" 신뢰도가 65%로 측정됨
**Then** 해당 필드 우측에 빨강 배지("⚠ 확인 필요")가 표시됨
**And** 사용자가 직접 값을 수정해 확정해야 [계산] 잠금이 풀림
**And** 70% 이상이면 회색 배지("✓ 자동 입력")만 표시되고 수정 없이 통과
**And** AI 추출값은 `input_drafts`에만 저장되며 확정값은 사용자 수정본만 `tenant_settings`로 승격

---

### Epic 2: Master Data & BOM

**Epic goal**: 회원이 우리 회사 카탈로그(제품·반제품·원자재·상품·서비스·BOM·계정·부서·지역·거래처)를 시스템 안에 올린다.

**FRs covered**: F1.1, F1.2
**NFRs touched**: NFR13
**Architecture binds**: AD-6, AD-18, AD-23

---

#### Story 2.1: Product & Item Master with Type Tags

As a **사장님**, I want **제품·반제품·원자재·상품·서비스를 한 화면에서 등록하고 각각 다른 색 배지를 받는 것**, so that **목록에서 어떤 종류인지 한눈에 구분**.

**Acceptance Criteria:**

- **Given** 나는 [기준정보] → [품목]에 진입했다
**When** "추가" 클릭 후 유형을 "원자재"로 선택
**Then** 파란색 배지("원자재")가 목록에 표시되고 코드는 `MAT-` 접두사로 자동 생성됨
**And** 제품 = 녹색 `PRD-`, 반제품 = 보라 `SEM-`, 상품 = 주황 `GDS-`, 서비스 = 회색 `SVC-`
**And** 동일 코드 존재 시 저장이 거부되고 "이미 존재하는 코드입니다" 토스트가 표시됨

#### Story 2.2: BOM Matrix with 100% Validation

As a **사장님**, I want **BOM 행렬에서 모(母)품목의 비중 합이 100%가 아니면 [계산] 버튼이 잠기는 것**, so that **틀린 비율로 계산되는 사고를 사전에 차단**.

**Acceptance Criteria:**

- **Given** 나는 "제품 A"의 BOM에 원자재 3개(40%, 30%, 20%)를 입력했다
**When** 마지막에 5%를 추가하려 한다
**Then** 합계가 95%일 때 [계산]이 disabled되고 "BOM 비중 합 100% 필요 (현재 95%)" 메시지가 표시됨
**And** 100%가 되는 순간 [계산]이 다시 활성화됨
**And** BOM 행렬은 `(모품목, 자품목, 비율%)` 3-튜플이며 `product_id` 단일 키로 join됨 (AD-18)

#### Story 2.3: Item Type Change Integrity Guard

As a **사장님**, I want **품목 유형을 바꾸려 할 때 BOM·수불 참조 0건일 때만 허용되는 것**, so that **이미 어디선가 쓰이는 품목이 갑자기 다른 종류로 바뀌는 사고를 방지**.

**Acceptance Criteria:**

- **Given** "원자재 X"가 BOM 3곳과 수불 12건에 참조되고 있다
**When** 유형을 "반제품"으로 변경 시도
**Then** 변경이 거부되고 "BOM 3건, 수불 12건에서 참조 중 — 신규 품목 생성 후 참조 이관 후 삭제" 안내가 표시됨
**And** 참조 0건인 경우에만 즉시 변경 가능
**And** 변경 성공 시 `audit_logs`에 `(actor, before_type, after_type, ts)` 1행 append

---

### Epic 3: Monthly Input Capture

**Epic goal**: 회원이 6종 데이터(주문·생산·판매·구매·경비·인원)를 월합계 또는 일자별로 입력하고, 일용직은 FTE로 자동 환산되며, 음수재고·조업도 초과는 즉시 경고로 잡힌다.

**FRs covered**: F2.1, F2.2, F2.3
**NFRs touched**: NFR9
**Architecture binds**: AD-13

---

#### Story 3.1: Six-Stream Monthly Input UI (Month-Total Default)

As a **사장님**, I want **6종 입력(주문·생산·판매·구매·경비·인원)이 월합계 기본으로 한 화면에 탭으로 보이는 것**, so that **엑셀에서 옮기는 작업이 한 페이지 안에서 끝남**.

**Acceptance Criteria:**

- **Given** 나는 [월 입력] 화면에 있다
**When** "2026-07" 기간을 선택
**Then** 6개 탭(주문/생산/판매/구매/경비/인원)이 가로 탭으로 보이고 기본은 "월합계" 모드
**And** "일자별" 토글을 켜면 일자 그리드(31행)가 펼쳐짐 (F2.1)
**And** 한 탭이라도 미완료면 탭 헤더에 노란 점 표시
**And** 모든 탭 완료 시 [계산] 활성화

#### Story 3.2: FTE Conversion for Daily Labor

As a **사장님**, I want **일용직 인원·일수를 입력하면 FTE 환산 인원·환산 임금이 자동 계산되어 표시되는 것**, so that **인건비를 월 기준으로 정규화하는 수고를 덜어줌**.

**Acceptance Criteria:**

- **Given** 나는 [인원] 탭에 일용직 3명, 각 8일, 일급 15만원 입력
**When** 저장을 클릭
**Then** FTE 환산 인원 = `3 × 8 / 22 ≈ 1.09명`, 환산 임금 = `1.09 × 월급여 기준액`으로 자동 계산 표시
**And** 계산 결과는 비활성 필드로 보여지고 수동 편집 불가
**And** 월합계 모드에서는 FTE 환산값만 보임 (일자별 모드에서만 일수/일급 편집 가능)

#### Story 3.3: Negative Inventory & Overcapacity Real-Time Warning

As a **사장님**, I want **입력 중 음수재고나 조업도 초과가 발생하면 즉시 빨강 경고가 뜨고, 마감 진입이 차단되는 것**, so that **데이터 오류가 계산 결과까지 흘러가지 않음**.

**Acceptance Criteria:**

- **Given** 기초재고 100개, 출고 130개 입력
**When** "130"을 입력하는 순간
**Then** "기말재고 -30 → 음수 경고" 토스트가 즉시 표시
**And** [마감] 버튼이 disabled 상태로 잠김
**And** 출고량을 100 이하로 수정하면 경고 사라지고 [마감] 다시 활성화
**And** 조업도 110% 입력 시에도 동일한 즉시 경고 동작 (조업도 한도 초과)

---

### Epic 4: Cost Calculation & Verification

**Epic goal**: [계산] 한 번에 §6.1 산식 체인 전체가 단일 트랜잭션으로 돌고 V1·V4·V7·V8을 통과한 결과만 `verified → committed` 상태로 잠근다. V8 회귀 테스트는 CI에서 빌드를 차단한다.

**FRs covered**: F3.1, F3.2, F6.1, F6.2
**NFRs touched**: NFR9·16·17
**Architecture binds**: AD-4·5·12·16·19·20·21

---

#### Story 4.1: Pure Cost Engine (No I/O, No Clock)

As a **사장님**, I want **원가 계산 엔진이 순수 함수로 구현되어 같은 입력에 항상 같은 출력이 나오는 것**, so that **회계사가 "왜 이번 달은 다르냐"고 물으면 1원 단위로 재현 가능**.

**Acceptance Criteria:**

- **Given** `packages/cost_engine/`에 `compute_period_cost(monthly_input: MonthlyInput, baseline: Baseline) -> CalcResult` 함수가 있다
**When** 동일한 `MonthlyInput` + `Baseline`으로 100번 호출
**Then** 100번 모두 동일한 `result_hash`를 반환 (V8 회귀 가능)
**And** 함수 본문에 `import os, time, random, requests, sqlalchemy` 등 I/O/시계/난수 모듈 호출이 없음
**And** 정적 분석(`ruff` + 커스텀 룰)이 `packages/cost_engine/` 내 I/O 호출을 빌드 실패로 차단

#### Story 4.2: Single Calculation Endpoint with REPEATABLE READ Transaction

As a **사장님**, I want **[계산]을 누르면 산식 체인 8단계가 한 트랜잭션으로 돌고 중간 실패 시 전부 롤백되는 것**, so that **"계산은 됐는데 V4가 빨강" 같은 부분 완료 상태가 안 생김**.

**Acceptance Criteria:**

- **Given** 나는 [계산] 버튼을 눌렀다
**When** POST `/api/v1/calc`가 호출된다
**Then** 1개의 DB 트랜잭션(`REPEATABLE READ`) 안에서 §6.1 8단계가 순차 실행됨
**And** 어느 단계든 예외 발생 시 트랜잭션 전체 ROLLBACK + "계산 실패" 메시지
**And** 단일 진입점은 `POST /api/v1/calc` 1개이며 다른 public calc endpoint 없음 (AD-19)
**And** `fiscal_period_snapshots`에 `state='draft'`로 1행 INSERT (M3만 writer)

#### Story 4.3: Verification V1→V4→V7→V8 in Order

As a **사장님**, I want **계산 직후 V1·V4·V7·V8이 자동 발동하고 1건이라도 위반이면 "검증 실패" 잠금이 표시되는 것**, so that **사용자가 빨간 줄을 보고 입력을 고치는 행동을 취함**.

**Acceptance Criteria:**

- **Given** 계산 완료 후 V1(인쇄무역)·V4(원가대체)·V7(CCR 정합)·V8(1원 단위 회귀)이 자동 실행됨
**When** V4가 위반(예: 제조원가가 음수) 탐지
**Then** `verification_status='failed'`로 잠금 + V4 상세("어떤 제품, 얼마") 표시
**And** V1→V4→V7→V8 순서 보장 (이전 검증 실패 시 다음 검증 스킵, AD-12)
**And** 검증 통과 시 `state='verified'` → `state='committed'`로 전이 (AD-20)

#### Story 4.4: V8 Regression CI Gate

As a **platform engineer**, I want **V8 1원 단위 회귀 테스트가 CI 빌드를 차단하는 것**, so that **어떤 PR이 엔진 출력의 1원이라도 바꾸면 머지 불가**.

**Acceptance Criteria:**

- **Given** V8 회귀 스위트 12개 시나리오가 `tests/engine/v8_*.py`에 있다
**When** PR이 머지되기 전 CI 실행
**Then** 12개 중 1개라도 실패 시 빌드 차단 + "V8 regression: 시나리오 N 실패" 코멘트
**And** V8 통과 + 다른 모든 테스트 통과 시에만 머지 가능
**And** V8 시나리오는 직전 분기 마감을 골든 파일로 사용 (분기마다 갱신)

---

### Epic 5: Inventory & Stock Control

**Epic goal**: 기초재고 후 자동 이월 체인이 시작되고, 이후 수동 입력은 잠기며, 음수 기말은 즉시 경고 + 마감 차단이다.

**FRs covered**: F4.1, F4.2
**NFRs touched**: NFR13
**Architecture binds**: AD-2·6·18·22

---

#### Story 5.1: Opening Inventory Auto-Carry Chain

As a **사장님**, I want **기초재고를 입력한 다음 달부터 자동으로 이월되고 수동 입력이 잠기는 것**, so that **매달 기초재고를 다시 안 쳐도 됨**.

**Acceptance Criteria:**

- **Given** "2026-07" 기초재고로 원자재 X 100개 입력
**When** "2026-08" 기간으로 이동
**Then** "2026-08" 기초재고가 자동으로 100개 표시되고 수동 편집 불가
**And** "2026-07"에 추가 출고가 발생하면 "2026-08" 기초재고가 자동 재계산
**And** 수동 편집 시도 시 "기초재고는 자동 이월됩니다" 메시지 + 잠금

#### Story 5.2: Inventory Ledger Append-Only Events

As a **platform engineer**, I want **수불부가 INSERT-only이면서 UPDATE/DELETE가 차단되는 것**, so that **감사 시 원본이 절대 안 바뀜**.

**Acceptance Criteria:**

- **Given** `inventory_ledger` 테이블에 PostgreSQL `BEFORE UPDATE OR DELETE` 트리거가 설치됨
**When** 기존 row를 UPDATE 시도
**Then** `append-only violation` 에러로 거부됨
**And** 수정 필요 시 AD-22 reversal 시퀀스(부호 반전 row + corrected row)로만 처리 (Epic 11에서 다룸)
**And** 모든 row는 `(tenant_id, product_id, period_key, event_type, qty, trace_id)` 컬럼을 가짐

#### Story 5.3: Negative Closing Inventory Guard

As a **사장님**, I want **월 마감 진입 시 기말재고가 음수면 즉시 경고 + 마감 차단되는 것**, so that **음수 재고로 마감을 못 박는 사고를 막음**.

**Acceptance Criteria:**

- **Given** "2026-07" 기말재고가 -5개로 계산됨
**When** [마감] 버튼 클릭
**Then** "기말재고 음수: 원자재 X -5개 → 마감 불가" 빨간 배너 표시
**And** [마감]이 disabled로 유지
**And** 출고/입고 수정으로 기말 ≥ 0이 되어야 [마감] 활성화
**And** V3(연결성) 검증과 동기화

---

### Epic 6: Reporting & Export

**Epic goal**: §9 21종 보고서를 종합/제품별/판매지역별로 토글하고, KRW/USD 동시 표시, PDF A4 인쇄 최적화 내보내기를 지원한다.

**FRs covered**: F5.1, F5.2, F5.3
**NFRs touched**: NFR10·17
**Architecture binds**: AD-8·16·18·20·24

---

#### Story 6.1: 21-Report Library with View Toggle

As a **사장님**, I want **21종 보고서가 좌측 트리에 한 페이지에 다 모이고 "종합/제품별/판매지역별" 뷰 토글이 상단에 있는 것**, so that **모든 보고서를 한 페이지에서 순회 가능**.

**Acceptance Criteria:**

- **Given** 나는 [보고서] 화면에 진입했다
**When** 뷰 토글에서 "제품별" 선택
**Then** 같은 보고서(예: 제조원가명세서)가 제품 1개당 1행으로 펼쳐져 표시됨
**And** "판매지역별" 토글 시 지역 컬럼이 추가됨
**And** 21종 보고서는 §9 #1~21 목록과 1:1 매칭, 모두 `fiscal_period_snapshots`에서 읽기 (M3 + M11만 writer)
**And** Recharts 기반 시각화(막대/꺾은선) — KPI 박스 4개 상단 고정

#### Story 6.2: KRW/USD Dual Display with Rate Source

As a **사장님**, I want **모든 금액이 KRW(정수) + USD(소수 2자리) 동시 표시되고 환율 출처가 보이는 것**, so that **해외 거래처와 공유할 때 환산본을 따로 안 만들어도 됨**.

**Acceptance Criteria:**

- **Given** 제조원가명세서가 표시됨
**When** 화면 진입
**Then** 각 행은 `₩1,234,567 / $934.56` 두 줄로 표시되고 헤더에 환율(예: `1 USD = 1,320 KRW, 출처: 한국은행 2026-07-25`) 명시
**And** USD 환산은 정수 KRW ÷ 환율 → 소수 2자리 반올림
**And** `tenant_settings.baseline.currency_pair`에 따라 환율 소스 변경 가능

#### Story 6.3: PDF A4 Export with Print Optimization

As a **사장님**, I want **선택한 보고서를 PDF A4로 다운로드할 때 페이지 분할·여백·헤더가 인쇄에 최적화된 것**, so that **종이로 출력해서 회계사에게 바로 전달 가능**.

**Acceptance Criteria:**

- **Given** 나는 "원가대체명세서" 보고서를 본다
**When** [PDF 내보내기] 클릭
**Then** A4(210×297mm) PDF가 다운로드되고 페이지당 1표, 헤더에 회사명·기간·페이지번호
**And** 좌우 여백 15mm, 폰트 10pt, 행 높이 6mm
**And** KRW/USD 모두 PDF에 포함
**And** PDF 생성은 서버 사이드(API) 호출, 클라이언트는 URL만 받음

---

### Epic 7: CVP/BEP Simulation

**Epic goal**: 슬라이더로 단가·원가·조업도를 흔들면 BEP 수량과 목표이익이 1초 안에 보이고, 차월 추정에 4종 파라미터를 강제 입력받는다.

**FRs covered**: F7.1, F7.2
**NFRs touched**: NFR9
**Architecture binds**: AD-5

---

#### Story 7.1: BEP Slider with 1-Second Recompute

As a **사장님**, I want **단가 슬라이더를 흔들면 BEP 수량과 목표이익이 1초 안에 갱신되는 것**, so that **가격 인상 전 미리 손익분기점을 확인 가능**.

**Acceptance Criteria:**

- **Given** 나는 [시뮬레이션] 화면에서 "단가" 슬라이더를 10,000원 → 12,000원으로 드래그
**When** 마우스 떼는 순간
**Then** 1초 이내에 "BEP 수량: 1,500개 → 1,250개" "예상 이익: 500만원 → 800만원" 카드 갱신
**And** 시뮬레이션은 DB를 건드리지 않음 — 순수 엔진 함수(`simulate_cvp` 등)만 호출
**And** Recharts 막대 차트가 실시간으로 변동 (현재 시나리오 vs 베이스라인)

#### Story 7.2: Next-Month Projection with 4 Required Parameters

As a **사원**, I want **차월(예: 2026-08) 추정 시 차입금·이자율·상승률·세율 4종을 입력해야 [예측 실행]이 활성화되는 것**, so that **필수 가정을 빠뜨리지 않고 예측을 돌림**.

**Acceptance Criteria:**

- **Given** 나는 [차월 추정] 탭에 진입
**When** 4종 파라미터 중 "이자율"만 입력하고 나머지 비움
**Then** [예측 실행] 버튼이 disabled
**And** 4종 모두 채우면 활성화
**And** 파라미터 4종: 차입금(원), 이자율(%), 원가 상승률(%), 법인세율(%)
**And** 추정 결과는 시뮬레이션 카드 + 차트 + "원가 예측 보고서" PDF 다운로드 버튼 3종으로 제공

---

### Epic 8: Budget vs Actual

**Epic goal**: 가상 기간(YYYY-MM#B<n>)으로 예산을 입력해 사전 표준원가계산 + 실적 대조를 보고, 1차 시나리오 1개만 허용, A×B×C×D는 회색 배지로 미구현을 명시한다.

**FRs covered**: F8.1, F8.2
**NFRs touched**: —
**Architecture binds**: AD-24

---

#### Story 8.1: Virtual Budget Period Key + Scenario Lock to One

As a **사장님**, I want **예산을 "2026-07#B1" 같은 가상 기간 키로 입력하고 1차 시나리오 1개만 만들 수 있는 것**, so that **복수 시나리오로 인한 혼선을 막음**.

**Acceptance Criteria:**

- **Given** 나는 [예산] → [신규 시나리오] 클릭
**When** "예산 시나리오 1"을 만들고 추가로 "예산 시나리오 2" 만들기를 시도
**Then** 2번째 시나리오 생성은 거부되고 "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)" 메시지
**And** 첫 시나리오는 `period_key = "2026-07#B1"`로 저장
**And** M8만 virtual key 발급, M11 close는 fiscal key만 잠금

#### Story 8.2: Budget vs Actual Variance Table with ABCD Gray Badge

As a **사장님**, I want **예산-실적 대조표에서 모든 차이 행이 빨강/녹색으로 보이고, A×B×C×D(차이 분석) 컬럼은 회색 배지로 비어 있는 것**, so that **MVP 한계를 사용자가 명확히 인지**.

**Acceptance Criteria:**

- **Given** 나는 "예산-실적 대조" 보고서를 본다
**When** "2026-07"을 본다
**Then** 행마다 (예산 / 실적 / 차액 / 차이율 %) 4컬럼이 표시되고 차이율 ±5% 이상은 노랑, ±10% 이상은 빨강
**And** 5번째 컬럼 "A×B×C×D 원가 차이 분석"은 회색 배지("2차 예정")로 비활성
**And** 비고란에 "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]" 표기

#### Story 8.3: Budget Pre-Standard Cost Preview

As a **사장님**, I want **예산 입력 완료 시 사전 표준원가(pre-standard cost)가 자동 계산되어 보이는 것**, so that **예산 시점의 단가 기준을 미리 잠금**.

**Acceptance Criteria:**

- **Given** 가상 기간 "2026-07#B1"에 예산 입력 완료
**When** [예측] 클릭
**Then** 사전 표준원가표(직접재료·직접노무·제조경비)가 표시되고 `fiscal_period_snapshots`에 `engine_type='budget'`로 저장
**And** 동일 입력 시 동일한 hash (엔진 순수성)
**And** 예산 시점과 실적 시점의 차이는 §9 #20 "예산-실적 차이 명세서"로 출력

---

### Epic 9: ABC / TDABC Engine (Service Business)

**Epic goal**: 서비스 업종 회사가 원가풀 → 활동 → 동인 → 원가대상으로 배부하는 ABC를 사용하고, TDABC에서 CCR을 1원 단위로 계산한다. 자체 public calc endpoint 없음 — M3에서 호출.

**FRs covered**: F9.1, F9.2
**NFRs touched**: NFR16
**Architecture binds**: AD-18·19·21

---

#### Story 9.1: Cost Pool + Activity + Driver 100% Validation

As a **사장님 (서비스 업종)**, I want **원가풀 행 합·활동 열 합·동인 합이 모두 100%가 아니면 [계산]이 잠기는 것**, so that **ABC 데이터 오류를 사전에 차단**.

**Acceptance Criteria:**

- **Given** 나는 [ABC] → [원가풀]에 부서 4개, 각 25%씩 입력
**When** 한 부서를 30%로 변경 → 합 105%
**Then** [계산] disabled + "원가풀 행 합 ≠ 100% (현재 105%)" 메시지
**And** 100%로 되돌리면 다시 활성화
**And** 활동·동인도 동일 가드 (열 합 100% 강제)

#### Story 9.2: ABC Allocation Engine (Single CCR, 1-Won Precision)

As a **사장님**, I want **CCR(자원동인율)이 부서별 원가 ÷ 실제 조업능력 시간으로 1원 단위 계산되는 것**, so that **TDABC 정확도를 보장**.

**Acceptance Criteria:**

- **Given** "여행상품 설계 부서" 원가 1,320만원, 실제 조업능력 400시간
**When** [계산] 클릭
**Then** CCR = `13,200,000 / 400 = 33,000원/시간`으로 1원 단위 계산
**And** 미사용 능력(예: 600시간 중 200시간 미사용)은 별도 행 "미사용능력 6,600,000원"으로 표시
**And** CCR 계산은 `CCRPort.compute(tenant_id, period_key, department_id)` 한 함수만 보유 (AD-21)

#### Story 9.3: ABC Calculation Routed via M3 Endpoint

As a **platform engineer**, I want **M9 ABC 계산이 자체 public endpoint 없이 M3의 `POST /api/v1/calc` 안에서 dispatch되는 것**, so that **계산 진입점이 단일하고 트랜잭션 일관성이 보장됨**.

**Acceptance Criteria:**

- **Given** 서비스 업종 테넌트가 [계산] 클릭
**When** POST `/api/v1/calc` 호출됨
**Then** AD-19 단일 진입점이 업종 = 서비스이면 M9의 ABC port를 내부 호출
**And** M9는 public REST endpoint를 노출하지 않음 (CLI/문서 검사)
**And** 결과는 동일하게 `fiscal_period_snapshots`에 `engine_type='abc'`로 commit됨

#### Story 9.4: ABC Report #21 (Cost Object Breakdown)

As a **사장님**, I want **§9 #21 "원가대상별 원가 집계표"가 ABC 결과를 보여주는 것**, so that **여행상품/물류 서비스별 원가 구조를 확인**.

**Acceptance Criteria:**

- **Given** 나는 [보고서] → [원가대상별 원가 집계표] 클릭
**When** 서비스 업종 테넌트에서 진입
**Then** `product_id`(원가대상)별 행 + 원가풀·활동·동인·배부액 4컬럼 표시
**And** 제조업 테넌트에서는 `engine_type='trad'`만 표시되고 ABC 컬럼은 회색("비활성")
**And** KRW/USD 동시 표시 (F5.2)

---

### Epic 10: AI Assistance

**Epic goal**: AI가 문서를 추출하고 인사이트 3개를 제공하며, 그 어떤 경우에도 확정 입력은 사용자가 직접 쓴 값만 적용된다. 마감 데이터 변경 시 캐시는 자동 무효화.

**FRs covered**: F10.1, F10.2
**NFRs touched**: NFR11
**Architecture binds**: AD-7·17·25

---

#### Story 10.1: AI Document Extraction to Input Drafts

As a **사장님**, I want **AI가 업로드한 PDF·Excel에서 6종 입력값을 추출해 `input_drafts`로 저장하고, 확정 입력은 사용자 수정본만 승격되는 것**, so that **AI가 잘못 쓴 값이 계산에 직접 안 들어감**.

**Acceptance Criteria:**

- **Given** 나는 PDF 1장(거래명세서 6월분)을 업로드
**When** AI 추출이 완료됨
**Then** 추출값은 `input_drafts` 테이블에 `state='draft'`로 저장됨
**And** UI에서 "AI 초안" 카드로 보여지고 사용자가 확정해야 `confirmed_inputs`로 승격
**And** 확정 입력은 사용자가 화면에서 수정한 값만 적용 (AD-17 promotion port)
**And** M10이 `confirmed_inputs`에 직접 쓰려고 하면 권한 거부 + 카운터 증가

#### Story 10.2: Three-Insight Cache Policy

As a **사장님**, I want **AI 인사이트 3개(원가 절감 후보·이상 패턴·예측)가 마감 완료 시점에 잠기고 다음 마감 시작 시점까지 보존되는 것**, so that **빠른 응답 + 데이터 일관성**.

**Acceptance Criteria:**

- **Given** "2026-07" 마감 완료
**When** AI 인사이트 조회
**Then** 3개 인사이트가 캐시에서 즉시 응답 (NFR11 P95 ≤ 30s 내외)
**And** 캐시 키 = `(tenant_id, period_key, calculation_result_hash)` (AD-25)
**And** "2026-08" 입력 시작 시점까지 보존
**And** 마감 데이터 변경(AD-22 reversal, Epic 11) 시 즉시 폐기 + 재계산
**And** 본 Story에서는 Epic 4 calc-hash 기반 무효화만 wire, Epic 11 close/reopen trigger는 Epic 11 Story 11.1/11.3에서 추가 wiring

#### Story 10.3: AI Reference vs Auto Analysis Badge Separation

As a **사장님**, I want **AI 의견과 자동 분석 의견이 시각적으로 다른 배지로 분리되는 것**, so that **무엇이 규칙이고 무엇이 AI 추측인지 구분 가능**.

**Acceptance Criteria:**

- **Given** 보고서 화면에서 "원가 분석 의견" 섹션 진입
**When** 표시됨
**Then** 자동 분석(고정 템플릿: "직접재료비 비중 45% > 업종 평균 30%")은 파란 배지 "📊 자동 분석" (AD-7 `auto_analysis`)
**And** AI 의견(예: "이번 달 원자재 가격 인상 영향으로 추정")은 보라 배지 "🤖 AI 참고(검증 필요)"
**And** AI 배지 클릭 시 "AI는 비권위적입니다 — 확정 책임은 사용자에게" 툴팁

#### Story 10.4: AI Promotion Port Idempotency

As a **platform engineer**, I want **`InputPromoter.promote()`가 `(tenant_id, period_key, source_draft_id)` 단위로 idempotent인 것**, so that **중복 승격으로 인한 입력 중복이 안 생김**.

**Acceptance Criteria:**

- **Given** 같은 `draft_id`에 대해 promote 호출 2회
**When** 2번째 호출
**Then** 1번째와 동일한 `confirmed_inputs` 결과 반환 (no duplicate insert)
**And** `input_drafts.state`는 `'promoted'`로 전이 (1회만)
**And** `audit_logs`에 promote 이벤트 2행 append (actor + draft hash + ts)

---

### Epic 11: Monthly Close & Audit

**Epic goal**: 부문분할→제조→ABC→공동 순서로 부분 마감 없이 잠그고, 이후 수정은 역분개로만 처리된다. 원본은 절대 안 바뀐다.

**FRs covered**: F11.1, F11.2
**NFRs touched**: NFR5
**Architecture binds**: AD-2·6·16·20·22·25

---

#### Story 11.1: Close Sequence Lock (Divisions → Manufacturing → ABC → Common)

As a **사장님**, I want **마감 순서가 부문분할→제조→ABC→공동 순서로 강제되고 부분 마감이 안 되는 것**, so that **한 단계만 잠그는 사고를 방지**.

**Acceptance Criteria:**

- **Given** 나는 [마감] 화면에서 "2026-07" 마감 시도
**When** 부문분할 단계만 완료 후 [마감] 클릭
**Then** "제조·ABC·공동 단계 미완료 — 전체 완료 후 마감 가능" 메시지 + 잠금
**And** 4단계 모두 완료 시에만 마감 진입
**And** 마감 완료 시 `fiscal_periods.status='closed'`로 전이, 이후 INSERT 거부 (AD-6)

#### Story 11.2: Snapshot Persistence on Close

As a **사장님**, I want **마감 완료 시점에 모든 계산 결과가 스냅샷으로 고정되어 이후 입력 변경에도 안 바뀌는 것**, so that **마감본 = 영구본**.

**Acceptance Criteria:**

- **Given** "2026-07" 마감 완료
**When** 이후 "2026-07"의 입력값(예: 출고량)을 수정 시도
**Then** "이미 마감된 기간입니다 — 역분개로 처리하세요" 메시지로 거부
**And** 마감본의 snapshot hash는 `fiscal_period_snapshots`에 영구 보존
**And** 보고서(Epic 6)는 마감본만 읽음 (M3 + M11만 writer)

#### Story 11.3: Reversal Sequence (Sign-Negating + Corrected)

As a **회계사**, I want **마감 후 오류를 발견하면 역분개로만 수정 가능한 것**, so that **원본이 절대 안 바뀌어 감사 추적이 보장됨**.

**Acceptance Criteria:**

- **Given** "2026-07" 마감 완료 후 오류 발견
**When** [역분개] 클릭 + 사유 입력
**Then** (1) 부호 반전 row 1개 INSERT (`reverses_event_id` link) + (2) corrected row INSERT (`correction_group_id` link) — 원본 row 변경 없음 (AD-22)
**And** `(tenant_id, reverses_event_id)` unique 제약 보장
**And** 재무 효과는 `committed → reversed` 상태로 정확히 0에 수렴
**And** M10 캐시 무효화 notification 자동 발행 (AD-25)

---

### Epic 12: Account & Security Operations

**Epic goal**: 2FA·역할 권한·자동 백업·계정 해지까지 운영자가 직접 관리할 수 있고, 새벽 1인 운영자도 4시간 안에 복구 가능하다.

**FRs covered**: F12.1, F12.2, F12.3
**NFRs touched**: NFR1·2·3·4·5·6·7
**Architecture binds**: AD-3·9·10

---

#### Story 12.1: 2FA Mandatory Gate to M2 Entry

As a **사장님**, I want **2FA 미설정 시 [월 입력] 화면 진입이 차단되는 것**, so that **내 회사 데이터가 약한 인증으로 새는 사고를 방지**.

**Acceptance Criteria:**

- **Given** 나는 로그인 후 [월 입력] 진입 시도
**When** 2FA 미등록 상태
**Then** "2FA 설정이 필요합니다 — [설정하기]" 모달이 뜨고 [월 입력] 차단
**And** 2FA 등록(TOTP) 완료 후에만 진입 허용
**And** AD-10: 역할 owner/member/viewer/consultant_proxy 권한별 진입 제어

#### Story 12.2: Daily Auto-Backup + JSON Self-Download

As a **운영자**, I want **매일 자동 백업이 Supabase Seoul에 쌓이고 JSON으로 셀프 다운로드 가능한 것**, so that **새벽 4시간 안에 수동 복구 가능**.

**Acceptance Criteria:**

- **Given** 일 1회 자동 백업 cron
**When** 매일 KST 02:00 실행
**Then** `(tenant_settings, products, bom, monthly_inputs, fiscal_period_snapshots, audit_logs)`이 JSON으로 Supabase Storage Seoul에 저장
**And** 보관 30일 자동 + 분기마다 1년 보존 (NFR4)
**And** 운영자 UI에서 "최근 7일 백업 다운로드" 버튼으로 JSON 즉시 다운로드
**And** 다운로드 JSON은 동일 schema로 RLS bypass 없이 복원 가능

#### Story 12.3: Account Deletion with Retention Consent

As a **사장님**, I want **계정 해지 시 보관일수 + 삭제 동의를 명시적으로 받는 것**, so that **개인정보 보호 의무 준수 + 데이터 복구 시점 명확화**.

**Acceptance Criteria:**

- **Given** 나는 [설정] → [계정 해지] 클릭
**When** 해지 진행
**Then** "데이터 보관일수: 30일 / 30일 후 완전 삭제 / 동의 체크 필수" 모달 표시
**And** 동의 체크 없이 [해지] 비활성
**And** 해지 요청 시 `tenants.status='pending_deletion'`, 30일 후 완전 삭제 (NFR5 감사로그는 5년 별도 보존)
**And** 동의 체크, 해지 요청 ts가 `audit_logs`에 append

---

## Story Count Summary

| Epic | Stories | FRs Covered | AD Touched |
|------|---------|-------------|------------|
| Epic 0 | 4 | — | AD-1·3·8·9·10·11·14·15·23 |
| Epic 1 | 3 | F0.1·F0.2·F0.3 | AD-3·7·23 |
| Epic 2 | 3 | F1.1·F1.2 | AD-6·18·23 |
| Epic 3 | 3 | F2.1·F2.2·F2.3 | AD-13 |
| Epic 4 | 4 | F3.1·F3.2·F6.1·F6.2 | AD-4·5·12·16·19·20·21 |
| Epic 5 | 3 | F4.1·F4.2 | AD-2·6·18·22 |
| Epic 6 | 3 | F5.1·F5.2·F5.3 | AD-8·16·18·20·24 |
| Epic 7 | 2 | F7.1·F7.2 | AD-5 |
| Epic 8 | 3 | F8.1·F8.2 | AD-24 |
| Epic 9 | 4 | F9.1·F9.2 | AD-18·19·21 |
| Epic 10 | 4 | F10.1·F10.2 | AD-7·17·25 |
| Epic 11 | 3 | F11.1·F11.2 | AD-2·6·16·20·22·25 |
| Epic 12 | 3 | F12.1·F12.2·F12.3 | AD-3·9·10 |
| **Total** | **43** | **30 FR 100%** | **25 AD ≥ 1회** |

**FR Coverage Map (final)**:
- Epic 0: (none — infra)
- Epic 1: F0.1, F0.2, F0.3
- Epic 2: F1.1, F1.2
- Epic 3: F2.1, F2.2, F2.3
- Epic 4: F3.1, F3.2, F6.1, F6.2
- Epic 5: F4.1, F4.2
- Epic 6: F5.1, F5.2, F5.3
- Epic 7: F7.1, F7.2
- Epic 8: F8.1, F8.2
- Epic 9: F9.1, F9.2
- Epic 10: F10.1, F10.2
- Epic 11: F11.1, F11.2
- Epic 12: F12.1, F12.2, F12.3

**Non-Goal 10개** (§14.B): Epic 범위 의도적 제외 — 제조부문ABC (Epic 9 회색 배지), 복수예산 (Epic 8 1개 잠금), A×B×C×D 엔진 (Epic 8 회색 배지), CPA 정밀 (회색), 다국어환산 (NFR18 ko-KR만), 멀티에이전트 (Epic 10 단일), 환경원가 (미포함), 모바일앱 (반응형 웹만), 부채자금 (미포함), ERP동기화 (미포함).

**AD Touch Coverage**: 25 AD 모두 1개 이상 Epic에서 bind. 미사용 AD = 0.

**Story Independence (intra-epic)**: 각 Epic 내 story는 이전 story 완료로만 동작 가능. 미래 story 의존 0건.

---

## Final Validation Report (Step 4)

| Check | Result | Evidence |
|-------|--------|----------|
| **FR Coverage 30/30** | ✅ PASS | F0.1~F12.3 모두 story에 매핑, 미배정 0건 |
| **AD Coverage 25/25** | ✅ PASS | AD-1~25 모두 ≥ 1 Epic에서 bind, 미사용 0건 |
| **NFR Coverage 20** | ✅ PASS | NFR1~20 모두 story에 distribute (보안 5·성능 3·볼륨 4·결정론 2·i18n 1·빌링 1·플랫폼 1 등) |
| **Non-Goal 명시** | ✅ PASS | §14.B 10개 [NON-GOAL] 모두 Epic 8/9/NFR18/20 + 비포함 명시 |
| **Epic Independence** | ✅ PASS | Epic 0→1→2→...→12 순방향 의존, 순환 0건 |
| **Story Independence (intra-epic)** | ✅ PASS | 모든 Epic의 story N.M이 N.(M-1) 이하만 사용 |
| **Cross-epic Story dep** | ⚠️ 1건 doc | Story 10.2 ↔ Epic 11 close trigger — AC 보강 명시 ("본 Story에서는 calc-hash만 wire, Epic 11에서 trigger 추가 wiring") |
| **File Churn Check** | ✅ PASS | M3+M6 → Epic 4 합치고 rationale 명시. 그 외 모듈 디렉터리 1:1 매핑으로 충돌 없음 |
| **Starter Template** | ✅ PASS | Architecture = Greenfield (자체 구현). Epic 0 Story 0.1이 monorepo 스캐폴드 담당 |
| **DB Tables per Story** | ✅ PASS | 각 story는 "필요한 table만 생성" 원칙. 초기 migration은 Epic 0 Story 0.2 (tenants/users/tenant_settings), 이후 story에서 점진 확장 |
| **User Value First** | ✅ PASS | Epic 0 = Platform(operator value), Epic 1~12 = user value 명시 |
| **Story Sizing** | ✅ PASS | 모든 story 단일 dev agent 작업 단위 (1~3일) |
| **Given/When/Then AC** | ✅ PASS | 43 story 모두 Given/When/Then 형식 채택 |
| **Template Structure** | ✅ PASS | Overview / Requirements Inventory / FR Coverage Map / Epic List / Epic Details & Stories / Final Validation Report 6섹션 |
| **CE Output File Format** | ✅ PASS | `{planning_artifacts}/epics.md` = `_bmad-output/planning-artifacts/epics.md` |
| **Frontmatter** | ✅ PASS | stepsCompleted: [1, 2, 3] |

**Validation Verdict**: ✅ **READY FOR DEVELOPMENT**

13 Epic · 43 Story · 30 FR · 25 AD · 20 NFR · 10 Non-Goal 명시. IR (Implementation Readiness) 단계 진입 가능.

**CE Workflow Output**: `epics.md` 확정. 다음 단계: `bmad-check-implementation-readiness` 또는 `bmad-sprint-planning`.

