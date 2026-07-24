# Validation Report — bizup (비즈업 통합 PRD v2.0)

- **PRD:** `C:/Users/c8rom/desktop/costmgr/_bmad-output/planning-artifacts/prd.md`
- **Rubric:** `C:/Users/c8rom/desktop/costmgr/.claude/skills/bmad-prd/assets/prd-validation-checklist.md`
- **Run at:** 2026-07-24T21:11:00+09:00
- **Grade:** Fair

> **⚠️ stale 보고서 메모 (2026-07-24 23:23 작성)**
>
> 본 validation의 3 Critical(User Journey / Success Metrics / Assumptions Index)은 21:56 시점 PRD 보강으로 해소되었습니다. 현재 PRD는 718 lines로 §2.A · §2.B · §부록 D 및 `[ASSUMPTION]` 인라인 마커를 포함합니다.
>
> **재검증(re-run) 권장**: 다음 세션에서 `/bmad-validate-prd` 를 새 컨텍스트로 실행해 등급 갱신을 확인하세요. (해소 priority: High — CE/IR 단계 진입 전 필수)

## Overall verdict

A 35KB / 12-section PRD with genuine domain depth: the §3 회계 공리 헌장 (A1–A11), §6.1 산식 체인, §11 검증 매트릭스 V1–V8, 부록 A 결정 Q-A~Q-J, and §8 모듈 표 M0–M12 all show engineering-grade rigor and decision traceability. The unification thesis (§1.2) is well-argued against empirical evidence ("수식 손상 4,468건·유령 링크 1,027건"). Six of seven rubric dimensions rate strong or adequate; only Downstream usability is thin.

However, three critical structural gaps block downstream UX/architecture/story extraction: no User Journey section, no Success Metrics anchored to the thesis, and no `[ASSUMPTION]` markers or Assumptions Index. The glossary covers 6 of ~30+ domain terms used. Treat this PRD as a strong technical specification; soft-launch it through a UX pass and an `[ASSUMPTION]`/Glossary expansion before epics and stories are written.

## Dimension verdicts

- Decision-readiness — adequate
- Substance over theater — strong
- Strategic coherence — adequate
- Done-ness clarity — adequate
- Scope honesty — adequate
- Downstream usability — thin
- Shape fit — adequate

## Findings by severity

### Critical (3)

**[Downstream usability · Shape fit]** — User Journey 부재 (§-)
다중 이해관계자 B2B SaaS (4개 페르소나, 4-Excel 워크플로 대체) 인데 UJ 섹션 자체가 없음. §1.3 불편함 목록과 §2 페르소나는 pre-persona 단계로 멈춤. UX·아키텍처·스토리 모두 흐름 추적 불가.
**Fix:** 제X장 User Journeys 신설, 최소 4개 명명 journey (월 사이클 / 예산 시뮬레이션 / 겸영 부문 카브아웃 / 관리자 온보딩), 각 journey에 protagonist·트리거·종착상태·예외 경로 명시.

**[Strategic coherence]** — Success Metrics 부재 (§2)
G1·G2는 출시 마일스톤·운영 모토일 뿐, 통합 thesis("ABC + 전통 + AI 통합이 SMB에 승리한다")를 검증할 지표가 없음. 카운터 메트릭도 없음.
**Fix:** Success Metrics 섹션 신설. 예: "월 마감 완료율(활성 테넌트)", "겸영 테넌트의 2-engine 동시 마감 비율", "AI 인사이트 채택률(계산결과 미변경 보장)". 각 메트릭에 카운터 메트릭(예: 마감 소요시간 ↔ 오류 재작업 빈도) 동반.

**[Scope honesty]** — `[ASSUMPTION]` 마커 및 Assumptions Index 부재 (§-)
"회계연도 시작월은 테넌트별 가변"(A1), "CCR 산출 단위 = 부서"(§7.2) 같은 추론이 확정 룰처럼 적혀 있고, 출처·확인 일자가 남지 않음.
**Fix:** 추론성 룰에 `[ASSUMPTION: ...]` 인라인 부착 + 문서 말미 Assumptions Index(원문 인용, 추론 근거, 일자) 부록 추가.

### High (3)

**[Decision-readiness]** — Open Questions 섹션 부재 (§-)
"서비스명 '비즈업'은 가칭, 확정 재논의"(§14), "파일럿 투입은 개발 중반 시점에 재논의"(§14) 같은 보류 결정이 한 줄로 흩어져 있고, owner·해결 마일스톤이 없음.
**Fix:** Open Questions 섹션 신설, 미해결 결정 목록화(owner·목표 마일스톤 부착). 각 미해결 긴장에 `[NOTE FOR PM]` 부착.

**[Done-ness clarity]** — §8 모듈 표에 인수 기준 부재
M0–M12는 입력/출력만 나열, 테스트 가능한 per-module done-ness 조건이 없음. M10 "AI 인사이트 질문 3개 자동 생성·캐시"의 "캐시" 정의도 미명시.
**Fix:** 각 모듈에 2–4개 인수 불릿("시스템은 X를 Y 시점에 Z 조건으로 수행한다" 형태, §11 V-row 포맷 참고). M10 예: "(a) 문서추출 신뢰도 ≥ X% 항목만 사용자 확정 후 저장 (b) 마감 데이터 변경 시 캐시 무효화 (c) 확정값만 A7/A11 계산에 투입".

**[Downstream usability]** — §부록 C 용어집 6항 vs PRD 사용 30+ 어휘
BOM, BEP, CVP, 세법 2기준, 기계시간, 역분개, append-only, 테넌트, RLS, 실제적 조업능력, TDABC, A×B×C×D 편성 엔진, 고정/변동 태그, 영업 손익, 매출원가 등 누락. 다운스트림 문서 간 cross-link가 끊김.
**Fix:** §3–§15에서 사용한 모든 도메인 어휘를 알파벳순으로 등재, 각 항목에 1행 정의 + 관련 axiom(Q-/A-/V-) 인용 추가.

### Medium (10)

**[Decision-readiness]** 가격 모델 민감도 부재 (§2) — "월 구독 1만원 단일 요금제"가 trade-off 없이 단언됨. persona "원가 전담자 없는 기업"과 G2 "새벽에 혼자 고칠 수 있는 시스템"으로 1단 요금제의 합리성을 1단락으로 정당화하거나 미해결 항목으로 명시.

**[Substance over theater]** Persona ④ "경영컨설턴트(대리 운영)" (§2) — 대리접속 기능 하나만驱动, §2 마케팅 라인에 부담. persona ①+④ 통합하거나 "운영자" 하위 섹션으로 분리.

**[Strategic coherence]** 2차 로드맵 항목 trigger 부재 (§10) — A×B×C×D 엔진·복수 예산 시나리오·CPA의 pull-forward 기준 부재. 각 2차 항목에 trigger 조항(예: "trigger: ≥5 테넌트가 예산 시나리오 2개 이상 요청 시").

**[Done-ness clarity]** §12 "캐시" 정의 미명시 — TTL·invalidation·eviction 정책 미명시. "캐시: 마감 완료 시점부터 다음 마감 시작까지 보존, 마감 데이터 변경 시 폐기" 형태로 구체화.

**[Done-ness clarity]** §13.1 디자인 어휘 형용사만 — "완전반응형", "사이드바 내비게이션"만 있고 breakpoint/grid 밀도/a11y 목표 부재. 구체 breakpoint(예: "≥1024px: PC 그리드 / <1024px: 폼 입력"), 12-col 8px base 그리드, WCAG AA 목표, Pretendard 폰트 fallback 명시.

**[Shape fit]** §14 NFR 표면적 — "월 계산 수 초 내"·"소형 여유 설계" 두 임계값만. 동시 사용자 N·데이터 볼륨·가용성 목표(예: 월 사이클 99.5%)·백업 RPO/RTO·감사로그 보존 기간 미명시. G2 "1인 운영자" 제약 아래에서도 RTO 목표는 필요.

**[Shape fit]** §13.1 디자인 토큰 미정 — breakpoint, grid, 대비비, a11y 기준 미정. UX 메모리에 잠긴 "WCAG AA / Professional 톤"과 동기화 필요.

**[Downstream usability]** M-ID가 모듈 단위, 기능 단위 FR- 번호 부재 (§8) — M0의 "업종 4지선다", M2의 "월합계 기본 + 일자별 선택 모드" 같은 개별 기능에 번호가 없음. F0.1 / F0.2 형식 도입 또는 별도 FR- 표 추가.

**[Downstream usability]** §-간 준용어 표류 — "원가경영관리"(부제) ↔ "원가 관리"(서론) ↔ "원가계산"(실적·예산) 드리프트. 글러서리에 정식 표기 확정.

**[Scope honesty]** "개발 중반 시점" 모호 (§14) — "M0–M6 완성 후 1주" 같은 구체 모듈 마일스톤으로 트리거 고정.

### Low (4)

**[Decision-readiness]** Q-G "report 파일은 기존 구조 분석으로 갈음" (부록 A) — 보류는 명시되었으나 영향 받는 26 보고서 surface 미열거. §9 목록으로 커버되는지 확인 또는 갭 플래그.

**[Substance over theater]** §2 "경쟁 우위" 중 "AI 온보딩·인사이트" 표현 — §12에서 3개 기능으로 좁혀지지만 framing이 일반적 AI-SaaS 주장과 겹침. "원가 영역 특화 AI" 또는 "회계 공리 가드레일 적용 AI"로 재구성.

**[Scope honesty]** §14 "파일럿 투입은 개발 중반 시점에 재논의" 모호성 — 모듈 마일스톤과 연결 필요.

**[Downstream usability]** §-간 준용어 드리프트 (minor) — 위 medium 항목 9와 동일 문제의 경미 버전.

### Mechanical notes

- **ID continuity**: All ID schemes contiguous — Q-A~Q-J (10 decisions), M0–M12 (13 modules), V1–V8 (8 verifications), A1–A11 (11 axioms). No gaps or duplicates observed.
- **Cross-references**: Bracket-prefixed references `[A1]`, `[A3]`, `[A5]`, `[A6]`, `[A7]`, `[A8]`, `[A9]`, `[A10]`, `[A11]`, `[Q-E]`, `[Q-F]` resolve cleanly. No dangling refs.
- **Assumptions Index roundtrip**: Not present — no `[ASSUMPTION]` markers, no index. Must be added.
- **UJ protagonist naming**: N/A — no UJ section exists.
- **Required sections for stakes (B2B SaaS greenfield)**: Vision ✓, Personas ✓, UJs ✗, FRs (inline in §8) △, NFRs ✓ (얇음), Success Metrics ✗, Non-Goals (분산·암묵) ✗, Open Questions ✗, Glossary ✗(얇음), Assumptions Index ✗.
- **Determinism**: §6.1 산식 체인은 Python 교차 검증 가능한 수준. §11 V8 "1원 단위 대조 회귀 테스트 스위트" 약속.
- **이론 인용**: §15 "이론 근거" 5개 항목이 출처(논문/모델/사이트) 없이 요지만 인용됨. AI-driven ABC·TDABC 표준화·클라우드 ABC·유휴원가 정론·지속가능성 원가 모두 검증 가능한 citation 필요.
- **서비스명**: §14 "비즈업은 가칭"이라고 명시했으나 문서 제목·메타는 "비즈업"을 확정처럼 사용. 사소한 불일치.

## Reviewer files

- `review-rubric.md`
