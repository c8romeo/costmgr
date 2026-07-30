# PRD 외부 링크 (Story 1.2 인계용)

Story 1.2 구현 시 참조한 PRD 섹션들의 외부 링크 + 인용 인덱스. PRD 자체는
이 repo에 비공개로 보관되므로 외부 export 위치가 확정되면 본 문서의 링크를 갱신한다.

| PRD 섹션 | 주제 | 본 repo 의 매핑 |
|---|---|---|
| §3.A1 | 회계연도 axiom (period key 포맷) | [`docs/conventions.md#04-wizard-필드-포맷-story-12`](./conventions.md) · [`docs/onboarding-schema.md`](./onboarding-schema.md) |
| §3.A6 | 1원 단위 검증 (KRW/USDTYPE) | [`docs/conventions.md#5-money-ad-8`](./conventions.md) |
| §3.A7 | 일관성 — 전진법 | [`docs/onboarding-flow.md#3-7-day-grace--a7-전진법-decision-1`](./onboarding-flow.md) |
| §3.A11 | CCR = 부서 원가 ÷ 실제적 조업능력 | [`docs/settings-wizard.md#4-industry-conditional-completion-prd-8m0b`](./settings-wizard.md) |
| §4.1 | 4지선다 표 | [`docs/onboarding-flow.md#2-업종--메뉴-매핑-prd-41`](./onboarding-flow.md) |
| §7.2 | TDABC 정의 (동인) | [`docs/onboarding-schema.md`](./onboarding-schema.md) |
| §8.M0(a) | 업종 자동 토글 | [`docs/onboarding-flow.md`](./onboarding-flow.md) |
| §8.M0(b) | 계산 잠금 (4필드 + 배부기준) | [`docs/settings-wizard.md`](./settings-wizard.md) |
| §14.NFR18 | ko-KR (MVP language lock) | [`docs/conventions.md`](./conventions.md) + ux-locked-decisions §4 |
| UJ-1 | 예외경로 (업종 변경 시도 → A7 차단) | [`docs/onboarding-flow.md#34-결정-사유-코드-industrychangedecisionreason`](./onboarding-flow.md) |

> **업데이트 정책**: PRD가 갱신될 때마다 본 문서의 매핑 셀도 함께 갱신한다.
> 불일치 발견 시 Story 0.5 (canonical doc index) 에서 일괄 정리.