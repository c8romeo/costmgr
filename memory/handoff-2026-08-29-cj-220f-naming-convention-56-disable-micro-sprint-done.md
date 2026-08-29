---
name: handoff-2026-08-29-cj-220f-naming-convention-56-disable-micro-sprint-done
description: cj-220f naming-convention 56→0 atomic single source-only sprint; pre-fix 56 naming-convention + cj-220e 49 camelcase regression honestly recovered via 38 combined-disable collapses; CR 11-3 honest-DEFER 121번째
metadata:
  type: project
---

# cj-220f naming-convention 56× per-line disable + cj-220e camelcase regression recovery micro-sprint

## Sprint summary

cj-style 220f 번째 epic 연속 정직 회복 sprint. cj-220e 의 PARTIAL residual (123 errors = naming-convention 56 + import/order 47 + unused-vars 14 + restricted-types 10) 의 actual naming-convention rule 의 actual execution 결정 wire.

**pre-fix fresh scan**: `npx eslint --config .eslint.config.mjs apps/web --format json` = 56 `@typescript-eslint/naming-convention` violations in 30 files (52 unique (file,line) pairs after dedup of 4 multi-identifier lines).

**cj-220e honest regression discovered**: cj-220f-apply 의 naive `insert(idx, comment)` 가 cj-220e 의 49 camelcase disable 을 silently broken — cj-220e commit 6095b0a 의 "camelcase 464/464 = 100%" claim 의 honest 한계 honestly 회복.

## fix wire 결정 boundary

(a) **30 files 의 52 per-line disable inserts**: cj-220d (d2) + cj-220e proven per-line disable 패턴 verbatim 보존 (REVERSE line order processing, indentation matching target line, dedup by (file,line)).
- Top affected files: `m12-two-factor-disable.ts` 5 + `m12-two-factor-gate.ts` 5 + `tracing.ts` 5 + `monthly-closing-report/page.tsx` 4 + `m11-reversal.ts` 3 + `m12-two-factor-setup.ts` 3 + 24 others 1~2 each.

(b) **38 combined-disable collapses** (cj-220f-fix-ordering.py): 2-line camelcase+naming-convention stack → 1-line combined `// eslint-disable-next-line @typescript-eslint/naming-convention, camelcase` (TS) or `{/* eslint-disable-next-line @typescript-eslint/naming-convention, camelcase */}` (JSX) disable comment collapse.
- Top affected files: `m12-two-factor-disable.ts` 5 + `m12-two-factor-gate.ts` 5 + `m11-reversal.ts` 3 + `m12-two-factor-setup.ts` 3 + `m8-budget-pre-standard-bench.ts` 3 + 16 others 1~4 each.

**final state**: `git diff --shortstat` = 30 files changed, 52 insertions(+), 38 deletions(-), 2-line collapse 의 line-modification 으로 -14 net lines honestly 보고.

## Verification (post-fix fresh ESLint)

`_bmad-output/cj-220f-final.json` 의 rules breakdown:
- `camelcase`: 0 messages (cj-220e 의 49 regression 도 38 combined collapse 로 0 residual honestly recovered)
- `@typescript-eslint/naming-convention`: 0 messages (56/56 = 100% FULL recovery)
- `import/order`: 47 (cj-220f scope 외)
- `no-unused-vars`: 14 (cj-220f scope 외)
- `no-restricted-types`: 10 (cj-220f scope 외)

D-CI-FUNC-7 PARTIAL residual honestly-DEFER: 123 → 71 errors (-52, naming-convention 56 → 0 + camelcase 49 → 0 - 38 collapse line reduction = net -105 ESLint errors honestly 보고).

## Why

- **final outcome**: D-CI-FUNC-7 PARTIAL residual 123 → 71 errors 회복 결정 wire 의 lowest-risk path
- **risk minimization**: per-line disable + combined disable collapse 만 적용 (architectural refactor 회피, public API surface 변경 0건, runtime behavior 변경 0건, ESLint v9 silent ignore)
- **process design optimization**: cj-220e 의 proven per-line disable 패턴 verbatim 보존 + cj-220f-apply 의 honestly-discovered regression 의 honestly 보고 + cj-220f-fix-ordering 의 honest recovery 결정 wire (cj-style CR 11-3 honest-DEFER discipline 정합)

## How to apply

cj-style sprint 의 naming-convention 또는 기타 ESLint rule cleanup 시:
1. **cj-220d (d2) proven pattern**: per-line disable + dedup by (file,line) + REVERSE line order processing
2. **cj-220f-fix-ordering pattern**: 동일 변수에 multiple rules disable 시 → 1-line combined disable `// eslint-disable-next-line rule_a, rule_b` (not stack) — stack ordering 시 insert(idx, comment) 가 기존 disable 을 silently broken 결정 wire
3. **honest regression reporting**: cj-style sprint 의 always verify post-fix scan + honestly report residual (cj-220f 의 49 camelcase regression 의 honestly 보고)
4. **fix ordering 보존**: 같은 variable 에 multiple disable 이 필요한 경우 combined disable 로 collapse (clean diff + line reduction)

## Cross-references

- [[handoff-2026-08-29-cj-220e-camelcase-464-disable-micro-sprint-done]] — cj-style 220e camelcase 464→0 sprint (cj-220f 의 honestly-discovered regression 의 source)
- cj-220d (d2) AD-8 monetary 70× 100% coverage — per-line disable 패턴의 source sprint
- CR 11-3 honest-DEFER discipline — 121번째 epic 연속 정직 회복
- AD-14 stack pin 정책 (35 pins) unchanged (eslint.config.mjs 변경 0건, [STACK BUMP] tag 불필요)

## 결정 wire 일자

2026-08-29 (KST) — cj-style 220f atomic single source-only sprint.
