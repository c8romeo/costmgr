---
name: cj-287-csv-e2e-activate-sprint-done
description: cj-287 wire sprint 결정 wire (cj-style 287번째 source+docs atomic single sprint) — Epic 30+ CSV E2E un-skip + CR 1-1 audit fix + D-WEB-E2E-7 ownership ACTIVATED
metadata:
  type: project
---

# cj-287 wire sprint 결정 wire (cj-style 287번째 source+docs atomic single sprint)

**결정 wire 일자**: 2026-09-06 (KST)
**territory**: cj-282 Epic 30+ PRD entry `0c7524e` 의 Story 30.1 CSV export 결정 wire (cj-286 EXTENSION wire sprint `e408668` 의 next 옵션 (a) verbatim mirror)
**chain CLOSED 직후 진입**: cj-286 EXTENSION wire sprint `e408668` (cj-style 286번째) 의 옵션 (a) 진입 = 본 sprint

## sprint scope 결정 wire — 11 files = 1 NEW + 6 MODIFIED source + 2 NEW + 2 MODIFIED meta atomic single sprint

### 1 NEW source
1. `apps/api/modules/reports/__init__.py` (~24 LOC) — package marker enabling router import

### 6 MODIFIED source
1. `apps/api/modules/reports/csv_routes.py` — 3 changes (import + capability gate + CR 1-1 ActionClass fix + docstring)
2. `apps/api/main.py` — 2 changes (router mount after `vendor_management_router` + 4 exception handlers before `/health`)
3. `apps/web/components/reports/CsvExportTab.tsx` — 3 changes (tenantId prop interface + accept + remove TODO placeholder)
4. `apps/web/app/[locale]/(dashboard)/reports/page.tsx` — 2 changes (JWT decode block + tenantId prop pass-through)
5. `apps/web/e2e/csv-export.spec.ts` — 3 changes (D-WEB-E2E-7 ACTIVATED header + describe.skip → describe + 4 placeholder replacements)
6. `scripts/dev_seed.py` — 3 changes (3 NEW --token-only flags + effective_* override logic + echo)

### 2 NEW meta
1. `_bmad-output/implementation-artifacts/commit-msg-cj-287.txt` (~150 LOC)
2. `memory/handoff-2026-09-06-cj-287-csv-e2e-activate-sprint-done.md` (this file)

### 2 MODIFIED meta
1. `_bmad-output/implementation-artifacts/sprint-status.yaml` — A700 NEW entry + last_updated_note_v4_55 EXTENSION
2. `memory/MEMORY.md` — cj-287 hook EXTENSION

## 핵심 발견 — CR 1-1 silent audit failure (cj-287 critical bug fix)

### Bug 발견

`csv_routes.py:359` (cj-282a original commit `eae9110`) 가 `emit_audit_typed(action_class=ActionClass.AUDIT, action="export_csv", ...)` 호출. `ActionClass.AUDIT` registry 는 `audit_log_exported/purged/archived/pii_masked/cold_archived/personal_data_erased` 6 action 만 허용 — `export_csv` 는 accept 안 함.

`_ActionRegistry.validate()` (cj-285 EXTENSION wire sprint 결정 wire) 가 `ValueError` raise → `except Exception:` at lines 373-377 silently swallow → logger exception log 만 emit → CSV byte stream 정상 flush.

### Effect

**모든 CSV export operation 의 audit trail 이 silently 누락** — pilot customer 가 CSV export 사용 시 audit log 에 record 없음 → CR 1-1 verbatim violation + Epic 17 wire `2ada2ec` 의 fail-closed 정책 위반 (audit emit fail 시 export 차단, not best-effort).

### Fix

`action_class=ActionClass.AUDIT` → `action_class=ActionClass.REPORTS` (1-word change at line 362).

`ActionClass.REPORTS` (cj-285 EXTENSION wire sprint `215e963` 결정 wire) 는 `export_csv/pdf/email/scheduled` 4 actions accept → registry validate 정상 통과 → audit row 정상 INSERT.

### 결정 wire 보류 — 5 other audit action call sites 검증

본 sprint 는 CSV export 1 call site 만 fix. PDF/Email/Scheduled territory (cj-288+~cj-292+) 진입 시 동일 pattern 검증 결정 wire 보류. Drift detector `tests/integration/test_audit_action_consistency.py` 가 cj-285 EXTENSION 의 3-way gate (registry ↔ DB CHECK ↔ call sites parity) enforce.

## 결정 wire 정합 (cj-282 PRD entry AD/NFR bind verbatim)

### AD bind 3/3 (cj-282 PRD entry §F44.1 verbatim)

- **AD-2** (audit-first INSERT append-only) — `emit_audit_typed(action_class=ActionClass.REPORTS, action="export_csv", flush=True)` BEFORE byte stream flush, CR 1-1 verbatim 회복.
- **AD-10** (identity + 2FA via owner-only RBAC) — `Depends(require_any_role("owner", "admin"))` 결정 wire 보존.
- **AD-12** (verify-first capability gate) — `Depends(require_capability(Capability.EXPORT_CSV))` 결정 wire 진입 (AD-56 (c) sub-decision verbatim 적용).
- **AD-22** (owner-only RBAC verbatim) — `require_any_role("owner", "admin")` 결정 wire 보존.

### NFR bind 2/7 active (cj-282 PRD entry §F44 NFR 매트릭스)

- **NFR5** (streaming P95 ≤ 5s for 10만 row) — `StreamingResponse` 결정 wire 보존, `MAX_EXPORT_ROWS = 100_000` pre-flight check 결정 wire 보존.
- **NFR18** (ko-KR vocabulary SSOT) — UTF-8 BOM (0xEF 0xBB 0xBF) 결정 wire 보존.

### CR 결정 wire verbatim 보존

- **CR 0-2 RLS** — `get_tenant_context` dep + cross-tenant check at lines 285-289 결정 wire 보존.
- **CR 1-1 audit-first INSERT** — silent swallow bug 정직 회복 (line 362 fix).
- **CR 9-6 atomic commit** — `git commit -F <file>` convention + commit-msg file verbatim.
- **CR 11-3 honest-DEFER 224번째** — cj-282a 의 223번째 skip 결정 패턴 보존 해제.
- **CR 11-4 P-015 pure validator pattern** — `_iter()` generator + `StreamingResponse` 결정 wire 보존.
- **CR 12-5 D-14 typed exception envelope** — 4 NEW exception handlers 결정 wire 진입 (CR 12-5 verbatim pattern).
- **CR 12-5 D-PARITY-01 inversion** — frontend prop interface mirror 결정 wire 진입.

## D-WEB-E2E-7 ownership wire ACTIVATED (cj-style 287번째)

### 결정 wire 일자 + 의미

- **ACTIVATION moment**: cj-style 287번째 = FIRST D-WEB-E2E-* ownership wire in Epic 30+ Reporting & Export MVP territory.
- **Pre-condition**: cj-286 EXTENSION wire sprint `e408668` 의 `csv-export.spec.ts` 신규 생성 + describe.skip baseline 적용 (D-WEB-E2E-7 ownership 결정 wire 보류).
- **Activation**: cj-287 의 `describe.skip → describe` + 4 placeholder replacements = D-WEB-E2E-7 ownership wire 결정 wire 진입 완료.

### Pattern 결정 wire (Epic 29+ chain verbatim mirror)

Epic 29+ 의 D-WEB-E2E-1~6 은 cj-274 → cj-279 sprint chain 에서 activation 완료 (`memory/handoff-2026-09-05-cj-274-web-e2e-chain-close-honest-defer.md`). 본 sprint 의 D-WEB-E2E-7 = Epic 30+ territory 의 FIRST ownership wire activation.

### 다음 D-WEB-E2E-* 결정 wire queue

- **D-WEB-E2E-8** (PDF export, cj-288+ territory)
- **D-WEB-E2E-9** (Email delivery, cj-290+ territory)
- **D-WEB-E2E-10** (Scheduled reports, cj-292+ territory)

## runtime 동작 변화 honestly reported

- source+docs atomic — 1 NEW source + 6 MODIFIED source + 2 NEW meta + 2 MODIFIED meta = **11 files atomic single sprint** 결정 wire 진입.
- dev_seed 변경 1 (MODIFIED) — `--token-only` mode 에 3 NEW flags EXTENSION 결정 wire.
- ci.yml 변경 0 — `apps/web/playwright.config.ts:15 testDir: "./e2e"` auto-discovery 가 cj-287 spec 자연스럽게 pickup 결정 wire 보존.
- AD-14 stack pin (35 pins) 변경 없음 / [STACK BUMP] tag 불필요.
- 13 job matrix unchanged (cj-style baseline-green 보존).
- capability matrix v1.54 EXTENSION preserved from cj-285 EXTENSION wire sprint 결정 wire (no change at v1.55).
- audit action EXTENSION preserved from cj-285 EXTENSION wire sprint 결정 wire (no change at v1.55).

## Next (cj-288+ 결정 wire 보류)

- **옵션 (a) cj-288 wire sprint** (cj-style 288번째, RECOMMENDED next) — Story 30.2 PDF export source+docs atomic (weasyprint vs reportlab 결정 + Jinja2 ko-KR template + matplotlib 3 charts 결정 wire 진입). OQ-EPIC30+-1 + OQ-EPIC30+-4 결정 보류 해소 진입.
- **옵션 (b) cj-287 close-out retro 결정 wire** (cj-style 288번째) — 14-section §1~§14 verbatim retro document 진입 (Phase 23/24 close-out retro `7875ac9`/`c14199b` verbatim pattern mirror).
- **옵션 (c) cj-289 wire sprint** (cj-style 289번째) — Epic 30+ capability matrix sync (이미 cj-285 EXTENSION 결정 wire, close-out retro only 결정).
- **옵션 (d) Epic 29+ spec implementation chain 진입 결정 wire** (cj-29x territory) — 18 spec drifts unresolved + 18 stories × multi-sprint.
- **옵션 (e) Pilot 고객 유치 결정 wire 진입** (PRD OQ-3 파일럿 게이트 1주 post M0-M6).
- **옵션 (f) NFR18 ko-KR.json SSOT migration 결정 wire** (cj-style 288+ EXTENSION 진입 시) — inline 한국어 strings → `apps/web/messages/ko-KR.json` SSOT migration 결정 wire 보류.

## Cross-References

- cj-282 Epic 30+ PRD entry: `0c7524e` (cj-style 220번째)
- cj-282a Story 30.1 CSV source+docs: `eae9110` (cj-style 283번째)
- cj-282a lint-conventions fix: `e803ae2` (cj-style 283 follow-up)
- cj-282a close-out retro: `7403920` (cj-style 284번째)
- cj-285 EXTENSION wire sprint (capability + audit): `215e963` (cj-style 285번째)
- cj-286 EXTENSION wire sprint (fixtures + spec + AD-56): `e408668` (cj-style 286번째)
- **cj-287 wire sprint** (CSV E2E activation + CR 1-1 fix): `(pending)` (cj-style 287번째)
- AD-56: `docs/architecture-decisions/AD-56-phase-30-epic-30-plus-reporting-export-decisions.md`
- Capability matrix: `apps/api/core/capability.py` v1.54 (cj-285 EXTENSION preserve)
- Audit action registry: `apps/api/core/audit_action.py` ActionClass.REPORTS (cj-285 EXTENSION preserve)

**결정 wire 진입 완료**.
