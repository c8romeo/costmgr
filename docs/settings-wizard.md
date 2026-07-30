# costmgr Settings Wizard (M0 — Story 1.2)

> **소속**: Epic 1 / Story 1.2
> **최종 갱신**: 2026-07-30
> **PRD 참조**: §8.M0(b) (계산 잠금) · §3.A1 (회계연도) · §3.A6 (1원 단위 검증) · §3.A7 (전진법) · §3.A11 (CCR)
> **UX locked-decisions**: Dark MVP · WCAG AA · Professional 톤 · ko-KR (NFR-18)

업종이 결정된 후 회계연도 시작월 · 통화 · 언어 · 배부기준 3종을 입력받는 마법사.
4개 필드가 모두 완료되어야 [계산] 버튼이 활성화된다 (PRD §8.M0(b)).

---

## 1. 라우트 흐름

```
[Story 1.1 완료: onboarding.industry 결정]
   │
   ▼  GET /dashboard (대시보드 진입)
[사이드바 상단: [계산] 버튼 — disabled]
   │
   │  →  클릭 시 tooltip:
   │     "설정 N/4 완료 — 다음 항목을 완료하세요: …"
   │
   ▼  /dashboard/settings/wizard  (마법사)
   │
   │  ① 회계연도 시작월 (YYYY-MM, Picker)
   │  ② 통화 (KRW | USD, Radio cards)
   │  ③ 언어 (ko-KR, read-only 확인)
   │  ④ 배부기준 3종
   │     · 직접/간접 계정 분류
   │     · 고정/변동 분류
   │     · 동인 정의 (manufacturing 업종은 건너뜀)
   │
   ▼  각 단계마다 POST → settings_version++ → audit row → /completion 재조회
[모든 필드 완료 → is_complete=true → [계산] 버튼 활성화]
   │
   ▼  클릭 → /dashboard/m3-calculate/period (Story 4.2)
```

---

## 2. 데이터 모델 — `tenant_settings.onboarding` (AD-23)

```json
{
  "industry": "manufacturing",
  "fiscal_year_start": "2026-01",
  "currency": "KRW",
  "language": "ko-KR",
  "allocation_criteria": {
    "direct_indirect": { "completed": true, "count": 5, "last_updated": "..." },
    "fixed_variable":  { "completed": true, "count": 5, "last_updated": "..." },
    "drivers":         { "completed": false, "count": 0, "last_updated": null }
  }
}
```

스키마 정의: [`docs/onboarding-schema.md`](./onboarding-schema.md)
도메인 enum + 포맷: [`docs/conventions.md#04-wizard-필드-포맷-story-12`](./conventions.md)

---

## 3. API 엔드포인트 (Story 1.2 Tasks 3 / 4)

| Method | Path | Body | 응답 | 권한 |
|---|---|---|---|---|
| `POST` | `/api/v1/tenant-settings/onboarding/fiscal-year-start` | `{ fiscal_year_start: "2026-01" }` | `OnboardingFieldSavedResponse` | owner |
| `POST` | `/api/v1/tenant-settings/onboarding/currency` | `{ currency: "KRW" \| "USD" }` | `OnboardingFieldSavedResponse` | owner |
| `POST` | `/api/v1/tenant-settings/onboarding/language` | `{ language: "ko-KR" }` | `OnboardingFieldSavedResponse` | owner |
| `POST` | `/api/v1/tenant-settings/onboarding/allocation-criteria` | `{ criterion: "direct_indirect" \| "fixed_variable" \| "drivers", count: int ≥1 }` | `OnboardingFieldSavedResponse` | owner |
| `GET`  | `/api/v1/tenant-settings/completion` | — | `CompletionStatusResponse` | any |
| `POST` | `/api/v1/baseline/accounts/classification` | `{ account_id, direct_indirect, fixed_variable }` | `AccountClassificationResponse` | owner (Epic 2 scaffold) |
| `POST` | `/api/v1/abc/drivers` | `{ driver_name, unit, practical_capacity_hours }` | `DriverCountResponse` | owner (Epic 9 scaffold) |

### 3.1 에러 응답 (AD-15)

| Code | HTTP | 의미 |
|---|---|---|
| `FORBIDDEN_ROLE` | 403 | `owner` 외 역할 — Story 1.1 Decision §3 |
| `FISCAL_YEAR_LOCKED` | 409 | A7 — `last_calc_date` 세팅 후 또는 7일 grace 경과 |
| `CURRENCY_LOCKED` | 409 | A7 — 동일 |
| `JSONB_SCHEMA_VIOLATION` | 400 | `enforce_onboarding_schema()` 위반 |
| `TENANT_SETTINGS_NOT_FOUND` | 404 | Story 0.2에서 행 생성 이후 발생 시 (defensive) |

---

## 4. Industry-conditional completion (PRD §8.M0(b))

| Industry | `direct_indirect` | `fixed_variable` | `drivers` |
|---|---|---|---|
| `manufacturing` (①) | ✅ | ✅ | ⛔ (A11 — ABC 엔진 없음) |
| `service` (②) | ✅ | ✅ | ✅ |
| `manufacturing_service` (③) | ✅ | ✅ | ✅ |
| `manufacturing_service_other` (④) | ✅ | ✅ | ✅ |

`manufacturing` 업종은 동인 정의 탭이 **숨김 처리**되며 `drivers_required=false` 가 응답에 포함됨. 다른 업종은 `drivers_required=true`.

판정 함수: `packages/services/m0_onboarding/settings_completion.compute_completion()` (순수 함수 — DB·시계 미의존).

---

## 5. A7 전진법 (lock) 적용

`fiscal_year_start` 와 `currency` 는 Story 1.1의 industry lock과 동일 패턴:

```
1) POST 요청 수신
2) SELECT ... FOR UPDATE → tenant_settings 행 잠금
3) onboarding.last_calc_date 가 set 인지 검사
   ├─ set → 409 FISCAL_YEAR_LOCKED / CURRENCY_LOCKED (A7 우위)
   └─ unset → 7일 grace 윈도우 검사
       ├─ grace 이내 → 진행 (audit row → write → completion 재계산)
       └─ grace 초과 → 409
4) POST 와 같은 값이면 no-op (F-8/F-9) — audit/version bump 없음
```

자세한 도메인 의미: [`docs/onboarding-flow.md#3-7-day-grace--a7-전진법-decision-1`](./onboarding-flow.md).

---

## 6. Frontend 통합

| 컴포넌트 | 위치 | 책임 |
|---|---|---|
| `SettingsWizardClient` | `apps/web/components/settings/wizard/SettingsWizardClient.tsx` | 4개 step + completion 상태 공유 |
| `FiscalYearStartStep` | `…/wizard/FiscalYearStartStep.tsx` | 12월 Picker + 연도 선택 |
| `CurrencyStep` | `…/wizard/CurrencyStep.tsx` | KRW/USD radio cards |
| `LanguageStep` | `…/wizard/LanguageStep.tsx` | ko-KR read-only 확인 |
| `AllocationCriteriaStep` | `…/wizard/AllocationCriteriaStep.tsx` | 3-탭 (업종별 동인 탭 숨김) |
| `useSettingsCompletion` | `apps/web/hooks/useSettingsCompletion.ts` | `GET /completion` 폴링 (5초 stale, 30초 cadence) |
| `CalcButton` | `apps/web/components/calc/CalcButton.tsx` | 사이드바 — disabled + 툴팁 + 클릭 시 `/m3-calculate/period` |
| `CalculatorBanner` | `apps/web/components/calc/CalculatorBanner.tsx` | 대시보드 상단 노란 배너 (`is_complete=false` 일 때만) |

### 6.1 UX 규칙 (locked-decisions)

- **Dark MVP**: 라이트 배경, 액센트 블루 (`#2563eb`).
- **WCAG AA**: gray(`#94a3b8`) on white = 4.6:1, blue(`#2563eb`) on white = 5.9:1.
- **Professional 톤**: 둥근 모서리, 보조 설명은 회색(`#475569`), 강조만 굵게.
- **ko-KR**: 라벨·메시지·placeholder 모두 한국어.

### 6.2 접근성

- `aria-disabled` — disabled 버튼 + tooltip id(`aria-describedby`).
- `role="radiogroup"` / `role="radio"` — 통화·월 선택.
- `role="tablist"` / `role="tab"` / `role="tabpanel"` — 배부기준 탭.
- 키보드 포커스 시 tooltip 표시 (`onFocus` / `onBlur`).

---

## 7. 테스트 커버리지

| 영역 | 파일 | 상태 |
|---|---|---|
| Pure logic (Pydantic + service role/lock) | `tests/api/test_settings_wizard.py` | ✅ 17/17 pass |
| Cross-language matrix (Python truth) | `tests/integration/test_completion_consistency.py` | ✅ 5/5 pass |
| Schema validator | `tests/api/test_jsonb_schemas.py` | ✅ 18/18 pass |
| Pure completion logic | `tests/services/test_settings_completion.py` | ✅ 18/18 pass |
| RLS-backed isolation | `tests/api/test_settings_wizard_isolation.py` | 🔒 CI-only (xfail strict=False) |
| Frontend unit (Vitest) | `apps/web/__tests__/CalcButton.test.tsx` | ⏳ Story 0.5 deferred (Vitest 미설치) |
| E2E (Playwright) | `apps/web/e2e/settings-wizard.spec.ts` | ⏳ Story 0.5 deferred (Playwright 미설치) |

---

## 8. 다음 스토리로의 인수인계

- **Story 1.3 (AI 문서 추출)**: `tenant_settings.ai` JSONB 채움. wizard 완료 후에만 호출 가능.
- **Epic 2 (M1 baseline)**: `apps/api/modules/m1_baseline/handlers.py` 의 scaffold 가 완전한 CRUD 로 확장됨. `account_classifications` 테이블 신설.
- **Epic 9 (ABC/TDABC)**: `apps/api/modules/m9_abc/handlers.py` 의 scaffold 가 완전한 동인 CRUD 로 확장됨. `abc_drivers` 테이블 신설.
- **Story 4.2 (calc endpoint)**: `[계산]` 클릭 → `/dashboard/m3-calculate/period`. 성공 시 `onboarding.last_calc_date` 동기화 → 이후 wizard의 fiscal_year_start / currency 변경이 409로 차단됨.

---

## 9. 변경 이력

| 날짜 | 변경 | 책임 |
|---|---|---|
| 2026-07-30 | Story 1.2 구현 — wizard 4 step + CalcButton + banner + 테스트 + 마이그레이션 + 문서 | kjw |