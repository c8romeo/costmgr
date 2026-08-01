# costmgr BOM Matrix (M1 — Story 2.2)

> **소속**: Epic 2 / Story 2.2
> **최종 갱신**: 2026-08-01
> **PRD 참조**: §8.M1(b) (BOM 비중 합 100%) · §6.1 (BOM parent/child type rules)
> **UX locked-decisions**: Dark MVP · WCAG AA · Professional 톤 · ko-KR (NFR-18)
> **직전**: [`product-item-master.md`](./product-item-master.md) (Story 2.1) — BOM은 products.id 를 FK 참조한다.

우리 회사 BOM(Bill of Materials, 자재 명세서) 행렬을 한 화면에서 등록·조회·비중 편집·전체 삭제하는 화면과 API.
PRD §6.1이 정한 모품목(parent) ↔ 자품목(child) 타입 규칙을 **OM으로 강제**하며, 비중 합이 정확히 100%일 때
계산(Epic 3) 잠금이 풀리도록 한다.

---

## 1. 데이터 모델 — `bom_lines` 테이블

`products`와 동일한 모듈(`m1_baseline`)에 속하지만, **append-only-leaning 패턴**이라
per-row PATCH endpoint가 **없다**. 변경은 전체 BOM SET (bulk-replace PUT) 만 허용한다.

| 컬럼              | 타입            | 제약 / 비고                                              |
|------------------|----------------|----------------------------------------------------------|
| `id`             | UUID PK        | UUID v7 (default `packages.common.uuid7.uuid7()`)       |
| `tenant_id`      | UUID NOT NULL  | UUID v4 — `tenants(id)` ON DELETE CASCADE                |
| `parent_product_id` | UUID NOT NULL | FK `products.id` ON DELETE RESTRICT (BOM FK 보존)        |
| `child_product_id`  | UUID NOT NULL | FK `products.id` ON DELETE RESTRICT (AC #4 코드 변경=불가) |
| `ratio`          | NUMERIC(7,4) NOT NULL | **비중 (%)** — 4자리 소수, 0 < ratio ≤ 100 (DB CHECK) |
| `created_at`     | TIMESTAMPTZ    | DEFAULT now()                                            |
| `updated_at`     | TIMESTAMPTZ    | DEFAULT now()                                            |

인덱스:
- `uq_bom_lines_tenant_parent_child` UNIQUE (tenant_id, parent_product_id, child_product_id) — 같은 parent에 같은 child 중복 방지
- `idx_bom_lines_tenant_parent` (tenant_id, parent_product_id) — parent별 BOM 목록 조회
- `idx_bom_lines_tenant_child` (tenant_id, child_product_id) — reverse lookup (이 자식이 들어간 BOM 검색)

---

## 2. 모품목/자품목 type rules (PRD §6.1)

**모품목**: `product_type IN ('product', 'semi_product')`
- 최종 제품 또는 BOM 중간 단계(반제품)만 BOM을 가질 수 있음.
- `material` / `goods` / `service` 는 BOM parent 불가 → 422 `BOM_INVALID_PARENT_TYPE`.

**자품목**: `product_type IN ('material', 'semi_product')`
- BOM 의 최하위 투입 요소(원자재) 또는 중간 단계(반제품)만 가능.
- `product` / `goods` / `service` 는 BOM child 불가 → 422 `BOM_INVALID_CHILD_TYPE`.

```python
# packages/services/m1_baseline/schemas.py
BOMParentType = frozenset({ProductType.PRODUCT, ProductType.SEMI_PRODUCT})
BOMChildType = frozenset({ProductType.MATERIAL, ProductType.SEMI_PRODUCT})
```

TS mirror `apps/web/lib/bom-validation.ts` 도 동일 set. 드리프트는
`tests/integration/test_bom_validation_consistency.py` 로 강제 차단.

---

## 3. 100% 불변식 (A6 axiom) — derived at read time

>BOM 의 모든 자식 행의 `ratio` 합은 **정확히 100.0000%** 이다. `is_complete` 는 DB 에 저장되지 않으며, 조회 시점에 계산된다.

```python
# packages/services/m1_baseline/bom_validation.py
TARGET_TOTAL: Final[Decimal] = Decimal("100.0000")

def is_complete_bom(rows: Iterable[Decimal]) -> bool:
    return sum_ratios(rows) == TARGET_TOTAL

def missing_to_complete(rows: Iterable[Decimal]) -> Decimal:
    return max(TARGET_TOTAL - sum_ratios(rows), Decimal("0.0000"))
```

우측 clamp는 RDB 변경 추적 시 비중 합이 100% 초과 (예: 105%) 가 되는 경우에도 0을 반환하기 위함이다.

### 왜 derived 인가

스토리 2.2 결정 — BOM 라인 정규화 CRUD 만 있고 100% 검증은 별도 작업으로 분리된다.
`is_complete` / `missing_ratio` 는 "지금 이 순간의 BOM 행 합계"로 계산되어야 의미가 정확하다.
캐싱은 후속 단계의 계산 엔진(Epic 3)이 `bom_lines` 를 직접 읽어 다시 도출한다.

---

## 4. 단일 행 추가 vs bulk-replace

**CR 2.1 lesson** — 단일 행 POST/PATCH 엔드포인트는 두 가지 함정을 만든다:

1. 비활성 row 를 별도 행으로 추가해 사이즈가 부풀려지는 문제
2. row-level 갱신이 100% invariant 을 잠시 깨는 race window 발생

따라서 BOM 변경은 **오직 두 가지 API**만 존재한다:

| API | 용도 | 비고 |
|---|---|---|
| `GET /api/v1/baseline/products/{product_id}/bom` | BOM 행렬 + 합계/완료 여부 | 항상 200, 빈 BOM 도 정상 |
| `PUT /api/v1/baseline/products/{product_id}/bom` | BOM bulk-replace | DELETE + INSERT in single transaction |
| `DELETE /api/v1/baseline/products/{product_id}/bom` | BOM 전체 삭제 | 행 수 0, is_complete=false |

PUT 의 요청 payload 는 BOM 행 전체 (lines 필드) 이며, 서버는 전체 삭제 후 재삽입한다.
**audit-first** (`emit_audit(flush=True)` BEFORE DELETE/INSERT) 가 첫 번째 commit 이 된다.

### Idempotent no-op skip (CR 2.1 lesson)

`BOMService._is_noop_replace()` 가 기존 BOM 과 새 BOM 의 (set of child ids, set of ratios) 가
모두 같으면 audit + DELETE+INSERT 를 모두 건너뛰고 기존 BOM 을 그대로 반환한다.
이는 클라이언트가 동일 payload 재전송 시 audit log 노이즈를 막는다.

---

## 5. Capability gate (AC #4)

BOM endpoint 는 `Capability.BOM` 게이트가 걸려 있다. 이 capability 는 다음 industry 만 보유:

- `manufacturing` (①) — 전통 개별원가
- `manufacturing_service` (③) — 두 엔진 병행
- `manufacturing_service_other` (④) — 두 엔진 + 격리 버킷

`service` (②) 업종은 BOM 자체가 없으므로 403 `INDUSTRY_NOT_SUPPORTED` 로 거부된다.
(자세한 결정: `apps/api/core/capability.py::_INDUSTRY_CAPABILITIES`.)

mutation (PUT / DELETE) 은 추가로 `require_role("owner")` 를 요구 — consultant 같은 viewer 역할을 가진 사용자는 BOM 을 볼 수만 있고 쓸 수는 없다.

---

## 6. Audit log (AD-2)

`action='bom_set'` audit row 가 DELETE+INSERT **이전** 에 INSERT된다. Payload:

```json
{
  "parent_product_id": "01920b8a-...-v7",
  "previous_line_count": 3,
  "new_line_count": 4,
  "previous_total_ratio": "100.0000",
  "new_total_ratio": "95.0000",
  "changed_ratios": [
    ["01920b8a-...-v7-ch", "40.0000", "50.0000"],
    ["01920b8a-...-v7-new", null, "10.0000"]
  ],
  "is_complete_new": false,
  "missing_ratio_new": "5.0000"
}
```

`changed_ratios` 의 tuple은 `(child_product_id, before_or_null, after_or_null)` 형태.
added 는 before=null, removed 는 payload 에 포함되지 않고 count 차이로만 드러난다.

`action='bom_cleared'` 는 DELETE 시에만 적재.

---

## 7. AC 워크스루 — 요청/응답 예시

### AC #1 — `GET /api/v1/baseline/products/{parent_id}/bom` (BOM 비어 있음)

```http
GET /api/v1/baseline/products/01920b8a-...-v7/bom
Authorization: Bearer <jwt>
```

```http
HTTP/1.1 200 OK

{
  "parent_product_id": "01920b8a-...-v7",
  "parent_code": "PRD-0001",
  "parent_name": "특허 받은 무선 이어폰",
  "parent_product_type": "product",
  "lines": [],
  "total_ratio": "0.0000",
  "is_complete": false,
  "missing_ratio": "100.0000"
}
```

### AC #2 — 100% 완성된 BOM

```http
GET /api/v1/baseline/products/01920b8a-...-v7/bom
```

```http
HTTP/1.1 200 OK

{
  "parent_product_id": "01920b8a-...-v7",
  "parent_code": "PRD-0001",
  "parent_name": "특허 받은 무선 이어폰",
  "parent_product_type": "product",
  "lines": [
    {
      "id": "01920b8a-...-v7-l1",
      "child_product_id": "01920b8a-...-m1",
      "child_code": "MAT-0001",
      "child_name": "ABS 플라스틱 펠릿",
      "child_product_type": "material",
      "child_is_active": true,
      "ratio": "60.0000"
    },
    {
      "id": "01920b8a-...-v7-l2",
      "child_product_id": "01920b8a-...-m2",
      "child_code": "MAT-0002",
      "child_name": "리튬폴리머 배터리 셀",
      "child_product_type": "material",
      "child_is_active": true,
      "ratio": "40.0000"
    }
  ],
  "total_ratio": "100.0000",
  "is_complete": true,
  "missing_ratio": "0.0000"
}
```

### AC #3 — `PUT /api/v1/baseline/products/{parent_id}/bom` (bulk-replace)

```http
PUT /api/v1/baseline/products/01920b8a-...-v7/bom
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "lines": [
    { "child_product_id": "01920b8a-...-m1", "ratio": "60.0000" },
    { "child_product_id": "01920b8a-...-m2", "ratio": "40.0000" }
  ]
}
```

성공 시: 200 OK + GET과 동일한 shape의 BOM (audit row 1개 INSERT).

### AC #7 — child_product_id 중복

```http
PUT .../bom
{ "lines": [
    { "child_product_id": "X", "ratio": "50.0000" },
    { "child_product_id": "X", "ratio": "50.0000" }
] }
```

```http
HTTP/1.1 422 Unprocessable Entity

{
  "code": "BOM_DUPLICATE_CHILD",
  "message_ko": "동일한 자식 품목이 두 번 입력되었습니다",
  "details": { "child_product_id": "X", "occurrences": 2 },
  "trace_id": "..."
}
```

### AC #8 — ratio 정밀도 초과

```http
PUT .../bom
{ "lines": [{ "child_product_id": "X", "ratio": "12.345678" }] }
```

```http
HTTP/1.1 422 Unprocessable Entity

{
  "code": "BOM_INVALID_RATIO",
  "message_ko": "비중은 소수점 4자리까지만 입력 가능합니다",
  "details": { "child_product_id": "X", "ratio": "12.345678", "max_decimal_places": 4 },
  "trace_id": "..."
}
```

### AC #10 — service 업종이 BOM GET

```http
GET /api/v1/baseline/products/01920b8a-.../bom
# tenant.industry = service
```

```http
HTTP/1.1 403 Forbidden

{
  "code": "INDUSTRY_NOT_SUPPORTED",
  "message_ko": "BOM 은 제조 업종에서만 사용할 수 있습니다",
  "details": { "current_industry": "service", "required_capability": "BOM" },
  "trace_id": "..."
}
```

---

## 8. UI 동작 (PRD §8.M1(b))

`apps/web/components/m1-baseline/products/BOMEditorClient.tsx` 에서 다음을 보장한다:

- 비중 합이 100% 가 아니면 [계산] 버튼 자체가 잠긴다 (UI 가 disabled, **합 N% 부족** 메시지 출현).
- 비활성 자식 행은 회색 + 취소선 + "(비활성)" 오버레이 — 계산 시 제외 의도를 명시한다.
- 추가/삭제는 **local state** 에서만 일어나고, [저장] 버튼이 bulk-replace PUT 을 발사한다.
  per-row API 호출은 의도적으로 없다 (CR 2.1 lesson).
- shadcn/ui Dialog 미도입 상태라 Story 0.5 plumbing stub (`<BOMRowAddDialogStub>`) 사용 — 후속 Story 0.5에서 shadcn Dialog 로 교체.

---

## 9. Cross-language consistency (AD-15)

Python `packages/services/m1_baseline/bom_validation.py` 와 TS `apps/web/lib/bom-validation.ts` 가
동일 결과를 보장한다:

| 함수 | Python | TypeScript |
|---|---|---|
| `TARGET_TOTAL` | `Decimal("100.0000")` | `new Decimal("100.0000")` |
| 합계 | `sum_ratios` | `sumRatios` |
| 완료 검사 | `is_complete_bom` | `isCompleteBom` |
| 부족치 | `missing_to_complete` | `missingToComplete` |
| 4자리 자르기 | `quantize_ratio` (ROUND_HALF_EVEN) | `quantizeRatio` (ROUND_HALF_EVEN) |
| 타입 set | `BOMParentType`, `BOMChildType` | `BOMParentTypes`, `BOMChildTypes` |

드리프트는 `tests/integration/test_bom_validation_consistency.py` 가 강제 차단 (Story 2.2 §6.5).

---

## 10. AD 크로스레퍼런스

- **AD-1** Modular Monolith + Hexagonal Core — `m1_baseline` 모듈이 `bom_lines` 소유.
- **AD-2** Append-only ledger-leaning — `audit_logs` 의 `bom_set` / `bom_cleared` action.
- **AD-3** Multi-tenant RLS — `tenant_id` from JWT (request body 무시). RLS policy는
  `supabase/policies/0007_bom_lines_rls.sql`.
- **AD-5** Cost-engine purity — `bom_validation.py`는 순수 함수 (no DB / clock / I/O).
- **AD-8** Monetary types — `ratio` 는 `NUMERIC(7,4)` (Python `Decimal`, TS `decimal.js`),
  `ROUND_HALF_EVEN`. Money 가 아니라 **ratio** 이지만 Money 와 동일한 정밀도 보장.
- **AD-11** Dependency direction — `apps/api` → `packages/services` → engine.
- **AD-15** Cross-language conventions — Python `snake_case` + TS `camelCase` mirror.
- **AD-18** Single product identity — `bom_lines.parent_product_id` / `child_product_id` 가
  모두 `products.id` (UUID v7) — BOM FK 보존.
- **AD-23** Tenant settings aggregate — `bom_lines` 는 별도 테이블 (JSONB 아님).

---

## 11. 변경된 파일

### Backend

- `apps/api/alembic/versions/0007_bom_matrix.py` — `bom_lines` 테이블 + 인덱스 3개 + DB CHECK
- `apps/api/core/db_models.py` — `BOMLine` ORM 추가
- `apps/api/core/capability.py` — `Capability.BOM` enum 추가
- `apps/api/modules/m1_baseline/schemas.py` — `BOMRowInput` / `BOMSetRequest` / `BOMLineResponse` / `BOMResponse` 추가
- `apps/api/modules/m1_baseline/services/bom_service.py` — bulk-replace + audit-first
- `apps/api/modules/m1_baseline/handlers.py` — 3 routes (GET / PUT / DELETE) + capability gate

### Database / RLS

- `supabase/policies/0007_bom_lines_rls.sql` — ENABLE + FORCE RLS:
  - SELECT: 모든 역할 (owner / member / consultant proxy)
  - INSERT / UPDATE: owner only
  - **DELETE policy 없음** — append-only-leaning + bulk-replace only

### Frontend

- `apps/web/lib/api-client.ts` — `BOMRowInput` / `BOMSetRequest` / `BOMLineResponse` / `BOMResponse` + `fetchBom` / `setBom` / `clearBom`
- `apps/web/lib/bom-validation.ts` — TS mirror (decimal.js ROUND_HALF_EVEN)
- `apps/web/lib/server-api.ts` — `fetchBomServerSide` (F-20 race-free)
- `apps/web/hooks/useBom.ts` — list + bulk-replace hook (30s polling, reqId race protection)
- `apps/web/components/m1-baseline/products/BOMEditorClient.tsx` — BOM matrix UI + add dialog stub
- `apps/web/app/[locale]/(dashboard)/m1-baseline/products/[productId]/page.tsx` — Server Component entry

### Pure helpers / packages

- `packages/services/m1_baseline/bom_validation.py` — `TARGET_TOTAL`, `sum_ratios`, `is_complete_bom`, `missing_to_complete`, `quantize_ratio`
- `packages/services/m1_baseline/schemas.py` — `BOMParentType` / `BOMChildType` / `is_valid_bom_parent` / `is_valid_bom_child`
- `packages/services/m1_baseline/__init__.py` — re-exports

### Tests

- `tests/services/test_bom_validation.py` — 35 pure-function tests
- `tests/api/test_bom.py` — 24 typed-exception contract tests
- `tests/integration/test_bom_validation_consistency.py` — 13 TS↔Python drift tests
- `tests/rls/test_bom_lines_isolation.py` — 5 RLS isolation tests (CI-only)

### Docs

- `docs/conventions.md` — §0.6 BOM type rules + §5.1 ratio
- `docs/product-item-master.md` — §8 Story 2.2 DONE link
- `docs/README.md` — BOM Matrix section
- `docs/bom-matrix.md` — 본 문서

---

## 12. 후속 스토리 (참조)

- **Story 2.3** Item Type Change Integrity Guard — `product_type` 변경 가능해진다면 BOM parent/child 자동 검증 필요.
- **Epic 3 / M2 Input** 계산 입력 폼 — BOM 행을 동적 전개해 활동/배부 기준을 끌어옴. `is_complete=true` 면 [계산] 버튼 enable.
- **Story 5.x** 수불부 — `bom_lines.ratio` × 기초재고.단가 = 자재 소요량. BOM 변경 → 수불부 영향 분석.
- **Story 6.x** Report Library — BOM dimension 보고서 (parent × child, total_ratio, is_complete).
