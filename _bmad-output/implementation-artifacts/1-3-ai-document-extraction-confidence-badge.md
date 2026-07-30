---
baseline_commit: bd58c180234abae60a1bd4e8bcd38ea766263d9a
---
# Story 1.3: AI 문서 추출 + 신뢰도 배지

Status: ready-for-dev

<!-- Ultimate context engine analysis completed - comprehensive developer guide created -->

## Story

As a **사장님** (신규 가입 사업자),
I want **PDF·Excel 회사 문서를 업로드하면 AI가 회사 설정 후보를 추출하고 필드별 신뢰도와 검토 상태를 보여주는 것**,
so that **AI가 틀린 값을 확정값으로 바로 사용하지 않고, 낮은 신뢰도 항목을 직접 확인한 뒤 안전하게 온보딩을 완료할 수 있다**.

이 Story는 Epic 1의 마지막 Story이며 F0.3/E5를 구현한다. AI는 초안만 만들고, 확정은 사람만 한다.

## Acceptance Criteria

1. **Given** 나는 업종 선택을 완료했고 `/[locale]/(dashboard)/settings/wizard`에 있다
   **When** PDF 1장(회사 소개서/사업자등록증)을 업로드하고 추출이 완료된다
   **Then** 업로드 문서는 테넌트에 귀속된 `uploaded_documents` 레코드로 추적되고, 추출 결과 각 필드가 `input_drafts`에 `state='draft'`로 저장된다
   **And** 화면에는 추출 필드(최소 사업자등록번호, 회사명, 업종/주소가 문서에 존재하는 경우)가 원문 위치/근거와 함께 표시된다
   **And** AI 응답 원문, 프롬프트, 파일 전체 내용/개인정보를 구조화 로그나 Railway 디스크에 남기지 않는다

2. **Given** AI가 "사업자등록번호"를 추출했고 confidence가 `0.65`이다
   **When** 결과 검토 화면을 렌더링한다
   **Then** 해당 필드 우측에 빨간 배지 `⚠ 확인 필요`가 표시된다
   **And** 배지에는 사람이 확인해야 하는 이유와 신뢰도(가능하면 `65%`)가 접근 가능한 텍스트로 제공된다
   **And** 사용자가 값을 직접 편집하거나 `확인`해야만 해당 draft가 검토 완료 상태가 된다
   **And** 낮은 신뢰도 필드가 하나라도 미확정이면 [계산] 진입은 잠긴 상태로 유지된다

3. **Given** AI가 어떤 필드를 `confidence >= 0.70`으로 추출했다
   **When** 결과 검토 화면을 렌더링한다
   **Then** 해당 필드에 회색 배지 `✓ 자동 입력`이 표시된다
   **And** 사용자는 값을 수정하지 않고도 해당 필드를 자동 검토 완료로 통과시킬 수 있다
   **And** 단, 높은 신뢰도라는 이유만으로 `tenant_settings`나 확정 월 입력 테이블에 직접 쓰지 않는다

4. **Given** 낮은 신뢰도 필드 또는 모든 추출 필드를 검토 중이다
   **When** 사용자가 값을 수정하고 [확정]을 누른다
   **Then** 서버는 사용자 수정값을 검증한 뒤 해당 draft만 `state='reviewed'` 또는 프로젝트의 동일한 검토 상태로 갱신하고 actor/time/hash를 감사 추적한다
   **And** AI 값과 사용자 확정값을 구분해 원본 draft를 보존한다
   **And** `input_drafts`의 테넌트 범위를 벗어난 draft ID, 이미 확정/승격된 draft, 다른 사용자의 권한 없는 확정 요청은 거부된다

5. **Given** 추출 결과가 전 항목 `confidence < 0.50`이거나 AI가 필드를 추출하지 못했다
   **When** 결과 화면이 표시된다
   **Then** 사용자에게 "AI 추출 신뢰도가 낮습니다. 직접 입력해 주세요"라는 수동 입력 폴백 안내가 표시된다
   **And** 실패/폴백 안내는 재업로드 또는 직접 입력으로 진행할 수 있어야 하며, 실패가 빈 성공 결과로 표시되지 않는다
   **And** [계산] 버튼은 필요한 설정/추출 필드가 사람에 의해 확정될 때까지 활성화되지 않는다

6. **Given** PDF 또는 Excel을 업로드한다
   **When** 파일 검증을 수행한다
   **Then** 허용 MIME/type과 크기 제한을 서버에서 재검증하고, 악성/손상/지원하지 않는 파일은 구조화 오류 `{code, message_ko, details, trace_id}`로 거부한다
   **And** 같은 테넌트에서 문서와 draft를 조회할 때만 결과가 반환되며 다른 테넌트 데이터는 RLS/API 경계에서 보이지 않는다
   **And** AI 추출 응답 P95 목표는 30초 이하이며 장시간 요청에는 진행/실패 상태가 표시된다

## Tasks / Subtasks

- [ ] **Task 1 — Domain contract and persistence for document extraction** (AC: #1, #2, #3, #4, #5)
  - [ ] 1.1 — Define `InputDraft`, `ExtractionField`, `ExtractionEvidence`, `DraftState`, `ReviewStatus` contracts in the M0/M10 boundary using `snake_case` DB/Python and PascalCase TypeScript types.
  - [ ] 1.2 — Create the story-owned migration under `supabase/migrations/` (or the repository's established Alembic location) for `uploaded_documents`/`input_drafts` only if the existing baseline does not already provide them. Use UUID v7 IDs, tenant ownership, timestamps, `state='draft'` default, confidence constrained to `[0,1]`, and indexes for `(tenant_id, created_at)` and draft lookup.
  - [ ] 1.3 — Preserve raw AI output only in the authoritative Seoul Supabase storage/database boundary as needed for review; store a content/hash reference and normalized fields rather than opaque unbounded response JSON. Retain the original document/draft audit source; do not delete it on review.
  - [ ] 1.4 — Add RLS policies and tests for tenant isolation. Derive `tenant_id` from JWT; never accept it from form data or request body.

- [ ] **Task 2 — Extraction port and provider adapter** (AC: #1, #5, #6)
  - [ ] 2.1 — Add one inbound use-case/port for document extraction under `apps/api/modules/m0_onboarding/` or the shared M10 port boundary; the UI must call the API, not the provider directly.
  - [ ] 2.2 — Add the Claude Vision adapter under `apps/api/modules/m10_ai/` (or the project’s established AI adapter path). Keep the exact model snapshot in the M10 configuration constant; do not scatter model IDs. Use structured output/schema validation for fields, confidence, evidence, and warnings.
  - [ ] 2.3 — Normalize provider failures, timeout, malformed JSON, unsupported document, and no-field results into the project error envelope. Never log document bytes, extracted personal data, prompts, or provider response bodies.
  - [ ] 2.4 — Make provider calls transient in Railway Singapore. No payload logging, persistent disk writes, response caching, or tenant-data edge caching. Document the PIPA cross-border notice/consent requirement before pilot.
  - [ ] 2.5 — Enforce the 30-second product SLO with a request timeout and explicit `processing/failed/completed` status; do not add Celery/Kafka/Redis as persistent infrastructure.

- [ ] **Task 3 — Backend API and review/promotion boundary** (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 3.1 — Add authenticated owner-facing endpoints, for example:
    - `POST /api/v1/onboarding/documents` — multipart upload and extraction job creation.
    - `GET /api/v1/onboarding/documents/{document_id}` — tenant-scoped status and normalized fields.
    - `GET /api/v1/onboarding/drafts/{draft_id}` — one draft with confidence/evidence.
    - `POST /api/v1/onboarding/drafts/{draft_id}/review` — user edit/confirm; request includes expected version for optimistic concurrency.
  - [ ] 3.2 — Return a stable response shape containing `draft_id`, `field_name`, `ai_value`, `confirmed_value`, `confidence`, `badge`, `review_required`, `state`, `evidence`, and `warnings`; use `confidence < 0.70` as the single badge threshold.
  - [ ] 3.3 — A review/confirmation endpoint may update only the draft/review audit boundary. It must not write confirmed monthly inputs, products, accounts, or calculations directly.
  - [ ] 3.4 — When a later M2 promotion flow is implemented, only `InputPromoter.promote(tenant_id, period_key, draft_ids)` may promote drafts to canonical confirmed input. Promotion is idempotent, retains the draft with `state='promoted'`, records actor and draft hash, and is not reimplemented in M0/M10.
  - [ ] 3.5 — Keep settings aggregation under AD-23: if company identity fields belong in `tenant_settings.onboarding`, use the version-checked settings service and preserve unrelated JSONB namespaces; do not create a parallel settings table.
  - [ ] 3.6 — Enforce owner/member/viewer policy explicitly. Viewer and consultant proxy are read-only; member cannot change onboarding settings unless the established role policy says otherwise.

- [ ] **Task 4 — Frontend upload and confidence review UX** (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 4.1 — Add an upload/review step to the existing settings wizard without breaking Story 1.1 industry menu or Story 1.2 completion hook/button.
  - [ ] 4.2 — Create components in the established Next.js tree, e.g. `apps/web/components/settings/wizard/DocumentExtractionStep.tsx`, `ExtractionFieldRow.tsx`, `ConfidenceBadge.tsx`, and `apps/web/hooks/useDocumentExtraction.ts`.
  - [ ] 4.3 — Render `⚠ 확인 필요` in red for `<70%`, `✓ 자동 입력` in gray for `>=70%`; do not rely on color alone—include text/icon and accessible labels. Show confidence percent, editable value, evidence/source location when available, and a per-field confirm action.
  - [ ] 4.4 — Show global state: processing progress, completed review count, unresolved low-confidence count, all-fields-low-confidence manual fallback, retry/re-upload, and structured Korean errors.
  - [ ] 4.5 — Feed unresolved review state into the Story 1.2 completion calculation so [계산] remains disabled until required extracted fields are user-confirmed. Preserve completion semantics for industries where no document is required.
  - [ ] 4.6 — Avoid client-side direct provider calls and avoid embedding tenant data in static/edge cacheable payloads. Use the authenticated API client and React Query conventions from Story 1.2.

- [ ] **Task 5 — Tests and security regression coverage** (AC: all)
  - [ ] 5.1 — Domain tests for threshold boundaries: `0.00`, `0.49`, `0.50`, `0.69`, `0.70`, `1.00`; missing confidence is review-required, not auto-approved.
  - [ ] 5.2 — Backend API tests for PDF/Excel accepted types, invalid MIME/oversized/corrupt files, timeout/provider error, malformed provider output, no-field fallback, status transitions, review validation, and optimistic concurrency.
  - [ ] 5.3 — Tenant and role isolation tests: tenant A cannot read/review tenant B drafts; viewer/consultant proxy cannot mutate; request-body `tenant_id` is ignored/rejected.
  - [ ] 5.4 — Non-authoritative boundary tests: extraction/review cannot insert/update confirmed input tables or invoke `/api/v1/calc`; draft remains source-of-truth until AD-17 promotion.
  - [ ] 5.5 — Frontend Vitest/RTL tests for red/gray badge exact labels, keyboard/focus accessible review, disabled calculation while unresolved, processing/error/fallback states, and retry.
  - [ ] 5.6 — Playwright E2E: upload representative PDF and Excel fixtures, verify field review, edit/confirm low-confidence value, confirm no-low-confidence completion, and verify a cross-tenant access attempt fails.
  - [ ] 5.7 — Add redaction/logging tests or static checks proving document bytes, personal data, provider prompts/responses, and tenant payloads are not logged.

- [ ] **Task 6 — Documentation and operational safeguards** (AC: #1, #5, #6)
  - [ ] 6.1 — Add `docs/ai-document-extraction.md` covering user flow, field schema, confidence threshold, review rules, manual fallback, state transitions, retention, and “AI는 초안, 확정은 사람” notice.
  - [ ] 6.2 — Document exact M10 provider model/config location, timeout, supported file types/limits, no-payload-logging rule, and how to rotate credentials.
  - [ ] 6.3 — Document PIPA cross-border processing notice/consent and processor-contract review as a pre-pilot operational gate.
  - [ ] 6.4 — Update onboarding/settings docs and Korean messages; explicitly state compliance/AI extraction is assistive and not accounting/legal confirmation.

## Dev Notes

### Story foundation and cross-story continuity

- Epic 1 goal is to complete onboarding in 10 minutes and block calculation until required settings are complete. Story 1.1 owns industry selection/menu toggling; Story 1.2 owns fiscal-year/currency/language/allocation completion and the disabled [계산] button. This story extends, rather than replaces, that completion source.
- Existing Story 1.2 establishes the intended paths and conventions: `apps/api/modules/m0_onboarding/handlers.py`, `schemas.py`, `services/settings_service.py`; `apps/web/app/[locale]/(dashboard)/settings/wizard/page.tsx`; wizard step components; `apps/web/hooks/useSettingsCompletion.ts`; `apps/web/components/calc/CalcButton.tsx`; and `tenant_settings.onboarding` as the one settings aggregate.
- Story 1.2 explicitly says AI extraction is separate and AI cannot auto-set user-driven fields. Preserve that boundary: AI may propose/extract, but human review/promotion is the only route to confirmed data.
- Previous story files are context specifications, not evidence that implementation files already exist. Inspect the actual tree before choosing UPDATE vs NEW paths.
- No implementation commit exists yet beyond the initial repository commit; do not infer unrecorded runtime patterns from git history.

### Architecture compliance guardrails

- **AD-3**: every read/write is tenant-scoped via Supabase RLS and JWT-derived identity. Never trust `tenant_id` in multipart metadata, query, or JSON.
- **AD-7**: AI output is non-authoritative and lives only in `input_drafts`; it cannot contaminate confirmed inputs or calculation. AI commentary, if any, is labeled `ai_reference`; deterministic text is `auto_analysis`.
- **AD-11**: keep dependency direction `ui → api → services → ports → engine`; provider SDK belongs in an adapter, not UI/domain.
- **AD-15**: DB/Python `snake_case`, routes `kebab-case`, React/TS PascalCase, UTC timestamps, Korean API errors `{code, message_ko, details, trace_id}`.
- **AD-17**: one future promotion port owned by M2. Do not invent a second promotion API in this story. Promotion must retain the source draft, be idempotent on `(tenant_id, period_key, source_draft_id)`, and audit actor/hash.
- **AD-23**: exactly one `tenant_settings` aggregate with namespaces `onboarding`, `baseline`, `abc`, `ai`; version-check writes and preserve sibling JSONB keys.
- **AD-9**: Supabase Seoul is storage; Railway Singapore may process tenant payloads transiently only. No Railway disk, payload logs, response cache, or Vercel tenant-data cache. PIPA review is a pre-pilot requirement.
- **AD-10**: enforce roles from JWT (`owner`, `member`, `viewer`, `consultant_proxy`); read-only proxy must remain read-only.
- **AD-25** is not a reason to add cache here; extraction results must not be cached as tenant payloads. If shared AI cache infrastructure is later added, use the architecture-defined invalidation rules.

### Data/state contract

Recommended normalized shape (adapt to existing schema, do not duplicate existing entities):

```json
{
  "draft_id": "uuid-v7",
  "tenant_id": "derived-from-jwt",
  "document_id": "uuid-v7",
  "field_name": "business_registration_number",
  "ai_value": "123-45-67890",
  "confirmed_value": null,
  "confidence": 0.65,
  "badge": "review_required",
  "review_required": true,
  "evidence": {"page": 1, "text": "...redacted/limited..."},
  "state": "draft",
  "reviewed_by": null,
  "reviewed_at": null,
  "draft_hash": "sha256:...",
  "version": 1
}
```

- `confidence` is normalized to `[0,1]`; values outside that range or non-numeric provider output are invalid and must fail closed.
- Badge mapping is deterministic: `<0.70` → `review_required` / red `⚠ 확인 필요`; `>=0.70` → `auto_input` / gray `✓ 자동 입력`. `null` → review required.
- Do not expose unbounded source snippets or full documents to logs; evidence shown in UI must be minimized and escaped.
- Suggested state machine: `draft → reviewed → promoted`; provider/job status separately `queued|processing|completed|failed`. Avoid mutating a promoted draft back to draft.
- The Epic/ERD also contains `ai_extractions` with `pending_review→approved`; reconcile this legacy naming with `input_drafts`/AD-7 before coding. Do not create both as competing sources of truth. If `ai_extractions` already exists, map it as an adapter/view or document the migration decision.

### Provider and latest-technology guardrails

- PRD selects Claude API with Vision, but the architecture intentionally leaves the exact model snapshot to M10 configuration. Pin the chosen snapshot in one config constant and record the date/version in docs; never hard-code it in handlers/components.
- Use the current official Anthropic SDK/API pattern available in the repository at implementation time. Because this story is a planning artifact, the dev must verify the provider’s current structured-output/document-input API and SDK version before implementation rather than copying a stale call signature.
- Keep the provider behind a port so tests use a fake adapter. Require schema-validated output and handle refusal, empty extraction, timeout, malformed output, and provider HTTP errors.
- Keep the provider behind a port so tests use a fake adapter. Require schema-validated output and handle refusal, empty extraction, timeout, malformed output, and provider HTTP errors.
- Use file type detection from content where possible, not only client MIME; enforce max size and request timeout server-side.
- SLO: AI extraction P95 ≤ 30 seconds (PRD §14). Provide asynchronous status if the provider call exceeds the request budget; do not silently retry duplicate extraction without an idempotency key.

### Source tree requirements

Expected changes, subject to actual repository verification:

```text
apps/api/
├── modules/
│   ├── m0_onboarding/
│   │   ├── handlers.py                         # UPDATE — upload/status/review routes, if Story 1.1/1.2 created it
│   │   ├── schemas.py                           # UPDATE — document/draft DTOs
│   │   └── services/settings_service.py         # UPDATE only if completion needs reviewed-draft gate
│   └── m10_ai/
│       ├── __init__.py                          # NEW
│       ├── config.py                             # NEW — model/timeout/file policy constants
│       ├── ports.py                              # NEW — provider/extraction contracts
│       ├── adapters/claude_vision.py             # NEW
│       ├── service.py                            # NEW — orchestration, validation, redaction
│       └── schemas.py                             # NEW/UPDATE
├── core/                                         # UPDATE only for existing upload/error/security helpers
└── main.py                                       # UPDATE — router wiring

apps/web/
├── app/[locale]/(dashboard)/settings/wizard/
│   └── page.tsx                                  # UPDATE — add extraction step
├── components/settings/wizard/
│   ├── DocumentExtractionStep.tsx                # NEW
│   ├── ExtractionFieldRow.tsx                   # NEW
│   └── ConfidenceBadge.tsx                       # NEW
├── hooks/useDocumentExtraction.ts                # NEW
├── lib/api-client.ts                             # UPDATE — multipart/status/review calls if existing
└── messages/ko-KR.json                            # UPDATE — Korean labels/errors

supabase/
├── migrations/                                    # NEW/UPDATE — only missing uploaded_documents/input_drafts
└── policies/                                      # UPDATE — RLS if not created with migration

tests/
├── api/test_document_extraction.py               # NEW
├── api/test_document_extraction_isolation.py     # NEW
├── services/test_extraction_contract.py          # NEW
├── integration/test_draft_promotion_boundary.py  # NEW
└── web/
    ├── __tests__/ConfidenceBadge.test.tsx         # NEW
    └── e2e/document-extraction.spec.ts            # NEW

docs/
└── ai-document-extraction.md                     # NEW
```

### Testing standards

- Backend: pytest 9.1.1, FastAPI test client, local Supabase/PostgreSQL fixtures; use fake provider adapter for deterministic unit tests.
- Frontend: Vitest + React Testing Library; Playwright for the upload/review journey. Use accessibility queries and keyboard/focus checks.
- Security: RLS isolation, role authorization, body tenant-id rejection/ignore, upload validation, logging redaction, and no writes to canonical input/calculation paths are mandatory regression tests.
- Contract: test exact 70% boundary and missing confidence. Test both PDF and Excel fixtures, not just file extensions.
- Performance: add a provider timeout test and, where infrastructure permits, a P95 extraction measurement/benchmark; report if unavailable rather than claiming it.
- The app must preserve Story 1.2 tests and completion behavior; run the full existing suite plus focused extraction tests.

### UX and localization lock

- Existing memory locks UX v1.0 to Dark MVP, WCAG AA, Professional tone, and ko-KR; respect these decisions even though the PRD’s older visual section mentions clear blue/white. Do not silently change global theme.
- Every user-visible string is Korean. Use text/icon plus color for badges. Red badge must have sufficient contrast, focus-visible controls, keyboard operation, and screen-reader label.
- Clearly state "AI는 초안이며, 확정 전 반드시 확인해야 합니다" and that this is assistive, not legal/accounting confirmation.

### Known ambiguities to resolve during implementation

- **Storage naming**: ERD names `ai_extractions` while architecture/epics mandate `input_drafts`. Adopt one canonical source, preferably `input_drafts` under AD-7, and document compatibility mapping.
- **Scope of company fields**: Story AC explicitly names business registration number but does not enumerate every required field. Keep schema extensible and make required-for-calculation mapping explicit rather than hard-coding all extracted fields as mandatory.
- **Auto-approved fields**: AC allows `>=70%` to pass without manual edit, while global PRD says “확정은 사람”. Treat `>=70%` as review-complete for the badge/calculation gate only, but do not promote to authoritative input without the future AD-17/M2 human promotion path.
- **M0 vs M10 ownership**: M0 owns onboarding surface; M10 owns provider/AI adapter. Keep one extraction port and avoid module-to-module duplicate endpoints.
- **Migration location**: Architecture seed says `supabase/migrations`; previous story specs mention Alembic. Inspect actual bootstrap and follow the repository’s real migration owner; do not generate duplicate migrations in both locations.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Epic 1` and `#Story 1.3`] — Epic objective, F0.3, AC, 70% threshold, `input_drafts` boundary.
- [Source: `_bmad-output/planning-artifacts/prd.md#UJ-4` and `#12. AI 기능 3종`] — Claude Vision onboarding journey, human confirmation, <50% fallback, AI feature scope.
- [Source: `_bmad-output/planning-artifacts/prd.md#13.2 기술 스택`] — Next.js/FastAPI/Supabase/Claude stack.
- [Source: `_bmad-output/planning-artifacts/prd.md#14. 비기능 요구·제약`] — AI extraction P95 ≤30s.
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-3`] — RLS and JWT tenant derivation.
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-7`] — AI non-authoritative, `input_drafts` only.
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-9`] — Seoul storage/Singapore transient processing/no payload logs.
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-17`] — sole future draft promotion port and idempotency/audit requirements.
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-23`] — singleton versioned tenant settings aggregate.
- [Source: `비즈업_통합ERD_v2.0.md#8. 도메인 H. 검증·AI·가져오기`] — existing `ai_extractions` pending_review→approved naming and source field conventions.
- [Source: `_bmad-output/implementation-artifacts/1-1-industry-selector-menu-auto-toggle.md`] — prior story architecture, routes, role, and settings patterns.
- [Source: `_bmad-output/implementation-artifacts/1-2-settings-wizard-calculation-block.md`] — prior story wizard/completion/CalcButton contract and explicitly separate AI boundary.
- [Source: `_bmad-output/implementation-artifacts/0-3-stack-pin-lockfile-build-pipeline.md`] — stack pin and M10 config location.
- [Source: `_bmad-output/implementation-artifacts/0-4-cross-language-conventions-monetary-types-foundation.md`] — naming/money/lint conventions.
- [Source: `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\ux-locked-decisions.md`] — Dark MVP/WCAG AA/Professional/ko-KR lock.

### Project Structure Notes

- This repository is currently a greenfield planning repository: the tracked commit contains planning artifacts and BMad configuration, while the implementation-artifacts directory contains story context files. The developer must verify whether implementation source directories have been created by earlier dev work before applying UPDATE paths.
- Story 1.2’s proposed `apps/api` and `apps/web` paths are the continuity contract, but Story 1.3 must not assume those files exist merely because they appear in a prior story specification.
- The ERD’s `ai_extractions` is a naming variance against architecture’s `input_drafts`; resolve through a documented migration/adapter, never by silently maintaining two independent draft stores.
- No existing architecture.md or UX contract file was found at the standard single-file paths; the authoritative architecture is the dated `architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md`, and UX constraints come from persistent memory.
- The initial working tree already contains user modifications to planning artifacts and untracked implementation artifacts. Do not overwrite unrelated changes.

## Developer Context Checklist

Before coding, the dev agent must:

- [ ] Read the actual current source tree and previous story files.
- [ ] Confirm migration owner and whether `uploaded_documents`, `ai_extractions`, or `input_drafts` already exist.
- [ ] Resolve the ERD/architecture naming variance in a documented decision.
- [ ] Verify current Anthropic SDK/document/structured-output API and model snapshot from official docs.
- [ ] Confirm file limits, retention, PIPA consent copy, and required-for-calc field mapping with the product owner if not already configured.
- [ ] Run focused tests and the full existing test/lint/build suite; report failures truthfully.

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Story context analysis completed on 2026-07-25.
- Story marked `ready-for-dev` for Epic 1 completion.

### File List

<!-- Dev agent should populate this section on completion with files created/modified and key decisions -->
