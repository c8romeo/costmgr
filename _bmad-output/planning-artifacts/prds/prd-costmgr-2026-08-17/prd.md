---
title: "Epic 10 — AI Assistance PRD Entry (costmgr)"
status: draft
created: 2026-08-17
updated: 2026-08-17
parent_prd: "_bmad-output/planning-artifacts/prd.md v2.0 (final, 2026-07-25)"
epic: 10
entry_mode: cj-style 25번째 epic 연속 = Epic 10 1번째 진입점
split_pattern: "(b) 4-story + retro 5번째 진입점" (Epic 8 retro §7 A23 권장안)
carries: "A31-A36 wire results (Epic 9 retro 9-6 follow-up sprint done 2026-08-17)"
capability_matrix: "v1.20 → v1.21 (AI_INSIGHT capability 1 NEW, industry-agnostic)"
---

# Epic 10 — AI Assistance PRD (costmgr)

> **Scope.** 본 문서는 master PRD v2.0 (`_bmad-output/planning-artifacts/prd.md`)의
> Epic 10 슬롯을 4-story + retro 5번째 진입점 cj-style 패턴으로 확정하는 Epic-level
> PRD extension이다. master PRD를 보완하는 형태로 본 PR만으로 Epic 10 wire의
> commitment가 성립하도록 작성한다. 본 PRD는 Epic 10 진입 시점에 cj-style 25번째
> epic 연속 = Epic 10 1번째 진입점이다.
>
> **Master PRD 정합.** 본 PRD는 master PRD §8.1 M10 + §12 AI 3종 + §14.B NON-GOAL
> #6과 모순되지 않으며, §F10.1·§F10.2·§8.1 M10 module acceptance criteria를
> 4-story PRD-level AC로 상세화하고, capability matrix v1.21 변경과 결정 이력을
> 부록에 보존한다.

---

## 1. Epic 10 한 문장 정의

> **"AI가 초안을 만들고, 확정은 사람이 한다 — 인사이트 3개 캐시 + 자동 분석과 AI 참고 분리 + 승격 포트로 안전하게 검증된 입력만 계산에 진입시키는, 원가 계산을 위한 AI 보조 영역"**

- AD-7 (AI non-authoritative) + AD-17 (promotion port) + AD-25 (cache invalidation) bind
- AI는 **`input_drafts`만** 쓴다. `confirmed_inputs`는 사용자가 화면에서 수정한 값만 승격 (AD-17)
- 인사이트 3개는 마감 완료 시점에 lock + 다음 마감 시작 시점까지 보존 (AD-25)
- 자동 분석(고정 템플릿)과 AI 의견(검증 필요)이 시각적으로 다른 배지로 분리 (AD-7)

---

## 2. User Journey — UJ-AI (신규 가입자 AI 온보딩 보강 + 회차 운영 중 AI 보조)

### UJ-AI. 신규 가입자 AI 온보딩 (master PRD §2.A UJ-4 보강)

- **Protagonist**: 박영수, 48세, 식품 제조+유통 겸영 업체 대표 (master PRD UJ-1과 동일).
  AI 추출 정확도가 떨어지는 파일(예: 사진으로 찍은 사업자등록증)을 가지고 M0 진입.
- **트리거**: master PRD UJ-4 step 1 (신규 가입 직후 M0 진입).
- **핵심 단계**:
  1. M0 진입 → PRD master UJ-4 step 1 (업종 4지선다).
  2. **Story 10.1** — 사진/PDF 업로드 시 `input_drafts` 테이블에 `state='draft'`로 AI 추출.
  3. UI는 "AI 초안" 카드로 표시하고 신뢰도 70% 미만은 빨강 배지 (master PRD M0-c 정합).
  4. **Story 10.3** — 자동 분석 의견 "📊 자동 분석" + AI 의견 "🤖 AI 참고(검증 필요)" 배지로 분리 (UJ-AI step 4 시각화).
  5. **Story 10.4** — 사용자가 검토·수정 후 `InputPromoter.promote()` 호출 (단일 진입점 AD-17) → `confirmed_inputs` 승격. 동일 draft_id 재호출 시 idempotent (no duplicate insert).
  6. M2 첫 입력 — 일부는 draft에서 자동 이관, 일부는 사용자 직접 입력 (master PRD UJ-4 step 5 유지).
- **종착상태**: 모든 추출 항목 사용자 확정 + 첫 월 데이터 입력 가능한 상태.
- **예외 경로**:
  - 추출 신뢰도 전 항목 < 50% → 사용자 수동 입력 폴백 안내 (master PRD UJ-4 정합).
  - **Story 10.2** — 계산 직후 인사이트 3개 자동 생성, 마감 완료 시점에 lock (NFR11 P95 ≤ 30s).

### UJ-AI 운영 (master PRD §2.A UJ-1 step 5 AI 보강)

- **Protagonist**: 이미숙, 42세, 여행상품 ABC 운영 대표 (master PRD UJ-2과 동일).
  마감 완료 후 다음 달 초 인사이트 조회.
- **핵심 단계**:
  1. [마감] 완료 → `fiscal_period_snapshots.state='committed'` 전이 (Epic 11 AD-16).
  2. **Story 10.2** — AD-25 cache key = `(tenant_id, period_key, calculation_result_hash)`
     로 lock + 즉시 응답 (NFR11 P95 ≤ 30s).
  3. **Story 10.3** — `Story 10.2`에서 제시된 3개 인사이트 카드별로
     "📊 자동 분석 (고정 템플릿)"과 "🤖 AI 참고 (검증 필요)" 배지 분리 표시.
  4. [보고서] 진입 시 모든 보고서 의견 section에 동일 배지 분리 (master PRD §9 #7
     "원가분석표" 정합).

---

## 3. Functional Requirements — §F10.1 + §F10.2 (상세화)

### F10.1 Three-Insight Cache Policy (master PRD §8.1 M10-(a) 확장)

- **(a)** 시스템은 `fiscal_period_snapshots.state='committed'` 전이 시점에
  `ai_cache` 키 `(tenant_id, period_key, calculation_result_hash)` 3-tuple로
  **인사이트 질문 3개 + 답변 3개**를 lock 한다 (NFR11 P95 ≤ 30s).
  - 본 Story(10-2)는 Epic 4 calc-hash 기반 AD-25 publisher 1 channel 만 wire 한다.
  - **Epic 11 close / reopen trigger 의존**: `cache_invalidation_log` 채널
    EXTENSION + close / reopen 시 발행되는 publisher 추가 wiring은
    Epic 11 Story 11.1/11.3에서 별도 spec 진입 시점에 wire (CR 1.1 forward-lock).
- **(b)** 시스템은 cache hit 시 마지막 마감 완료 시점부터 다음 마감 시작
  시점까지 보존된 인사이트를 반환하고, 동일 hit은 0~수십 ms 내 응답한다
  (cache 없으면 NFR11 SLO 내 cold compute).
- **(c)** 시스템은 마감 데이터 변경(AD-22 reversal INSERT, Epic 11) 시
  AD-25 publisher가 invalidation log를 emit 하면 adapter가
  `WHERE tenant_id=? AND period_key=?` 매칭 cache entry를 즉시 폐기한다.
- **(d)** 시스템은 `cache_invalidation_log` 채널에 `ai_cache` 외 채널이
  추가되어도 본 캐시만 영향받지 않도록 channel-specific invalidation
  filter를 강제한다 (`channel = 'ai_cache'` filter).

### F10.2 AI Reference vs Auto Analysis Badge Separation (master PRD §8.1 M10-(b) 확장)

- **(a)** 시스템은 보고서 의견 section 진입 시 모든 문장별 `source_kind`
  (`auto_analysis` | `ai_reference`)를 함께 렌더링하고:
  - `source_kind='auto_analysis'` → 파란 배지 "📊 자동 분석" + tooltip
    "이 의견은 고정 템플릿입니다" (master PRD §12 "자동 분석" 정합).
  - `source_kind='ai_reference'` → 보라 배지 "🤖 AI 참고(검증 필요)" + tooltip
    "AI는 비권위적입니다 — 확정 책임은 사용자에게" (master PRD §12 "AI 참고"
    + AD-7 verbatim).
- **(b)** 시스템은 `auto_analysis` / `ai_reference` 키 외 value (예:
  `human_authored` 등) 도착 시 strict reject + 1행 counter increment를 wire
  한다 (master PRD §A11 시스템은 틀리지 않는다 / hover 후 미변경 = 안전).
- **(c)** 시스템은 SM-3a "계산 결과 변경 시도 = 0건" 별도 tracking을 위해
  `auto_analysis` 의견 수정 시도도 동일 카운터로 추적한다 (master PRD §2.B
  + AD-7 "M10 attempts to write confirmed-input tables are denied and counted").
- **(d)** 시스템은 `source_kind` 강제 검증 실패 시 1-line ko-KR 메시지로
  reject (예: "분석 의견 출처가 불분명합니다") + counter 증가 + 200 OK
  envelope.

---

## 4. Epic 10 4-Story Acceptance Criteria (PRD-Level)

### Story 10.1 — AI Document Extraction to Input Drafts (PRD §F10.1 + AD-7·17 verbatim)

**As a 신규 가입 사장님**, I want **AI가 업로드한 PDF/Excel에서 6종 입력값 중
추출 가능한 항목을 `input_drafts`로 저장하고, 확정 입력은 사용자가 화면에서
수정한 값만 `confirmed_inputs`로 승격되는 것**, so that **AI가 잘못 쓴 값이
계산에 직접 들어가는 일이 없다** (master PRD §8.1 M10 정합).

- **Given** 나는 [M0] 진입 후 사진 1장(사업자등록증)을 업로드했다
- **When** AI 추출이 완료됨
- **Then** 추출값은 `input_drafts` 테이블에 `state='draft'`로 저장됨
  (AD-7 verbatim: "AI output is stored only as `input_drafts`")
- **And** UI는 "AI 초안" 카드로 보여지고 사용자가 확정해야 `confirmed_inputs`
  로 승격 (master PRD §2.A UJ-4 정합)
- **And** **M10이 `confirmed_inputs`에 직접 쓰기 시도 → 거부 + 카운터 증가**
  (AD-7 verbatim: "M10 attempts to write confirmed-input tables are denied
  and counted (target zero)")
- **And** 신뢰도 < 70% 필드는 빨강 배지 + 사용자 확정 강제 (master PRD §8.1 M0-c)
- **And** Story 10.4 AD-17 promotion port 만 `confirmed_inputs` 쓰기 권한 보유

### Story 10.2 — Three-Insight Cache Policy (PRD §F10.1 verbatim + AD-25 verbatim)

**As a 사장님**, I want **AI 인사이트 3개(원가 절감 후보·이상 패턴·예측)가
마감 완료 시점에 lock 되어 다음 마감 시작 시점까지 보존되는 것**, so that
**빠른 응답 + 데이터 일관성** (master PRD §2.A UJ-1 step 5 정합).

- **Given** "2026-07"이 `fiscal_period_snapshots.state='committed'`로
  전이되었다 (Epic 4 M3 atomic COMMIT)
- **When** AI 인사이트 조회
- **Then** 3개 인사이트 질문 + 답변이 `ai_cache` 채널 lock 되어 즉시 응답
  (NFR11 P95 ≤ 30s)
- **And** cache key = `(tenant_id, period_key, calculation_result_hash)`
  (AD-25 verbatim: "M10 cache key: (tenant_id, period_key,
  calculation_result_hash)")
- **And** **Epic 11 close / reopen trigger는 본 Story 범위 외**: 본 Story는
  Epic 4 AD-25 publisher 1 channel (`ai_cache`) 만 wire, Epic 11 trigger는
  Story 11.1/11.3 진입 시점에 publisher channel EXTENSION (CR 1.1 forward-lock).
- **And** 마감 데이터 변경 (AD-22 reversal INSERT, Epic 11 wire) 시 즉시
  폐기 + 재계산 (Epic 11 wire 시점; 본 Story 범위는 변경 event 없을 때의
  정상 cache lifecycle 만 wire)
- **And** `cache_invalidation_log.channel = 'ai_cache'` filter 가 강제됨
  (cross-channel contamination 방지, F10.1-(d))

### Story 10.3 — AI Reference vs Auto Analysis Badge Separation (PRD §F10.2 verbatim)

**As a 사장님**, I want **보고서의 자동 분석 의견(고정 템플릿)과 AI 의견이
시각적으로 다른 배지로 분리되는 것**, so that **무엇이 규칙이고 무엇이 AI
추측인지 구분 가능** (master PRD §12 정합).

- **Given** 나는 [보고서] → "원가분석표" (§9 #7)의 "원가 분석 의견" section
  진입
- **When** 표시됨
- **Then** `source_kind='auto_analysis'` 의견은 **파란 배지 "📊 자동 분석"**
  (master PRD §12 verbatim)
- **And** `source_kind='ai_reference'` 의견은 **보라 배지 "🤖 AI 참고
  (검증 필요)"** + tooltip "AI는 비권위적입니다 — 확정 책임은 사용자에게"
  (AD-7 verbatim)
- **And** `source_kind` 미매칭 value → strict reject + counter (SM-3a 정합)
- **And** AI 배지 클릭 시 tooltip 노출 (master PRD §12 정합)
- **And** 동일 배지 분리는 UJ-AI 운영 step 3 (cache 조회 후 인사이트 표시)
  에서도 동일 강제

### Story 10.4 — AI Promotion Port Idempotency (PRD §AD-17 verbatim + epics.md Story 10.4 AC 정합)

**As a 플랫폼 엔지니어**, I want **`InputPromoter.promote()`가
`(tenant_id, period_key, source_draft_id)` 단위로 idempotent 인 것**, so that
**중복 승격으로 인한 입력 중복이 발생하지 않음** (AD-17 verbatim).

- **Given** 같은 `source_draft_id`에 대해 `InputPromoter.promote()` 호출 2회
- **When** 2번째 호출
- **Then** 1번째와 동일한 `confirmed_inputs` 결과 반환 (no duplicate
  insert; AD-17 verbatim "Idempotent on (tenant_id, period_key,
  source_draft_id)")
- **And** `input_drafts.state`는 `'promoted'`로 1회만 전이 (idempotent)
- **And** `audit_logs`에 promote 이벤트 2행 append (actor + draft hash +
  ts; CR 1.1 audit-first INSERT)
- **And** Story 10.1 AD-17 정합: M10은 `confirmed_inputs`에 직접 쓰기 불가
  (counter increment; target zero)

---

## 5. Architectural Decision Bind (AD-7 / AD-17 / AD-25 verbatim + Epic 0~9 carry-over)

### 5.1 Epic 10 신규 bind

| AD | 내용 | Story bind |
|---|---|---|
| **AD-7 AI non-authoritative** (verändert master PRD) | AI output → `input_drafts` only. `confirmed_inputs` 도달은 **AD-17 경로만**. AI commentary `source_kind='ai_reference'`. 자동 분석 `source_kind='auto_analysis'`. M10 attempts to write confirmed-input tables → denied + counted (target 0). | 10-1·10-3·10-4 |
| **AD-17 AI draft promotion port** | Only M2 may call `InputPromoter.promote(tenant_id, period_key, source_draft_id) -> MonthlyInput`. Idempotent on `(tenant_id, period_key, source_draft_id)`. Promotion retains draft with `state='promoted'`, records actor + draft hash in audit_logs, writes canonical confirmed-input shape. M10 never writes confirmed inputs. | 10-1 + 10-4 |
| **AD-25 AI insight cache invalidation** | M10 cache key: `(tenant_id, period_key, calculation_result_hash)`. New AD-4 commit, AD-22 reversal insert, or M11 reopen emits one DB notification per `cache_invalidation_log` channel. M10 adapter consumes it and invalidates matching entries. Application polling + input-write-only invalidation forbidden. | 10-2 |

### 5.2 Epic 10 carry-over (A28/A29/A30 forward-lock 3-chain, Epic 8 retro §7 검증)

- **A28** (Epic 9 Story 9-2 wire DONE): CCR ↔ Activity ↔ Cost Object Breakdown
  3-way wire. **Epic 10 wire 진입 시점에 `packages/cost_engine/abc_engine.py`
  surface cross-import 0건 정합 보존** (A26 Option A 정합).
- **A29** (Epic 9 Story 9-3 wire DONE): M3 dispatch EXTENSION + Capability
  dual-route `require_any_capability(COST_CALCULATION, ABC_CALCULATION)` ANY-OF +
  Discriminated union envelope `CalcResponse | CalcAbcResponse` with
  `engine_type: Literal["trad", "abc"]` tag. **Epic 10 INSERT route 동일
  11-step pipeline 패턴 적용** (audit-first INSERT → snapshot → verification →
  COMMIT).
- **A30** (Epic 9 Story 9-4 wire DONE): SHARED `packages/services/m5_reports/
  pdf_generator.py` Discriminated union `report_id: Literal[15..21]` factory.
  **Epic 10 첫 reuse case는 A31 결정 (Report #15 wire 진입 시점)**. 본 Epic 10
  진입 시점에는 A30 SHARED factory 보존 확인만.

### 5.3 NFR Touch

- **NFR11** (AI P95 ≤ 30s): 10-2 cache hit sub-100ms, cold compute NFR11 SLO.
- **NFR16** (engine purity): Epic 10 INSERT는 service layer 만; pure kernel
  신규 surface 없음.
- **NFR18** (ko-KR-only 1차): 10-3 배지 tooltip은 한국어만 (master PRD §13.1
  정합).
- **NFR8** (감사로그 5년 append-only): 10-4 promote event 2행 append (AD-7
  + AD-17 정합).

---

## 6. Capability Matrix v1.21 Update (Single Capability)

### 6.1 추가 capability: `AI_INSIGHT`

```yaml
Capability.AI_INSIGHT:
  description: "AI 추출·인사이트·승격 포트 + cache invalidation 통합 capability"
  granted_to:
    - manufacturing           # CR 12-1 L4 precedent: cross-cutting 인프라
    - service                 # AI는 업종 무관 cross-cutting 인프라
    - manufacturing_service   # 겸영
    - manufacturing_service_other  # 겸영+기타
  industry_agnostic: true  # 4-industry grant
  story_coverage:
    - "10-1"  # extraction → input_drafts (POST /api/v1/ai/extract)
    - "10-2"  # Three-Insight Cache (GET /api/v1/ai/insights + AD-25 invalidation)
    - "10-3"  # badge separation (GET /api/v1/ai/comments source_kind discriminator)
    - "10-4"  # Promotion Port idempotency (POST /api/v1/ai/promote)
  precedent: "CR 12-1 L4 (TWO_FACTOR_AUTH industry-agnostic), CR 12-1 L4
              (BACKUP_EXPORT industry-agnostic), CR 12-1 L4 (BUDGET_SCENARIO
              industry-agnostic) — AI는 cross-cutting 인프라로 4-industry grant"
  capability_matrix_version: "v1.21 (v1.20 + AI_INSIGHT row 1 NEW)"
```

### 6.2 기존 `AI_EXTRACT` capability 행과의 관계

- `AI_EXTRACT` (master PRD §8.1 M0-c + Story 1.3 wire already) = **신규 가입
  온보딩 추출** 한정. 1.3 wire 시점에 capability row 이미 4-industry grant.
- `AI_INSIGHT` (Epic 10 v1.21 신규) = **Epic 10 전체 (10-1~10-4 wire)** 통합
  capability. `AI_EXTRACT` 와 별개 row 신설 (capability matrix v1.21 =
  v1.20 + 1 NEW row).
- 한 row 신설만 추가 (CR 11-3 즉시 sweep 회피 패턴 — Epic 9 9-1 wire 시
  `ABC_CALCULATION` 1개로 9-2/9-3/9-4 4 stories dispatch 와 동일 패턴).

### 6.3 Drift detector

- 신규: `tests/integration/test_capability_matrix_v1_21_drift.py` (P-015 SSOT
  pattern; ABC_CALCULATION row 12 cases precedent).
- 4-industry grant parity 정합 (manufacturing / service / manufacturing_service
  / manufacturing_service_other 모두 ✅).
- enum ↔ docs ↔ 4-industry grants ↔ ALLOWED_SERVICE_SUBMODULES (m10_ai 신규
  submodule 등록, CR 11-3 D-2) parity.

---

## 7. 결정 이력 — Epic 9 Retro A23~A36 (9-6 follow-up sprint wire DONE 2026-08-17)

> 본 섹션은 Epic 9 retro 결정 사항을 Epic 10 PRD 슬롯에 verbatim 보존한다.
> 출처: `_bmad-output/implementation-artifacts/epic-9-retro-2026-08-17.md`
> §5, §7, §11. Epic 9 9-7 follow-up sprint (atomic commit `146a7da`) 으로 wire DONE.

### 7.1 Epic 8 Retro Follow-through (A23~A27 — Epic 9 wire 시 결정)

| ID | 결정 | Epic 10 follow-through |
|---|---|---|
| **A23** | Epic 9 cj-style (b) 4-story + retro 5번째 진입점 | **Epic 10 동일 (b) 4-story + retro 5번째 진입점 패턴 미러** |
| **A24** | capability matrix v1.18 — Epic 9 capability 1 NEW | **Epic 10 capability matrix v1.21 — AI_INSIGHT 1 NEW** |
| **A25** | A19 cohesion pattern 6 surface = `abc_engine.py` | Epic 10 wire 시점에 surface 9 진입 (= Report #15 wire pdf_generator EXTENSION, A33 결정) 또는 별도. Epic 10 자체는 신규 pure kernel surface 없이 service layer + frontend 위주 |
| **A26** | Epic 9 8-3 honestly DEFER #4 해소 (2026-08#P1) | Epic 10 carry-over 보존 (cross-import 0건 정합) |
| **A27** | A19 follow-up sprint for 8 honestly DEFER | Epic 10 진입 시점에 Epic 9 honestly DEFER profile = mixed (4 categories — A34 결정 적용) |

### 7.2 Epic 9 Retro 신규 결정 (A28~A36 — Epic 9 wire 시 또는 retro 신규)

| ID | 결정 | Epic 10 follow-through |
|---|---|---|
| **A28** | CCR ↔ Activity ↔ Cost Object Breakdown 3-way wire (9-2 DONE) | Epic 10 INSERT route 동일 11-step pipeline 패턴 |
| **A29** | M3 dispatch + Capability dual-route + Discriminated union (9-3 DONE) | Epic 10 wire 시점에 Capability dual-route 정확히 동일 패턴 (`require_any_capability`) |
| **A30** | SHARED PDF generator Discriminated union `Literal[15..21]` (9-4 DONE) | Epic 10 본체에서 A30 SHARED factory 보존 + Report #15 wire는 A31 결정 시점 |
| **A31** | Report #15 wire schedule (cj-style Epic 9 6번째 진입점 권장) | Epic 10 진입 후 결정; Epic 10 PRD entry는 Report #15 wire 자체는 미포함 |
| **A32** | A30 SHARED factory reuse entry 1st case = Report #15 wire | Epic 10 본체와 별개 (Epic 9 보강) |
| **A33** | A19 cohesion pattern 9 surface 진입 시점 = Report #15 wire | Epic 10 wire 시점에 신규 surface 안 만듦 (보고서 외 surface); 보존 |
| **A34** | Mixed honestly DEFER 4-category framework (a)~(d) | **Epic 10 진입 시점에 적용**: (a) docs 정합 (b) retro input (c) separate epic (d) dedicated sprint |
| **A35** | Frontend test debt honestly DEFER (d) + 9-7 follow-up sprint 진입 | **Epic 10 진입 gate ✅ DONE** (9-7 atomic wire 2026-08-17, cj-style 24번째 epic 연속); Epic 10 본 wire에서 신규 컴포넌트는 CR 11-4 D-001 mount + D-002 ko-KR.json SSOT + D-005 unknown state reject + P-015 SSOT drift detector 정합 필수 |
| **A36** | SDR claim 검증 프로토콜 wire | **Epic 10 wire 시점에 자동 검증 단계 적용**: commit prefix lint (D5) + sprint-status structure 검증 (D4) + vitest file count drift (D2) + commit consistency (D1) |

### 7.3 A34 4-Category Mixed DEFER Framework (Epic 10 진입 시점 적용)

- **(a) docs 정합** (lowest risk + docs only RESOLVE 가능): Epic 10 spec
  진입 시점에 §F10.1·§F10.2 detail PRD 정합, ko-KR.json SSOT 정합
- **(b) retro input** (retro 결정 입력): Epic 10 close-out retro에서 A37+
  결정 도출
- **(c) separate epic scope** (별도 epic territory): EX: AI 인사이트 3개
  카테고리 (절감·이상·예측) 별도 epic 진입 시 Epic 10 carry-over는 미포함
- **(d) dedicated sprint scope** (전용 sprint): EX: AI extraction 정확도
  > 95% 개선 전용 sprint (master PRD §8.1 M0-c 70% 임계값 외)

### 7.4 A35 + A36 Epic 10 wire 진입 정합 (cj-style 24번째 epic 연속 정직 회복)

- **A35**: Epic 10 wire 시 모든 신규 React 컴포넌트는 vitest mount 검증
  필수 + TS mirror parity test 필수 + ko-KR.json SSOT 1 namespace 분리
  (CR 11-4 D-001/D-002/D-005/P-015)
- **A36**: Epic 10 wire 시 commit prefix lint wire + sprint-status structure
  검증 + vitest file count drift 자동 검증 + commit consistency 자동 검증
  4-step 자동 검증 단계 적용

---

## 8. Risk Profile + 3중 게이트 영향 평가

### 8.1 Risk Profile (Epic 10 4-story 진입 시)

| Risk | Impact | Severity | Mitigation |
|---|---|---|---|
| **AI 비용/지연 결정성 결여** | AI 호출 단가 변동 / NFR11 SLO 30s 이탈 가능 | high | F10.1 cache key 결정성 보장 + Three-Insight 정책 재호출 0회 (NFR11 SLO 충족) |
| **"Three-Insight Cache" 모호성** | spec 작성 시 흔들림 | medium | F10.1 4 bullets detail + key = `(tenant_id, period_key, calc_result_hash)` 명시 |
| **"Promotion Port" 의미** | UX 결정 결여 | low | AD-17 verbatim 인용 + idempotent on `(tenant_id, period_key, source_draft_id)` |
| **A35/A36 carry-over 누락** | retro 정직성 깸 / SDR overclaim 재발 | medium | §7.4 A35+A36 wire 진입 정합 + CI lint 자동 검증 |
| **Epic 11 close trigger 의존** | Epic 11 wire 시 trigger 추가 wiring 필요 | low | F10.1-(a) AC에 "본 Story는 calc-hash만 wire, Epic 11에서 trigger 추가" 명시 |
| **`AI_EXTRACT` vs `AI_INSIGHT` capability 충돌** | capability matrix 일관성 결함 | low | §6.2 별도 row 신설 + drift detector로 4-industry grants 정합 강제 |
| **3중 게이트 영향 (Epic 10 본 wire)** | backend 100% + frontend D2/D3 honestly DEFER 패턴 회귀 가능 | medium | A35 wire 진입 정합 준수 + 9-7 follow-up sprint atomic wire 그대로 검증 |

### 8.2 3중 게이트 영향 평가 (Epic 10 PRD entry 시점 — 본 doc)

- **ruff scoped** = 0 NEW (본 doc는 docs only)
- **import-linter** = 2 KEPT 0 broken (본 doc 변경 없음)
- **pytest focused** = 변경 없음 (capability matrix 신규 test는 Epic 10 wire
  진입 시점에 작성)
- **vitest** = 변경 없음
- **tsc** = 변경 없음

**3중 게이트 impact = NONE** (Epic 10 PRD entry는 docs only 변경;
capability matrix v1.21 wire 자체는 Epic 10 첫 story spec 진입 시점에
별도 atomic wire).

---

## 9. Non-Goals Reaffirmation (master PRD §14.B 정합)

본 Epic 10은 master PRD §14.B 비목표 10개 가운데 다음 항목을 의도적으로
미구현한다:

- **[NON-GOAL for MVP #6]** 멀티에이전트 원가분석 위원회 (master PRD
  §14.B 정합). 본 Epic 10의 AI 인사이트는 단일 모델 + 고정 템플릿의
  패턴만 wire. 다중 에이전트 협의·합의 알고리즘 = 3차 로드맵.
- **[NON-GOAL for MVP #5]** 다국어·다통화 자동 환산 (master PRD §14.B
  정합). `source_kind='ai_reference'` + `auto_analysis` 배지 tooltip은
  ko-KR 만. 2차 로드맵.
- **[NON-GOAL for MVP #8]** 모바일 네이티브 앱 (master PRD §14.B 정합).
  AI 추출 / 승격 / 인사이트 / 배지 분리 UI는 **반응형 웹 (`apps/web` +
  Next.js 16.2.11 App Router)** 만 제공. 모바일 네이티브 = 별도
  의사결정 후.

---

## 10. 오픈 질문 (Open Questions) — Epic 10 wire 진입 시점 결정

| ID | 항목 | 현 상태 | Owner | 결정 시점 |
|---|---|---|---|---|
| OQ-EPIC10-1 | "Three-Insight" 3개 카테고리 (절감·이상·예측) 구체화 | master PRD §12 "원가 절감 후보·이상 패턴·예측" 명시 | Alice + Charlie | Epic 10 Story 10.2 spec 진입 시 |
| OQ-EPIC10-2 | AI 추출 정확도 임계값 (master PRD §8.1 M0-c 70% vs 95% 목표) | master PRD §8.1 M0-c 70% 정합 | Alice + Amelia | Epic 10 Story 10.1 spec 진입 시 |
| OQ-EPIC10-3 | AD-25 cache eviction 정책 (LRU vs TTL vs invalidation-only) | master PRD §12 "캐시 = 마감 완료 ~ 다음 마감 시작" 정합 | Charlie + Amelia | Epic 10 Story 10.2 spec 진입 시 |
| OQ-EPIC10-4 | AI 모델 선택 (Claude Sonnet vs Haiku 등) | master PRD §13.2 "Claude API (Vision 포함)" 정합 | Amelia + Alice | Epic 10 Story 10.1 spec 진입 시 |

해소 절차: 각 항목 owner가 결정 확정 시 본 표에서 삭제하고 본 PRD §7 결정 이력에
`A37+` 로 추가. 결정 사항은 memlog에 `event: "OQ-EPIC10-N resolved → A-N
결정"`으로 기록.

---

## 11. 다음 단계 (Next Steps)

1. **Epic 10 본 PRD entry 종료 (handoff)**: 본 doc → final.
2. **bmad-create-story 진입**: 10-1 AI Document Extraction spec 진입
   (cj-style Epic 10 1번째 진입점). baseline_commit = 9-7 follow-up done
   tip (`8df01bc`).
3. **10-1 wire → 10-2 wire → 10-3 wire → 10-4 wire** cj-style 4-story 표준
   진입 (cj-style 25~28번째 epic 연속).
4. **Epic 10 close-out retro** (10-1~10-4 done 진입 후): A37+ 결정 도출 +
   Epic 11 또는 차기 Epic 진입 결정 (cj-style 5번째 진입점).
5. **OQ-EPIC10-1~4 해소**: 위 4개 항목 owner 결정 확정 → A37+ 결정 이력 승격.

---

## 부록 A. 결정 이력 verbatim (Epic 8 Retro A23~A27 + Epic 9 Retro A28~A36)

verbatim 보존은 본 doc §7 참조. 새 결정은 Epic 10 close-out retro 시점에 본
부록에 추가.

## 부록 B. Capability Matrix v1.20 → v1.21 변경점

본 doc §6 참조. capability matrix 본체는 `docs/capability-matrix.md` 에
별도 edit.

## 부록 C. 본 PRD의 master PRD 정합 검증

| 항목 | Master PRD 정합 위치 | 본 PRD 정합 |
|---|---|---|
| UJ-4 step 3 (AI 추출) | master PRD §2.A UJ-4 step 3 | UJ-AI step 2 (Story 10.1 bind) |
| §8.1 M0-c (70% 임계값) | master PRD §8.1 M0 (c) | Story 10.1 AC (red badge + 강제 확정) |
| §8.1 M10 (a) (cache policy) | master PRD §8.1 M10 (a) | F10.1 (a)~(d) 4 bullets 확장 |
| §8.1 M10 (b) (badge separation) | master PRD §8.1 M10 (b) | F10.2 (a)~(d) 4 bullets 확장 |
| §12 AI 3종 (문서추출/인사이트/고정변동) | master PRD §12 | 본 PRD §1 한 문장 정합 + UJ-AI |
| §14.B #6 (멀티에이전트) | master PRD §14.B | 본 PRD §9 정합 + 명시 인용 |
| AD-7 / AD-17 / AD-25 | master PRD AD-7·17·25 + ARCHITECTURE-SPINE | 본 PRD §5.1 verbatim 인용 |

---

*— 본 Epic 10 PRD entry 종료. 다음: Epic 10 Story 10.1 `bmad-create-story`
진입 (cj-style Epic 10 1번째 진입점) OR Epic 10 PRD 검증 (`bmad-validate-prd`).*
