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

## M1 Baseline — Product / Item Master & BOM (Epic 2 / M1)

- [`product-item-master.md`](./product-item-master.md) — Story 2.1. 5종 product_type + 코드 자동생성 + capability gate.
- [`bom-matrix.md`](./bom-matrix.md) — Story 2.2. BOM 비중 합 100% invariant + bulk-replace PUT + 모품목/자품목 type rules.
- [`item-type-change.md`](./item-type-change.md) — **Story 2.3 (2026-08-01)**. 품목 유형 변경 무결성 가드 — `product_type` 변경 시 BOM·수불 참조 0건 검증, 참조 존재 시 **409 PRODUCT_TYPE_HAS_REFERENCES** (RFC 7231 §6.5.8 상태 충돌). `code`는 여전히 403 PRODUCT_IMMUTABLE_FIELD (AD-18). Epic 5 수불 stub 마커 포함.

## Epic 3 — Monthly Input (M2)

- [`monthly-input.md`](./monthly-input.md) — Story 3.1. 6-stream 입력 + 일자별 토글 + 완료 게이트.
- [`monthly-input-fte.md`](./monthly-input-fte.md) — **Story 3.2 (2026-08-01)**. PRD §6.1 인건비 정밀 — `pay_type` 분기 (monthly 정규직 vs daily 일용직) + 5개 breakdown 필드 (기본급·시간외·복리후생·상여·퇴직충당금) + 회사부담임률. `tenant_settings.payroll` JSONB per-tenant override. TS mirror `apps/web/lib/l2-input-fte.ts`. Capability unchanged (FTE precision = `MONTHLY_INPUT_LABOR`의 일부).

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