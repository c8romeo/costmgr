# AD-7 — AI Extraction Table Naming (`input_drafts` canonical)

> **Status**: Accepted (2026-07-31, Story 1.3 review)
> **Supersedes**: ERD §8 `ai_extractions.pending_review` / `approved` naming
> **Deciders**: Architecture owner, Product owner
> **Related**: AD-1 (architecture supersedes ERD), AD-7 (AI non-authoritative), AD-17 (sole promotion port), AD-23 (4-namespace rule)

## Context

The business ERD (`비즈업_통합ERD_v2.0.md §8 도메인 H. 검증·AI·가져오기`)
declares an `ai_extractions` table with two states: `pending_review`
and `approved`. The architecture spine
(`architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md AD-7`)
declares `input_drafts` as the canonical AI output container with a
3-state machine: `draft` / `reviewed` / `superseded`.

Story 1.3 (AI document extraction + confidence badge) needs to ship a
persistence boundary. The two naming candidates diverge in:

| Dimension | ERD `ai_extractions` | Architecture `input_drafts` |
|---|---|---|
| State vocabulary | `pending_review`, `approved` (2) | `draft`, `reviewed`, `superseded` (3) |
| Promotion semantic | `approved` implies write-through | `reviewed` is review-only; promotion is a separate AD-17 port |
| Re-upload handling | (not specified) | `superseded` is the explicit "replaced by a later extraction" state |
| Alignment with `tenant_settings.onboarding.*` | None | Writes via `SettingsService.update_onboarding_field("company_subblock", ...)` — same audit chain as wizard fields |
| Idempotency | (not specified) | Unique `(tenant_id, document_id, field_name)` for re-upload guard |

## Decision

**`input_drafts` is canonical.** The architecture spine is the
authoritative source per AD-1; the ERD §8 `ai_extractions` naming is
**superseded** for any new code path.

### State mapping (legacy → canonical)

For any pre-Story-1.3 row written under the ERD naming:

| Legacy `ai_extractions.state` | Canonical `input_drafts.state` |
|---|---|
| `pending_review` | `draft` |
| `approved` | `reviewed` |

The mapping is 1-to-1; no data loss. Story 1.3 ships a one-time view
(or migration step) that aliases `ai_extractions` → `input_drafts` for
any pilot environment that already has the legacy table.

### Why three states (not two)

- `draft` — the AI extracted a candidate value; user has not confirmed.
- `reviewed` — user has explicitly confirmed (via `POST /ai-drafts/{id}/review`
  with an `If-Match` header that bumps `version`).
- `superseded` — a later extraction of the same field replaced this row
  (re-upload of the same document, or a more recent upload that extracted
  the same field with higher confidence). Original row is preserved for
  audit; replaced by a new `draft` row referencing the same `field_name`.

The `promoted` state is **intentionally absent**. AD-17's
`InputPromoter.promote()` is the sole promotion path for monthly-input
fields (Epic 3). AI company-identity fields (Epic 1 onboarding) flow
through `SettingsService.update_onboarding_field("company_subblock", ...)`
— that is a different namespace and a different code path.

## Consequences

- New code paths must use `input_drafts`. The legacy `ai_extractions`
  table (if it exists in pilot environments) is read-only via the
  mapping view; no new INSERTs against `ai_extractions`.
- Story 1.3 ship checklist: every API surface, JSONB schema, RLS policy,
  and ORM model names `input_drafts`. Cross-language mirrors (TS) use
  `InputDraft` (PascalCase per AD-15).
- Documentation updates: `docs/onboarding-schema.md`,
  `docs/ai-document-extraction.md`, `docs/conventions.md` all reference
  `input_drafts`. The ERD §8 paragraph is annotated with a
  "superseded by AD-7" footnote pointing to this document.
- Test coverage: `tests/integration/test_badge_consistency.py` and
  `tests/api/test_document_extraction.py` use `input_drafts` only.

## Migration history

| Revision | Date | Change |
|---|---|---|
| (this) | 2026-07-31 | `input_drafts` declared canonical; ERD §8 `ai_extractions` superseded. |

## Cross-references

- AD-1 — Architecture supersedes ERD for naming decisions.
- AD-7 — AI output is non-authoritative; lives in `input_drafts` only.
- AD-17 — Sole promotion port; `InputPromoter.promote()` reserved for monthly input.
- AD-23 — Singleton `tenant_settings` aggregate (4 namespaces).
- AD-15 — Snake_case DB/Python; PascalCase TS.
- `docs/conventions.md §3` — UUID v7 for business IDs, UUID v4 for tenant_id.