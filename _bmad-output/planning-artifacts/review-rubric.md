# PRD Quality Review — bizup 통합 PRD v2.0

- **PRD:** `C:/Users/c8rom/desktop/costmgr/_bmad-output/planning-artifacts/prd.md`
- **Rubric:** `C:/Users/c8rom/desktop/costmgr/.claude/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-07-25 (re-run after 2026-07-24 21:56 patch)
- **Previous verdict:** Fair (3 Criticals — UJ absent, SM absent, [ASSUMPTION] absent)

## Overall verdict

The 2026-07-24 21:56 patch substantively resolves all three previous Criticals: §2.A ships 4 named-protagonist user journeys (UJ-1~4), §2.B introduces 4 thesis-anchored success metrics plus 4 counter-metrics (SM-1~4 / CM-1~4), and §부록 D catalogues 6 assumptions (AS-1~6) with 5 inline `[ASSUMPTION]` markers that roundtrip cleanly to A1, §6.1 (3), §6.1 (4), §7.1, §7.2. Two carried Highs also closed: §14.A introduces 7 owner-bearing Open Questions (OQ-1~7), and §8.1 attaches 2~3 acceptance bullets per M0–M12 module. The PRD is now a defensible green-light document at the **Good** grade.

Two residual gaps prevent an Excellent: (1) a formal Non-Goals section is still absent — the 2차/3차 로드맵 (§15) is framed as future work rather than explicit MVP non-goals, leaving "what we will *not* ship" implicit; (2) §14 NFR surface remains thin (only "월 계산 수 초 내" + "소형 여유 설계"), which downstream architecture will struggle to source-extract from. Persona ④ "경영컨설턴트" remains in §2 (line 82) without a dedicated UJ — partially mitigated by UJ-4's optional 대리접속 step, but the persona-flow gap persists.

## Decision-readiness — adequate

Trade-offs are now surfaced with empirical anchors where the data exists. Q-F carries the strongest example — "매출기준 배부 폐기 — pl3 92% 왜곡 실증" with the actual numbers (생산 14,900 vs 판매 10,450). Q-A forces the user to pick from 3 explicit 배부기준 alternatives rather than burying the choice as a "consideration". §14.A replaces the previous scattered one-liner deferrals with a structured OQ table (owner + milestone), and the single inline `[NOTE FOR PM]` at line 334 (UX 부호 처리) is tracked through OQ-6.

What keeps this dimension at adequate rather than strong: §2's "월 구독 1만원 단일 요금제" (line 83) is stated as a single-rate decision with no trade-off paragraph; the previous "Medium" finding that persona "원가 전담자 없는 기업" + G2 "새벽에 혼자 고칠 수 있는 시스템" should justify single-tier pricing is still partly unaddressed — it now lives in OQ-2 ("가격 정책 1단 vs 단계형") as an open question, which is a defensible choice but the one-paragraph justification the rubric wants is still missing. Q-G (report 파일 갈음, line 645) is honestly flagged in 부록 A but does not enumerate which 26 surface maps to which of §9's 14+7 reports — this is carried in OQ-5 but the gap itself remains.

### Findings
- **[medium]** 가격 모델 1단 단언, trade-off 단락 부재 (§2, line 83) — persona "원가 전담자 없는 기업" + G2 "혼자 고치는 시스템"으로 단일 요금제 합리화를 1단락으로 정당화하거나 단언을 제거. *Fix:* §2 아래에 "왜 단일 요금제인가" 3~5행 추가 (비용 구조: 월 인프라 10만원 + Stripe 수수료 + 파일럿 무료 트레이드오프).
- **[medium]** Q-G report 파일 26 surface 커버리지 매핑 미수행 (부록 A line 645 → OQ-5 line 594) — 결정 보류는 정직하나 §9 21종으로의 매핑은 본문에서 수행 가능. *Fix:* 부록 또는 §9 말미에 원본 26 보고서 → §9 14+7 매핑 표 추가 (covg gap은 명시).

## Substance over theater — strong

The §3 회계 공리 헌장 (A1–A11) is product-specific and load-bearing — A4's "pl3 92% 왜곡 실증" reference, A9's 미사용능력 정량화, A10의 세법 76조 2기준 인용 모두 본문 결정에 인과로 묶여 있다. §6.1 산식 체인은 Python 교차 검증 가능한 1원 단위 수준이며 §11 V1~V8 검증 매트릭스가 같은 수준으로 묶여 있다. Vision (§1.1) "월 1회, 6가지 데이터만 입력하면 원가·재고·손익·분석이 전부 자동으로" — 교환 불가한 제품 고유 문장이다.

Persona theater는 1개 잔존: persona ④ "경영컨설턴트(대리 운영)" (line 82)이 §2 표에만 등장하고 UJ-4의 protagonist는 "신규가입자(§2 페르소나 ①·② 공통)" (line 143) — 즉 persona ④는 흐름에서 고아 상태. 다만 UJ-4 step 6 "(선택) 대리접속 동의"에서 컨설턴트가 등장하므로 완전히 미사용은 아니며, CM-4 "대리접속 발동 빈도" 카운터 메트릭도 persona ④에 묶여 있어 어느 정도는 가중되었다. 이전 보고의 medium finding은 partially resolved.

NFR theater는 1개 잔존: §14의 "월 계산 수 초 내"와 "소형 여유 설계" 두 임계값뿐. CM-1 "마감 중앙값 ≤ 4시간"은 UJ-1 → CM-1 경로로 산입되어 있으나, 이는 사용자 운영 부담 임계이지 시스템 응답성 임계가 아니다. 동시 사용자 N·데이터 볼륨·가용성 목표·백업 RPO/RTO·감사로그 보존 기간이 §13.2/§14 어디에도 없다.

### Findings
- **[high]** §14 NFR 표면적 — 동시 사용자·가용성·RPO/RTO·감사로그 보존 미명시 (lines 574-580) — 1인 운영자 SaaS라도 G2 "새벽에 혼자"는 RTO가 필요. *Fix:* §14에 "동시 사용자 N=___ / 가용성 99.X% / RPO 24h / RTO 4h / 감사로그 N년" 표 추가.
- **[medium]** Persona ④ 고아 (line 82) — §2 표에만 등장, UJ 없음. *Fix:* UJ-4 step 6을 "컨설턴트 대리 운영" 별도 UJ로 승격하거나 §2에서 persona ④ 제거하고 "지원 수단: 대리접속"으로 통합.

## Strategic coherence — adequate

The 통합 thesis is now stated (§2.B line 162: "ABC + 전통 + AI 통합이 한국 SMB 원가경영관리의 표준이 된다") and the SMs validate it directly: SM-1 measures active tenant completion (engagement), SM-2 measures 2-engine simultaneous closure (the unification thesis 핵심 KPI), SM-3 measures AI insight adoption with SM-3a "계산 결과 변경 시도 = 0건" as a thesis-protection guardrail, SM-4 measures 미사용능력 보고서 열람 (TDABC 정착). Counter-metrics (CM-1~4) are paired with their respective SMs — CM-1 vs SM-1, CM-2 vs SM-2, CM-3 standalone as A11 input quality proxy, CM-4 vs SM-3 (consulting dependency). This is genuinely thesis-anchored measurement design, not DAU/MAU boilerplate.

What keeps this at adequate: §15 로드맵의 2차 항목 (A×B×C×D 엔진·복수 예산·CPA·다국어) trigger 기준이 OQ-7에서 "1차 출시 후 6개월 시점"으로 잡혀 있으나, 이는 시점 트리거일 뿐 채택 트리거가 아니다. "≥5 테넌트가 복수 예산 시나리오 요청 시" 같은 데이터-기반 trigger가 추가로 필요. 또한 §10 예산 시나리오는 1차 범위에 들어 있는데 SM은 예산 사용률/정확도를 측정하지 않는다 — 통합 thesis의 "예산/실적 이중 운영" 정착 검증이 빠졌다.

### Findings
- **[medium]** §15 2차 로드맵 trigger 부재 (lines 605-615) — 시점(OQ-7 "출시 후 6개월")은 있으나 데이터 트리거 없음. *Fix:* 각 2차 항목에 "trigger: ≥N 테넌트 요청 시 / ≥M개월 후" 데이터-기반 트리거 추가.
- **[medium]** 예산 시나리오 정착 SM 부재 (§2.B) — §10 예산 시나리오는 1차 범위지만 측정 지표 없음. *Fix:* SM-5 "예산 시나리오 활성 테넌트 비율" 또는 "예산 대비 실적 오차율" 추가.

## Done-ness clarity — strong

§8.1 모듈별 인수 기준 (M0~M12, 12 modules × 2-3 bullets = ~30 acceptance criteria) follows the rubric's preferred "시스템은 X를 Y 시점에 Z 조건으로 수행한다" pattern and ties back to §11 V-row IDs (e.g., M2-c references "[A11, V3·V5]", M3-b references "§11 V1·V4·V7·V8"). This is significantly better than the previous "input/output only" 모듈 표. M10-a even preemptively closes the previous "캐시 정의 미명시" medium finding with "캐시 = 마감 완료 시점부터 다음 마감 시작까지 보존, 마감 데이터 변경 시 폐기" — exact policy wording.

§11 V1~V8 검증 매트릭스 itself is testable: each row has a content + 시점 column, the V8 회귀 테스트 스위트 (line 534) is CI-blocking. V4의 4요소 분해 ("수량차·배부차·단가차·재고조정", line 530)는 본문 §6.1 (5) "제품 재고 조정" 라인과 인과로 묶여 있다.

Residual concerns: §13.1 디자인 어휘 ("완전반응형", line 553)는 여전히 형용사만 — breakpoint·grid 밀도·a11y 목표·Pretendard fallback 등 이전 medium finding이 §13.1 또는 별도 §13.4에 추가되지 않음. §13.3 보안·운영은 "저장 데이터 암호화" (line 570) 단언으로 끝나고 알고리즘·키 관리 미명시.

### Findings
- **[medium]** §13.1 디자인 토큰 미정 (line 553) — breakpoint·grid·a11y 기준 부재. *Fix:* §13.4 신설 또는 §13.1 확장 — "≥1024px PC 그리드 / <1024px 폼 입력, 12-col 8px base, WCAG AA, Pretendard fallback".
- **[medium]** §13.3 "저장 데이터 암호화" 알고리즘 미명시 (line 570) — "AES-256 at rest" 등 명시. *Fix:* "AES-256 at rest, TLS 1.3 in transit, 키 KMS 관리" 형태로 구체화.

## Scope honesty — adequate

The Assumptions Index (§부록 D, AS-1~6) is the strongest addition. Each row has 위치·추론 내용·추론 근거·추론일·해소 owner 컬럼, and the inline `[ASSUMPTION]` markers (5 found at lines 188, 319, 326, 379, 391) roundtrip cleanly to AS-1, AS-4, AS-3, AS-5, AS-2 (in the order they appear). Owner assignment is mixed — PM (3), 운영자 (3), UX designer (2), 운영자+UX (1) — appropriate distribution.

What keeps this at adequate rather than strong:

1. **Non-Goals section absent** — the rubric flags "Non-Goals (분산·암묵)" as a required section for B2B SaaS greenfield in mechanical notes, and §15의 "2차 / 3차 로드맵"이 implicit non-goals 역할을 부분적으로 수행하나 명시적 "[NON-GOAL for MVP]" callout은 0건. downstream extractor는 "이것은 의도된 미구현"인지 "잊힌 미구현"인지 구분 불가.

2. **AS-6 roundtrip 미완** — §부록 D AS-6 (§9 #21 부문귀속명세서 시각화 형식, line 714)은 인덱스에 존재하나 본문 §9 #21 (line 509) 또는 §7.3 (line 398) 어디에도 inline `[ASSUMPTION]` 마커가 없다. 5 markers vs 6 entries — 1:1 roundtrip 실패.

3. **AS-6 위치 표기 모호** — 부록 D "위치" 컬럼이 "§9 #21"로 표기되어 있으나 본문 line 509에는 #21이 보고서 목록의 한 항목으로만 존재, 시각화 형식 단언이 본문에 없음. AS-6은 AS-2(§7.2)나 §7.3 line 398에 자연스럽게 들어갈 자리.

### Findings
- **[high]** Non-Goals 섹션 부재 — §15가 부분 대체하나 "[NON-GOAL for MVP]" callout 0건 (§-). *Fix:* §2 또는 §15 앞에 "MVP 비목표" 섹션 신설 (예: "1차 출시에서는 X 안 함: 제조 부문 ABC, A×B×C×D 엔진, 멀티에이전트 위원회, 다국어 확장" — 2차/3차 항목에서 가져옴).
- **[medium]** AS-6 inline marker 부재 (§9 #21) — 인덱스 line 714에만 존재, 본문 마커 없음. *Fix:* §7.3 line 398 또는 §9 #21 line 509에 "[ASSUMPTION: 부문귀속명세서 시각화 형식(표/차트)은 추론. ...]" 마커 추가, 1:1 roundtrip.

## Downstream usability — adequate

Glossary is now substantial (§부록 C, ~33 entries vs previous 6) with each row defining a domain term and referencing its axiom/decision (§7.2 CCR, [A8] append-only, [A10] 세법 2기준, etc.). UJ protagonists carry context inline — 박영수 (UJ-1), 이미숙 (UJ-2), 김도현 (UJ-3), 신규가입자 (UJ-4) — each persona profile is embedded in the UJ header (occupation, age, §2 페르소나 reference, triggering context), eliminating the need for a separate Persona section reference.

ID continuity holds across the major schemes: Q-A~Q-J (10), M0~M12 (13), V1~V8 (8), A1~A11 (11), UJ-1~4 (4), SM-1~4 (4), CM-1~4 (4), OQ-1~7 (7), AS-1~6 (6). All contiguous, no gaps, no duplicates. Cross-references resolve cleanly throughout — bracket-prefixed `[A1]`~`[A11]`, `[Q-A]`~`[Q-J]`, `[V1]`~`[V8]`, `[E1]`~`[E11]` (장치 참조), `§6.1`, `§7.2`, `§11`, `§14.A`, `§부록 A/B/D`, `M0`~`M12` 모두 grep으로 추적 가능.

What keeps this at adequate rather than strong: **FR-level numbering absent**. §8 모듈 표 and §8.1 인수 기준 모두 module-level granularity (M0–M12)이며, M0 "업종 4지선다"나 M2 "월합계 기본 모드" 같은 개별 기능에 F0.1 / F2.3 스타일 번호가 없다. Stories 작성 단계에서 atomic FR ID가 없으면 "이 인수 기준이 어떤 FR에 대응하는가" 추적이 모듈 단위로만 가능. 또한 §-간 준용어 — "원가경영관리"(§1.1, §부록 C 정의) ↔ "원가 경영관리"(§1.4 인용문) ↔ "원가 관리"(§2 페르소나 컨텍스트) 드리프트는 여전히 잔존하나 부록 C "원가경영관리: 본 제품의 정식 명칭(부제). 단일 표기로 통일" (line 689) 한 줄로 봉합 의도가 표시됨.

### Findings
- **[medium]** M-ID 모듈 단위, FR 단위 번호 부재 (§8, §8.1) — atomic story 추적 곤란. *Fix:* §8 모듈 표에 F-module.N 형식 도입 (예: M2.a 월합계 기본, M2.b 일용직 FTE 환산, M2.c 음수재고 경고) 또는 별도 FR- 표 추가.
- **[low]** §-간 준용어 미수표기 ("원가경영관리" vs "원가 경영관리") — §1.4 line 67이 원본 manual 인용이라 의도된 표기일 가능성 높으나 본문 여타 위치와 미동기화. *Fix:* §1.4 인용문 외 모든 위치에서 "원가경영관리"(띄어쓰기 없음) 통일, §1.4에 *원문 인용* 주석 추가.

## Shape fit — adequate

The PRD is the right shape for a B2B SaaS for SMBs: UJs with named protagonists (load-bearing for multi-stakeholder product), Personas table (4, slightly overloaded with persona ④), SMs with counter-metrics, NFRs (thin but present), Glossary, Decision log. Brownfield conventions are followed — §1.2 "원본 자산의 정체 (5개 파일 학습 종합)" and §13.2 technical stack are anchored to the original Excel files (costmgr, djob, inv2, report, ABCost) with explicit "원본 __ 시트 계승" attributions throughout §6.1, §7.1, §11.

Internal-tool / single-operator bias is visible — §13.2 "배제: Celery 등 복잡 인프라 — G2 '새벽에 혼자 고칠 수 있는 시스템'" (line 567), §14 "소형 여유 설계 (제품 수백·자재 수천 무리 없음)" (line 576). These constraints are honestly stated, but they leak into the PRD as scope restrictions without corresponding upper-bound NFRs (concurrent users N, data volume limits, etc.) — the reader cannot tell whether "수백·수천 무리 없음" is a design choice or a hidden ceiling.

What keeps this at adequate rather than strong: the persona ④ issue (see Substance), and the absence of an explicit "this is a greenfield SaaS, not a brownfield modernization" framing — §1.2 lists the original files but does not state the architectural relationship to them (will bizup call into Excel VBA? No — §13.2 명시 FastAPI + Python). A one-paragraph "greenfield vs integration" framing would help downstream architecture.

### Findings
- **[medium]** Greenfield/brownfield 경계 명시 부재 — §1.2 원본 5파일 학습 + §13.2 FastAPI + 순수 Python 엔진 → 의도된 greenfield이나 명시적 선언 없음. *Fix:* §1.2 말미에 "bizup는 greenfield 웹 SaaS — 원본 5파일은 회계 로직 참조용이며 런타임 의존성 없음" 단락 추가.
- **[medium]** "수백·수천 무리 없음" 한계 미정량 (§14 line 576) — 실제 동시 사용자·테넌트 수·제품 수 임계값 부재. *Fix:* "동시 사용자 ≤10, 제품 ≤500, 자재 ≤2000, 테넌트 ≤100 (1차)" 형태로 구체화.

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
- **Assumptions Index roundtrip**: 5 inline `[ASSUMPTION]` markers (lines 188, 319, 326, 379, 391) ↔ AS-1, AS-4, AS-3, AS-5, AS-2 (1:1). **AS-6 has no inline marker** (§부록 D line 714) — 1개 roundtrip 실패.
- **[NOTE FOR PM] roundtrip**: 1 inline marker (line 334, §6.1 (5) UX 부호) ↔ OQ-6 (line 595) — 1:1 정상.
- **UJ protagonist naming**: All 4 UJs have named protagonists carrying context inline — 박영수 (UJ-1, 식품 제조+유통 겸영 대표, 48세), 이미숙 (UJ-2, 여행상품 ABC 대표, 42세), 김도현 (UJ-3, 겸영 프랜차이즈 재무 담당, 53세), 신규가입자 (UJ-4, §2 페르소나 ①·② 공통). 고아 UJ 없음.
- **Required sections for stakes (B2B SaaS greenfield)**: Vision ✓ (§1.1), Personas △ (4, persona ④ 고아), UJs ✓ (§2.A), FRs △ (모듈 단위, FR-level 번호 부재), NFRs △ (§14 얇음), Success Metrics ✓ (§2.B), Non-Goals ✗ (분산·암묵), Open Questions ✓ (§14.A), Glossary ✓ (~33 항목), Assumptions Index ✓ (roundtrip 5/6), Decisions Log ✓ (Q-A~Q-J).
- **Determinism**: §6.1 산식 체인은 Python 교차 검증 가능. §11 V8 "1원 단위 대조 회귀 테스트 스위트" 약속, §8.1 M3-b에서 CI-blocking 명시.
- **이론 인용**: §15 이론 근거 5항목은 웹 검증 완료 표기(line 16 "웹 검증 완료"). 다만 개별 citation URL 부재 — 이전 보고 medium finding 잔존.
- **서비스명**: §14 "비즈업은 가칭"이라고 명시 + OQ-1에서 PM owner + UX 진입 전 milestone으로 추적. 양호.

## Findings by severity

### Critical (0)

이전 3 Critical 모두 해소됨 (UJ / SM / [ASSUMPTION]).

### High (2)

1. **[Scope honesty]** Non-Goals 섹션 부재 — §15 2차/3차 로드맵이 부분 대체하나 "[NON-GOAL for MVP]" callout 0건. downstream extractor가 "의도된 미구현 vs 잊힌 미구현" 구분 불가.
2. **[Substance over theater / Shape fit]** §14 NFR 표면적 — 동시 사용자 N·가용성·RPO/RTO·감사로그 보존 기간 미명시. G2 "새벽에 혼자"는 RTO 요구를 함축하나 임계값 없음.

### Medium (10)

1. **[Decision-readiness]** 가격 모델 1단 단언, trade-off 단락 부재 (§2 line 83 → OQ-2)
2. **[Decision-readiness]** Q-G 26 surface 커버리지 매핑 미수행 (부록 A → OQ-5)
3. **[Substance over theater]** Persona ④ 고아 (§2 line 82, UJ 없음)
4. **[Strategic coherence]** §15 2차 로드맵 trigger 부재 (OQ-7 시점만, 데이터 트리거 없음)
5. **[Strategic coherence]** 예산 시나리오 정착 SM 부재 (§2.B, §10 1차 범위이나 측정 없음)
6. **[Done-ness clarity]** §13.1 디자인 토큰 미정 (line 553)
7. **[Done-ness clarity]** §13.3 "저장 데이터 암호화" 알고리즘 미명시 (line 570)
8. **[Scope honesty]** AS-6 inline marker 부재 (§9 #21, 부록 D line 714)
9. **[Downstream usability]** M-ID 모듈 단위, FR 단위 번호 부재 (§8, §8.1)
10. **[Shape fit]** Greenfield/brownfield 경계 명시 부재 (§1.2)

### Low (2)

1. **[Downstream usability]** §-간 준용어 ("원가경영관리" vs "원가 경영관리") — 부록 C로 봉합 의도 표시
2. **[Shape fit]** "수백·수천 무리 없음" 한계 미정량 (§14 line 576)

## Summary

이전 Fair → **Good** 승급. 3 Criticals (UJ / SM / [ASSUMPTION]) 모두 해소되었고, §8.1 모듈별 인수 기준 + §14.A Open Questions + §부록 C 용어집 확장으로 carried Highs도 거의 해소. 잔존 gap은 (1) Non-Goals 명시 부재, (2) §14 NFR 표면적, (3) FR-level numbering 부재, (4) Persona ④ 고아 — 모두 medium급이며 다음 패치(CE/IR 진입 전)에서 닫으면 Excellent 도달 가능.

## Reviewer files

- This file: `C:/Users/c8rom/desktop/costmgr/_bmad-output/planning-artifacts/review-rubric.md`
- Previous report (stale): `C:/Users/c8rom/desktop/costmgr/_bmad-output/planning-artifacts/validation-report.md`
