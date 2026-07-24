# PRD Quality Review — bizup (통합 PRD v2.0)

## Overall verdict

A domain-rich, well-structured PRD that earns its weight through the Axioms Charter (§3) and the verification framework (§11), with a clear unification thesis (§1.2) backing every module decision. What holds up is the math chain rigor and the explicit decision history (Q-A through Q-J in 부록 A). What's at risk is the downstream handoff: a green-light-to-build PRD for a B2B SaaS that omits User Journeys, has no Success Metrics anchored to the thesis, and lacks the `[ASSUMPTION]` / `[NOTE FOR PM]` markers that downstream UX and architecture extraction will need to run cleanly. Treat it as a strong technical specification — but soft-launch it through a UX pass before stories are written.

## Decision-readiness — adequate

Decisions are mostly stated as decisions, not buried. §3 elevates A1–A11 to a Charter with explicit "본 장은 비즈업의 최상위 규범이다. 이하 모든 기능·화면·산식은 본 장과 충돌할 수 없으며, 충돌 시 본 장이 우선한다" — a clean rule that downstream feature conflicts can resolve against. The decision register in 부록 A is excellent: Q-A through Q-J consolidate twenty-three distinct products of the workshop (e.g., "Q-A: 제조경비 배부기준 = 직접노무원가 / 직접노무시간 / 기계시간 3종 택1 (기계시간 신규 입력)"). Q-F is a textbook example of a trade-off with evidence: "매출기준 배부 시 직접인건비가 매출 대비 92%로 튜는 왜곡을 실증(생산 14,900 vs 판매 10,450인데 노무비 전액을 당월 매출에 배부)" — the rejected alternative is named, the cost of the rejected alternative is shown, and the chosen path is anchored in empirical data.

The weakness is not in what is decided but in what is explicitly deferred without structure. §14 says "서비스명 '비즈업'은 가칭, 확정 재논의" and "파일럿 투입은 개발 중반 시점에 재논의 (예정 과업)" — these are deferred decisions written as one-line asides, not surfaced as Open Questions or `[NOTE FOR PM]` callouts. The PRD has no Open Questions section, no `[NOTE FOR PM]` markers, and no `[ASSUMPTION]` tags. A reader pushing back on, say, "회계연도 시작월은 테넌트별 가변" (A1) has no place to log the objection.

### Findings
- **[high]** No Open Questions section (§ missing) — Deferrals like "서비스명 '비즈업'은 가칭, 확정 재논의" (§14) and "파일럿 투입은 개발 중반 시점에 재논의" (§14) are scattered inline, not surfaced. *Fix:* Add an Open Questions section enumerating unresolved decisions with owner and target milestone; flag `[NOTE FOR PM]` at each unresolved tension.
- **[medium]** Pricing model is asserted without sensitivity (§2) — "월 구독 1만원 단일 요금제(전 기능 제공)" is stated as a decision but no trade-off is named (e.g., why no per-seat tier, why no free tier). *Fix:* Add a one-paragraph rationale anchoring the chosen tier to the "원가 전담자 없는 기업" persona and the G2 "새벽에 혼자 고칠 수 있는 시스템" operational constraint, or note the open item.
- **[low]** Q-G "report 파일은 기존 구조 분석으로 갈음" (부록 A) — the deferral is named but the affected 26 보고서 surface is not enumerated. *Fix:* Confirm whether report's 26 reports are covered by §9's list, or flag a gap.

## Substance over theater — strong

The PRD carries real domain weight. §1.2 quotes original spreadsheet facts: "수식 손상 4,468건·유령 링크 1,027건" and "BOM1 시트로 costmgr을 6,174개 수식으로 미러링" — these are not invented problem statements. §6.1's math chains are reproduced with cell-level fidelity, including the "730h→3.2명" FTE conversion and the "차이시간 = 총작업가능시간 − 생산요구시간 → 금액화하여 미사용능력 보고 [A9]" derivation. Even the §11 verification table has 8 distinct conditions with timing (입력 시 / 계산 시 / CI), thresholds (1원 단위), and the matrix mapping V1 ⇒ A6 / V4 ⇒ A11 — this is engineering-grade substance.

Potential furniture: the §2 persona list ("① 제조업 경영자/경리 ② 서비스업(물류·여행·용역) 대표 ③ 제조+유통 겸영(프랜차이즈·식품) ④ 경영컨설턴트(대리 운영)") has four personas but only persona ③ consistently drives a feature in the PRD (the §4.2 segment-engine mapping and §7.3 카브아웃). Persona ④ is invoked only by "대리접속(고객 동의+읽기전용)" in §2 and §13.3 — borderline theater. Vision (§1.1) is concrete and product-specific: "월 1회, 6가지 데이터만 입력하면 원가·재고·손익·분석이 전부 자동으로 나오는, 제조업과 서비스업을 한 지붕에 담은 원가경영관리 웹 SaaS" — this would not swap into another PRD unmolested.

§12 "AI 기능 3종" is brief but principled: "AI는 초안, 확정은 사람" appears as a guardrail, and "계산 결과를 변경하지 않음" is a hard architectural constraint. §13.2 technology choices are operational and decisive ("Celery 등 복잡 인프라 제외" / G2 "새벽에 혼자 고칠 수 있는 시스템") — this is the right kind of restraint for a 1-person-operator product.

### Findings
- **[medium]** Persona ④ "경영컨설턴트(대리 운영)" (§2) — drives only one feature (대리접속) and adds load to §2 marketing line. *Fix:* Either consolidate ①+④ into "대리 운영자(경영컨설턴트 대행 포함)" or move persona ④ to a separate "운영자" sub-section so it doesn't compete with the user-persona row.
- **[low]** §2 list of "경쟁 우위" — "AI 온보딩·인사이트" is a claim that the PRD then narrows (§12) to 3 specific features. The framing is honest but blurs novelty. *Fix:* Reframe as "원가 영역 특화 AI" or "회계 공리 가드레일 적용 AI" to distinguish from generic AI-SaaS claims.

## Strategic coherence — adequate

The thesis is clear: unify traditional absorption costing + ABC for Korean SMBs under one platform with a 1만원/month subscription (the §1.2 split "동일 저작자(원가바이블)의 검증된 두 원가 엔진이다" frames the unification as a heresy of necessity — the original ABCost already mirrors costmgr via 6,174 formulas, "원본 스스로 통합 필요성을 증명"). Feature prioritization follows the thesis: M0 (설정) → M1 (기준정보) → M2 (입력) → M3 (계산) → M4 (재고) → M5 (보고) → M6 (검증) → M7 (시뮬레이션) → M8 (예산) → M9 (ABC) → M10 (AI) → M11 (마감) → M12 (계정·운영). The 1차/2차/3차 roadmap is also thesis-aligned: 2차 defers A×B×C×D budget engine and 활동별 classic/TDABC 혼용 (§10, §7.2), 3차 unlocks 제조부문 ABC (§4.2) and 멀티에이전트 원가분석 위원회.

The thinness is in §2's goals. "G1: 12모듈 완성 후 출시+파일럿 1~2곳 무료 / G2: '새벽에 혼자 고칠 수 있는 시스템'" — these are milestones and operational goals, not success metrics. There is no metric that validates the thesis: no "월 마감 완료율", no "활성 테넌트 중 2-engines 활성화 비율", no "예측 인사이트采纳率". The thesis claims that "ABC + 전통 + AI 통합" wins in the SMB segment, but the PRD does not define what would prove that. Without counter-metrics the PRD is open to the failure mode of "shipped but the thesis turned out to be wrong".

### Findings
- **[critical]** No Success Metrics anchored to the thesis (§2) — G1 is a release milestone, G2 is an operational mantra. The PRD never quantifies the unification thesis. *Fix:* Add a Success Metrics section with 3–5 metrics tied to the thesis: e.g., "월 마감 완료율 (활성 테넌트 기준)", "겸영 테넌트의 2-engine 동시 마감 비율", "AI 인사이트采纳率 (계산 결과 미변경 보장)", with counter-metrics (e.g., "마감 소요시간" vs "오류 재작업 빈도").
- **[medium]** §10 deferral pattern is healthy but 2차 items (A×B×C×D engine, 복수 예산 시나리오, CPA) are listed without trigger criteria — when does a "2차" item get pulled forward? *Fix:* For each 2차 item add a `trigger:` clause (e.g., "trigger: ≥5 테넌트가 예산 시나리오 2개 이상 요청 시").

## Done-ness clarity — adequate

The strongest part of the PRD is §11's verification matrix: V1 "각 배부 단계 합계 = 원금액 (1원 단위) [A6]" (시점: 계산 시), V3 "품목별 기말 < 0 감지 즉시 경고" (시점: 입력 시), V4 "제조원가↔매출원가↔재고 차이를 4요소 자동 분해: ①생산·매출 수량차 재료비 ②노무비+제조경비 배분차 ③총평균단가차 ④재고조정 → '제품 재고 조정' 라인 산출 근거" (시점: 계산 시) — each is a testable consequence with a measurable outcome and a timing. §6.1's equations similarly have testable thresholds via "1원 단위 엑셀 대조 테스트 통과 필수" (M3) and V8 ("1원 단위 대조하는 회귀 테스트 스위트" CI). §14 sets a performance bound: "월 계산 수 초 내(소형 데이터 전제), 계산 버튼 방식으로 예측 가능성 확보".

The weakness is the gap between V-level rigor and module-level rigor. §8 module table M0 through M12 lists each module's content but not its acceptance criteria. M0: "업종 4지선다, 부문, 회계연도 시작월, 통화(KRW/USD)·언어(한/영), 배부기준 3종 선택, AI 문서추출" — these are inputs, not done-ness conditions. M5: "제9장 보고서 체계 전체" — points outward but does not specify acceptance. M10: "문서추출 / 인사이트 질문 3개 생성·캐시 / 고정·변동 3단계 추정" — "캐시" is undefined here (cache of what? TTL? invalidation rules?). §13.1 design says "좌측 사이드바 내비게이션, PC 그리드 입력 / 모바일 폼 입력, 완전반응형" — no breakpoints, no grid density, no a11y targets.

### Findings
- **[high]** §8 module table lacks acceptance criteria — M0–M12 list inputs and outputs but no testable per-module done-ness. *Fix:* For each module, add 2–4 acceptance bullets in the shape "시스템은 X를 Y 시점에 Z의 조건으로 수행한다" (cf. §11 V-row format). Example for M10: "M10-acceptance: (a) 문서추출 결과는 신뢰도 ≥ X% 항목만 사용자가 확정한 후 저장 (b) AI 인사이트는 계산 직후 3개 자동 생성, 캐시는 마감 데이터 변경 시 무효화 (c) 고정·변동 추정은 확정값만 A7/A11의 계산에 사용".
- **[medium]** §12 "인사이트 큐레이션" "캐시" 의미 불명 — "AI 인사이트 질문 3개 자동 생성·캐시" is stated but cache policy (TTL, invalidation on data change, eviction) is not specified. *Fix:* Specify "캐시: 마감 완료 시점부터 다음 마감 시작까지 보존, 마감 데이터 변경 시 폐기" or similar.
- **[medium]** §13.1 design language is adjective-only — "완전반응형", "사이드바 내비게이션" without breakpoints (sm/md/lg) or grid density. *Fix:* Add concrete breakpoints (e.g., "≥1024px: PC 그리드 / <1024px: 폼 입력") and grid density (e.g., "12-col, 8px base").

## Scope honesty — adequate

Explicit deferrals are present and well-placed. §14 names 두 가지: "법적 문서(약관·개인정보처리방침)는 프로젝트 마무리 단계에 초안 작성 (예정 과업)" and "파일럿 투입은 개발 중반 시점에 재논의 (예정 과업)". §15 roadmap is three-phase and clear: 2차 defers "A×B×C×D 예산 편성 엔진", "복수 예산 시나리오", "활동별 classic/TDABC 혼용 (method_override 활성화)", "고객수익성 분석(CPA)", "다국어 확장(중·일)", "원가 이상감지 알림"; 3차 defers "제조 부문 ABC 개방" and "멀티에이전트 원가분석 위원회". §4.2 is particularly tight: "제조 부문에 대한 ABC 적용(병행 뷰)은 3차 로드맵 — 스키마는 확장 차단 없이 설계" — explicitly carrying the burden into schema design while not pretending to ship it. §7.2 notes "method_override 예비 필드로 활동별 혼용은 2차" — preserves the field without exercising it.

However, the absence of standardized markers is a real gap. The PRD uses no `[ASSUMPTION]` tags, no `[NOTE FOR PM]` callouts, and no Open Questions section. "결정 Q-A ~ Q-J" in 부록 A is excellent for closed decisions but silent on gaps. Derivative assumptions (e.g., "회계연도 시작월은 테넌트별 가변" in A1) are stated as rules without flagging that they are inferences the user has not confirmed. The deferral "서비스명 '비즈업'은 가칭, 확정 재논의" is the only place a "name" decision is flagged, and it is a one-liner.

### Findings
- **[critical]** No `[ASSUMPTION]` markers and no Assumptions Index (§-) — Inferences like "회계연도 시작월은 테넌트별 가변" (A1) and "CCR 산출 단위 = 부서" (§7.2) are stated as rules without tagging. *Fix:* Add `[ASSUMPTION: ...]` inline at each inferred-but-unconfirmed rule, and append an Assumptions Index at end of document with the source and the date of inference.
- **[high]** No `[NOTE FOR PM]` callouts at tensions (§-) — e.g., the trade-off between "± 제품재고조정" 손익 표시 (§6.1 (5)) and the user-facing "재고 증감은 '제품 재고 조정' 라인으로 자동 산출" claim is uncontested. UX wants to know when this line flips sign. *Fix:* Add `[NOTE FOR PM]` at each product decision with UX-facing uncertainty.
- **[low]** "파일럿 투입은 개발 중반 시점에 재논의 (예정 과업)" (§14) — too vague; "개발 중반" is not a milestone. *Fix:* Tie to a specific module milestone (e.g., "trigger: M0–M6 완성 후 1주").

## Downstream usability — thin

The PRD has excellent ID hygiene. Q-A through Q-J (부록 A), M0–M12 (§8), V1–V8 (§11), A1–A11 (§3) are all contiguous, unique, and well-referenced via bracket-prefixed cross-references (e.g., "§6.1의 산식 체인 ... [A3]", "A5의 Causality 원칙", "Q-F 공수 단일"). §16 enumerates the four downstream artifacts: "통합 ERD v2.0 작성", "통합 DDL 스크립트 (RLS·마감잠금 트리거 포함)", "엔진 산식 명세서 (엑셀 셀 → Python 함수 매핑, V8 대조 테스트 설계)", "화면 정의서 (HTML 목업) + 디자인 가이드". The next-step list is concrete and the PRD explicitly hands off to ERD consolidation: "본 문서 확정 후 기존 ERD 2권+테이블명세서를 1권으로 통합".

The blockers for downstream extraction are real. First, the PRD has no UJ (User Journey) section. For a B2B SaaS whose UX is greenfield (replacing four open Excel files), User Journeys are load-bearing — they tell architecture where the data flows live, and they tell stories where the edge cases hide. The closest the PRD comes is §1.3's "불편함" list (9 items) and §2's personas, but these are pre-persona-Journeys. Second, the glossary at §부록 C has 6 terms ("회사부담임률", "미사용능력", "카브아웃", "CCR", "제품 재고 조정", "전진법") but the PRD uses dozens of domain terms without entries — "BOM", "BEP", "CVP", "세법 2기준", "기계시간", "역분개", "투입시간", "배부기준", "레버리지", "총평균법", "FTE", "실제적 조업능력", "TDABC", "CCR" (entry exists for CCR but "TDABC" itself is not), "ABCost", "역분개", "append-only", "테넌트", "RLS". The downstream glossary is too thin to anchor cross-document linking. Third, there is no FR- numbering scheme distinct from M- numbering — module IDs cover modules but not individual features.

### Findings
- **[critical]** No User Journey section (§-) — B2B SaaS replacing a four-file Excel workflow has clear primary journeys (월 입력 → 계산 → 마감 → 보고서) but none are documented. *Fix:* Add a 제X장 User Journeys with at least 4 named journeys: "월 사이클(입력 → 계산 → 검증 → 마감)", "예산 시뮬레이션", "겸영 기업의 부문 카브아웃", "관리자 온보딩(문서추출 → 검토 → 확정)" — each with protagonist, trigger, end-state, and exception paths.
- **[high]** Glossary at §부록 C has 6 terms vs ~30+ used in the PRD — Missing: BOM, BEP, CVP, 세법 2기준, 기계시간, 역분개, append-only, 테넌트, RLS, 실제적 조업능력, TDABC, A×B×C×D 편성 엔진, 고정/변동 태그, 영업 손익, 매출원가, 이익, BEP, ABC. *Fix:* Expand glossary to cover all domain terms used in §3–§15, sorted alphabetically, with a one-line definition referencing the canonical axiom (if applicable).
- **[medium]** Module IDs cover modules but not features (§8) — M0–M12 identify modules but individual features (e.g., M0's "업종 4지선다", M2's "월합계 기본 + 일자별 선택 모드") are not numbered. *Fix:* Introduce FR-/F- numbering within each module (e.g., F0.1, F0.2) so downstream stories can pinpoint the unit. Alternatively, treat module content as FRs in a separate FR- table.
- **[low]** Cross-section synonym drift — "원가경영관리" (sub-title) vs "원가 관리" (intro) vs "원가계산" (실적·예산) — minor. *Fix:* Pick one canonical form and add to glossary.

## Shape fit — adequate

The product is a B2B SaaS for Korean SMBs with significant technical depth and a defined primary user (an owner/operator who is also the bookkeeper). The PRD's shape is well-suited to the domain: an Axioms Charter (§3) at the top to lock accounting principles, math chains (§6, §7) reproduced from the source Excel, a module table (§8) covering the full surface, and a verification matrix (§11) that doubles as acceptance scaffolding. §1.1's one-line definition ("월 1회, 6가지 데이터만 입력하면 원가·재고·손익·분석이 전부 자동으로 나오는, 제조업와 서비스업을 한 지붕에 담은 원가경영관리 웹 SaaS") is product-specific and would not transplant to another PRD. §8's M0–M12 module table maps cleanly to a 1-person-operator build pace: M0 onboarding → M1 master data → M2 inputs → M3 engine → M4 inventory → M5 reports → M6 verification → M7 simulation → M8 budget → M9 ABC → M10 AI → M11 close → M12 ops. The §13.2 tech stack ("Celery 등 복잡 인프라 제외") reinforces the operator constraint.

The shape mismatch is the absence of User Journeys for a B2B SaaS. Per the rubric: "Consumer product / multi-stakeholder B2B / meaningful UX → UJs with named protagonists are load-bearing." The PRD is multi-stakeholder (4 personas), the UX is meaningful (replacing 4-Excel workflow), and the PRD does not have a single UJ. The PRD is also slightly under-formalized on NFR: §14 has one threshold ("월 계산 수 초 내") and one scale note ("소형 여유 설계"), but no concurrency targets, no data-volume thresholds, no availability targets, no specific backup retention. For a "G2: 새벽에 혼자 고칠 수 있는 시스템" goal, recovery-time targets are missing.

### Findings
- **[critical]** No UJ section (§-) — Multi-stakeholder B2B SaaS without UJs is the rubric's named red flag. *Fix:* See Decision-readiness fix above (add 4+ UJs).
- **[medium]** NFRs in §14 are paper-thin — "월 계산 수 초 내(소형 데이터 전제), 계산 버튼 방식으로 예측 가능성 확보" and "데이터 규모: 소형 여유 설계(제품 수백·자재 수천 무리 없음 — 원본 슬롯 한계 철폐)" are the only two thresholds. *Fix:* Add NFR table with: response time (≤Xs for given rows), concurrency (≥N simultaneous 테넌트), data volume (max products, max months), availability target (e.g., 99.5% for monthly cycle), backup RPO/RTO (acceptable since 1-operator), audit log retention.
- **[medium]** §13.1 design language is adjective-only — breakpoints, grid density, color contrast, a11y not specified. *Fix:* Add WCAG target (AA), contrast ratio for negative-number red, font fall-back (Pretendard + ?), breakpoints (sm/md/lg).

## Mechanical notes

- **ID continuity**: All ID schemes are contiguous — Q-A through Q-J (10 decisions), M0–M12 (13 modules), V1–V8 (8 verifications), A1–A11 (11 axioms). No gaps or duplicates observed.
- **Glossary drift**: §부록 C has 6 terms; PRD uses ~30+ domain terms unlabeled. "원가경영관리" (sub-title) vs "원가 관리" vs "원가계산" drift is minor. "완전원가" (§6.1 (4)) vs "관리 회계 뷰" (A2) vs "full_cost" (A2) — three phrasings of the same concept.
- **Cross-references**: Bracket-prefixed references (e.g., [A1], [A3], [A5], [A6], [A7], [A8], [A9], [A10], [A11], [Q-E], [Q-F]) resolve cleanly. No dangling refs to unknown IDs. §-section references (§1.2, §6.1, §8) also resolve.
- **Assumptions Index roundtrip**: Not present — no `[ASSUMPTION]` markers, no index. Should be added.
- **UJ protagonist naming**: Not applicable — no UJ section exists.
- **Required sections for stakes**: For a B2B SaaS greenfield, the rubric expects Vision, Personas, UJs, FRs, NFRs, Success Metrics, Non-Goals, Open Questions, Glossary, Assumptions Index. The PRD has Vision (§1.1), Personas (§2), FRs (inline in §8), NFRs (§14), partial Glossary (§부록 C). Missing: UJs, Success Metrics, Non-Goals explicit, Open Questions, Assumptions Index.
- **Determinism**: §6.1's math chains are explicit enough that a Python implementation could be cross-checked mechanically. §11 V8 ("1원 단위 대조하는 회귀 테스트 스위트") commits to a testable harness.
- **Theoretical citation**: §15 "이론 근거 (2026-07 웹 검증 요지)" is thin — five claims but no specific paper, model, or source cited. For a PRD that invokes "AI-driven ABC", "TDABC 표준화", "클라우드 ABC", "유휴원가 정론", "지속가능성 원가" without citation, the downstream may want to verify the claim, not just accept it.
- **Service name**: §14 explicitly notes "서비스명 '비즈업'은 가칭, 확정 재논의" — flagged, but the document's title (top of file) uses "비즈업" as if it were committed. Minor inconsistency.
