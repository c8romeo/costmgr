# costmgr Onboarding Flow (M0)

> **소속**: Epic 1 / Story 1.1
> **최종 갱신**: 2026-07-29
> **PRD 참조**: §4.1 (4지선다 표) · §8.M0(a) (자동 토글) · §3.A7 (전진법) · UJ-4 (신규 가입자)

신규 가입 사장님이 처음 로그인할 때 거치는 M0 온보딩 단계. 4지선다 한 번이
`tenant_settings.onboarding.industry` JSONB 한 칸에 기록되고, 그 값이 이후
사이드바 메뉴 토글의 단일 소스가 된다 (AD-23).

---

## 1. 라우트 흐름

```
[Story 0.2: signup & tenant row 생성]
   │
   ▼  GET /api/v1/tenant-settings  → onboarding.industry IS NULL
[Story 1.1: /onboarding/industry]
   │
   │  ① 제조업
   │  ② 서비스업
   │  ③ 제조+서비스
   │  ④ 제조+서비스+기타
   │
   ▼  POST /api/v1/tenant-settings/onboarding/industry
[Story 1.1: tenant_settings.onboarding = { industry, selected_at, is_initial }]
   │
   ▼  GET /api/v1/tenant-settings  → onboarding.industry = "service"
[Story 1.1: /dashboard  (sidebar filtered by industry)]
```

### 1.1 첫 진입 판정

`tenant_settings.onboarding.industry IS NULL` → 4지선다 화면.
이미 값이 있으면 → `/dashboard`로 redirect.

판정은 Server Component (`apps/web/app/[locale]/(auth)/onboarding/industry/page.tsx`)에서
수행. 클라이언트는 첫 GET 응답으로 `industry`를 받아 즉시 라우팅.

---

## 2. 업종 → 메뉴 매핑 (PRD §4.1)

| enum 값 | 한글 라벨 | 노출 메뉴 | 비고 |
|---|---|---|---|
| `manufacturing` | ① 제조업 | BOM, 기초재고, 수불부, 품목, 계정, 부서, 거래처, AI추출, 시뮬레이션, 예산, 보고서, 마감, 계정관리 | ABC 메뉴(원가풀·활동·동인) 숨김 |
| `service` | ② 서비스업 | 원가풀, 활동, 동인, 계정, 부서, 거래처, AI추출, 시뮬레이션, 예산, 보고서, 마감, 계정관리 | BOM·기초재고·수불부 **숨김** |
| `manufacturing_service` | ③ 제조+서비스 (겸영) | 위 13개 + **카브아웃 분할** | §7.3 [A10] 재무제표 업로드 필수 |
| `manufacturing_service_other` | ④ 제조+서비스+기타 | ③과 동일 + 격리 버킷 | '기타' 부문은 m3_calculate 내부에서 격리 처리 |

> **드리프트 주의**: PRD §4.1 본문에는 "BOM·수불부 등 제조 메뉴 숨김"으로 짧게 표현되어 있지만,
> epics.md의 AC는 더 포괄적입니다 — **기초재고**도 함께 숨깁니다. 이 문서는 epics AC를
> 따르며, 후속 reader는 `INDUSTRY_MENU_MAP` 정의를 기준으로 동작을 검증하세요.

### 2.1 단일 진실 공급원

| 위치 | 종류 | 비고 |
|---|---|---|
| `packages/services/m0_onboarding/industry_menu.py` | **Python (SSOT)** | `Industry` enum, `MenuItem` enum, `INDUSTRY_MENU_MAP` |
| `apps/web/lib/menu-config.ts` | TypeScript 미러 | Next.js 사이드바가 import |
| `tests/integration/test_menu_config_consistency.py` | 드리프트 가드 | 두 파일의 enum value·라벨·메뉴 순서를 파싱 비교 |

`Industry` enum value는 snake_case (`manufacturing_service`), `MenuItem` value는
한글 라벨(UI-facing string)로 분리합니다. enum 이름은 PascalCase (AD-15).

---

## 3. 7-day grace + A7 전진법 (Decision §1)

### 3.1 결정 함수 (`is_industry_change_allowed`)

순수 함수 — DB·시계 의존 없음. 결정 규칙 (Story 1.1 Subtask 1.5):

```
allowed = is_initial OR days_since_selection < GRACE_PERIOD_DAYS
```

- `is_initial = true`: 첫 선택/첫 변경 윈도우 — 항상 허용.
- `is_initial = false`, `days_since < 7`: 허용 + 응답 헤더
  `X-Onboarding-Warning: initial-change-allowed-for-7-days`.
- `is_initial = false`, `days_since >= 7`: **A7 전진법 잠금**.

### 3.2 응답 헤더 컨벤션

| 상태 | HTTP | 헤더 | 본문 |
|---|---|---|---|
| 첫 선택 (`is_initial=true` POST) | 200 | (없음) | `{ industry, menu, settings_version, is_initial: false, selected_at }` |
| 7일 이내 변경 | 200 | `X-Onboarding-Warning: initial-change-allowed-for-7-days` | 동일 |
| 7일 경과 후 변경 시도 | **409** | (없음) | `{ code: "INDUSTRY_LOCKED", message_ko: "...", details: { current_industry, next_fiscal_year_start }, trace_id }` |
| 비-owner 시도 | **403** | (없음) | `{ code: "FORBIDDEN_ROLE", message_ko: "...", details: { role }, trace_id }` |

### 3.3 첫 계산 후 잠금 (A7 보강)

`tenant_settings.onboarding.is_initial = true` 플래그는 첫 번째
원가 계산(`POST /api/v1/calc`)이 성공하면 서비스 레이어가 즉시
`false`로 갱신합니다 (Story 4.2와 합류 시점에 wiring — 현재는 industry 변경 시점에만 `false`로 전환).

이 시점 이후 7일 grace가 진행 중이더라도 grace가 만료되면 A7 전진법이
적용됩니다. 단, grace 만료 전에 `last_calc_date`가 채워지면 즉시 잠금
처리됩니다 (Story 1.2 wizard에서 `last_calc_date` 동기화 시점에 wiring).

### 3.4 결정 사유 코드 (`IndustryChangeDecision.reason`)

| reason | 의미 | 클라이언트 표시 |
|---|---|---|
| `initial` | 첫 선택 | 토스트 없음 |
| `within_grace` | 7일 이내 변경 | "7일 이내 변경 안내" 토스트 |
| `no_change` | 동일 업종 idempotent POST | 토스트 없음 |
| `locked_after_grace` | 7일 경과 — A7 전진법 잠금 | "A7 전진법" alert (read-only) |

---

## 4. 역할 게이트 (Decision §3)

업종 변경은 **`owner`만** 가능. 다른 역할은 모두 `403 FORBIDDEN_ROLE`.

| 역할 | 업종 변경 | 비고 |
|---|---|---|
| `owner` | ✅ 허용 | |
| `member` | ❌ 403 | Story 1.2 wizard 입력은 가능 |
| `viewer` | ❌ 403 | 읽기 전용 |
| `consultant_proxy` | ❌ 403 | middleware 레벨에서 거부 (consent-bound read-only는 Story 12.1) |

`role`은 JWT `app_metadata.role`에서 추출 (AD-3 — user_metadata는 신뢰 불가).

---

## 5. RLS + 격리 (AD-3)

`tenant_settings.onboarding` 쓰기는 모두 RLS 정책으로 tenant_id가 필터링됩니다.
Story 0.2가 설치한 `tenant_settings_isolation` 정책이 `tenant_id`가 JWT의
`app_metadata.tenant_id`와 일치하는 행만 노출합니다.

테넌트 격리 테스트는 `tests/api/test_industry_isolation.py` (CI 전용 —
`CI=true` 또는 `RLS_RUN_LOCAL=1` 필요, Decision 2: Docker CI-only).

---

## 6. 다음 스토리로의 인수인계

- **Story 1.2 (settings wizard)**: 업종이 결정된 후 회계연도 시작월·통화·언어·배부기준
  3종을 미완료 상태로 [계산] 진입을 차단합니다. `tenant_settings.baseline` JSONB
  네임스페이스를 채웁니다.
- **Story 1.3 (AI document extraction)**: `tenant_settings.ai` JSONB 네임스페이스를
  채우며, 업종 선택 후에만 호출 가능합니다.
- **Story 12.1 (2FA + consultant-proxy)**: 업종 변경 role gate에 `consultant_proxy`
  거부 + 2FA 강제.
- **Epic 4 (calc)**: `last_calc_date` 채우는 시점에 `is_initial`을 `false`로 동기화.

---

## 7. 변경 이력

| 날짜 | 변경 | 책임 |
|---|---|---|
| 2026-07-29 | Story 1.1 구현 (initial) — industry_menu.py + handlers + service + migration + frontend + 테스트 | kjw |
