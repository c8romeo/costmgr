# Epic 17 T2+T3 UI frontend atomic wire DONE — handoff

**Date**: 2026-08-22 (KST)
**Cycle**: cj-style Epic 17 4번째 진입점 = **cj-style 83번째** epic 연속 정직 회복 atomic wire
**Wire scope**: frontend (T2+T3) + tests + atomic commit = **22 files atomic single sprint**
**Backend scope (T1+T4+T5+T6+T7)**: already DONE in `2ada2ec` (cj-style 82번째), D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED this sprint

---

## §1 Sprint summary

### Wire scope (22 files atomic single sprint)
| File | Type | LOC | Purpose |
|------|------|-----|---------|
| `apps/web/app/[locale]/(dashboard)/audit-log/layout.tsx` | NEW | ~30 | auth gate (cookie check → redirect /ko-KR/login) |
| `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` | NEW | ~100 | RSC — fetches `fetchAuditLogServerSide`, hands to `<AuditLogPanel>` |
| `apps/web/components/audit/AuditLogPanel.tsx` | NEW | ~200 | Client orchestrator (filters + page + data + loading + error + modal state) |
| `apps/web/components/audit/AuditLogFilterPanel.tsx` | NEW | ~150 | 8-field filter form (actor_id, action, action_class, resource_type, resource_id, start_date, end_date, trace_id) + Apply/Reset |
| `apps/web/components/audit/AuditLogTable.tsx` | NEW | ~150 | 7 columns table (time, actor, action, resource, ip, trace_id, payload), click trace_id opens detail modal |
| `apps/web/components/audit/AuditLogPagination.tsx` | NEW | ~70 | Prev/Next + page indicator + total count |
| `apps/web/components/audit/AuditLogExportButton.tsx` | NEW | ~80 | CSV export with current filter snapshot via `exportAuditLogCsv` |
| `apps/web/components/audit/AuditLogDetailModal.tsx` | NEW | ~120 | `<dialog>` element with payload + actor_id + ip + user_agent + trace_id + copy button |
| `apps/web/lib/audit/audit-log-client.ts` | NEW | ~365 | TS interface mirrors + 5 fetch wrappers + `AuditLogApiError` class |
| `apps/web/app/[locale]/(dashboard)/activity/layout.tsx` | NEW | ~30 | auth gate (all tenant members allowed, no role check) |
| `apps/web/app/[locale]/(dashboard)/activity/page.tsx` | NEW | ~80 | RSC — fetches `fetchActivityStreamServerSide` with URL `window_days` param |
| `apps/web/components/activity/ActivityStreamPanel.tsx` | NEW | ~180 | Client orchestrator with window state + URL sync via `router.replace` |
| `apps/web/components/activity/ActivityStreamWindowSelector.tsx` | NEW | ~80 | 4 buttons (1d/7d/30d/90d) with `aria-pressed` |
| `apps/web/components/activity/ActivityStreamTimeline.tsx` | NEW | ~110 | Bucket list with `formatBucket` for hourly/daily/weekly buckets |
| `apps/web/components/activity/ActivityStreamEntry.tsx` | NEW | ~80 | Single entry row with deep-link to `/audit-log?trace_id=...` |
| `apps/web/lib/server-api.ts` | MODIFIED | +80 | 2 NEW server-side helpers: `fetchAuditLogServerSide` + `fetchActivityStreamServerSide` |
| `apps/web/messages/ko-KR.json` | MODIFIED | +48 keys | `audit_log.*` 35 keys + `activity.*` 13 keys (SSOT only, P-015 verbatim) |
| `apps/web/__tests__/audit-log/page.test.tsx` | NEW | ~280 | 8 NEW vitest cases (D-001, empty, forbidden, table render, modal open, filter apply, export click, loading) |
| `apps/web/__tests__/audit-log/audit-log-client.test.ts` | NEW | ~250 | 11 NEW vitest cases (GET paths, 400/403/404/413 envelopes, TS interface shape parity) |
| `apps/web/__tests__/i18n/audit-log-i18n-ssot.test.ts` | NEW | ~85 | 3 NEW SSOT drift detector cases (35 keys min + verbatim invariants) |
| `apps/web/__tests__/activity/page.test.tsx` | NEW | ~210 | 7 NEW vitest cases (D-001, empty, timeline render, window selector, window change, error envelope, all-tenant-members visibility) |
| `apps/web/__tests__/i18n/activity-i18n-ssot.test.ts` | NEW | ~85 | 3 NEW SSOT drift detector cases (13 keys min + verbatim invariants) |

**Wire scope tally**:
- **20 NEW files** (T2: 9 NEW = 1 layout + 1 page + 6 components + 1 client + i18n_test shared; T3: 6 NEW = 1 layout + 1 page + 4 components; tests: 5 NEW)
- **2 MODIFIED files** (ko-KR.json + lib/server-api.ts)
- **Total**: 22 files atomic single sprint

### Sprint transitions
- `epic-17-t2-t3-ui-wire: backlog → done` (per sprint-status.yaml §1111 insert)
- `D-EPIC-17-WIRE-DEFER-T2-T3-UI: open → RESOLVED` (honest resolution; no carry-over)

---

## §2 ACs satisfied (PRD §F21.2 + §F21.3 verbatim)

### §F21.2 — audit log viewer UI ✅ (16 ACs verbatim)
- §F21.2.1 — `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW (RSC + `fetchAuditLogServerSide` race-free initial fetch via F-20)
- §F21.2.2 — `apps/web/components/audit/AuditLogPanel.tsx` NEW (orchestrator with `useState` for filters/page/data/loading/error/selectedEntry)
- §F21.2.3 — `AuditLogFilterPanel.tsx` NEW (8-field filter form, Apply/Reset, URL-sync via `router.replace`)
- §F21.2.4 — `AuditLogTable.tsx` NEW (7 columns: time/actor/action/resource/ip/trace_id/payload, click trace_id opens modal)
- §F21.2.5 — `AuditLogPagination.tsx` NEW (Prev/Next + page indicator + total count)
- §F21.2.6 — `AuditLogExportButton.tsx` NEW (CSV export with filter snapshot via `exportAuditLogCsv`)
- §F21.2.7 — `AuditLogDetailModal.tsx` NEW (`<dialog>` element, payload + actor_id + ip + user_agent + trace_id + copy button)
- §F21.2.8 — `apps/web/lib/audit/audit-log-client.ts` NEW (TS interface mirrors + 5 fetch wrappers)
- §F21.2.9 — `apps/web/messages/ko-KR.json` EXTENSION (35 keys `audit_log.*` namespace SSOT, P-015 verbatim)
- §F21.2.10 — `(dashboard)` route group protected (Phase 3-1 T4 wire 정합)
- §F21.2.11 — owner/admin RBAC at backend (`audit-log` endpoints owner/admin only per `2ada2ec` §F21.1)
- §F21.2.12 — vitest RTL render discipline (`apps/web/__tests__/audit-log/page.test.tsx` 8 cases)
- §F21.2.13 — TS interface shape parity (CR 12-5 D-PARITY-01 verified via `audit-log-client.test.ts`)
- §F21.2.14 — vitest i18n SSOT drift detector (CR 11-4 D-002 + P-015 verbatim via `audit-log-i18n-ssot.test.ts`)
- §F21.2.15 — capability gate per-tenant on/off (CR 12-5 D-GATE-01 via `AUDIT_LOG_VIEW` capability)
- §F21.2.16 — `apps/web/lib/server-api.ts` EXTENSION (server-side helper `fetchAuditLogServerSide` with 5s AbortController timeout)

### §F21.3 — activity stream UI ✅ (8 ACs verbatim)
- §F21.3.1 — `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW (RSC + `fetchActivityStreamServerSide`)
- §F21.3.2 — `ActivityStreamPanel.tsx` NEW (orchestrator with window state + URL sync via `router.replace`)
- §F21.3.3 — `ActivityStreamWindowSelector.tsx` NEW (4 buttons 1d/7d/30d/90d with `aria-pressed`)
- §F21.3.4 — `ActivityStreamTimeline.tsx` NEW (bucket list with `formatBucket` for hourly/daily/weekly buckets)
- §F21.3.5 — `ActivityStreamEntry.tsx` NEW (single entry row with deep-link to `/audit-log?trace_id=...`)
- §F21.3.6 — all tenant members allowed (PRD §F21.3 verbatim — no role check, all members can view)
- §F21.3.7 — vitest RTL render discipline (`apps/web/__tests__/activity/page.test.tsx` 7 cases)
- §F21.3.8 — `apps/web/messages/ko-KR.json` EXTENSION (13 keys `activity.*` namespace SSOT)

### Backend carry-over (T1+T4+T5+T6+T7) — already DONE in `2ada2ec` ✅
- §F21.1 audit log query API ✅
- §F21.4 cross-region audit log visibility ✅ (Phase 5 wire `f093f8c` carry-over)
- §F21.5 CSV export ✅
- §F21.6 Capability gate AUDIT_LOG_VIEW ✅
- §F21.7 tests backend ✅ (29 NEW pytest)

---

## §3 3중 게이트 FINAL CLEAN (cj-style 83번째 standard)

### (1) vitest focused — 5 NEW test files
```
__tests__/audit-log/page.test.tsx             8 cases PASS
__tests__/audit-log/audit-log-client.test.ts 11 cases PASS
__tests__/i18n/audit-log-i18n-ssot.test.ts    3 cases PASS
__tests__/activity/page.test.tsx              7 cases PASS
__tests__/i18n/activity-i18n-ssot.test.ts     3 cases PASS
─────────────────────────────────────────────────
TOTAL                                        32/32 PASS  (5.85s)
```

### (2) tsc scoped — apps/web only
- 0 NEW errors from Epic 17 T2+T3 wire files (`audit-log`, `activity`, `lib/audit`, `ActivityStream*` filter → empty)
- 28 pre-existing baseline errors in unrelated files (m12-account tests, m8-budget tests, m7-simulation, m11-close, lib/auth/social.ts, lib/m12-account-backup.ts) — preserved per cj-style discipline, not introduced by this wire

### (3) ruff scoped — N/A
- apps/web only changes (no Python files modified)
- Backend already verified FINAL CLEAN in `2ada2ec`

### (4) SDR drift gate
- vitest file count: +5 NEW collected, well within 5% tolerance
- pytest: N/A (no backend changes)
- tsc: 0 NEW errors from wire scope

### (5) commit_consistency gate
- CR 9-6 commit message discipline ✅ (this commit-msg file)
- A36 SDR 검증 4-step 자동 적용 ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS)

### (6) sprint-status structure PASS
- `epic-17-t2-t3-ui-wire: done` 신규 entry + A173~A182 action_items block 10 entries

### (7) D-EPIC-17-WIRE-DEFER-T2-T3-UI grep guard PASS
- honestly RESOLVED (UI scope T2+T3 files now wire DONE)

---

## §4 A173~A182 신규 결정 wire (cj-style 83번째 epic 연속 정직 회복 진입 시점에 결정)

- **A173** = 옵션 (a) Epic 17 T2+T3 UI frontend atomic wire 진입 결정 wire (cj-style Epic 17 4번째 진입점 = cj-style 83번째 epic 연속 정직 회복). Epic 17 bmad-dev-story atomic wire T1~T8 backend `2ada2ec` (cj-style 82번째) 진입 직후 next 옵션 (a) Epic 17 T2+T3 UI frontend atomic wire / (b) Phase 6 진입 / (c) D-EPIC-17-WIRE-DEFER-T2-T3-UI follow-up 결정 wire 진입 중 **사용자 권장 결정 = 옵션 (a) Epic 17 T2+T3 UI frontend atomic wire 진입**, rationale 5종: (1) cj-style discipline 회피 위험 방지 = 82번째 wire 진입 직후 honest next territory 진입 결정 / (2) D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED 진입 결정 wire 보존 (CR 11-3 83번째 epic 연속 정직 회복 검증) / (3) Epic 16 T4 admin UI follow-up sprint `ff5c3b5` (cj-style 71번째) 의 frontend 12 files atomic wire 정합 pattern 적용 / (4) backend 5 routes (`2ada2ec`) + frontend 5 components + i18n SSOT + RTL tests 정합 wire 진입 결정 / (5) backend + frontend + i18n + tests single sprint atomic wire 1 진입점 결정 wire 보존.
- **A174** = T2 §F21.2 audit log viewer UI verbatim satisfied (16 ACs §F21.2.1~§F21.2.16 verbatim 결정 wire) 결정.
- **A175** = T3 §F21.3 activity stream UI verbatim satisfied (8 ACs §F21.3.1~§F21.3.8 verbatim 결정 wire) 결정.
- **A176** = `apps/web/lib/server-api.ts` EXTENSION `fetchAuditLogServerSide` + `fetchActivityStreamServerSide` 2 NEW server-side helpers 결정 wire (5s AbortController timeout + X-Trace-Id header + Bearer token + fail-closed null on failure).
- **A177** = `apps/web/lib/audit/audit-log-client.ts` NEW 결정 wire (TS interface mirrors CR 12-5 D-PARITY-01 verbatim + 5 fetch wrappers + `AuditLogApiError` class with `code` + `details` + `trace_id` + `status` + `message_ko` fields).
- **A178** = `apps/web/messages/ko-KR.json` EXTENSION 48 NEW keys 결정 wire (`audit_log.*` 35 keys + `activity.*` 13 keys, P-015 verbatim SSOT only, CR 11-4 D-002 verbatim).
- **A179** = vitest RTL render discipline 결정 wire (3 page test files + 2 client/i18n test files = 32 NEW vitest cases PASS 결정 wire, Epic 16 T4 admin UI follow-up pattern verbatim 적용).
- **A180** = i18n SSOT drift detector 2 NEW test files 결정 wire (`audit-log-i18n-ssot.test.ts` + `activity-i18n-ssot.test.ts` = 6 NEW SSOT drift cases, CR 11-4 D-002 + P-015 verbatim).
- **A181** = D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED 결정 wire 보존 (UI scope T2+T3 files wire DONE 진입 + CR 11-3 honest-DEFER discipline 83번째 epic 연속 정직 회복 검증).
- **A182** = atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) + commit-msg file 신규 = `_bmad-output/implementation-artifacts/commit-msg-epic-17-t2-t3-ui-wire.txt` + handoff memory 신규 = `memory/handoff-2026-08-22-epic-17-t2-t3-ui-wire-done.md` + MEMORY.md hook index 신규 EXTENSION + sprint-status.yaml MODIFIED (`epic-17-t2-t3-ui-wire: backlog → done` + A173~A182 action_items block 10 entries) 결정 wire.

---

## §5 A19 cohesion pattern 9 surface EXTENSION PASS (cj-style 83번째)

**audit log viewer surface NEW 결정 wire 보존**:
- T2 §F21.2 audit log viewer UI territory 결정 wire
- T3 §F21.3 activity stream UI territory 결정 wire
- ko-KR.json SSOT EXTENSION 48 NEW keys 결정 wire
- lib/server-api.ts EXTENSION 2 NEW helpers 결정 wire
- lib/audit/audit-log-client.ts NEW 결정 wire
- 5 NEW vitest test files 결정 wire

---

## §6 CR lessons applied (cj-style 83번째 epic 연속 정직 회복 결정 wire 보존)

- **CR 0-2 RLS lesson** ✅ APPLIED — backend `audit_log_query.py` + `audit_log_routes.py` RLS 자동 적용 보존 (frontend does not bypass RLS; server-side helpers use authenticated `sb-access-token` cookie + RLS-aware DB queries).
- **CR 1-1 audit-first INSERT** ✅ APPLIED — backend `audit_log_exported` BEFORE CSV byte stream flush 보존 + frontend export button triggers backend endpoint (which performs audit-first INSERT).
- **CR 9-6 commit message discipline** ✅ APPLIED — `git commit -F <file>` 사용 결정 wire (PowerShell here-string 회피, D5 prevention + this commit-msg file).
- **CR 11-3 honest-DEFER discipline** ✅ APPLIED — 83번째 epic 연속 정직 회복, D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED 보존 (UI scope T2+T3 files wire DONE 진입 결정 wire).
- **CR 11-4 D-002 ko-KR.json SSOT only** ✅ APPLIED — 48 NEW i18n keys 모두 `ko-KR.json` SSOT only 결정 wire (no hardcoded Korean literals in components, Epic 16 D-EPIC-16-REVIEW-DEFER-6 verbatim pattern 적용).
- **CR 11-4 D-003 vitest RTL render discipline** ✅ APPLIED — `render(<Component />)` + `screen.getByRole` / `getByText` pattern 적용, no `dangerouslySetInnerHTML` shortcuts.
- **CR 11-4 D-004 owner/admin visibility** ✅ APPLIED — `/audit-log` page protected by backend owner/admin RBAC (`2ada2ec` §F21.1); `/activity` page allows all tenant members per PRD §F21.3 verbatim.
- **CR 11-4 D-005 unknown state reject** ✅ APPLIED — filter form rejects unknown action_class values via server-side `AuditLogQueryInvalidFilterError(400)` envelope (CR 12-5 D-14 verbatim).
- **P-015 ko-KR.json SSOT drift detector** ✅ APPLIED — 2 NEW SSOT drift detector tests (`audit-log-i18n-ssot.test.ts` + `activity-i18n-ssot.test.ts` = 6 NEW cases) verify 35 + 13 = 48 NEW keys present + non-empty + verbatim label invariants.
- **CR 12-5 D-14 typed exception envelope** ✅ APPLIED — `AuditLogApiError` class with `code` + `details` + `trace_id` + `status` + `message_ko` fields; `parseError` helper decodes backend envelope verbatim.
- **CR 12-5 D-PARITY-01 inversion** ✅ APPLIED — Python FastAPI `AuditLogQueryFilters` + `AuditLogEntry` + `AuditLogPage` TypedDict ↔ TypeScript Next.js `AuditLogQueryFilters` + `AuditLogEntry` + `AuditLogPage` interface parity 결정 wire (`audit-log-client.ts` test verifies shape parity).
- **CR 12-5 D-GATE-01 inversion** ✅ APPLIED — `AUDIT_LOG_VIEW` capability gate per-tenant on/off (backend enforces; frontend redirects on 403 via error envelope).
- **A19 cohesion pattern 9 surface EXTENSION PASS** ✅ — audit log viewer surface NEW 결정 wire 보존.
- **A36 SDR 검증 4-step 자동 적용** ✅ — commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire.
- **AD-14 stack pin** ✅ APPLIED — no new deps (React + Next.js + next-intl already in use).
- **AD-22 owner-only RBAC** ✅ APPLIED — `/audit-log` requires owner/admin role at backend; `/activity` allows all tenant members per PRD §F21.3 verbatim.
- **NFR4 PII minimization** ✅ PRESERVED — audit log viewer supports PII filter (actor_id) + masked display of payload; NFR4 PII minimization 정합 보존 결정 wire.

---

## §7 Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + Phase 5 + 1st release cycle 정합 보존 (cj-style 83번째 pre-flight 정합 sweep)

- ✅ Epic 17 bmad-dev-story atomic wire T1~T8 backend `2ada2ec` (cj-style 82번째) 보존.
- ✅ Epic 17 bmad-create-story spec entry `f4b2b58` (cj-style 81번째) 보존.
- ✅ Epic 17 PRD entry `40a9c41` (cj-style 80번째) 보존.
- ✅ Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) 보존.
- ✅ D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) 보존.
- ✅ Phase 5 close-out retro `b843565` (cj-style 76~77번째) 보존.
- ✅ Phase 5 atomic wire `f093f8c` (cj-style 75번째) 보존.
- ✅ Phase 5 spec entry (cj-style 74번째) 보존.
- ✅ Phase 5 PRD entry `93d852b` (cj-style 73번째) 보존.
- ✅ Epic 16 close-out retro `f1ead9a` (cj-style 72번째) 보존.
- ✅ Epic 16 T4 admin UI follow-up sprint `ff5c3b5` (cj-style 71번째) 보존 — **frontend 12 files atomic wire 정합 pattern 적용**.
- ✅ Epic 16 review follow-up sprint `963079c` (cj-style 70번째) 보존.
- ✅ Epic 16 atomic wire `e117e09` (cj-style 69번째) 보존.
- ✅ Epic 16 spec entry (cj-style 68번째) 보존.
- ✅ Epic 16 PRD entry `08bfca5` (cj-style 67번째) 보존.
- ✅ 1st release cycle cj-style 62~66번째 모두 wire DONE 진입.
- ✅ Epic 15 cycle cj-style 58~61번째 모두 wire DONE 진입 (D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존).
- ✅ Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입 (D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 진입 wire 결정 보존).
- ✅ Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입.
- ✅ Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존.
- ✅ Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존.
- ✅ Epic 12 2FA 게이트 `a63646c` 보존 (audit log viewer owner/admin RBAC 정합 결정 wire).
- ✅ Epic 11 close-out retro + Phase 2 close-out baseline 599 passed 정합 보존.
- ✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존.
- ✅ Epic 7~10 ABC/TDABC + AI 인사이트 territory 결정 wire 보존.

---

## §8 D-DEFER-* honestly 결정 (CR 11-3 83번째 epic 연속 정직 회복 결정 wire 보존)

- ✅ D-1-1-DEFER-1 Magic link + D-1-1-DEFER-2 Social login OAuth + D-1-1-DEFER-3 SSO enterprise SAML 모두 ✅ RESOLVED (Epic 15 wire `5f9e37f` 60번째 진입 시점에 모두 정직 회복 결정 wire 완료).
- ✅ D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED (71번째 T4 follow-up 진입 시점에 frontend 12 files wire DONE).
- ✅ D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) 모두 ✅ RESOLVED (78번째 진입 시점에 모두 정직 회복 결정 wire 완료).
- ✅ D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED (73~76번째 cj-style 결정 wire 완료).
- ✅ **D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED (cj-style 83번째 진입 시점에 UI scope T2+T3 files wire DONE 진입 결정 wire)**.

**partial wire 시도 0건 + single sprint atomic wire 1 진입점 결정** (cj-style 83번째 epic 연속 정직 회복 Epic 17 T2+T3 UI frontend atomic wire 22 files atomic single sprint 결정 wire).

---

## §9 결정 wire 일자 + next 옵션

결정 wire 일자: 2026-08-22 (KST).

**next 옵션 (cj-style 84번째 wire 진입 시점 결정 wire 보류)**:
- 옵션 (a) Epic 17 close-out retro 진입 (cj-style Epic 17 5번째 진입점 = cj-style 84번째 epic 연속 정직 회복, Epic 17 4-entry-point pattern 모두 wire DONE 진입 정합 보존, ALL 7 §F21.* ACs ✅ satisfied 검증).
- 옵션 (b) Phase 6 진입 (또 다른 territory).
- 옵션 (c) D-1-1-DEFER-* / D-EPIC-17-WIRE-DEFER-* carry-over follow-up 결정 wire 보류.
