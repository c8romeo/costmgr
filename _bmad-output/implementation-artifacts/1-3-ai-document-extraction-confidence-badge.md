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
  - [ ] 1.2 — Create the story-owned Alembic migration **`apps/api/alembic/versions/0005_ai_documents_input_drafts.py`** for `uploaded_documents` and `input_drafts`. Use **business UUID v7 for entity IDs (`document_id`, `draft_id`, `field_id`)** and **`tenant_id` UUID v4** (per AD-15 variance — `docs/conventions.md §3`, `docs/architecture-decisions/AD-15-tenant-id-variance.md`). Schema: `tenant_id UUID NOT NULL`, `document_id UUID NOT NULL` FK to uploaded_documents, `field_name TEXT NOT NULL`, `ai_value JSONB` (typed: string/number/decimal/date), `confirmed_value JSONB NULL`, `confidence NUMERIC(4,3) CHECK (confidence >= 0 AND confidence <= 1)` NULL allowed, `state TEXT NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','reviewed','superseded'))`, `evidence JSONB NOT NULL DEFAULT '{}'::jsonb`, `draft_hash BYTEA` (sha256), `version INTEGER NOT NULL DEFAULT 1`, `requested_by UUID`, `requested_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `reviewed_by UUID NULL`, `reviewed_at TIMESTAMPTZ NULL`, `uploaded_document_id UUID` FK, `tenant_id` RLS-friendly, INDEXES `(tenant_id, created_at)` and `(tenant_id, document_id, field_name)` and `(tenant_id, state)`. **Companion policy**: `supabase/policies/0005_ai_documents_input_drafts.sql` adds RLS for both tables (no production cross-tenant read). **`input_drafts` is the canonical name** (architecture AD-7 supersedes ERD §8 `ai_extractions`; see new AD `docs/architecture-decisions/AD-7-ai-extraction-table-naming.md` per Task 6.5).
  - [ ] 1.3 — Preserve raw AI output only in the authoritative Seoul Supabase storage/database boundary as needed for review. Store a content hash + Supabase Storage path reference (NOT unbounded response JSON). **Evidence policy**: `evidence.text` max **200 chars**, redacted via `apps/api/core/logging.py redact_processor` patterns (email regex `[^@\s]+@[^@\s]+`, KR phone `0\d{1,2}-\d{3,4}-\d{4}`, business_no `\d{3}-\d{2}-\d{5}`), HTML-escaped before render. Original document/draft audit source retained; never deleted on review. **Re-upload policy**: same `tenant_id` + same `sha256(document_bytes)` returns **409 `DOCUMENT_ALREADY_EXISTS`** with the existing `document_id`; do not create a duplicate. Retention: 90 days post `reviewed_at`, then a daily cron (`apps/api/jobs/document_retention.py`) soft-deletes (`deleted_at TIMESTAMPTZ`) the Storage object and marks drafts `state='superseded'`; raw bytes PII is purged in line with PIPA cross-border review.
  - [ ] 1.4 — Add RLS policies and tests for tenant isolation. Derive `tenant_id` from JWT; never accept it from form data or request body.

- [ ] **Task 2 — Extraction port and provider adapter** (AC: #1, #5, #6)
  - [ ] 2.1 — Add one inbound use-case/port for document extraction under `apps/api/modules/m0_onboarding/` or the shared M10 port boundary; the UI must call the API, not the provider directly.
  - [ ] 2.2 — Add the Claude Vision adapter under **`apps/api/modules/m10_ai/adapters/claude_vision.py`**. **Stack-pin add (this story, `[STACK BUMP]` tag)**: `anthropic` (Python SDK, exact pin in `apps/api/pyproject.toml` workspace member — pin the latest stable on the implementation date per claude-api skill guidance), `pdfplumber` (PDF text+tables extraction), `pillow` (image rendering for non-PDF uploads), `python-magic` (server-side MIME validation), and `python-multipart` (FastAPI upload — verify covered by `fastapi[standard]` extras before adding). Add via `uv add --package apps.api anthropic==<exact> pdfplumber==<exact> pillow==<exact> python-magic==<exact>` per the Story 0.4 lesson. Pin the **model snapshot** in **`apps/api/modules/m10_ai/config.py`** (single source) — do NOT scatter model IDs.

  **Provider surface (locked 2026-07-31 by user decision)**:
  - **Model**: `claude-opus-5` (claude-api skill default, Vision-capable, $5/$25 per 1M tokens). Config constant: `DOCUMENT_EXTRACTION_MODEL = "claude-opus-5"`.
  - **Region/base URL**: first-party US (`api.anthropic.com`). AD-9 "Singapore transient" applies to non-model-call code paths; the model call is documented in `docs/ai-document-extraction.md` §"Provider region" as an explicit AD-9 variance — PIPA cross-border review must include this surface.
  - **Transport**: **base64 inline** (`source={"type":"base64","media_type":...,"data":...}`), NOT Files API. Reasoning: PIPA simple (no persistent tenant bytes on Anthropic storage), 10 MB limit already enforced locally, single-region US egress is already covered by cross-border notice.
  - **Structured output**: `client.messages.create(model=..., messages=[...], output_config={"format":{"type":"json_schema","schema":ExtractionResult.model_json_schema()}}, ...)`. Use `anthropic.Anthropic().messages.create(timeout=PROVIDER_TIMEOUT_S)`.
  - **Supported MIME**: `application/pdf`, `image/jpeg`, `image/png`, `image/gif`, `image/webp`. **Excel is OUT of scope for MVP** (decision 2026-07-31 — Claude Vision does not natively support `.xlsx`; defer to a future story if needed). `ALLOWED_MIME = {"application/pdf", "image/jpeg", "image/png", "image/gif", "image/webp"}`.
  - **Determinism**: `temperature=0`, `top_p=1.0` (or lowest), `max_tokens=8192`. Required for `draft_hash = sha256(canonical_json(...))` reproducibility.
  - **Streaming**: NOT used. Single blocking call inside `asyncio.to_thread(...)` so the FastAPI event loop is not blocked.

  **Confidence semantics (locked 2026-07-31 by user decision)**: the `confidence` returned by the model is **self-rated heuristic, NOT a calibrated probability**. The prompt explicitly asks Claude to self-rate per-field confidence 0.00–1.00. The 0.70 threshold is therefore a **heuristic cutoff**, not a statistical guarantee. Document this caveat in `docs/ai-document-extraction.md` §"Confidence semantics" so users understand "✓ 자동 입력" means "model rated itself ≥70% confident", not "verified by an independent oracle".
  - [ ] 2.3 — Normalize provider failures, timeout, malformed JSON, unsupported document, and no-field results into the project error envelope `{code, message_ko, details, trace_id}` (AD-15 §4). Never log document bytes, extracted personal data, prompts, or provider response bodies. **Extend `apps/api/core/logging.py redact_processor`** to cover the keys `value`, `ai_value`, `confirmed_value`, `evidence.text`, `extracted_text`, `prompt`, `provider_response`, `document_bytes`. Add a static test (`tests/architecture/test_logging_redaction.py`) asserting the processor scrubs those keys before any structlog event hits stdout.
  - [ ] 2.4 — Make provider calls transient in Railway Singapore. No payload logging, persistent disk writes, response caching, or tenant-data edge caching. **PIPA cross-border gate**: add `apps/api/core/pipa_gate.py::require_pipa_review()` dependency and attach to all four M10 routes. The dependency reads `settings.PIPA_REVIEW_COMPLETED` (env flag, default `False`); if `False`, return `503 PIPA_REVIEW_PENDING` with `message_ko: "PIPA 국외이전 검토가 완료되지 않아 AI 추출 기능이 비활성화되어 있습니다."`. CI workflow `apps/api/.github/ci.yml` adds a job `pipa-gate-check` that asserts the flag is `True` for any production deployment (the operator flips it after the PIPA processor-contract review is signed). Document the PIPA cross-border notice/consent requirement before pilot.
  - [ ] 2.5 — Enforce the 30-second product SLO with **`apps/api/modules/m10_ai/config.py::PROVIDER_TIMEOUT_S = 28`** and explicit job status `queued|processing|completed|failed` (separate from draft `state='draft|reviewed|superseded'`). Use `anthropic.Anthropic().messages.create(timeout=PROVIDER_TIMEOUT_S)`; on timeout, transition job to `failed` with `code=AI_PROVIDER_TIMEOUT` and `details={"elapsed_seconds": <int>}`. Do not add Celery/Kafka/Redis as persistent infrastructure. **Upload limits** (`apps/api/modules/m10_ai/config.py`): `MAX_UPLOAD_BYTES = 10 * 1024 * 1024` (10 MB), `ALLOWED_MIME = {"application/pdf", "image/jpeg", "image/png", "image/gif", "image/webp"}` (Excel removed per 2026-07-31 decision — Claude Vision does not natively support `.xlsx`), `MAX_PDF_PAGES = 20`, `MAX_IMAGE_PIXELS = 4096 * 4096`. Reject above limits with `422 UPLOAD_LIMIT_EXCEEDED`. Enforce a per-tenant daily quota (50 uploads/day) via a Redis-free in-memory counter persisted to `tenant_settings.onboarding.ai.daily_upload_count` JSONB (no Redis).

- [ ] **Task 3 — Backend API and review/promotion boundary** (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 3.1 — Add authenticated owner-facing endpoints under kebab-case (AD-15) prefix `onboarding/ai-documents`:
    - `POST /api/v1/onboarding/ai-documents` — multipart upload. **Accepts `Idempotency-Key: <uuid>` header (recommended)**: same key + same body returns the existing `document_id` (200) instead of creating duplicates. Missing key → generate and return in `X-Idempotency-Key` response header. Returns `{ document_id, status: "queued", upload_url }`.
    - `GET /api/v1/onboarding/ai-documents/{document_id}` — tenant-scoped status; returns `{ document_id, status: "queued|processing|completed|failed", error?, drafts: [{draft_id, field_name, confidence, state, badge}] }`.
    - `GET /api/v1/onboarding/ai-drafts/{draft_id}` — one draft with confidence/evidence.
    - `POST /api/v1/onboarding/ai-drafts/{draft_id}/review` — user edit/confirm; **request includes `If-Match: <draft_hash_b64>`** (Story 1.2 deferred F-33 lifted for this route). Mismatch returns `409 DRAFT_VERSION_CONFLICT` with `message_ko: "다른 사용자가 이미 이 초안을 수정했습니다. 새로고침 후 다시 시도해 주세요."`, `details: {"current_version": <int>, "your_version": <int>}`. Partial confirm returns `{ draft_id, confirmed_fields: ["business_registration_number"], remaining_review_count: 3, settings_version: <int> }`.
  - [ ] 3.2 — Return a stable response shape derived from **`apps/api/core/confidence.py::REVIEW_THRESHOLD`**: `{ draft_id, field_name, ai_value, confirmed_value, confidence, badge, state, evidence, warnings, version }`. **`review_required` is NOT a separate field** — the UI derives it as `confidence IS NULL OR confidence < REVIEW_THRESHOLD`. The `badge` string is also derived (`confidence IS NULL OR confidence < REVIEW_THRESHOLD → "review_required" / red ⚠ 확인 필요`; otherwise → `"auto_input"` / gray ✓ 자동 입력). Single source of truth avoids the Story 1.2 F-7 anti-pattern of duplicating the same derived state across multiple fields.
  - [ ] 3.3 — A review/confirmation endpoint may update only the draft/review audit boundary. It must not write confirmed monthly inputs, products, accounts, or calculations directly.
  - [ ] 3.4 — **Resolution of Epic Story 1.3 AC line 657 vs AD-7/AD-17 conflict (Option C — `company_subblock`)**: confirmed values from reviewed drafts flow into **`tenant_settings.onboarding.company_subblock`** (a new schema-validated JSONB subkey inside the existing `onboarding` namespace — AD-23 4-namespace rule preserved). Concretely:
    - Extend `packages/services/m0_onboarding/settings_completion.py::compute_completion()` (Story 1.2 pure function) with a third parameter `pending_extractions: list[DraftSummary]`; the function returns `missing += [f"AI 추출 미확정: {d.field_name}" for d in pending_extractions if d.review_required]`. Mirror in TS (`apps/web/lib/menu-config.ts` or new sibling `apps/web/lib/completion.ts`) and add `tests/integration/test_completion_consistency.py` parametrized cases.
    - M10 review endpoint, on user confirm, calls **`SettingsService.update_onboarding_field(tenant_id, "company_subblock", company_subblock_payload, actor_id)`** (the Story 1.2 2-transaction pattern: audit-first via `emit_audit` then `with_service_role` SELECT FOR UPDATE → `jsonb_set` → commit). Draft retains `state='reviewed'`; an empty (no fields) `state='promoted'` row is **NOT** created here — AD-17's `InputPromoter.promote(tenant_id, period_key, draft_ids)` is reserved exclusively for monthly-input promotion and is **not reimplemented** by M0/M10. The relationship is: AI company-identity fields (Epic 1 onboarding) live in `company_subblock`; monthly input fields (Epic 3) flow through AD-17 promotion. These are distinct paths, distinct namespaces.
  - [ ] 3.5 — Keep settings aggregation under AD-23: company-identity fields are written into **`tenant_settings.onboarding.company_subblock`**, NOT a parallel settings table and NOT a 5th top-level namespace. JSONB schema is added to `apps/api/core/jsonb_schemas.py::validate_onboarding_schema()` (Story 1.2 helper) and to `docs/onboarding-schema.md`. The four AD-23 namespaces (`onboarding` / `baseline` / `abc` / `ai`) remain the only top-level keys. `tenant_settings.ai` keeps AD-23's reserved meaning (AI defaults / cache policy) and is NOT used for draft persistence.
  - [ ] 3.6 — Enforce **owner-only** for `POST /api/v1/onboarding/ai-documents` and `POST /api/v1/onboarding/ai-drafts/{id}/review` (matches Story 1.2 anti-pattern line 335 + AD-10 hard rule — "unless established policy says otherwise" hedge removed). `member`, `viewer`, `consultant_proxy` receive `403 ROLE_NOT_ALLOWED`. `GET` endpoints are open to all four roles (read-only). Wrap the routes with `dependencies=[Depends(require_capability(Capability.AI_EXTRACT))]` (per `apps/api/core/capability.py`, deferred-work F-6 wiring) — AI_EXTRACT is granted to every Industry per ARCHITECTURE-SPINE capability map, so this is a defense-in-depth gate, not a tenant-kind filter.

- [ ] **Task 4 — Frontend upload and confidence review UX** (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 4.1 — Add an upload/review step to the existing settings wizard without breaking Story 1.1 industry menu or Story 1.2 completion hook/button. The new step is inserted **after** the AllocationCriteriaStep in `apps/web/app/[locale]/(dashboard)/settings/wizard/page.tsx`. Follow the **F-20 server-side initial-fetch pattern** (`apps/web/lib/server-api.ts` from Story 1.2 review patches) to avoid the render-race window where a user could click Save before the first poll. Lift `accessToken` plumbing via `MenuContext` exactly as Story 1.1/1.2 did; defer the F-32 cookie-hardening fix to a hardening sprint (consistent with Story 1.2 deferred).
  - [ ] 4.2 — Create components in the established Next.js tree, e.g. `apps/web/components/settings/wizard/DocumentExtractionStep.tsx`, `ExtractionFieldRow.tsx`, `ConfidenceBadge.tsx`, and `apps/web/hooks/useDocumentExtraction.ts`. The hook must mirror the Story 1.2 `useSettingsCompletion` hardening: `cancelledRef`, `statusRef`, `window focus` + `document visibilitychange` listeners, `isLoading=true` only on first fetch, **exponential backoff polling** (1s, 2s, 4s, 8s, cap 10s) while job status is non-terminal, error path clears cached status. No `STALE_MS` gate.
  - [ ] 4.3 — Render `⚠ 확인 필요` in red for `<70%`, `✓ 자동 입력` in gray for `>=70%`; do not rely on color alone—include text/icon and accessible labels. Show confidence percent, editable value, evidence/source location when available, and a per-field confirm action.
  - [ ] 4.4 — Show global state: processing progress, completed review count, unresolved low-confidence count, all-fields-low-confidence manual fallback, retry/re-upload, and structured Korean errors.
  - [ ] 4.5 — Feed unresolved review state into the Story 1.2 completion calculation so [계산] remains disabled until required extracted fields are user-confirmed. Preserve completion semantics for industries where no document is required.
  - [ ] 4.6 — Avoid client-side direct provider calls and avoid embedding tenant data in static/edge cacheable payloads. Use the authenticated API client and React Query conventions from Story 1.2.

- [ ] **Task 5 — Tests and security regression coverage** (AC: all)
  - [ ] 5.1 — Domain tests for threshold boundaries: `0.00`, `0.49`, `0.50`, `0.69`, `0.70`, `1.00`; missing confidence is review-required, not auto-approved.
  - [ ] 5.2 — Backend API tests for PDF/Excel accepted types, invalid MIME/oversized/corrupt files, timeout/provider error, malformed provider output, no-field fallback, status transitions, review validation, and optimistic concurrency.
  - [ ] 5.3 — Tenant and role isolation tests: tenant A cannot read/review tenant B drafts; viewer/consultant proxy cannot mutate; request-body `tenant_id` is ignored/rejected.
  - [ ] 5.4 — Non-authoritative boundary tests: extraction/review cannot insert/update confirmed input tables or invoke `/api/v1/calc`; draft remains source-of-truth until AD-17 promotion.
  - [ ] 5.5 — Frontend Vitest/RTL tests for red/gray badge exact labels, keyboard/focus accessible review, disabled calculation while unresolved, processing/error/fallback states, and retry. **Defer to Story 0.5** (test framework wire-up) — same deferral phrasing as Story 1.2 T7.3 + `apps/web/__tests__/IndustrySelector.test.tsx` header. Files ship as inert scaffolding; CI picks them up after Story 0.5 lands. No new test stack introduced here.
  - [ ] 5.6 — Playwright E2E: upload representative PDF and Excel fixtures, verify field review, edit/confirm low-confidence value, confirm no-low-confidence completion, and verify a cross-tenant access attempt fails. **Defer to Story 0.5** (same as 5.5).
  - [ ] 5.7 — Add redaction/logging tests or static checks proving document bytes, personal data, provider prompts/responses, and tenant payloads are not logged. **Required** (not deferred): `tests/architecture/test_logging_redaction.py` parametrizes structlog calls with each of the forbidden keys (`value`, `ai_value`, `confirmed_value`, `evidence.text`, `extracted_text`, `prompt`, `provider_response`, `document_bytes`) and asserts the captured stdout event has the key scrubbed. Pattern follows `tests/architecture/test_api_calls_only_ports.py` (Story 0.4 lesson — AST guard).

- [ ] **Task 6 — Documentation and operational safeguards** (AC: #1, #5, #6)
  - [ ] 6.1 — Add `docs/ai-document-extraction.md` covering user flow, field schema, confidence threshold (`REVIEW_THRESHOLD = Decimal("0.70")`), review rules, manual fallback, state transitions, retention (90 days post `reviewed_at`), and "AI는 초안, 확정은 사람" notice.
  - [ ] 6.2 — Document exact M10 provider model/config location (`apps/api/modules/m10_ai/config.py`), timeout (`PROVIDER_TIMEOUT_S = 28`), supported file types/limits (MIME, max bytes, max pages, max rows, daily quota), no-payload-logging rule, and how to rotate credentials (`ANTHROPIC_API_KEY` env → secret manager).
  - [ ] 6.3 — Document PIPA cross-border processing notice/consent and processor-contract review as a pre-pilot operational gate. Reference `apps/api/core/pipa_gate.py` and CI job `pipa-gate-check`.
  - [ ] 6.4 — Update onboarding/settings docs and Korean messages; explicitly state compliance/AI extraction is assistive and not accounting/legal confirmation. Cross-link `docs/onboarding-schema.md` for `company_subblock` schema.
  - [ ] 6.5 — **NEW** — Create `docs/architecture-decisions/AD-7-ai-extraction-table-naming.md` resolving the ERD (`ai_extractions`) vs architecture (`input_drafts`) variance. Decision: **`input_drafts` is canonical**; ERD §8 is superseded per AD-1. Document the migration mapping (any legacy `ai_extractions.pending_review`/`approved` rows map to `input_drafts.state='draft'`/`state='reviewed'`). Add to AD register.

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
  "tenant_id": "uuid-v4-from-jwt",
  "document_id": "uuid-v7",
  "field_name": "business_registration_number",
  "ai_value": "123-45-67890",
  "confirmed_value": null,
  "confidence": 0.65,
  "badge": "review_required",
  "state": "draft",
  "evidence": {"page": 1, "text": "...max 200 chars, redacted..."},
  "version": 1,
  "draft_hash": "sha256:...",
  "requested_by": "uuid-v4",
  "requested_at": "2026-07-31T08:00:00Z",
  "reviewed_by": null,
  "reviewed_at": null
}
```

- `tenant_id` is **UUID v4** derived from JWT (`auth.jwt() ->> 'tenant_id'`) per AD-15 variance (`docs/conventions.md §3`); business IDs (`draft_id`, `document_id`, `field_id`) are **UUID v7**.
- `confidence` is normalized to `[0,1]` via `NUMERIC(4,3) CHECK`; values outside that range or non-numeric provider output are invalid and must fail closed (record `state='draft'` with `confidence=NULL` and surface as `review_required`).
- **Single-source badge mapping** (no duplicate `review_required` field): `confidence IS NULL OR confidence < apps.api.core.confidence.REVIEW_THRESHOLD` → `badge='review_required'` (red `⚠ 확인 필요`); otherwise → `badge='auto_input'` (gray `✓ 자동 입력`). The UI derives the same `review_required` boolean locally for aria-labels.
- `evidence.text` max 200 chars, redacted via `apps/api/core/logging.py redact_processor` (email, KR phone, business_no patterns), HTML-escaped before render.
- **State machine**: `draft → reviewed → superseded` (note: NOT `promoted` — `promoted` is AD-17 monthly-input semantics, not used here; user-confirmed fields write to `tenant_settings.onboarding.company_subblock` directly via `SettingsService`). Provider job status separately: `queued | processing | completed | failed`. `state` is never mutated backward.
- `input_drafts` is the **canonical** name (AD-7 + new `docs/architecture-decisions/AD-7-ai-extraction-table-naming.md`). Legacy `ai_extractions` table (if it exists) is mapped via adapter/view; do not maintain two competing draft stores.
- Confirmed values flow to `tenant_settings.onboarding.company_subblock` JSONB subkey (NOT a 5th top-level namespace — AD-23 preserved). Subkey schema lives in `apps/api/core/jsonb_schemas.py::validate_onboarding_schema()` and `docs/onboarding-schema.md`.
- `draft_hash` is `sha256(canonical_json(draft_payload))` (canonical form excludes `version`); `If-Match` request header carries `base64(draft_hash)`. Mismatch → `409 DRAFT_VERSION_CONFLICT`.

### Provider and latest-technology guardrails

- PRD selects Claude API with Vision, but the architecture intentionally leaves the exact model snapshot to M10 configuration. Pin the chosen snapshot in one config constant and record the date/version in docs; never hard-code it in handlers/components.
- Use the current official Anthropic SDK/API pattern available in the repository at implementation time. Because this story is a planning artifact, the dev must verify the provider’s current structured-output/document-input API and SDK version before implementation rather than copying a stale call signature.
- Keep the provider behind a port so tests use a fake adapter. Require schema-validated output and handle refusal, empty extraction, timeout, malformed output, and provider HTTP errors.
- Use file type detection from content where possible, not only client MIME; enforce max size and request timeout server-side.
- SLO: AI extraction P95 ≤ 30 seconds (PRD §14). Provide asynchronous status if the provider call exceeds the request budget; do not silently retry duplicate extraction without an idempotency key.

### Source tree requirements

Expected changes, subject to actual repository verification:

```text
apps/api/
├── modules/
│   ├── m0_onboarding/
│   │   ├── handlers.py                            # UPDATE — onboarding/ai-documents + ai-drafts routes
│   │   ├── schemas.py                             # UPDATE — document/draft DTOs, kebab-case routes
│   │   └── services/settings_service.py           # UPDATE — compute_completion takes pending_extractions
│   └── m10_ai/                                    # FIRST story to populate
│       ├── __init__.py                            # NEW
│       ├── config.py                              # NEW — DOCUMENT_EXTRACTION_MODEL, PROVIDER_TIMEOUT_S, MAX_UPLOAD_BYTES, ALLOWED_MIME, MAX_PDF_PAGES, MAX_XLSX_ROWS_PER_SHEET
│       ├── ports.py                               # NEW — DocumentExtractionPort, DocumentExtractionJob
│       ├── adapters/claude_vision.py              # NEW — Anthropic SDK call, structured output
│       ├── service.py                             # NEW — orchestration, validation, redaction
│       ├── schemas.py                             # NEW — request/response models (Pydantic)
│       └── handlers.py                            # NEW — FastAPI router for /api/v1/onboarding/ai-{documents,drafts}
├── core/
│   ├── confidence.py                              # NEW — REVIEW_THRESHOLD = Decimal("0.70")
│   ├── pipa_gate.py                               # NEW — require_pipa_review dependency
│   ├── logging.py                                 # UPDATE — redact_processor covers value/ai_value/confirmed_value/evidence.text/extracted_text/prompt/provider_response/document_bytes
│   ├── jsonb_schemas.py                           # UPDATE — validate_onboarding_schema accepts company_subblock
│   ├── capability.py                              # (existing — wiring lift per deferred-work F-6)
│   └── jobs/document_retention.py                 # NEW — 90-day soft-delete cron
├── main.py                                        # UPDATE — register m10_ai.router
└── pyproject.toml                                 # UPDATE — `[STACK BUMP]` pins: anthropic, pdfplumber, openpyxl, python-magic

apps/api/alembic/versions/
└── 0005_ai_documents_input_drafts.py              # NEW — uploaded_documents + input_drafts schema

supabase/policies/
└── 0005_ai_documents_input_drafts.sql             # NEW — RLS for both tables

packages/services/m10_ai/
└── extraction_port.py                             # NEW — port interface consumed by M0

apps/web/
├── app/[locale]/(dashboard)/settings/wizard/
│   └── page.tsx                                   # UPDATE — insert DocumentExtractionStep after AllocationCriteriaStep
├── components/settings/wizard/
│   ├── DocumentExtractionStep.tsx                 # NEW
│   ├── ExtractionFieldRow.tsx                     # NEW
│   └── ConfidenceBadge.tsx                        # NEW
├── hooks/useDocumentExtraction.ts                 # NEW — cancelledRef + statusRef + backoff polling
├── lib/api-client.ts                              # UPDATE — Idempotency-Key + If-Match + retry/timeout
├── lib/server-api.ts                              # (existing — F-20 pattern reused)
└── messages/ko-KR.json                            # UPDATE — 정확_필요 / 자동_입력 / AI_추출_폴백

tests/
├── api/
│   ├── test_document_extraction.py                # NEW — boundary + provider-error + status transitions
│   ├── test_document_extraction_isolation.py      # NEW — tenant/role isolation, body tenant_id rejection
│   └── test_draft_review_if_match.py              # NEW — 409 DRAFT_VERSION_CONFLICT
├── services/
│   ├── test_extraction_contract.py                # NEW — port contract, fake adapter
│   └── test_settings_completion.py                # UPDATE — pending_extractions parameter cases
├── integration/
│   ├── test_draft_promotion_boundary.py           # NEW — extraction never writes confirmed input
│   ├── test_badge_consistency.py                  # NEW — Python ↔ TS badge mapping parity
│   └── test_completion_consistency.py             # UPDATE — pending_extractions mirror cases
├── architecture/
│   └── test_logging_redaction.py                  # NEW — AST + runtime guard for forbidden keys
└── web/
    ├── __tests__/ConfidenceBadge.test.tsx         # NEW (deferred to Story 0.5 — scaffolding only)
    └── e2e/document-extraction.spec.ts            # NEW (deferred to Story 0.5 — scaffolding only)

docs/
├── ai-document-extraction.md                      # NEW — flow + threshold + state machine + retention
├── onboarding-schema.md                           # UPDATE — company_subblock JSONB schema
├── conventions.md                                 # UPDATE — input_drafts naming, REVIEW_THRESHOLD constant
└── architecture-decisions/
    └── AD-7-ai-extraction-table-naming.md         # NEW — input_drafts canonical, ai_extractions superseded
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

### Known ambiguities — resolved during validation (2026-07-31)

- **Storage naming (C2/P9) — RESOLVED**: `input_drafts` is canonical (AD-7 supersedes ERD §8 per AD-1). New AD `docs/architecture-decisions/AD-7-ai-extraction-table-naming.md` documents the mapping (legacy `ai_extractions.pending_review/approved` → `input_drafts.state='draft'/'reviewed'`).
- **Promotion target (C3) — RESOLVED (Option C: `company_subblock`)**: Epic Story 1.3 AC line 657 ("확정값은 `tenant_settings`로 승격") is honored via `tenant_settings.onboarding.company_subblock` JSONB subkey. AD-17 `InputPromoter.promote()` is reserved exclusively for monthly-input promotion (Epic 3) and is NOT reused here. AI company-identity fields (Epic 1 onboarding) flow through `SettingsService.update_onboarding_field(..., "company_subblock", ..., actor_id)` (Story 1.2 2-transaction audit-first pattern). Two distinct paths, two distinct namespaces.
- **M0 vs M10 ownership (C4) — RESOLVED**: M10 owns the port + adapter (`apps/api/modules/m10_ai/{config,ports,adapters/claude_vision,service,schemas}.py`); M0 owns the onboarding surface and calls the M10 port via `apps/api/modules/m0_onboarding/handlers.py`. Story 1.3 is the FIRST story to populate M10 (current `__init__.py` is a one-line stub); Epic 10.1+ subsequently fill out insights + cache. No cross-module duplicate endpoints.
- **Migration location (C5/A1) — RESOLVED**: `apps/api/alembic/versions/0005_ai_documents_input_drafts.py`. The `supabase/migrations/` path in the original spec was incorrect (directory does not exist). Companion RLS lives in `supabase/policies/0005_ai_documents_input_drafts.sql`.
- **Completion contract change (C6/E1) — RESOLVED**: extend `packages/services/m0_onboarding/settings_completion.py::compute_completion()` with a third parameter `pending_extractions: list[DraftSummary]`. Mirror in TS and add `tests/integration/test_completion_consistency.py` parametrized cases for the new behavior. Story 1.2 status is currently `in-progress`; the signature change ships BEFORE Story 1.2 → done, ensuring the 1.2 → done promotion can use the new shape.
- **`tenant_settings` namespace (C7) — RESOLVED**: `tenant_settings.onboarding.company_subblock` subkey. AD-23 4-namespace rule preserved (`onboarding`/`baseline`/`abc`/`ai`). JSONB schema added to `apps/api/core/jsonb_schemas.py` and `docs/onboarding-schema.md`.
- **Duplicate `review_required` field (C8) — RESOLVED**: removed. UI derives `review_required` and `badge` from `confidence IS NULL OR confidence < REVIEW_THRESHOLD`. Single source of truth.
- **Re-upload / retention (C9) — RESOLVED**: same `tenant_id + sha256(document_bytes)` → `409 DOCUMENT_ALREADY_EXISTS`; retention 90 days post `reviewed_at` then daily cron soft-deletes Storage + marks drafts `state='superseded'`.
- **M10 deps pins (A2) — RESOLVED**: `[STACK BUMP]` tag added in spec; exact pins for `anthropic`, `pdfplumber`, `openpyxl`, `python-magic` recorded in dev notes section.
- **Model snapshot constant (A3) — RESOLVED**: `apps/api/modules/m10_ai/config.py::DOCUMENT_EXTRACTION_MODEL = "<exact-snapshot>"`; same file holds `PROVIDER_TIMEOUT_S`, `MAX_UPLOAD_BYTES`, `ALLOWED_MIME`, `MAX_PDF_PAGES`, `MAX_XLSX_ROWS_PER_SHEET`.
- **Logging redaction (A4) — RESOLVED**: `apps/api/core/logging.py` redact_processor extended; `tests/architecture/test_logging_redaction.py` enforces.
- **PIPA gate (A5) — RESOLVED**: `apps/api/core/pipa_gate.py::require_pipa_review()` dependency; CI job `pipa-gate-check`.
- **Router wiring (A6) — RESOLVED**: `apps/api/main.py` registration of M10 router listed in source tree.
- **`REVIEW_THRESHOLD` constant (A7) — RESOLVED**: `apps/api/core/confidence.py::REVIEW_THRESHOLD = Decimal("0.70")`.
- **Upload limits (A8) — RESOLVED**: 10 MB / 20 PDF pages / 5000 rows/sheet / 50 uploads/day.
- **Idempotency header (A9) — RESOLVED**: `Idempotency-Key` header on `POST /ai-documents`.
- **Partial confirm response (A10) — RESOLVED**: `{ draft_id, confirmed_fields[], remaining_review_count, settings_version }`.
- **Audit pattern reuse (A11) — RESOLVED**: `SettingsService.emit_audit + with_service_role` 2-transaction pattern invoked from M10 review handler.
- **Test framework deferral (A12) — RESOLVED**: 5.5 + 5.6 explicitly defer Vitest/RTL + Playwright E2E to Story 0.5.
- **Scope of company fields**: still open — see Open questions below.
- **Auto-approved fields**: still open — see Open questions below.

### Open questions (require product owner confirmation before dev)

- **Scope of company fields**: Story AC explicitly names business registration number but does not enumerate every required field. Keep schema extensible; the MVP set is `{business_registration_number, company_name, address, representative_name, industry}` — confirm with PM whether more fields are required-for-calc.
- **Auto-approved fields**: AC allows `>=70%` to pass without manual edit, while global PRD says "확정은 사람". Treat `>=70%` as review-complete for the badge/calculation gate only (so the user can proceed to [계산]); do NOT promote to authoritative `company_subblock` write without explicit user confirmation click. Confirm with PM whether the `>=70%` auto-review is acceptable or whether every field requires an explicit "확인" click.

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
- [ ] **Story 1.2 dependency gate**: verify `packages/services/m0_onboarding/settings_completion.py::compute_completion()` accepts the new `pending_extractions` parameter; if not, ship the signature change FIRST (before this story's other tasks), so Story 1.2 → done can use the new shape.
- [ ] Confirm migration owner (`apps/api/alembic/versions/0005_ai_documents_input_drafts.py` is the correct path — `supabase/migrations/` does not exist).
- [ ] **`input_drafts` is canonical** (per AD-7 + new `docs/architecture-decisions/AD-7-ai-extraction-table-naming.md`). Confirm `ai_extractions` does NOT already exist; if it does, write an adapter/view mapping rather than maintaining two stores.
- [ ] Verify current Anthropic SDK/document/structured-output API and model snapshot from official docs. Pin the exact snapshot in `apps/api/modules/m10_ai/config.py::DOCUMENT_EXTRACTION_MODEL`.
- [ ] `[STACK BUMP]`-tag the dependency adds (`anthropic`, `pdfplumber`, `openpyxl`, `python-magic`) and record exact pins.
- [ ] Run focused tests and the full existing test/lint/build suite; report failures truthfully.
- [ ] Confirm PIPA cross-border review status (`PIPA_REVIEW_COMPLETED` env flag); routes return `503 PIPA_REVIEW_PENDING` until operator flips the flag.
- [ ] Run `make lint-conventions` and confirm zero violations on new files.

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Story context analysis completed on 2026-07-25.
- Story marked `ready-for-dev` for Epic 1 completion.
- 2026-07-31 validation pass: `critical+plumbing` option applied. Resolved 9 Critical (C1–C9) + 12 Architecture Blocker (A1–A12) + 10 Plumbing packages (P1–P10). New `docs/architecture-decisions/AD-7-ai-extraction-table-naming.md` to be created in Task 6.5. Two open questions for product owner (scope of company fields, `>=70%` auto-review semantics). Ready-for-dev status preserved.

### File List

<!-- Dev agent should populate this section on completion with files created/modified and key decisions -->
