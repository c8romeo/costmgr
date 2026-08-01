# AI 문서 추출 + 신뢰도 배지 (Story 1.3)

> 운영자 가이드 — bizup/costmgr의 AI 문서 추출 기능이 어떻게 동작하고,
> 운영 시 무엇을 확인해야 하는지 설명한다.

## 한 줄 요약

테넌트가 PDF / 이미지를 업로드하면 **M10 AI** 모듈이 추출해서
`input_drafts`에 저장하고, 사용자는 5개 필드 (회사 정보)에 대해
신뢰도(0.00–1.00) 배지를 보면서 확인/거부한다. `business_registration_number`
1개만 확정되면 `tenant_settings.onboarding.company_subblock` JSONB로 승격된다.

## 동작 흐름

```
[Web 업로드] → POST /api/v1/ai-documents (base64 body, Idempotency-Key)
       ↓
[M0 Onboarding handlers] — PIPA gate (require_pipa_review)
       ↓
[M10 service.upload_document] — MIME/size 검증, sha256 계산
       ↓
[Adapter (Fake | Claude)] — DocumentExtractionPort.extract()
       ↓
[input_drafts rows] — 5개 field_name × {ai_value, confidence, evidence}
       ↓
[PATCH /ai-drafts/{id} confirm|reject] — 사용자가 검토
       ↓
[POST /ai-drafts/promote] — company_subblock JSONB 승격
```

## 신뢰도 배지 의미 (AC #5.1)

`apps/api/core/confidence.py::REVIEW_THRESHOLD = Decimal("0.70")` 가 단일 기준.

| confidence | 배지 | 의미 |
|---|---|---|
| `< 0.70` 또는 `NULL` | 🟠 확인 필요 (review_required) | AI가 확신 못함 — 사용자 검토 필수 |
| `>= 0.70` | ⚪ 자동 입력 (auto_input) | AI가 추출 — 그래도 검토 권장 |

- NULL confidence는 절대 자동 승격 안 됨 (review_required).
- 0.70은 휴리스틱 — calibrated probability 아님 (UI에 명시).
- MVP는 자동 승격 ❌ — 사용자가 명시적으로 "확인" 클릭 필요 (스펙 §AC #4).

## 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `AI_PROVIDER_ENABLED` | `false` | `true`로 설정 시 real Claude Vision adapter 활성 |
| `ANTHROPIC_API_KEY` | (없음) | real adapter 활성 시 필수 |

> real adapter는 [STACK BUMP] 워크플로우 후속 (Story 0.3 lesson 재적용).
> 현재 MVP는 `FakeDocumentExtractionAdapter`로 동작 — 동일 bytes → 동일 fields.

## 어댑터 선택 규칙 (`apps/api/modules/m10_ai/service.py::select_adapter`)

```
AI_PROVIDER_ENABLED=true AND ANTHROPIC_API_KEY 가 설정됨
    → ClaudeVisionAdapter (real, [STACK BUMP] 후속)
그 외 (test/dev/CI)
    → FakeDocumentExtractionAdapter
```

## PIPA gate (Task 2.4)

업로드 라우트는 `require_pipa_review` dependency로 보호됨. tenant가
`onboarding.pipa_consent=true` + `onboarding.pipa_region=KR` 모두 만족해야 통과.
그렇지 않으면 **451 PIPA_CONSENT_MISSING** (HTTP "Unavailable for Legal Reasons")
반환. MVP allow-list: KR only.

## 보존 정책 (Task 1.3)

`apps/api/jobs/document_retention.py` cron이 매일 1회 실행되어
`DOCUMENT_RETENTION_DAYS = 90`일 지난 `uploaded_documents` 행을 soft-delete
(`deleted_at` 컬럼 세팅). Hard delete는 별도 작업 (1년 audit 보관, NFR-22).

Railway cron 스케줄: 매일 KST 03:00 (UTC 18:00).

## RLS / 멀티테넌시

- `supabase/policies/0005_ai_documents_input_drafts.sql` — tenant_id 격리
- 모든 라우트는 `get_tenant_context` dependency 통과 후에만 동작
- cross-tenant 접근 시도 → RLS가 row를 0개 반환 → 404 매핑

## Deferral / 후속 작업

이번 스토리에서 **의도적으로 미완성** 항목 (sprint status에는 명시):

1. **real Claude Vision adapter** (`claude_vision.py`은 stub) — [STACK BUMP]
   워크플로우로 Anthropic SDK 추가 후 `claude_vision.extract()` 본문 작성.
2. **Frontend 업로드 + 검토 UI** — Story 0.5 plumbing (shadcn/ui, sonner,
   next-intl, vitest/Playwright) 의존.
3. **Logging redaction 테스트** (`tests/architecture/test_logging_redaction.py`)
   — `apps/api/core/logging.py` structlog redact_processor 미설치. Story 0.5
   후속.
4. **Reprocess 시 storage 다운로드** — 현재 reprocess는 501 (스토리지 연결
   후 가능). Story 0.5 plumbing 후속.
5. **TS mirror parity test** (`tests/integration/test_extraction_parity.py`) —
   Frontend 후속 작업.

## 실패 시나리오 매핑 (AD-15 envelope)

| 코드 | HTTP | 원인 |
|---|---|---|
| `DOCUMENT_MIME_NOT_ALLOWED` | 415 | MIME not in `ALLOWED_MIME` |
| `DOCUMENT_TOO_LARGE` | 413 | byte_size > 8 MiB |
| `DOCUMENT_DECODE_FAILED` | 400 | base64 디코딩 실패 |
| `DOCUMENT_NOT_FOUND` | 404 | document_id not in tenant |
| `DRAFT_NOT_FOUND` | 404 | draft_id not in tenant |
| `DRAFT_STATE_INVALID` | 409 | already reviewed/superseded |
| `PROMOTE_REQUIRED_FIELDS_MISSING` | 409 | 필수 필드 review 누락 |
| `PIPA_CONSENT_MISSING` | 451 | tenant 동의 누락 |
| `PIPA_REGION_NOT_ALLOWED` | 451 | KR 외 지역 |
| `AI_PROVIDER_NOT_CONFIGURED` | 500 | real adapter 미설정 + fake도 실패 |

## 디버깅

- 모든 작업에 `trace_id` 부여 → 응답 `X-Trace-Id` 헤더 + audit_logs.payload.trace_id
- `audit_logs` `action='document_uploaded'` / `input_draft_confirm` / `company_subblock_promoted`
  등으로 행위 추적 가능
- `input_drafts.evidence.text`는 200자 truncate + redact_processor 후속 (위 defer #3)
