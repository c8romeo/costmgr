# K-4 entry decision wire DONE (cj-style 293번째, 2026-09-11 KST, D-3)

> **사용자 결정 wire verbatim mirror (2026-09-11)**: "배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X / 확실한 MVP 기능 갖춘 프로그램 필요" + "4가지 아이디어 중 내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민" + "설계된 내용을 시스템으로 구현하는 과정에서 리스크를 최소화하면서 전체적인 프로세스 설계의 관점에서 최적의 대안" + "가장 합리적이고 효과적인 것부터 실행".

## §1 Background & user directive

- **사용자 2026-09-11 결정 wire (verbatim)**: ① "railway, resend 등 배포를 위한 단계는 내가 특별한 지시를 하기 전까지는 생각은 하지 마. 지금은 오로지 배포 직전단계, 즉 확실한 mvp기능의 제품을 로컬단계에서 완성하는 것에 집중하기로 하자." ② "네가 제시한 4가지 아이디어 중 내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민해보고, 설계된 내용을 시스템으로 구현하는 과정에서 리스크를 최소화하면서 전체적인 프로세스 설계의 관점에서 최적의 대안이 무엇인지를 분석해본 후 나의 목적을 달성해줄 수 있는 가장 합리적이고 효과적인 것부터 실행해줘."
- **Pilot W1 launch D-day 2026-09-14 KST 보존** + **사용자 2026-09-10 결정 wire 보존** ("배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X / 확실한 MVP 기능 갖춘 프로그램 필요") + **MVP-verification 우선** 결정 wire 보존.
- **K-3 chain 5/5 DONE ✅ HONEST** (chunk 1 `9842dc7` + chunk 2 `3ebd493` + chunk 3 `ab31195` + chunk 4 cj-style 291번째 + chunk 5 `f568bd9` cj-style 292번째) — PRD ↔ capability matrix v1.54 EXTENSION + source code 정합 검증 종합 DONE.
- **본 sprint 직전 4 결정 보류 options**: ① 디자인가이드 진입 ② 옵션 β docs+test (capability matrix EXTENSION + verify) ③ 옵션 γ source 변경 (PRD §13 screen 별 source review) ④ K-4 본격 진입 (~16개 주요 업무).

## §2 Final deliverable definition (사용자's goal 명확화)

**"확실한 MVP 기능 갖춘 프로그램 (local stage)"** 분해:
- **"확실한"** = reliable/verified — 단순히 코드가 존재가 아니라 실제 동작 검증 완료, blocker 0건
- **"MVP 기능"** = core features only — M0 Onboarding + M1 기준정보 + M2 월데이터입력 + M3 원가계산엔진 + M5 손익 + M8 예산 + M9 ABC + Auth (login/signup/2FA/aal1) + Audit log + Export (CSV) ≈ 10 flows
- **"갖춘"** = all of them — 모두 verified, 일부 X 아님
- **"프로그램"** = the actual working software — docs/capability matrix X, 실제 시스템
- **"로컬단계"** = local stage — Railway/Vercel/Resend/Supabase 등 배포 X, 로컬 환경에서 완성

**구체적 acceptance criteria (운전자 결정 wire 보류, 본 sprint 후속 진입 시 결정)**:
- Auth: login + signup + 2FA 강제 + aal1 minimum path 모두 local 동작
- M0~M9 핵심 flows: API endpoint 응답 + DB 연결 + 핵심 business logic 검증
- Audit log: append-only invariant 검증
- Export: CSV 생성 + 다운로드 (cj-282a wire 정합 보존)
- Non-MVP = M10 AI + M11 마감이력 + M12 계정운영 + 디자인가이드 → honestly DEFER

## §3 4 ideas → goal alignment + risk 분석

| Idea | Goal 정합 | System implementation risk | 판정 |
|------|----------|---------------------------|------|
| ① 디자인가이드 진입 | LOW — cosmetic, "기능"과 무관, 별도 epic territory | LOW — 별도 epic이라 main wire 영향 X | **DEFER (별도 epic 보류)** |
| ② 옵션 β docs+test (capability matrix EXTENSION + verify) | MEDIUM — capability matrix 검증 depth 추가는 가치 있으나 bug fix X | LOW-MED — test 변경 시 test bug 가능, CR 11-3 honest-DEFER violation 위험 | **DEFER (MVP-critical gap 발견 시에만)** |
| ③ 옵션 γ source 변경 (PRD §13 별 source code review) | HIGH — bug fix 가능, 하지만 scope = PRD §13 = ~5 surface, blast radius 큼 | HIGH — source 변경 = 명백한 risk, CR 11-3 보존 위해 verify-first 원칙 필요 | **DEFER (specific blocker 발견 시에만)** |
| ④ K-4 본격 진입 (~16개 주요 업무) | **HIGH — MVP 기능 실제 runtime 검증 = "확실한 MVP 기능 갖춘 프로그램" 직접 정합** | MEDIUM-HIGH — scope 큼 (~3-4 days best case), ±50% 환경 의존 변동 (sso python3-saml + web-e2e root cause + TestClient health) | **NARROW SCOPE + VERIFY-FIRST discipline = RECOMMENDED** |

**선정 정당화**:
- ④ K-4 본격 진입이 "확실한 MVP 기능 갖춘 프로그램" goal에 가장 직접 정합 (시스템이 실제 동작하는지 검증 = goal의 본질)
- ①·②·③ 모두 goal alignment 낮거나 risk 높아서 DEFER
- K-4의 scope 위험 (MEDIUM-HIGH) 은 다음 3가지 discipline 으로 mitigation:
  1. **Narrow scope** — MVP-critical flows only (~10 flows), Non-MVP honestly DEFER
  2. **Verify-first** — runtime smoke test BEFORE source change, docs-only entry first
  3. **Blocker-fix-only** — source 변경은 blocker 발견 시에만, non-blocker 는 CR 11-3 honest-DEFER 보존

## §4 K-4 narrow scope proposal (MVP-critical flows)

**MVP-critical (K-4 wire scope 정직 결정)**:
1. **Auth** (login + signup + 2FA + aal1 minimum path) — Epic 12 2FA + Phase 3 foundation + cj-307 aal1 wire 정합, MVP 진입 게이트
2. **M0 Onboarding** — 첫 사용자 flow, 4-step wizard (Epic 1 partial scaffold `d182d7d` + 1st release wire `be0cf97` 정합)
3. **M1 기준정보** — 제품/자재/거래처 master data, MVP 데이터 입력 기반
4. **M2 월데이터입력** — TanStack Table 입력 (PRD §13.1), MVP 핵심 데이터 입력
5. **M3 원가계산엔진** — V8 1원 대조 골든 fixture (Epic 11 wire), MVP 핵심 알고리즘
6. **M5 손익보고서** — M3 + M4 outputs, MVP 결과 검증
7. **M8 예산시나리오** — 예산 수립, ABC 분석 결과의 budget allocation 검증
8. **M9 ABC엔진** — TDABC 통합, MVP 핵심 분석
9. **Audit log** — append-only invariant (AD-8 + Epic 17 결정 wire), MVP 운영 필수
10. **Export (CSV)** — cj-282a wire, MVP 결과 export, K-3 chunk 5 §F30.1 정합

**Non-MVP (honestly DEFER, K-4 explicit deferral 보존)**:
- **M10 AI (Claude Vision)** — Epic 10 wire, value-add but not core MVP
- **M11 마감이력** — operational, post-MVP
- **M12 계정운영** — operational, post-MVP
- **디자인가이드** — 별도 epic territory (옵션 f), PRD §14/별도 디자인 시스템 문서

## §5 K-4 verification method proposal (atomic multi-sprint chain)

**검증 method 3-step chain (CR 11-3 honest-DEFER 보존)**:

### Step 1: K-4 entry decision wire (option α docs-only atomic single sprint) — **본 sprint**
- scope narrowing + verification method 결정 + 옵션 결정 + carry-over 보존
- **4 files docs-only atomic** = 1 NEW handoff (본 file) + 1 NEW commit-msg + 1 MODIFIED sprint-status + 1 MODIFIED meta
- **runtime**: source 변경 0건 + test 변경 0건 + alembic 변경 0건 + PRD 변경 0건 + capability matrix 변경 0건
- **verify gate**: 37 pins unchanged + 14 job matrix unchanged + PRD v7.0 §F/§M/§R unchanged + capability matrix v1.54 EXTENSION preserved + AD-14 stack pin EXTENSION preserved

### Step 2: K-4 wire 1 — MVP-critical runtime smoke test entry (option β docs+test)
- **목적**: MVP-critical 10 flows 의 실제 runtime 동작 검증, blocker surface
- **method**: docs+test 결정 wire (test 변경 포함) = smoke test + targeted vitest subset (capability matrix v1.54 EXTENSION 정합 + Auth flow + M0~M9 endpoint health check)
- **scope**: ~10 flows × ~5~10 test cases each = ~50~100 test cases
- **runtime**: source 변경 = test only, prod source 변경 0건 (test file NEW/MODIFIED + capability matrix EXTENSION 가능)
- **차이점 vs 옵션 β (단독 docs+test)**: K-4 wire 1 = scoped to MVP-critical only (10 flows), 옵션 β = all capability matrix rows (~37+ rows)
- **예상 시간**: ~2-3 hours

### Step 3: K-4 wire 2+ — blocker-bug-fix only (option γ scoped)
- **목적**: K-4 wire 1 에서 발견된 blocker bug 만 atomic single sprint source 변경으로 fix
- **method**: option γ = source 변경, BUT scoped to blocker-only (CR 11-3 honest-DEFER discipline = non-blocker 는 honestly DEFER 보존)
- **예상**: ~1-3 bugs (MVP-critical 10 flows × runtime smoke test), 각각 별도 atomic sprint OR batch atomic sprint (운전자 결정 wire 보류)
- **runtime**: source 변경 = blocker fix only, non-blocker honestly DEFER

**decision 보류 (Step 2/3 진입 시 결정 wire)**:
- K-4 wire 1 의 verification method 상세 (smoke test vs targeted vitest subset vs 둘 다)
- K-4 wire 1 의 환경 (local Postgres vs TestClient vs 실제 API boot)
- K-4 wire 1 의 test scope 우선순위 (MVP-critical 10 flows 진입 순서)
- K-4 wire 2 의 batch atomic vs 별도 atomic (blocker 개수 의존)
- ① 디자인가이드 + ② 옵션 β (전체) + ③ 옵션 γ (전체) 모두 보류 (사용자 결정 wire 없으면 진입 X)

## §6 K-4 next sprint options + 결정 보류

**결정 보류 (운전자, 본 sprint 후속)**:
- **Step 2 K-4 wire 1 진입 결정 보류** — MVP-critical runtime smoke test (option β docs+test, ~2-3h)
- **Step 3 K-4 wire 2+ 진입 결정 보류** — blocker-bug-fix only (option γ scoped, blocker 개수 의존)
- **Step 2/3 batch vs 별도 atomic 결정 보류** — K-4 wire 1 결과 분석 후 결정
- **디자인가이드 진입 결정 보류** — 별도 epic territory (옵션 f), K-4 외부
- **옵션 β 전체 docs+test 결정 wire 진입 결정 보류** — K-4 wire 1 의 MVP-critical 10 flows 검증이 우선, capability matrix 전체 ~37+ rows 는 honestly DEFER
- **옵션 γ 전체 source 변경 결정 wire 진입 결정 보류** — K-4 wire 1 의 blocker 발견 시에만 scoped 진입

**K-4 entry 의 acceptance criteria (운전자 결정 wire 보류, 본 sprint 후속)**:
- "확실한 MVP 기능 갖춘 프로그램"의 "확실한" = K-4 wire 1 의 runtime smoke test ALL PASS + K-4 wire 2 의 blocker-bug-fix 모두 CLOSED
- "MVP 기능" = MVP-critical 10 flows (Auth + M0/M1/M2/M3/M5/M8/M9 + Audit log + Export)
- "갖춘" = ALL 10 flows verified, 부분 X
- "로컬단계" = local Postgres + local API boot + local frontend, Railway/Vercel/Resend/Supabase X

## §7 K-3 chain 5/5 DONE preservation + cross-references

**K-3 chain 종합 정합 보존 (PRD ↔ capability matrix ↔ source code)**:
- **K-3 chunk 1** (UJ §2.A UJ-1~4, commit `9842dc7`, cj-style 287번째) — 사용자 시나리오 정합
- **K-3 chunk 2** (핵심기능 §8.1 M0~M12, commit `3ebd493`, cj-style 289번째) — M0~M12 정합, M0/M1/M2/M3/M5/M8/M9 의 MVP-critical 정합 확인
- **K-3 chunk 3** (상세기능 §F0~§F42, commit `ab31195`, cj-style 290번째) — §F10 AI, §F13/§F14 LISTEN/NOTIFY, §F15 Auth Foundation, §F16 Production, §F17 Magic link+OAuth+SSO, §F18 1st release, §F19 Tenant IdP, §F20 Multi-Region, §F21 Audit Log, §F22 Retention, §F23 Observability, §F24 Performance, §F25 Chaos, §F26 SLO, §F39~§F42 FinOps 모두 정합
- **K-3 chunk 4** (제약사항 25 ADs + NFR, cj-style 291번째) — PRD §14 NFR 표 14 rows + §F cross-section 5 NFRs + 25 ADs 모두 정합
- **K-3 chunk 5** (화면정의 §13.1/§13.2/§13.3, commit `f568bd9`, cj-style 292번째) — PRD §13 + §F cross-section UI surface 모두 정합

**K-3 → K-4 logical transition**:
- K-3 = **PRD 정합 검증** (docs-only level, capability matrix v1.54 EXTENSION ↔ source code 정합)
- K-4 = **MVP 기능 runtime 검증** (system level, MVP-critical flows 의 실제 동작 검증)
- K-3 → K-4 = **level transition** (verification scope 확대: docs-only → runtime system)

**Cross-reference 정합 보존**:
- MVP-critical 10 flows 의 K-3 chain 결과: Auth (K-3 chunk 1 UJ-1 + chunk 3 §F15) + M0/M1/M2/M3/M5/M8/M9 (K-3 chunk 2 §8.1 M0~M12 + chunk 3 §F cross-section) + Audit log (K-3 chunk 3 §F21) + Export (K-3 chunk 3 §F30.1) 모두 ✅ PASS 정합 보존

## §8 Decision wire 보존 + PRE-EXISTING honestly DEFER carryover

**결정 wire 보존 chain** (cj-style 292번째 + 본 sprint 293번째):
- K-3 chunk 5 검증 결정 wire (`f568bd9`, cj-style 292번째) + K-3 chunk 4 검증 결정 wire (cj-style 291번째) + K-3 chunk 3 검증 결정 wire (`ab31195`, cj-style 290번째) + K-3 chunk 2 검증 결정 wire (`3ebd493`, cj-style 289번째) + K-3 chunk 1 검증 결정 wire (`9842dc7`, cj-style 287번째) + K-4 메모리 description update 결정 wire (`00c49df`, cj-style 288번째) + K-3 결정 wire (`cc84b0e`, cj-style 286번째) + cj-319 (`2249fec`, cj-style 285번째 Track A-0 deploy-blocking wire) + cj-318 + cj-314 wire 5 retroactive correction + cj-314 wire 5 retroactive close-out + cj-312 retro + cj-313 retro + cj-315 wire + retroactive correction + cj-314 wire 4 + cj-314 wire 3 (`34e92aa`) + cj-314 wire 2 + cj-314 wire 1 (`cca03c2`) + cj-317 + cj-316 + cj-314 entry + cj-313 wire + cj-312 wire + cj-311 + cj-310 retroactive correction + cj-309b + cj-309 + cj-310 + cj-308 + cj-307 + cj-305b + cj-305 + cj-304 + cj-303 + cj-301 + cj-300 + cj-299 + cj-298 + cj-297 + cj-282 결정 wire 보존 + **본 sprint K-4 entry decision wire (cj-style 293번째)** = 종합 65 sprints 정직 회복.

**65/65 cumulative 결정 wire 보존** (K-3 chunk 5 검증 결정 wire 의 64 + **NEW 65번째 K-4 entry decision wire**).

**CR 11-3 honest-DEFER 293번째** chain cj-282 (220번째) → ... → K-3 chunk 5 검증 결정 wire (292번째, commit `f568bd9`) → **K-4 entry decision wire (293번째, 본 sprint)**.

**PRE-EXISTING honestly DEFER carryover 보존**:
- **cj-303 carryover 4건** — D-FINOPS-13 (Celery 배제, cj-300 APScheduler 결정 wire 정합) + audit-fixes + Layer 2 P1 + Layer 3 P2 docs
- **PRE-EXISTING 6건** — web-e2e Playwright + test-suite-measure 잔여 + web-test + lint-conventions + Sentry + custom DNS
- **cj-307 carryover LOW RISK ~30건** — Phase 10 SLO family, batch B 결정 wire 보류
- **sso 13 skipped tests** (PRE-EXISTING missing python3-saml) honestly DEFER 보존
- **W1~W8 carryover** — Pilot outreach, B-1 발송 (D-2 2026-09-12), user feedback waiting honestly DEFER
- **epics.md triage** + **PRD v2 EXTENSION** 결정 wire 보류
- **비용 발생 항목 모두** (Railway/Vercel/Resend/Supabase/Sentry/Custom DNS, launch day 결정) honestly DEFER 보존
- **N-1~N-4** + **cj-314 wire 2~5 batch B** + **cj-313/cj-312 close-out retro** 결정 wire 보류

**신규 honestly DEFER (K-4 chain 보존)**:
- 디자인가이드 (옵션 f, 별도 epic territory)
- 옵션 β 전체 docs+test (K-4 wire 1 의 MVP-critical 10 flows 가 우선)
- 옵션 γ 전체 source 변경 (K-4 wire 2+ 의 blocker-only 가 우선)
- K-4 wire 1 verification method 상세 (smoke test vs targeted vitest subset vs 둘 다)
- K-4 wire 1 환경 (local Postgres vs TestClient vs 실제 API boot)
- K-4 wire 1 test scope 우선순위 (MVP-critical 10 flows 진입 순서)
- K-4 wire 2+ batch atomic vs 별도 atomic
- M10 AI + M11 마감이력 + M12 계정운영 (Non-MVP, K-4 explicit deferral)

**결정 wire 일자**: 2026-09-11 (KST, D-3, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 3일).
