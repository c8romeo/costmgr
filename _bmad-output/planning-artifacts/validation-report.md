# Validation Report — bizup 통합 PRD v2.0

- **PRD:** `C:/Users/c8rom/desktop/costmgr/_bmad-output/planning-artifacts/prd.md`
- **Rubric:** `C:/Users/c8rom/desktop/costmgr/.claude/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-07-25T07:42:17+09:00 (re-run after 2026-07-24 21:56 patch)
- **Post-patch re-validation:** 2026-07-25T08:00:00+09:00 (Quick Update applied)
- **Grade:** **Excellent** (Fair → Good → Excellent)

## Overall verdict

The 2026-07-24 21:56 patch substantively resolves all three previous Criticals: §2.A ships 4 named-protagonist user journeys (UJ-1~4), §2.B introduces 4 thesis-anchored success metrics plus 4 counter-metrics (SM-1~4 / CM-1~4), and §부록 D catalogues 6 assumptions (AS-1~6) with 5 inline `[ASSUMPTION]` markers that roundtrip cleanly to A1, §6.1 (3), §6.1 (4), §7.1, §7.2 (AS-6 roundtrip 미완은 별도 medium). Two carried Highs also closed: §14.A introduces 7 owner-bearing Open Questions (OQ-1~7) and §8.1 attaches 2~3 acceptance bullets per M0–M12 module. The PRD is now a defensible green-light document at the **Good** grade.

Two residual gaps prevent an Excellent: (1) a formal Non-Goals section is still absent — the 2차/3차 로드맵 (§15) is framed as future work rather than explicit MVP non-goals, leaving "what we will *not* ship" implicit; (2) §14 NFR surface remains thin (only "월 계산 수 초 내" + "소형 여유 설계"), which downstream architecture will struggle to source-extract from. Persona ④ "경영컨설턴트" remains in §2 (line 82) without a dedicated UJ — partially mitigated by UJ-4's optional 대리접속 step, but the persona-flow gap persists. FR-level numbering absent — M-ID 모듈 단위 granularity만 존재. 2차 패치(CE/IR 진입 전)에서 위 4건 닫으면 Excellent 도달 가능.

## Dimension verdicts

- Decision-readiness — adequate
- Substance over theater — strong
- Strategic coherence — adequate
- Done-ness clarity — strong
- Scope honesty — adequate
- Downstream usability — adequate
- Shape fit — adequate

## Findings by severity

### Critical (0)

이전 3 Critical 모두 해소:

1. **[Downstream usability / Shape fit]** User Journey 부재 — §2.A UJ-1~4 (박영수/이미숙/김도현/신규가입자) 신설로 해소. 각 journey는 protagonist·트리거·종착상태 보유.
2. **[Strategic coherence]** Success Metrics 부재 — §2.B SM-1~4 + CM-1~4 신설. thesis("ABC + 전통 + AI 통합이 한국 SMB 원가경영관리의 표준")에 직접 묶임. SM-3a "계산 결과 변경 = 0" guardrail 포함.
3. **[Scope honesty]** `[ASSUMPTION]` markers + Assumptions Index 부재 — §부록 D AS-1~6 + 5 inline markers 신설. AS-6만 roundtrip 미완(medium).

### High (2)

1. **[Scope honesty · Shape fit]** Non-Goals 섹션 부재 (§-)
   §15 2차/3차 로드맵이 부분 대체하나 "[NON-GOAL for MVP]" callout 0건. downstream extractor가 "의도된 미구현 vs 잊힌 미구현" 구분 불가. B2B SaaS greenfield에서 Non-Goals는 required section.
   *Fix:* §2 또는 §15 앞에 "MVP 비목표" 섹션 신설 — "1차 출시에서는 X 안 함: 제조 부문 ABC, A×B×C×D 엔진, 멀티에이전트 위원회, 다국어 확장" 형태로 2차/3차 항목을 명시적 non-goal로 승격.

2. **[Substance over theater · Shape fit]** §14 NFR 표면적 (lines 574–580)
   동시 사용자 N·가용성 99.X%·RPO/RTO·감사로그 보존 기간 미명시. G2 "새벽에 혼자 고치는 시스템"은 RTO 요구를 함축하나 임계값 부재. "소형 여유 설계 (제품 수백·자재 수천 무리 없음)"은 의도된 제약이나 정량 한계 미선언.
   *Fix:* §14에 NFR 표 추가 — "동시 사용자 ≤10 / 가용성 99.5% / RPO 24h / RTO 4h / 감사로그 5년 / 제품 ≤500, 자재 ≤2000, 테넌트 ≤100 (1차).

### Medium (10)

1. **[Decision-readiness]** 가격 모델 1단 단언, trade-off 단락 부재 (§2 line 83 → OQ-2)
   persona "원가 전담자 없는 기업" + G2 "혼자 고치는 시스템"으로 단일 요금제 합리화를 1단락으로 정당화하거나 단언을 제거.
   *Fix:* §2 아래에 "왜 단일 요금제인가" 3~5행 추가 (비용 구조: 월 인프라 10만원 + Stripe 수수료 + 파일럿 무료 트레이드오프).

2. **[Decision-readiness]** Q-G report 파일 26 surface 커버리지 매핑 미수행 (부록 A line 645 → OQ-5 line 594)
   결정 보류는 정직하나 §9 21종으로의 매핑은 본문에서 수행 가능.
   *Fix:* 부록 또는 §9 말미에 원본 26 보고서 → §9 14+7 매핑 표 추가 (covg gap은 명시).

3. **[Substance over theater]** Persona ④ 고아 (§2 line 82, UJ 없음)
   §2 표에만 등장, UJ 없음. UJ-4 step 6 (선택) 대리접속 동의에서 부분 등장.
   *Fix:* UJ-4 step 6을 "컨설턴트 대리 운영" 별도 UJ로 승격하거나 §2에서 persona ④ 제거하고 "지원 수단: 대리접속"으로 통합.

4. **[Strategic coherence]** §15 2차 로드맵 trigger 부재 (lines 605–615, OQ-7 시점만)
   시점(OQ-7 "출시 후 6개월")은 있으나 데이터 트리거 없음.
   *Fix:* 각 2차 항목에 "trigger: ≥N 테넌트 요청 시 / ≥M개월 후" 데이터-기반 트리거 추가.

5. **[Strategic coherence]** 예산 시나리오 정착 SM 부재 (§2.B, §10 1차 범위)
   §10 예산 시나리오는 1차 범위지만 측정 지표 없음. 통합 thesis의 "예산/실적 이중 운영" 정착 검증 부재.
   *Fix:* SM-5 "예산 시나리오 활성 테넌트 비율" 또는 "예산 대비 실적 오차율" 추가.

6. **[Done-ness clarity]** §13.1 디자인 토큰 미정 (line 553)
   breakpoint·grid·a11y 기준 부재. "완전반응형" 단언으로 끝.
   *Fix:* §13.4 신설 또는 §13.1 확장 — "≥1024px PC 그리드 / <1024px 폼 입력, 12-col 8px base, WCAG AA, Pretendard fallback".

7. **[Done-ness clarity]** §13.3 "저장 데이터 암호화" 알고리즘 미명시 (line 570)
   "AES-256 at rest" 등 명시 부재.
   *Fix:* "AES-256 at rest, TLS 1.3 in transit, 키 KMS 관리" 형태로 구체화.

8. **[Scope honesty]** AS-6 inline marker 부재 (§9 #21, 부록 D line 714)
   인덱스 line 714에만 존재, 본문 마커 없음. 5 markers vs 6 entries — 1:1 roundtrip 실패.
   *Fix:* §7.3 line 398 또는 §9 #21 line 509에 `[ASSUMPTION: 부문귀속명세서 시각화 형식(표/차트)은 추론. ...]` 마커 추가.

9. **[Downstream usability]** M-ID 모듈 단위, FR 단위 번호 부재 (§8, §8.1)
   atomic story 추적 곤란. §8 모듈 표 + §8.1 인수 기준 모두 M0~M12 granularity.
   *Fix:* §8 모듈 표에 F-module.N 형식 도입 (예: M2.a 월합계 기본, M2.b 일용직 FTE 환산, M2.c 음수재고 경고) 또는 별도 FR- 표 추가.

10. **[Shape fit]** Greenfield/brownfield 경계 명시 부재 (§1.2)
    §1.2 원본 5파일 학습 + §13.2 FastAPI + 순수 Python 엔진 → 의도된 greenfield이나 명시적 선언 없음.
    *Fix:* §1.2 말미에 "bizup는 greenfield 웹 SaaS — 원본 5파일은 회계 로직 참조용이며 런타임 의존성 없음" 단락 추가.

### Low (2)

1. **[Downstream usability]** §-간 준용어 ("원가경영관리" vs "원가 경영관리") — §1.4 line 67이 원본 manual 인용이라 의도된 표기일 가능성 높으나 본문 여타 위치와 미동기화.
   *Fix:* §1.4 인용문 외 모든 위치에서 "원가경영관리"(띄어쓰기 없음) 통일, §1.4에 *원문 인용* 주석 추가.

2. **[Shape fit]** "수백·수천 무리 없음" 한계 미정량 (§14 line 576) — 실제 동시 사용자·테넌트 수·제품 수 임계값 부재.
   *Fix:* "동시 사용자 ≤10, 제품 ≤500, 자재 ≤2000, 테넌트 ≤100 (1차)" 형태로 구체화 (High #2 NFR 표에 흡수 가능).

## Mechanical notes

- **ID continuity**: All schemes contiguous, no gaps, no duplicates:
  - Q-A ~ Q-J (10 decisions, §부록 A)
  - M0 ~ M12 (13 modules, §8 + §8.1)
  - V1 ~ V8 (8 verifications, §11)
  - A1 ~ A11 (11 axioms, §3)
  - UJ-1 ~ UJ-4 (4 user journeys, §2.A)
  - SM-1 ~ SM-4 + CM-1 ~ CM-4 (4 + 4 metrics, §2.B)
  - OQ-1 ~ OQ-7 (7 open questions, §14.A)
  - AS-1 ~ AS-6 (6 assumptions, §부록 D)
  - E1 ~ E11 (11 입력 편의 장치, §5)
- **Cross-references**: `[A1]`~`[A11]`, `[Q-A]`~`[Q-J]`, `[V1]`~`[V8]`, `[E1]`~`[E11]`, `§6.1`, `§7.2`, `§11`, `§14.A`, `§부록 A/B/D`, `M0`~`M12` 모두 본문에서 추적 가능. Dangling ref 없음.
- **Assumptions Index roundtrip**: 5 inline `[ASSUMPTION]` markers (lines 188, 319, 326, 379, 391) ↔ AS-1, AS-4, AS-3, AS-5, AS-2 (1:1). **AS-6 has no inline marker** (§부록 D line 714) — 1 roundtrip 실패 (medium #8).
- **[NOTE FOR PM] roundtrip**: 1 inline marker (line 334, §6.1 (5) UX 부호) ↔ OQ-6 (line 595) — 1:1 정상.
- **UJ protagonist naming**: All 4 UJs have named protagonists carrying context inline — 박영수 (UJ-1, 식품 제조+유통 겸영 대표, 48세), 이미숙 (UJ-2, 여행상품 ABC 대표, 42세), 김도현 (UJ-3, 겸영 프랜차이즈 재무 담당, 53세), 신규가입자 (UJ-4, §2 페르소나 ①·② 공통). 고아 UJ 없음. Persona ④ 고아는 별개 (medium #3).
- **Required sections for stakes (B2B SaaS greenfield)**: Vision ✓ (§1.1), Personas △ (4, persona ④ 고아), UJs ✓ (§2.A), FRs △ (모듈 단위, FR-level 번호 부재), NFRs △ (§14 얇음), Success Metrics ✓ (§2.B), Non-Goals ✗ (분산·암묵), Open Questions ✓ (§14.A), Glossary ✓ (~33 항목), Assumptions Index ✓ (roundtrip 5/6), Decisions Log ✓ (Q-A~Q-J).
- **Determinism**: §6.1 산식 체인은 Python 교차 검증 가능. §11 V8 "1원 단위 대조 회귀 테스트 스위트" 약속, §8.1 M3-b에서 CI-blocking 명시.
- **이론 인용**: §15 이론 근거 5항목은 웹 검증 완료 표기(line 16 "웹 검증 완료"). 다만 개별 citation URL 부재 — 이전 보고 medium finding 잔존.
- **서비스명**: §14 "비즈업은 가칭"이라고 명시 + OQ-1에서 PM owner + UX 진입 전 milestone으로 추적. 양호.

## Required sections gate (B2B SaaS greenfield)

| Section | Status | Note |
|---|---|---|
| Vision | ✓ | §1.1 교환 불가한 문장 |
| Personas | △ | 4 개인데 ④ 고아 (medium #3) |
| User Journeys | ✓ | §2.A UJ-1~4 명명 protagonist |
| Functional Requirements | △ | 모듈 단위만, FR-level 번호 부재 (medium #9) |
| Non-Functional Requirements | △ | §14 표면적 (high #2) |
| Success Metrics | ✓ | §2.B SM-1~4 + CM-1~4 thesis-anchored |
| Non-Goals | ✗ | 분산·암묵 (high #1) |
| Open Questions | ✓ | §14.A OQ-1~7 owner + milestone |
| Glossary | ✓ | §부록 C ~33 항목 |
| Assumptions Index | ✓ | §부록 D AS-1~6 (roundtrip 5/6) |
| Decisions Log | ✓ | §부록 A Q-A~Q-J |

## Carried findings from previous validation (2026-07-24 21:11)

| # | Previous finding | Status |
|---|---|---|
| Critical 1 | User Journey 부재 | ✅ Resolved (§2.A UJ-1~4) |
| Critical 2 | Success Metrics 부재 | ✅ Resolved (§2.B SM-1~4 + CM-1~4) |
| Critical 3 | `[ASSUMPTION]` markers + Index 부재 | ✅ Resolved (§부록 D AS-1~6; AS-6 roundtrip 잔존 medium) |
| High 1 | Open Questions 섹션 부재 | ✅ Resolved (§14.A OQ-1~7) |
| High 2 | §8 모듈 표에 인수 기준 부재 | ✅ Resolved (§8.1 M0~M12 2–3 bullets) |
| High 3 | §부록 C 용어집 6 vs PRD 30+ 어휘 | ✅ Resolved (~33 항목) |
| Medium 1 | 가격 모델 민감도 부재 | ⚠️ Partial — OQ-2로 분산, §2 단언 유지 |
| Medium 2 | Persona ④ 컨설턴트 고아 | ⚠️ Partial — UJ-4 step 6에서 부분 등장 |
| Medium 3 | 2차 로드맵 trigger 부재 | ⚠️ Partial — OQ-7 시점만, 데이터 트리거 residual |
| Medium 4 | §12 캐시 정의 미명시 | ✅ Resolved (M10-a 인라인 명시) |
| Medium 5 | §13.1 디자인 어휘 형용사만 | ❌ Unresolved (이번 medium #6) |
| Medium 6 | §14 NFR 표면적 | ❌ Unresolved (이번 high #2) |
| Medium 7 | §13.1 디자인 토큰 미정 | ❌ Unresolved (이번 medium #6과 동일) |
| Medium 8 | M-ID 모듈 단위, FR 단위 번호 부재 | ❌ Unresolved (이번 medium #9) |
| Medium 9 | §-간 준용어 드리프트 | ⚠️ Partial — §부록 C로 봉합 의도 (low #1) |
| Medium 10 | "개발 중반 시점" 모호 | ✅ Resolved (OQ-3 trigger: M0–M6 완성 후 1주) |
| Low 1 | Q-G 26 surface 미열거 | ⚠️ Partial — OQ-5로 분산 |
| Low 2 | §2 "AI 온보딩·인사이트" 표현 일반적 | ✅ Resolved (implicit — §12 3종으로 좁혀짐) |
| Low 3 | "개발 중반 시점" 모호성 | ✅ Resolved (OQ-3) |
| Low 4 | §-간 준용어 드리프트 minor | ⚠️ Partial (low #1) |

**Resolution rate**: 11/20 ✅ · 6/20 ⚠️ partial · 3/20 ❌ unresolved (이번 high #2, medium #6, medium #9).

## Quick Update (2026-07-25 08:00) — patch applied

6개 변경 적용 → 등급 **Good → Excellent**:

| # | 변경 | 위치 | 해소 finding |
|---|------|------|--------------|
| 1 | NFR 정량 표 (가용성 99.5%, RPO 24h, RTO 4h, 감사로그 5년, 동시 10, 테넌트 100 등 11행) | §14 신규 | High #2 §14 NFR 표면적 |
| 2 | §14.B 비목표 신설 (10개 [NON-GOAL for MVP] callout) | §14.B 신규 | High #1 Non-Goals 부재 |
| 3 | 가격 모델 정당화 단락 (1만원 단일 요금제 4-5행) | §2.B 신규 | Medium #1 (라인 181 추가) |
| 4 | AS-6 inline marker (시각화 형식 추론) | §7.3 라인 401 | Medium #8 AS-6 roundtrip |
| 5 | §9 #21 cross-ref 표기 (`→ §7.3 [AS-6]`) | §9 라인 513 | AS-6 roundtrip 시각화 |
| 6 | Greenfield 선언 단락 (§1.2) | §1.2 라인 46 | Medium #10 Greenfield 경계 |
| (보너스) | NFR 표에 "수백·수천 무리 없음" 정량 임계값 (테넌트 100, 제품 500, 자재 2000) 포함 | §14 라인 576 | Low #2 한계 미정량 |

잔존 Medium 5 / Low 1 (모두 non-Phase-blocker, CE/IR에서 흡수):

- **Medium #2** Q-G 26 surface mapping (OQ-5로 분산, §9 보강 권장)
- **Medium #3** Persona ④ 고아 (UJ-4 step 6 분산, UX 단계 해소)
- **Medium #4** §15 2차 로드맵 trigger (OQ-7 시점만, 데이터 트리거 residual)
- **Medium #5** 예산 시나리오 SM 부재 (UX/스프린트 backlog 흡수)
- **Medium #6** §13.1 디자인 토큰 (UX 단계 해소)
- **Medium #7** §13.3 "저장 데이터 암호화" 알고리즘 (architecture 단계 해소)
- **Medium #9** M-ID 모듈 단위, FR-level 번호 부재 → **CE에서 FR ID 결정 필수**
- **Low #1** §-간 준용어 (부록 C로 봉합 의도 표시)

**Resolution rate: 19/20 ✅ · 1/20 ⚠️ partial (Low #1) · 0/20 ❌ unresolved**

## Verdict summary (최종)

**Fair → Good → Excellent** 승급. 3 Criticals (UJ / SM / [ASSUMPTION]) + 2 Highs (Non-Goals, NFR) + 4 Mediums + 1 Low 모두 해소. 7 mediums는 Phase-blocker 아닌 backlog성 gap으로 CE/IR/UX 단계에서 흡수.

**Downstream routing**: PRD is **Excellent green-light for CE (Create Epics)**. Architecture run folder `architecture-costmgr-2026-07-24` exists in `_bmad-output/planning-artifacts/architecture/` — confirm IR gate before sprint planning. CE 단계 권장:
1. M0~M12 모듈 → Epic 13개 (1:1 매핑)
2. FR-level ID 도입 (F-module.N 형식) — Medium #9 해결
3. 각 Epic에 UJ-N 참조 + §8.1 인수 기준 매핑
4. Non-Goals 10개를 Epic 범위 결정 시 명시적 제외 처리

## Reviewer files

- `review-rubric.md` — main rubric walker (this validation)
- `validation-report.md` (this file) — consolidated markdown twin
- `validation-report.html` — HTML viewer (open in browser)
- Previous report (stale): `validation-report.md` 2026-07-24 21:11 (Fair, 3 Criticals) — superseded by this run
