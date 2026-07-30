# costmgr Documentation Index

이 폴더는 프로젝트의 canonical 문서를 보관한다.

## Conventions (필수)

- [`conventions.md`](./conventions.md) — **모든 언어의 명명·시간·통화·ID·에러·포맷 규칙**
  - 새 코드를 작성하기 전에 반드시 읽는다.
  - 이 문서에 명시되지 않은 컨벤션은 사용하지 않는다.
  - 변경은 PR 리뷰 + 최소 1명 승인을 요구한다.

## Onboarding · Settings Wizard (Epic 1 / M0)

- [`onboarding-flow.md`](./onboarding-flow.md) — Story 1.1. 업종 선택 + 4지선다 메뉴 자동 토글 + A7 전진법.
- [`settings-wizard.md`](./settings-wizard.md) — Story 1.2. 회계연도 시작월·통화·언어·배부기준 3종 + [계산] 잠금.
- [`onboarding-schema.md`](./onboarding-schema.md) — `tenant_settings.onboarding` JSONB 스키마 + 검증 함수.
- [`PRD-외부-링크.md`](./PRD-외부-링크.md) — Story 1.2 인계용 PRD 매핑 인덱스.

## Architecture Decisions

- [`STACK_PIN.md`](./STACK_PIN.md) — AD-14 스택 핀 정책 + 현재 핀 표 (single source of truth)
- [`STACK_PIN.yaml`](./STACK_PIN.yaml) — 자동 검증용 YAML 미러
- [`architecture-decisions/AD-15-tenant-id-variance.md`](./architecture-decisions/AD-15-tenant-id-variance.md) — `tenant_id`는 UUID v4 (Supabase Auth 호환)
- [`architecture-decisions/AD-8-money-types-decision.md`](./architecture-decisions/AD-8-money-types-decision.md) — `Decimal` (Python) + `decimal.js` (TS) 결정 근거

## Lint 강제

컨벤션은 자동으로 강제된다:

- Python: `uv run ruff check` + `uv run python scripts/check_money_types.py`
- TypeScript: `pnpm lint:conventions` (apps/web)
- 통합: `make lint-conventions` (Story 0.4)
- CI: `.github/workflows/ci.yml` `lint-conventions` 잡

## CI / Dev

- [`DEPENDABOT.md`](./DEPENDABOT.md) — Dependabot 설정 (Story 0.3)
- [`../.github/CODEOWNERS`](../.github/CODEOWNERS) — 리뷰 책임자 매트릭스