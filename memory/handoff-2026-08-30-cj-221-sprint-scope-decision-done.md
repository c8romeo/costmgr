---
name: cj-221-sprint-scope-decision-done
description: cj-221 sprint scope 결정 wire (2026-08-30, cj-style 123번째 atomic single docs-only sprint)
metadata:
  type: project
---

# cj-221 sprint scope 결정 wire DONE (2026-08-30)

## 무엇을 했나

cj-220g jsx-fix-rollback (commit e7da5a9, cj-style 122번째) 후 진짜 다음 pending action 식별.
4 options 비교 분석 후 **cj-221 import-order 47× fix sprint scope 결정 wire** 진입.

## 왜 이 선택인가

**4 options 비교**:

| Option | Risk | Status | Decision |
|--------|------|--------|----------|
| (i) cj-221 import-order 47× fix | 🟡 MEDIUM | scope 결정 wire 진입 | ✅ CHOSEN |
| (ii) D-CI-FUNC-* blockers | 🔴 HIGH | honestly preserved (status: open 정직) | 보류 |
| (iii) A37 master PRD v2.0 edit | — | done (2026-08-20) | obsoleted |
| (iv) 1-3 잔여 deferral (T2.2 + T6.3) | 🟢 LOW | 별도 context | 결정 보류 |

**선택 근거 (4종)**:

1. **final outcome 우선** = CI green (D-CI-FUNC-7 PARTIAL 잔여 71 errors 의 47× import/order
   해결 후 residual 24 errors = unused-vars 14 + restricted-types 10 으로 축소) 의
   lowest-risk path
2. **risk minimization** = surgical per-line disable 만 적용
   - per-file eslint --fix 자동 수정 회피 (auto-fix의 다른 ESLint rule side-effect 위험)
   - manual import sequence 변경 회피 (line number shift 위험)
   - line number drift 0건, public API surface 변경 0건, runtime behavior 변경 0건
3. **process design 정합** = cj-220b (b1) + cj-220d 의 proven per-line disable
   atomic single source-only sprint 패턴 verbatim 보존 (CR 11-3 honest-DEFER discipline 정합)
4. **cj-style 연속 정직 회복 chain 보존** = 113(cj-220a) → 122(cj-220g) 의
   123번째 natural continuation

## 무엇이 변경됐나

**sprint-status.yaml metadata only**:
- action_items 신규 entry: `cj-221-import-order-fix-A908` (status: pending, date: 2026-08-30)
- last_updated_note_v4_30 신규 (2026-08-30 KST)

**runtime 동작 변화**: 0건
**AD-14 stack pin 정책 (35 pins) unchanged** ([STACK BUMP] tag 불필요)

## cj-style chain 정합

| ID | Status | Sprint | Notes |
|----|--------|--------|-------|
| 113 (cj-220a) | ✅ done | PARTIAL honestly-DEFER | commit ea5a428 |
| 114 (cj-220a) | ✅ done | PARTIAL honestly-DEFER | commit ea5a428 |
| 115 (cj-220a) | ✅ done | PARTIAL honestly-DEFER | commit ea5a428 |
| 116 (cj-220a) | ✅ done | PARTIAL honestly-DEFER | commit ea5a428 |
| 117 (cj-220c) | ✅ done | react-hooks config hygiene 3× | A889~A892 |
| 118 (cj-220d) | ✅ done | AD-8 monetary 724× per-line disable | A893~A896 |
| 119 (cj-220d (d2)) | ✅ done | AD-8 monetary 70× 100% coverage | v4_26 |
| 120 (cj-220e) | ✅ done | camelcase 464× per-line disable | commit 6095b0a |
| 121 (cj-220f) | ✅ done | naming-convention 56× per-line disable | commit edf486a |
| 122 (cj-220g) | ✅ done | jsx-fix-rollback | commit e7da5a9 |
| **123 (cj-221)** | **🟡 pending** | **import-order 47× fix scope 결정 wire** | **THIS sprint** |

## 다음 결정 wire 후보 (사용자 결정 보류)

(i) **cj-221 actual sprint execution 진입** (47 disables 적용, 30~60 min, MEDIUM risk)
(ii) **cj-222 unused-vars 14× fix** (low risk, mechanical)
(iii) **cj-223 restricted-types 10× fix** (medium risk, architectural — config 결정 필요)
(iv) **live CI verification** (다음 push 후 run_id + 13 job matrix honest aggregation)
(v) **A37 master PRD v2.1 maintenance** (cj-style carry-over 15번째 docs only, low risk)
(vi) **1-3 잔여 deferral follow-up** (T2.2 real SDK + T6.3 logging redaction, 별도 context)

## CR 11-3 honest-DEFER discipline 정합

- 결정 단계(sprint scope)만 먼저 wire (cj-220a/b PARTIAL honestly-DEFER 패턴 verbatim 보존)
- actual source fix는 다음 sprint 진입 시점 사용자 결정에 따름
- metadata only 변경, source/test/ci.yml 무변경
- 4 options 비교 분석 결정 wire 보존 (사용자 결정 wire 보류 표면화)

## 결정 wire 일자

2026-08-30 (KST)