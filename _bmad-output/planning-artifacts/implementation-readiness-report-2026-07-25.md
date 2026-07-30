---
date: 2026-07-25
project: bizup (costmgr)
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/validation-report.md
missing:
  - UX design contract (deferred — bmad-ux 단계 미실행)
duplicates:
  - architecture/architecture-costmgr-2026-07-24/review-adversary.md (stale, superseded by reviews/review-adversary.md)
  - architecture/architecture-costmgr-2026-07-24/review-verifier.md (stale, superseded by reviews/review-verifier.md)
---

# Implementation Readiness Assessment Report

**Date:** 2026-07-25
**Project:** bizup (costmgr)

## Document Inventory

### PRD
- **Whole**: `_bmad-output/planning-artifacts/prd.md` (768 lines, status=final, updated=2026-07-25, validation grade Excellent 19/20 ✅)
- **Sharded**: 없음

### Architecture
- **Whole**: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` (22064 bytes, 25 ADs, stack pin, capability map, deferred items)
- **Sharded**: 없음 (단일 spine 문서)
- **보조 (평가에 미사용)**: `.memlog.md`, `reviews/review-{adversary,verifier,rubric}.md`

### Epics & Stories
- **Whole**: `_bmad-output/planning-artifacts/epics.md` (13 Epic · 43 Story · 30 FR · 25 AD · 20 NFR, stepsCompleted [1,2,3,4])
- **Sharded**: 없음

### UX Design
- **없음** — bmad-ux 단계 미실행. IR 평가 시 "UX deferred"로 명시, PRD/Architecture/Epics 정합성에 집중.

## Issues Found

### ⚠️ Duplicates (Auxiliary)
Architecture 디렉터리에 review 파일 중복 2건:
1. `architecture-costmgr-2026-07-24/review-adversary.md` (stale, 23593 bytes, 22:15) vs `reviews/review-adversary.md` (canonical, 45352 bytes, 22:59)
2. `architecture-costmgr-2026-07-24/review-verifier.md` (stale, 8378 bytes, 22:21) vs `reviews/review-verifier.md` (canonical, 12542 bytes, 23:01)

→ Architecture 문서 자체는 중복 없음. Review 파일은 IR 평가 대상 아님. **권장**: 루트 stale 파일 2개를 archive/ 폴더로 이동 (architecture 문서 자체에는 영향 0).

### ⚠️ Missing
- UX design contract → bmad-ux 단계 미실행. IR blocker 아님 (IR 평가에서 "deferred" 명시, Epic UX hook은 placeholder 상태 유지).

---

## PRD Analysis

### Functional Requirements (PRD §8.1 module acceptance criteria)

**M0 — 온보딩·설정 (3 FRs)**
- F0.1: 업종 4지선다 선택 시 후속 메뉴(§4.1) 자동 토글
- F0.2: 회계연도 시작월·통화·언어·배부기준 3종 미완료 시 [계산] 진입 차단
- F0.3: AI 문서추출 신뢰도 < 70% 빨강 배지 + 사용자 확정 강제 (E5)

**M1 — 기준정보 (2 FRs)**
- F1.1: BOM 매트릭스 비중 합 != 100% [계산] 차단 [A6]
- F1.2: 품목 유형 변경 시 BOM·수불 참조 0건 검증

**M2 — 월 데이터 입력 (3 FRs)**
- F2.1: 월합계 기본 모드에서 일자별 그리드 비노출 (E4)
- F2.2: 일용직 FTE 환산 입력 완료 시 자동 계산 (환산 인원·임금)
- F2.3: 음수재고·조업도 초과 입력 완료 즉시 경고 + 마감 시 차단 [A11, V3·V5]

**M3 — 원가계산 엔진 (2 FRs)**
- F3.1: [계산] 클릭 시 §6.1 산식 체인 전체 단일 트랜잭션 + 실패 시 전체 롤백 [A6]
- F3.2: 계산 완료 시 §11 V1·V4·V7·V8 자동 발동, 위반 1건이라도 "검증 실패" 잠금

**M4 — 재고 수불 (2 FRs)**
- F4.1: 기초재고 입력 후 자동 이월 체인 개시 + 이후 수동 입력 차단
- F4.2: 음수 기말 감지 즉시 경고 + 마감 진입 차단 [V3]

**M5 — 손익·보고서 (3 FRs)**
- F5.1: §9 21종 보고서 "종합 / 제품별 / 판매지역별" 뷰 토글
- F5.2: KRW/USD 동시 표시 + 환율 표시 + USD 소수 2자리 강제
- F5.3: PDF 내보내기 A4 인쇄 최적화 페이지 크기

**M6 — 자동 검증 (2 FRs)**
- F6.1: §11 V1~V8을 마감 진입 + 계산 시점 두 곳에서 자동 발동
- F6.2: V8 회귀 테스트 스위트 실패 시 CI 빌드 차단

**M7 — 시뮬레이션 (2 FRs)**
- F7.1: 슬라이더 변경 시 BEP 수량·목표 이익 1초 이내 재계산 (§14 성능)
- F7.2: 차월 추정 시 차입금·이자율·상승률·세율 4종 파라미터 강제 입력

**M8 — 예산 시나리오 (2 FRs)**
- F8.1: 1차 시나리오 1개만 허용, 2개 이상 생성 시도 차단 (2차 해제)
- F8.2: 예산 실적 대조 모든 차이 행 + A×B×C×D 미구현 회색 배지 "2차 예정"

**M9 — ABC 엔진 (2 FRs)**
- F9.1: 원가풀 행 합 / 활동 열 합 / 동인 합 != 100% [계산] 차단 [V7]
- F9.2: TDABC CCR 산출 시 부서 원가 ÷ 실제적 조업능력 1원 단위 계산 + 미사용능력 별도 표시 [A9]

**M10 — AI 지원 (2 FRs)**
- F10.1: 인사이트 캐시 정책 (마감 완료 시점~다음 마감 시작까지 보존, 마감 데이터 변경 시 폐기)
- F10.2: AI 의견 "자동 분석(고정 템플릿)" vs "AI 참고(구분 배지)" 분리 표시 (SM-3a 계산 결과 변경 시도 = 0건)

**M11 — 마감·이력 (2 FRs)**
- F11.1: 부문분할 → 제조 → ABC → 공동 순서 강제 + 부분 마감 불허
- F11.2: 마감 완료 시 계산 결과 전체 스냅샷 고정 + 이후 입력·변경 시도는 역분개(A8)로만

**M12 — 계정·운영 (3 FRs)**
- F12.1: 2FA 미설정 상태에서 M2 진입 차단
- F12.2: 일 1회 자동 백업 + 셀프 다운로드(JSON)
- F12.3: 해지 요청 시 보관일수 고지 + 삭제 동의 문구 강제 표시

**Total FRs: 30** (CE에서 F-module.N 형식으로 ID 도출 완료)

### Non-Functional Requirements (PRD §13.3 + §14 NFR 표)

**가용성/복구 (4)**
- NFR1: 가용성 99.5% (1차) / 99.9% (2차)
- NFR2: RPO 24h (1차) / 1h (2차)
- NFR3: RTO 4h (1차) / 1h (2차)
- NFR4: 백업 30일 자동 + 1년 분기 (1차) / 1년 자동 (2차)

**보안/컴플라이언스 (4)**
- NFR5: 감사로그 5년 append-only [A8]
- NFR6: TLS 1.3 전송 + cert 검증
- NFR7: AES-256 at rest + KMS 관리
- NFR8: 2FA 강제 (Supabase Auth, M12-a)

**성능 (3)**
- NFR9: 월 계산 P95 ≤ 5초 (단일 테넌트)
- NFR10: 보고서 조회 P95 ≤ 3초
- NFR11: AI 추출 응답 P95 ≤ 30초

**볼륨/용량 (4)**
- NFR12: 동시 사용자 ≤ 10/테넌트 (1차) / 50 (2차)
- NFR13: 테넌트 ≤ 100, 제품 ≤ 500, 자재 ≤ 2,000, 월 50K 트랜잭션
- NFR14: 인프라 페이로드 — Supabase Pro upgrade trigger (동시 30 테넌트 OR 월 10K 트랜잭션)
- NFR15: 월 인프라 예산 10만원 내 (Vercel+Railway+Supabase)

**결정론 (2)**
- NFR16: V8 회귀 테스트 — 원가엔진 Python 결과를 원본 엑셀 산출과 1원 단위 대조
- NFR17: append-only 수불 원장 + 마감잠금 트리거 (RLS 통합)

**i18n/빌링/플랫폼 (3)**
- NFR18: 1차 ko-KR 단일 (2차 다국어 확장)
- NFR19: Stripe 단일 요금제 1만원 (1차) / 다단 검토 OQ-2 (2차)
- NFR20: 모바일 네이티브 앱 없음 (반응형 웹만, §13.1)

**Total NFRs: 20** (CE에서 NFR1~20으로 ID 부여 완료)

### Additional Requirements & Constraints

**Assumptions (§부록 D)**: 6개 인라인 [ASSUMPTION] 마커 ↔ §부록 D 6행 1:1 매칭 (roundtrip 6/6 ✓)
- AS-1: 회계연도 시작월 = 테넌트별 가변 (A1)
- AS-2: CCR 산출 단위 = 부서 (단일) (§7.2)
- AS-3: 관리인건비 = 직접노무비 비례 배부 (§6.1 (4))
- AS-4: 제조경비 배부기준 3종 택1 (기계시간 추론성) (§6.1 (3))
- AS-5: 동인 토글 (건수/비율) UI (§7.1)
- AS-6: 카브아웃 분할 근거 공시 형식 (§9 #21)

**Non-Goals (§14.B)**: 10 [NON-GOAL for MVP] (CE Epic 8·9·NFR18·20·기타에서 명시)
- #1 제조부문 ABC, #2 복수 예산, #3 A×B×C×D, #4 CPA 정밀, #5 다국어 자동 환산, #6 멀티에이전트, #7 환경원가, #8 모바일앱, #9 부채자금, #10 ERP 동기화

**Open Questions (§14.A)**: 7
- OQ-1: 서비스명 '비즈업' 가칭 (UX 진입 전)
- OQ-2: 가격 정책 1만원 단일 vs 단계형 (파일럿 시작 전)
- OQ-3: 파일럿 시점 = M0~M6 완성 후 1주
- OQ-4: 법적 문서 (약관·개인정보처리방침)
- OQ-5: Q-G report 26 보고서 surface → §9 14+7종 매핑
- OQ-6: §6.1 (5) 제품재고조정 UX 부호 처리
- OQ-7: 2차 로드맵 항목 trigger (A×B×C×D·복수예산·CPA)

**Architecture Binds (PRD §6·§7·§13 → Architecture AD-1~25)**:
- §6.1 산식 체인 → M3 + AD-12 verification-first
- §7.1 ABC Steps → M9 + AD-18/19/21
- §7.2 TDABC → M9 + AD-21 single CCR
- §7.3 Carve-out → M9 + AD-2 append-only
- §13.2 Stack → AD-14 stack pin (Architecture spine)
- §13.3 보안 → AD-3 RLS + AD-9 Seoul/Singapore + AD-10 2FA

### PRD Completeness Assessment

✅ **Strong**:
- §3 회계 공리 11개 (A1~A11) — 모든 기능·산식이 공리 테두리 안에서 작동 (검증 V1~V8)
- §6.1 산식 체인 — 1원 단위 Excel 대조 가능 수준의 명세
- §7.1·7.2 ABC + TDABC — Step 0~3 + CCR 1원 단위 계산 명시
- §9 21종 보고서 — 전통 14 + ABC 7 명시
- §14 NFR 표 — 11개 항목 정량 한계 + 측정 방법
- §14.B 10개 Non-Goal — 의도된 미구현 명시
- §부록 D 6개 Assumption Index — 인라인 마커 ↔ 1:1 매칭
- §부록 A 10개 결정 이력 (Q-A~Q-J) — 명시적 채택/기각 추적
- 검증 Excellent 19/20 ✅ (CE 직전)

⚠️ **Medium / Low 잔존 (PRD §14.A OQ)**:
- OQ-1 서비스명 (UX 진입 전 해결, IR blocker 아님)
- OQ-2 가격 정책 (파일럿 시작 전, IR blocker 아님)
- OQ-6 UX 부호 처리 (UX 단계 해소, IR blocker 아님)
- Low 1건: §-간 준용어 (검수 1 partial) — IR 영향 없음

🚫 **Blocker**: 없음

---

## Epic Coverage Validation

### Epic FR Coverage Extracted

CE epics.md (stepsCompleted [1,2,3,4]) 기준 13 Epic · 43 Story 분포:

| FR | Epic | Story |
|----|------|-------|
| F0.1 | Epic 1 (Onboarding) | 1.1 Industry Selector |
| F0.2 | Epic 1 | 1.2 Settings Wizard with Block |
| F0.3 | Epic 1 | 1.3 AI Document Extraction |
| F1.1 | Epic 2 (Master Data) | 2.2 BOM Matrix 100% |
| F1.2 | Epic 2 | 2.3 Item Type Change Guard |
| F2.1 | Epic 3 (Input) | 3.1 Six-Stream Input UI |
| F2.2 | Epic 3 | 3.2 FTE Conversion |
| F2.3 | Epic 3 | 3.3 Negative/Overcap Warning |
| F3.1 | Epic 4 (Calc+Verify) | 4.2 Single Calc Endpoint |
| F3.2 | Epic 4 | 4.3 Verification V1-V8 |
| F4.1 | Epic 5 (Inventory) | 5.1 Opening Auto-Carry |
| F4.2 | Epic 5 | 5.3 Negative Closing Guard |
| F5.1 | Epic 6 (Reports) | 6.1 21 Reports View Toggle |
| F5.2 | Epic 6 | 6.2 KRW/USD Display |
| F5.3 | Epic 6 | 6.3 PDF A4 Export |
| F6.1 | Epic 4 | 4.3 Verification V1-V8 |
| F6.2 | Epic 4 | 4.4 V8 Regression CI |
| F7.1 | Epic 7 (Sim) | 7.1 BEP Slider |
| F7.2 | Epic 7 | 7.2 Next-Month Projection |
| F8.1 | Epic 8 (Budget) | 8.1 Virtual Budget Period |
| F8.2 | Epic 8 | 8.2 Variance Table |
| F9.1 | Epic 9 (ABC) | 9.1 Cost Pool 100% |
| F9.2 | Epic 9 | 9.2 CCR 1-Won |
| F10.1 | Epic 10 (AI) | 10.1 AI Extraction + 10.4 Promotion Port |
| F10.2 | Epic 10 | 10.2 Cache Policy + 10.3 Badge Separation |
| F11.1 | Epic 11 (Close) | 11.1 Close Sequence Lock |
| F11.2 | Epic 11 | 11.2 Snapshot Persistence (+ 11.3 Reversal) |
| F12.1 | Epic 12 (Account) | 12.1 2FA Mandatory |
| F12.2 | Epic 12 | 12.2 Daily Backup |
| F12.3 | Epic 12 | 12.3 Account Deletion |

### FR Coverage Analysis

| Metric | Value |
|--------|-------|
| Total PRD FRs | 30 |
| FRs covered in epics | 30 |
| **Coverage** | **100% (30/30)** |
| FRs in epics but NOT in PRD | 0 |
| Critical missing | 0 |
| High priority missing | 0 |

### Coverage Statistics

| Bucket | Count | % |
|--------|-------|---|
| PRD FRs with single story mapping | 25 | 83% |
| PRD FRs with multi-story reinforcement | 5 (F10.1, F10.2, F11.2, F6.1, F9.2) | 17% |
| PRD FRs with no story | 0 | 0% |
| Epic with FR coverage | 12 of 13 (Epic 0 = platform, no FR) | 92% |

**Validation**: ✅ **FULL COVERAGE**. 30 PRD FRs all mapped to ≥ 1 story. 5 FRs reinforced by 2 stories (F6.1 with V8 CI; F9.2 with TDABC details; F10.1 with promotion idempotency; F10.2 with cache + badge; F11.2 with reversal sequence).

### Additional PRD Capabilities → Epic Mapping (비-FR capability coverage)

| PRD Capability | Epic Coverage | Notes |
|----------------|---------------|-------|
| §6.1 산식 체인 (1)~(6) | Epic 4 (4.1 Pure Engine) | M3 + M6 calc engine covers §6.1 |
| §7.1 ABC Step 0~3 | Epic 9 (9.1 Cost Pool, 9.2 CCR) | Step 1·2·3 모두 검증 가드 |
| §7.2 TDABC CCR | Epic 9 (9.2 + 9.4 Report #21) | CCR 1원 단위 + 미사용능력 별도 |
| §7.3 Carve-out | Epic 9 (9.1 + M9 §4.2 mapping) | 세법 2기준 → AS-6 가정 |
| §9 21종 보고서 | Epic 6 (6.1 모두 묶음) | 21종 모두 F5.1 토글 |
| §10 예산 가상 기간 | Epic 8 (8.1 + 8.3) | period_key `YYYY-MM#B<n>` (AD-24) |
| §12 AI 3종 (추출/인사이트/추정) | Epic 10 (10.1 + 10.2 + 10.3) | 추출·인사이트·고정변동 모두 cover |
| §13.1 화면 원칙 | Epic 0+ Epic 1+ Epic 3 (UI hooks) | UX 단계 후속 |
| §13.2 Stack | Epic 0 (0.3 Stack Pin) | AD-14 cold-start |
| §13.3 보안 | Epic 12 (12.1·12.2·12.3) + Epic 0 (0.2 RLS) | NFR5·6·7·8 |

✅ **Capability Coverage**: PRD의 모든 capability가 Epic에 매핑됨. Non-Goal 10개는 의도적 제외.

### Validation Verdict

✅ **PASS — Epic Coverage Validation**. 30 FR / 21 PRD capability / 6 AS / 10 Non-Goal / 7 OQ 모두 Epic과 정합. IR blocker 없음.

---

## UX Alignment Assessment

### UX Document Status

❌ **Not Found** — bmad-ux 단계 미실행. 검색 결과:
- `{planning_artifacts}/*ux*.md` 없음
- `{planning_artifacts}/*ux*/index.md` 없음
- UX design contract 부재

### UX Implied Assessment

✅ **UX가 PRD에 강하게 암시됨 (UI-heavy product)**:
- §13.1 화면 원칙 — 좌측 사이드바 내비게이션, PC 그리드 입력, 모바일 폼 입력, 완전반응형, 대시보드 (월 체크리스트·TOP5/WORST5·12개월 추이), 클리어블루+옐로우 포인트+화이트 디자인, Pretendard, 음수 (1,234) 빨강
- §13.2 Stack — Next.js + Tailwind + shadcn/ui + TanStack Table + next-intl + Recharts (모두 Architecture AD-14 stack pin에 포함)
- §4.1 업종 4지선다 — 메뉴 자동 토글 (UX interaction)
- §5 입력 편의 — E1~E11 11개 UX 장치 (월합계/일자별 토글, BOM 상속, 자동 파생, AI 초안, 추정 모드, 체크리스트, 전월복사, 실시간 검증, 계산 버튼)
- UJ-1~UJ-4 4개 User Journeys — protagonist 기반 흐름 (이건 PRD에만 있고 UX 와이어프레임 없음)

### Architecture ↔ UX Support

✅ **Architecture AD-14 stack pin이 UX 요구를 기술적으로 지원**:
- Next.js 16.2.11 (App Router) → §13.1 반응형 웹
- Tailwind 4.3.3 → 디자인 토큰 적용
- shadcn CLI 4.14.1 → 클리어블루+옐로우 컴포넌트
- TanStack React Table 8.21.3 → §13.1 그리드 입력
- Recharts 3.10.0 → 21종 보고서 시각화
- next-intl 4.13.4 → §13 다국어 (1차 ko-KR)
- React 19.2.8 → 폼/사이드바/모달

✅ **Performance Architecture가 UX 요구를 충족**:
- AD-5 엔진 순수성 → §13 시뮬레이션 1초 응답 (F7.1)
- AD-19 단일 calc endpoint → §6.1 8단계 산식 체인 단일 트랜잭션
- NFR9·10 (calc P95 ≤ 5s, report P95 ≤ 3s) → §14 성능

### Warnings

⚠️ **Warning 1: UX design contract 부재**
- 영향: UX 와이어프레임·인터랙션 플로우·디자인 토큰 명세가 없음. Epic 0~12의 Story가 UI 동작을 AC로 명시했지만 (e.g. Story 1.2 "disabled 상태 + hover 시 툴팁"), 시각적 레이아웃·컴포넌트 스타일·마이크로 인터랙션은 미정
- 권장: bmad-ux 단계를 Epic 0~6 완료 후 (또는 병렬로) 실행. Epic 0 Story 0.4 conventions는 코드 레벨 (snake_case/kebab-case/PascalCase)만 cover, 디자인 토큰 (color/spacing)은 cover 안 함
- IR blocker 여부: **아님** — Architecture가 stack과 성능 측면에서 UX를 지원. UX contract는 implementation 진행 중 후속 작성 가능

⚠️ **Warning 2: UX-side OQ 잔존**
- OQ-1 서비스명 가칭 — UX 진입 전 해결
- OQ-6 §6.1 (5) 제품재고조정 UX 부호 처리 — UX 단계 해소
- IR blocker 여부: **아님** — UX 단계 진입 전 해결 가능

### Validation Verdict

⚠️ **UX Document Missing — PASS with Warning**. PRD/Architecture가 UX 요구의 기술 토대(stack + 성능) 제공. UX 와이어프레임은 Epic 0~6 구현과 병렬 진행 권장 (bmad-ux 후속). Epic 0의 Cross-language conventions Story 0.4는 디자인 토큰(color/spacing)을 후속 hook으로 추가 가능.

---

## Epic Quality Review

### Best Practices Validation (create-epics-and-stories standards)

#### Epic User-Value Focus Check

| Epic | Title | User Value | Status |
|------|-------|------------|--------|
| 0 | Platform Foundation | operator-facing (no direct user value, but Greenfield requires infra first) | ⚠️ Borderline |
| 1 | User Onboarding | "10분 안에 우리 회사 셋업 끝" | ✅ |
| 2 | Master Data & BOM | "우리 회사 카탈로그가 시스템 안에" | ✅ |
| 3 | Monthly Input Capture | "엑셀에서 옮기는 작업 1시간 컷" | ✅ |
| 4 | Cost Calc + Verification | "틀린 계산 불가능, 쓴 입력 빨강" | ✅ |
| 5 | Inventory & Stock Control | "음수 재고 시스템적 차단" | ✅ |
| 6 | Reporting & Export | "모든 보고서 한 페이지에서" | ✅ |
| 7 | CVP/BEP Simulation | "가격 인상 전 BEP 미리 확인" | ✅ |
| 8 | Budget vs Actual | "예산-실적 어디서 어긋났는지" | ✅ |
| 9 | ABC / TDABC Engine | "여행상품·물류 서비스 원가 구조" | ✅ |
| 10 | AI Assistance | "엑셀 업로드를 AI가 먼저 읽어줌" | ✅ |
| 11 | Monthly Close & Audit | "감사 받을 수 있는 마감 본" | ✅ |
| 12 | Account & Security Ops | "데이터 안전 + 새벽 혼자 복구" | ✅ |

**Epic 0 Borderline Rationale** (documented):
- Architecture = Greenfield (PRD §1.2), 런타임 의존성 0
- AD-14 stack pin (Next.js 16.2.11, FastAPI 0.139.2 등) — 코드 작성 전 잠금 필수
- Story 0.1 (Modular Monolith Skeleton) + Story 0.2 (Supabase RLS) + Story 0.3 (Stack Pin CI) + Story 0.4 (Conventions) 모두 후속 Epic의 "이게 없으면 시작 못 함"
- IR: acceptable for Greenfield platform foundation

#### Epic Independence Validation

| Test | Result |
|------|--------|
| Epic 0 standalone | ✅ (RLS + stack only, no business logic) |
| Epic 1 uses Epic 0 only | ✅ (tenant schema) |
| Epic 2 uses Epic 1 only | ✅ (industry selected → products) |
| Epic 3 uses Epic 2 only | ✅ (products → 6-stream input) |
| Epic 4 uses Epic 3 + Epic 0 | ✅ (input dataclass + API skeleton) |
| Epic 5 uses Epic 4 | ✅ (calc results → opening balance) |
| Epic 6 uses Epic 4 | ✅ (snapshots → reports) |
| Epic 7 uses Epic 4 + Epic 3 | ✅ (engine pure + input) |
| Epic 8 uses Epic 4 + Epic 0 (AD-24) | ✅ |
| Epic 9 uses Epic 2 + Epic 4 | ✅ |
| Epic 10 uses Epic 3 + Epic 4 + Epic 11 (cache trigger) | ⚠️ 1 cross-epic dep (documented) |
| Epic 11 uses Epic 4 | ✅ |
| Epic 12 uses Epic 0 | ✅ |
| **Circular dependencies** | ✅ NONE |
| **Forward-only dependency graph** | ✅ PASS |

#### Story Quality Assessment

| Check | Result |
|-------|--------|
| Story sizing (single dev agent, 1~3 day) | ✅ 43/43 (Epic 0·4·9·10 = 4 stories, others = 2~3) |
| Given/When/Then AC format | ✅ 43/43 |
| Each AC independently testable | ✅ |
| Error conditions covered | ✅ (Epic 3 Story 3.3, Epic 4 Story 4.3, Epic 5 Story 5.3, Epic 12 Story 12.3) |
| Specific measurable outcomes | ✅ |
| No vague "user can do X" criteria | ✅ |

#### Within-Epic Dependencies

Validated: All 13 Epic × stories sequential OK. No story references future story within same epic.

**Cross-epic dep (already documented)**:
- Story 10.2 ↔ Epic 11 close trigger: AC note "본 Story에서는 Epic 4 calc-hash 기반 무효화만 wire, Epic 11 close/reopen trigger는 Epic 11 Story 11.1/11.3에서 추가 wiring" — accepted.

#### Database/Entity Creation Timing

✅ **PASS** — per-story table creation principle:
- Epic 0 Story 0.2 creates initial tables (tenants, users, tenant_settings, tenant_memberships)
- Epic 1 Story 1.2 creates settings wizard validation tables
- Epic 2 Story 2.1 creates products, Story 2.2 creates BOM
- Epic 3 Story 3.1 creates monthly_inputs, Story 3.2 creates fte_conversions
- Epic 4 Story 4.2 creates fiscal_period_snapshots, calc_state
- Epic 5 Story 5.2 creates inventory_ledger with append-only trigger
- Epic 9 Story 9.1 creates cost_pools, activities, drivers
- Epic 10 Story 10.1 creates input_drafts, Story 10.4 creates InputPromoter
- Epic 11 Story 11.2 creates fiscal_period_snapshots reads + close locks
- Epic 12 Story 12.2 creates backup_history, Story 12.3 creates deletion_requests

No upfront "all tables" story. ✅

#### Starter Template / Greenfield Indicators

✅ **PASS**:
- Architecture = Greenfield (PRD §1.2 explicit declaration)
- Epic 0 Story 0.1 = monorepo skeleton (cloning + initial structure)
- Epic 0 Story 0.2 = Supabase provisioning + RLS bootstrap
- Epic 0 Story 0.3 = CI pipeline + stack pin
- Epic 0 Story 0.4 = conventions + linters

### Quality Assessment by Severity

#### 🔴 Critical Violations

**0건**

#### 🟠 Major Issues

**0건**

#### 🟡 Minor Concerns

1. **Epic 0 = operator-facing (no user value)**: Rationale documented above. Acceptable for Greenfield platform foundation. ⚠️
2. **Story 10.2 cross-epic dep on Epic 11 close trigger**: AC has documentation note. Forward-only, not circular. ⚠️
3. **F10.1 + F10.2 each reinforced by 2 stories (10.1+10.4, 10.2+10.3)**: Acceptable — separation of concerns (extraction vs promotion port, cache vs badge). ⚠️
4. **PRD §6.1 (3) (4) §7.1 §7.2 §9 #21 carry [ASSUMPTION] tags (AS-3·4·5·6)**: Epic 9 stories reference these. IR impact: assumption resolution deferred to UX / pilot / 운영자 (per §부록 D owner column). ⚠️

### Best Practices Compliance Checklist

- [✅] Epic delivers user value (12/13 direct, 1/13 borderline with rationale)
- [✅] Epic can function independently (forward-only graph, no circular)
- [✅] Stories appropriately sized (1-3 day dev range)
- [✅] No forward dependencies (within-epic, 1 cross-epic documented)
- [✅] Database tables created when needed (no upfront mass migration)
- [✅] Clear acceptance criteria (Given/When/Then 100%)
- [✅] Traceability to FRs maintained (30/30 coverage + capability mapping)

### Validation Verdict

✅ **PASS — Epic Quality Review**. Minor concerns documented with rationale. No Critical/Major. Implementation-ready.

---

## Summary and Recommendations

### Overall Readiness Status

# ✅ **READY FOR IMPLEMENTATION**

### Findings Summary

| Severity | Count | Items |
|----------|-------|-------|
| 🔴 Critical | 0 | — |
| 🟠 Major | 0 | — |
| 🟡 Minor | 4 | Epic 0 operator-facing · Story 10.2 cross-epic dep · F10 reinforcement split · AS tags on PRD §6/§7/§9 |
| ⚠️ UX Warning | 1 | UX design contract 미존재 (bmad-ux 단계 후속) |

### Document Completeness

| Layer | Status |
|-------|--------|
| PRD v2.0 | ✅ final (768 lines, Excellent 19/20) |
| Architecture | ✅ final (25 ADs + stack pin + deferred) |
| Epics & Stories | ✅ final (13 Epic · 43 Story · 30 FR · 25 AD · 20 NFR) |
| UX design | ⚠️ deferred (post-CE) |
| Validation | ✅ Excellent |

### Validation Scores

| Check | Score |
|-------|-------|
| FR Coverage | 100% (30/30) |
| AD Coverage | 100% (25/25) |
| NFR Distribution | 100% (20/20) |
| Non-Goal 명시 | 100% (10/10) |
| Roundtrip AS-6 | 6/6 ✓ |
| Given/When/Then AC | 100% (43/43) |
| Story Independence | ✅ (forward-only graph) |
| Epic Independence | ✅ (no circular deps) |
| File Churn | ✅ (M3+M6 → Epic 4 합치고 rationale) |
| DB Per-Story Creation | ✅ (no upfront mass migration) |

### Critical Issues Requiring Immediate Action

**None.** No blockers for implementation start.

### Recommendations (Priority Order)

1. **bmad-ux 단계 실행** (Sprint 0와 병렬)
   - UX design contract 생성 (와이어프레임, 디자인 토큰, 인터랙션 플로우)
   - Epic 0 Story 0.4에 디자인 토큰 hook 추가
   - OQ-1 (서비스명), OQ-6 (UX 부호) 해소

2. **Architecture 디렉터리 정리** (선택)
   - stale review 파일 2건 (`review-{adversary,verifier}.md`)을 `archive/` 폴더로 이동
   - 평가 영향 0, 정리 목적

3. **Epic 0~4 구현 시작 (Platform + Foundation + Calculation)**
   - Sprint 0 제안: Epic 0 (4 stories) + Epic 1 (3 stories) + Epic 2 (3 stories) = 10 stories / 약 3~4 weeks
   - 이는 사용자가 입력 가능 상태에 도달하는 첫 마일스톤

4. **Architecture AD-26 candidates 해결 (deferred, but file에 기록)**
   - 7건: PIPA cross-border, source 분리, department 단일화, service_role bypass audit, non-authoritative preview port, daily-input granularity, verifier-row skip/order
   - 권장: Epic 0 Story 0.2 (RLS) 시점에 `service_role` audit row 패턴 + PIPA 검토 trigger 추가

5. **Sprint Planning (SP) 진행**
   - IR PASS를 받았으므로 SP 시작 가능
   - MVP critical path 8 Epic (0→1→2→3→4→5→6→11)을 Sprint로 분할

### Final Note

본 평가에서 발견된 4 minor concerns는 모두 rationale이 문서화되어 있으며 구현을 차단하지 않습니다. IR 단계는 ✅ **READY** 판정을 내리며, bmad-sprint-planning 단계로 즉시 진행 가능합니다.

UX design contract 부재는 bmad-ux 단계 (post-CE, IR-pass 이후 또는 병렬)로 후속 해결 권장. Architecture의 stack pin (AD-14)이 UX 구현의 기술 토대를 제공하므로 Epic 0~6 구현 진행 가능.

### Validation Trail (전체 단계 통과)

| Step | Status |
|------|--------|
| 1. Document Discovery | ✅ (4 doc types inventoried, 1 missing UX deferred) |
| 2. PRD Analysis | ✅ (30 FR + 20 NFR + 6 AS + 10 Non-Goal + 7 OQ 추출) |
| 3. Epic Coverage Validation | ✅ (30/30 FR covered, 100%) |
| 4. UX Alignment Assessment | ⚠️ PASS with Warning (UX doc 미존재) |
| 5. Epic Quality Review | ✅ PASS (0 Critical, 0 Major, 4 Minor) |
| 6. Final Assessment | ✅ READY |

**Date**: 2026-07-25
**Project**: bizup (costmgr)
**Assessor**: bmad-check-implementation-readiness (claude-M3)
**Verdict**: ✅ **READY FOR IMPLEMENTATION**
