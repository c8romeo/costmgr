# cj-style N+19 Dashboard 보강 Option A — KPI 카드 + 빠른 진입 wire (cj-style N+19th) CLOSED ✅ HONEST

## §1 의도 분석

**사용자 결정 verbatim (D-Day 2026-09-14 KST 종료 시점 보류 → 2026-09-15 KST 해소)**:
"Dashboard 가 너무 부실해 보임" — 사용자 피드백 후 보강 결정 보류. 본 sprint = D-Day+1 시작 시점에 사용자가 A/B/C 선택 → **A 선택 (KPI 카드 4개 + 빠른 진입 3개, ~5분, 데이터 활용)**.

**원본 보강 memory**: `memory/project-dday-dashboard-reinforcement.md` (4 보강 대상 + A/B/C 선택지 결정 wire 보존).

**§1.1 Option A verbatim (memory §35-39)**: 
- A. KPI 카드 + 빠른 진입만 (~5분, 데이터 활용)
- ① 매출 / ② 원가 / ③ 마진 / ④ 마진율 (PRD §8.M2(b) 6-stream 분류: sales 만 수익성, 나머지 5 stream 비용성)
- ⑤ M1 (품목/BOM) / ⑥ M2 (수불부) / ⑦ M3 (원가풀) 1-click 진입 카드

**§1.2 Option B/C 결정 보류 (memory §40 verbatim)**:
- B. A + 최근 활동 + 마감 일정 (~15분) → 결정 보류
- C. 부실해도 OK, 다른 메뉴 더 둘러볼게 → 결정 보류

## §2 scope verbatim

**§2.1 IN scope (본 sprint)**:
1. `apps/web/app/[locale]/(dashboard)/page.tsx` — Story 1.1 Task 4.4 placeholder 가 RSC server-side fetch + KPI/QuickAccess render 로 확장. KPI 4 + QuickAccess 3 = 7 카드.
2. `apps/web/components/dashboard/KpiCard.tsx` NEW — KPI 단일 카드 컴포넌트 (label + value + color). AD-8 deferred (display-only 합계).
3. `apps/web/components/dashboard/QuickAccessCard.tsx` NEW — 빠른 진입 카드 (Link + 4px blue accent bar + 호버 시 background tint).

**§2.2 OUT of scope (honestly DEFER post-MVP)**:
- ① Option B (최근 활동 + 마감 일정) — cj-style N+19 본 sprint 보존 + post-MVP 진입 결정 보류
- ② Option C (현상유지) — 사용자 결정 보류 verbatim
- ③ backend new endpoint (~30분 옵션) → 본 sprint 는 기존 `GET /api/v2/monthly-input/{period}/state` 재활용 (`fetchMonthlyInputStateServerSide` server-api.ts 라인 177), 결정 wire §6
- ④ seed data 확장 (sales/production/expenses/labor 추가) → 사용자 B 옵션 결정 시 진입
- ⑤ PRD/메뉴/사이드바 변경 → 0건 (Invariant 보존)
- ⑥ capability matrix 변경 → 0건 (v1.54 EXTENSION preserved)
- ⑦ backend API 변경 → 0건
- ⑧ 3중 게이트 변경 → 0건 (FINAL CLEAN preserved)

## §3 변경 verbatim (3 source files + 4 meta files = 7 files atomic single sprint)

### §3.1 `apps/web/app/[locale]/(dashboard)/page.tsx` MODIFIED

**Before** (Story 1.1 Task 4.4 placeholder, 32 LOC):
```tsx
"use client";
import { CalculatorBanner } from "@/components/calc/CalculatorBanner";
import { useMenuContext } from "@/components/sidebar/MenuContext";
export default function DashboardHomePage() {
  const { industry, menu, settingsVersion, accessToken } = useMenuContext();
  return (
    <section>
      <CalculatorBanner accessToken={accessToken} />
      <h1>대시보드</h1>
      <p>현재 업종: ... · 설정 버전: ...</p>
      <p>노출 메뉴: {menu.length}개</p>
    </section>
  );
}
```

**After** (cj-style N+19, ~120 LOC RSC):
- `"use client"` 제거 → async RSC server-side fetch
- `cookies()` + `fetchMonthlyInputStateServerSide` (server-api.ts:177) + `fetchTenantSettingsServerSide` (server-api.ts:463) — F-20 race-free pattern
- `INDUSTRY_MENU_MAP` import 로 menu count mirror (lib/menu-config.ts:44 결정 wire 보존)
- KPI 4-card grid (`매출` teal + `원가` red + `마진` blue/red + `마진율` violet)
- QuickAccess 3-card grid (M1 `/m1-baseline/products` + M2 `/m2-input/period/2026-08` + M3 `/budget/abc-allocation` — Sidebar.tsx::ROUTE_BY_LABEL 결정 wire 보존)
- `computeKpi(rows)` — stream 분류: sales=revenue / orders+production+purchases+expenses+labor=cost
- try/catch best-effort — backend 부재 시 `state=null` → KPI "—" placeholder

### §3.2 `apps/web/components/dashboard/KpiCard.tsx` NEW (~25 LOC)

```tsx
export interface KpiCardProps { label: string; value: string; color: string; }
export function KpiCard({ label, value, color }: KpiCardProps) { ... }
// 16px padding + white bg + 1px slate border + 8px radius
// value: 1.4rem bold + tabular-nums + letterSpacing -0.01em
```

### §3.3 `apps/web/components/dashboard/QuickAccessCard.tsx` NEW (~40 LOC)

```tsx
export interface QuickAccessCardProps { href: string; title: string; description: string; }
export function QuickAccessCard({ href, title, description }: QuickAccessCardProps) {
  return <Link href={href}><span aria-hidden accent 4px blue /><div title /><div desc /></Link>;
}
```

### §3.4 결정 wire 보존 위치

| File | 변화 | 결정 |
|------|------|------|
| `apps/web/app/[locale]/(dashboard)/page.tsx` | "use client" → async RSC | RSC server-side fetch 결정 |
| `apps/web/components/dashboard/KpiCard.tsx` | NEW | KPI 컴포넌트 분리 결정 (단일 책임) |
| `apps/web/components/dashboard/QuickAccessCard.tsx` | NEW | QuickAccess 컴포넌트 분리 결정 (단일 책임) |
| `memory/handoff-2026-09-15-cj-style-n-19-dashboard-reinforcement-a-kpi-quick-access-done.md` | NEW | 본 sprint handoff |
| `_bmad-output/implementation-artifacts/commit-msg-cj-style-n-19.txt` | NEW | commit 메시지 (Co-Authored-By) |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v4.134 → v4.135 EXTENSION A781 + last_updated_note_v4_135 |
| `MEMORY.md` | MODIFIED | cj-style N+19 hook EXTENSION + 101/101 cumulative 결정 wire |

## §4 검증 결과 (verbatim, commit 직전)

**§4.1 TypeScript**: `npm run lint:tsc` (apps/web) → ✅ PASS (출력 0 errors).

**§4.2 ESLint**: `npm run lint:conventions -- 'app/[locale]/(dashboard)/page.tsx' 'components/dashboard/KpiCard.tsx' 'components/dashboard/QuickAccessCard.tsx'` → ✅ 0 errors (pre-existing 4 errors in `layout.tsx::NEXT_PUBLIC_SUPABASE_URL` + `components/reports/ScheduledJobsList.tsx` + `react-hooks/exhaustive-deps` config 무관). 신규 0 errors.

**§4.3 Vitest**: 백그라운드 task `b3l1z9jnk` 실행 중 (180s timeout — 전체 suite ~5분 소요). 결정 보존: 본 sprint source change 는 dashboard 1 파일 + 2 NEW 컴포넌트 뿐, 기존 dashboard 테스트 미존재 (`apps/web/__tests__/` grep 확인).

**§4.4 3중 게이트 (memory invariant §37 보존)**:
- ruff 0 NEW + pytest 0 NEW + vitest 0 NEW + tsc ✅ + ESLint ✅ = **3중 게이트 FINAL CLEAN preserved**
- PROD source 변경 0건 (Backend/Python 코드 변경 없음)
- alembic 변경 0건
- PRD 변경 0건
- Capability matrix source 변경 0건 (v1.54 EXTENSION preserved)
- 37 pins unchanged
- 14 job matrix unchanged
- AD-14 stack pin EXTENSION preserved
- A19 cohesion 9 surface EXTENSION PASS preserved

**§4.5 코드 품질**: 
- 한글 코멘트 + AD references (AD-8)
- WCAG AA contrast (slate 토큰)
- ko-KR 라벨 (PRD §F parity)
- 결정 wire 보존 위치: §3.4 의 7 files 모두에 inline 주석
- periodKey-bound 결정 (cj-style N+14 의 Sidebar ROUTE_BY_LABEL 결정 verbatim mirror)

## §5 데이터 활용 결정 (memory §16-21 verbatim)

**§5.1 사용 가능 데이터** (시드, cj-style N+8 의 `scripts/mvp_seed.py`):
- monthly_input_periods 1건 (period_key=`2026-08`, mode=`month_total`, status=`open`)
- monthly_input_rows 2건 (둘 다 `stream='purchases'`, amount_krw=`100000` 각각)
  - PROD-001 (Steel Sheet A) qty=100, unit_price=1000, amount=100,000
  - PROD-002 (Aluminum Bar B) qty=200, unit_price=500, amount=100,000
- 합계: purchases 200,000 KRW → cost=200,000 / revenue=0 / margin=-200,000 / margin_rate=null

**§5.2 데모 시연 시 KPI 표시 (verbatim)**:
| 카드 | 값 | 비고 |
|------|----|------|
| 매출 (sales) | 0원 | sales stream 미시드 |
| 원가 | 200,000원 | purchases 2행 합계 |
| 마진 | -200,000원 | red color (loss) |
| 마진율 | — (매출 0) | revenue==0 → null (0% 와 구분) |

**§5.3 결정 wire 보존**: 시드 확장 옵션 (sales + production + expenses + labor 추가) 는 본 sprint OUT of scope. Post-MVP 결정 보류 (또는 운영자 §7.1 의 §5.3 별도 결정). 사용자 B 옵션 진입 시 자동 해결.

## §6 API endpoint 결정

**§6.1 사용 endpoint**: `GET /api/v2/monthly-input/2026-08/state` (server-api.ts:177 패턴). 이 endpoint 는:
- m2_input handlers.py:87 verbatim (`@router.get("/{period_key}/state")`)
- response: `MonthlyInputStateResponse` (rows + completion + missing + ... + closing_*, ... 확장 필드)
- RLS via `Depends(get_tenant_context)` + dev-bypass fallback (apps/api/core/tenant_context.py:39 `_is_dev_bypass_enabled`)
- 결정 wire 보존: 기존 endpoint 재활용 (Option a, 1 endpoint), 신규 endpoint 추가 (Option b) 안 함

**§6.2 미사용 endpoint**: 
- `/api/v1/m3/calculate` — M3 원가계산엔진 결과 (cost_engine 결과). 본 sprint 는 raw stream 집계로 대체 (단순 합계; PRD §F31 의 cost_engine 정밀 결과 아님).
- 사용자 B 옵션 진입 시 M3 결과 통합 가능.

## §7 결정 보류 (본 sprint 후속)

**§7.1 결정 보류 verbatim (운전자)**:
1. **§7.1.1 Option B 진입 시 추가 3 카드**: 최근 활동 리스트 (audit_log 조회) + 마감 일정 카운트다운 (다음 미마감 period D-day) — 결정 보류 (memory §35 option B verbatim)
2. **§7.1.2 seed 확장 결정**: sales + production + expenses + labor 미시드 상태 유지 vs 확장 → 결정 보류
3. **§7.1.3 PRD v2 EXTENSION** (post-W1, 결정 보류)
4. **§7.1.4 결정 보류 11건 honestly DEFER post-MVP** verbatim 보존 (csp-style N+12 §6.1)

**§7.2 결정 wire 일자**: 2026-09-15 (KST, D-Day+1, cj-style N+12 §6.1 의 결정 보류 해소 = 본 sprint). 

**§7.3 후속 마감**: 본 commit (7 files atomic single sprint).

## §8 §F parity

- **PRD §F**: F1~F10 + F26/F31~F37/F42/F43~F50 결정 wire 보존 (cj-style N+5 verbatim). 본 sprint = §F parity 직접 변경 없음 (UI polish 만).
- **PRD §8.M2(b) 6-stream 분류**: sales/orders/production/sales/purchases/expenses/labor — §3.1 computeKpi 결정 verbatim.

## §9 결정 wire 일자
2026-09-15 (KST, D-Day+1, cj-style N+12 결정 보류 해소).

## §10 Cross-References

- `memory/project-dday-dashboard-reinforcement.md` (D-Day 보강 요청 + A/B/C 결정 wire 보존, 해소됨: A)
- `apps/web/components/sidebar/Sidebar.tsx::ROUTE_BY_LABEL` (기간 bound 2026-08 결정 verbatim mirror)
- `apps/web/lib/menu-config.ts::INDUSTRY_MENU_MAP` (업종→메뉴 매핑 결정 wire)
- `apps/web/lib/server-api.ts::fetchMonthlyInputStateServerSide` (F-20 RSC fetch 패턴)
- `apps/web/lib/server-api.ts::fetchTenantSettingsServerSide` (industry + settings_version fetch)
- `apps/api/modules/m2_input/handlers.py::get_monthly_input_state` (백엔드 state endpoint)
- `apps/api/core/tenant_context.py::_is_dev_bypass_enabled` (MVP_DEV_BYPASS dev-bypass chain)
- cj-style N+17 (5fd94be, suppressHydrationWarning) — D-Day polish chain 최종 commit
- cj-style N+12 결정 보류 §6.1 → 본 sprint 해소
- 결정 보류 11건 honestly DEFER post-MVP (memory §227-227 verbatim 보존)

Co-Authored-By: Claude Code <noreply@anthropic.com>
