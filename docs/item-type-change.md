# costmgr Item Type Change — Integrity Guard (M1 — Story 2.3)

> **소속**: Epic 2 / Story 2.3 (PRD §6.1)
> **최종 갱신**: 2026-08-01
> **PRD 참조**: §6.1 (변경 가능 필드) · §8.M1 (기준정보/품목) · §8.M1(b) (BOM)
> **상위 문서**: [`product-item-master.md`](./product-item-master.md) — 품목 CRUD/색/코드, [`bom-matrix.md`](./bom-matrix.md) — BOM 행렬, [`conventions.md`](./conventions.md)
> **UX locked-decisions**: Dark MVP · WCAG AA · Professional 톤 · ko-KR (NFR-18)

`product_type`은 한 번 정해지면 끝이 아니다. BOM(Story 2.2)·수불부(Epic 5)에서 FK 참조되기 때문에, 변경하기 전에 **참조 0건** 임을 검증해야 한다. 검증하지 않으면 행렬의 자식·모품목 관계가 깨지고 수불 이동 평균 단가가 틀어진다. Story 2.3은 이 가드를 PATCH 핸들러 레이어에서 강제한다.

---

## §1 Story 2.3 개요

`product_type`은 **열 자체는 가변**(nullable 아님, default 없음)이지만 도메인 규칙상 **참조가 없을 때만 변경 가능**하다.

| 항목                       | 값                                                            |
|---------------------------|--------------------------------------------------------------|
| 가드 발동 조건              | `PATCH /api/v1/baseline/products/{id}` body에 `product_type` 포함 + 기존 값과 다름 |
| 검증 대상                  | `bom_lines.parent_product_id` ∪ `bom_lines.child_product_id` (BOM 행렬) + Epic 5 수불 |
| 통과 조건                  | `total_references == 0`                                       |
| 실패 시 응답                | **409 PRODUCT_TYPE_HAS_REFERENCES** (AD-15 §4 envelope)       |
| 통과 시 동작                | `products.product_type` 갱신 + `audit_logs.product_type_changed` (단일 필드) 또는 `product_updated` (name 등 다른 필드와 동시 변경 시) |

---

## §2 데이터 모델 — 참조 카운트가 의존하는 컬럼

### BOMLine (Story 2.2 — 이미 존재)

```sql
CREATE TABLE bom_lines (
  id                  UUID PRIMARY KEY,
  tenant_id           UUID NOT NULL,                -- RLS scoped
  parent_product_id   UUID NOT NULL,                -- FK products(id) — parent side count
  child_product_id    UUID NOT NULL,                -- FK products(id) — child  side count
  ratio               NUMERIC(7,4) NOT NULL,
  created_at          TIMESTAMPTZ,
  updated_at          TIMESTAMPTZ
);

CREATE INDEX idx_bom_lines_parent_tenant ON bom_lines(tenant_id, parent_product_id);
CREATE INDEX idx_bom_lines_child_tenant  ON bom_lines(tenant_id, child_product_id);
```

두 인덱스 모두 `parent_product_id` ∪ `child_product_id` UNION 쿼리(Story 2.3 PATCH 시점 카운트)에 사용된다. 둘 다 이미 존재하므로 **마이그레이션 없음** (Story 2.3 = no schema change).

### Ledger (Epic 5 — 스텁)

`packages/services/m1_baseline/product_references.py` 안의 `LEDGER_REFERENCE_QUERY_STUB: Final[str] = ""` 마커로 Epic 5에서 편입 예정. 그 시점에 `inventory_movements.tenant_id` 인덱스가 등장하고 카운트 쿼리가 추가된다.

---

## §3 참조 카운트 규칙 — parent + child 합산 (이유)

`bom_lines` 테이블은 양방향 참조다. `parent_product_id`는 "이 제품으로 무엇을 만드는가", `child_product_id`는 "이 제품이 무엇의 재료인가"를 나타낸다. 어느 쪽이든 1건이라도 존재하면:

| 케이스                                          | 영향                                                                 |
|------------------------------------------------|--------------------------------------------------------------------|
| `parent_product_id = X` 1건 (X가 다른 제품의 모품목) | X의 자식 변경 시 X의 BOM 행(예: 0.6 SEM-1001 + 0.4 MAT-0007)이 모순. semi_product→service 변경 시 의미 자체가 뒤집힘. |
| `child_product_id = X` 1건 (X가 다른 제품의 자식)  | X의 비율/모품목 정보가 바뀌면서 부모 제품의 원가 계산 결과가 통째로 달라짐.     |

따라서 **양쪽 OR** 가드의 보수적 판단이 옳다. 이것이 PRD §6.1 line 433 *"참조가 0건임을 검증"* 의 의미.

```sql
SELECT COUNT(*)
  FROM bom_lines
 WHERE tenant_id = :tenant_id
   AND (parent_product_id = :product_id OR child_product_id = :product_id)
```

---

## §4 409 vs 403 — 왜 409 Conflict 인가

| 상태 코드 | 의미                         | Story 2.3 적합성                                          |
|----------|-----------------------------|----------------------------------------------------------|
| **403 Forbidden**  | 인가 거부 / 불가                 | `PRODUCT_IMMUTABLE_FIELD`(code), `INDUSTRY_NOT_SUPPORTED`에 사용. `product_type`은 이제 "조건부 가변"이므로 403은 부적절. |
| **422 Unprocessable Entity** | 페이로드 검증 실패                | `INVALID_PRODUCT_CODE`, `BOM_INVALID_RATIO`에 사용. `product_type` 변경 거부 사유는 **상태 충돌**(현재 BOM/수불 참조 존재)로 페이로드 자체는 유효. 422는 잘못된 케이스. |
| **409 Conflict**   | RFC 7231 §6.5.8 — 대상 리소스의 현재 상태와 충돌 | Story 2.3에 정확히 일치: 본문은 유효하나 현재 상태(참조 존재)가 변경을 막음. 클라이언트는 신규 품목 생성 + 참조 이관 후 삭제로 해소 가능. |

**Story 2.3 contract**: `409 Conflict` + `code: "PRODUCT_TYPE_HAS_REFERENCES"` + `details.bom_count / ledger_count / total_count`.

---

## §5 PATCH 처리 순서

FastAPI 핸들러(`apps/api/modules/m1_baseline/handlers.py::update_product`)의 try/except 순서. **구체적인 예외 → 포괄적인 예외** 순으로 배치 (AD-15 §4).

```
1. Capability:  require_capability(Capability.PRODUCT) — 403 INDUSTRY_NOT_SUPPORTED
2. Owner role:  require_role("owner")                   — 403 FORBIDDEN_ROLE
3. is_active-only short-circuit → soft_delete_product
4. service.update_product(...)
   ├─ ProductNotFoundError                  → 404 PRODUCT_NOT_FOUND
   ├─ ProductTypeHasReferencesError         → 409 PRODUCT_TYPE_HAS_REFERENCES  ← Story 2.3
   ├─ ProductImmutableFieldError            → 403 PRODUCT_IMMUTABLE_FIELD
   └─ (success)                             → 200 + audit row
5. if body.is_active in same call: soft_delete_product (별도 audit)
```

**순서가 중요한 이유**: `ProductImmutableFieldError` (403)는 `code` 변경에만 발생. `product_type`은 별도 가드(`ProductTypeHasReferencesError`, 409)를 거친다. 만약 403이 409보다 먼저 잡히면 type 변경이 무조건 차단되어 PRD §6.1 위반. → 409를 먼저 매칭한다.

---

## §6 audit log shape — `product_type_changed`

AD-2 audit-first, AD-15 §4 self-describing payload (`before` / `after`).

```jsonc
{
  "id": "…uuid…",
  "tenant_id": "…uuid…",
  "actor_id": "…uuid…",
  "action": "product_type_changed",
  "entity_type": "product",
  "entity_id": "…uuid…",
  "payload": {
    "before": { "product_type": "material" },
    "after":  { "product_type": "semi_product" },
    "changed_fields": ["product_type"]
  },
  "occurred_at": "2026-08-01T12:34:56.789Z"
}
```

다른 필드(name, unit, 단가 등)와 동시 변경 시 → **단일** audit row, action은 `product_updated`, `changed_fields = ["name", "product_type", …]`. AC #8.

same-type PATCH(no-op) → audit skip (CR 2.1 lesson).

---

## §7 AC walkthrough (9 acceptance criteria)

| AC | 설명 | 검증 위치 |
|----|------|----------|
| #1 | BOM·수불 참조 N>0 → 409 PRODUCT_TYPE_HAS_REFERENCES | `test_update_product_with_references_raises_typed_error` |
| #2 | 참조 0건 → type 변경 허용 + audit `product_type_changed` (before/after) | `test_update_product_zero_references_allows_change` + `test_update_product_type_change_audit_payload_before_after` |
| #3 | BOM 행 자체는 변경되지 않음 (가드는 카운트만, 행 변경 X) | service.test + handler 흐름 |
| #4 | parent + child 양쪽 모두 카운트 (OR) | `test_update_product_bom_parent_count_counts` + `BOM_REFERENCE_QUERY` SQL |
| #5 | 핸들러가 PATCH 호출에 대해 409 응답 (envelope `{code,message_ko,details,trace_id}`) | `test_handlers_emit_product_type_has_references_409` |
| #6 | 409 응답 메시지 한국어 + BOM/수불 카운트 포함 | `_format_type_references_message_ko` + `test_handlers_message_ko_helper_present` |
| #7 | `code` 변경은 여전히 403 PRODUCT_IMMUTABLE_FIELD (AD-18) | `test_update_product_code_still_immutable` |
| #8 | name + product_type 동시 변경 시 단일 audit row (action=`product_updated`, changed_fields 둘 다) | `test_update_product_mixed_type_change_with_name_emits_one_audit` |
| #9 | same-type PATCH는 BOM count + audit 모두 skip (idempotent no-op) | `test_update_product_same_type_is_noop` |

---

## §8 AD 교차 참조

| AD           | Story 2.3에서 어떻게 적용되는가                                                                 |
|--------------|-----------------------------------------------------------------------------------------------|
| AD-2 (audit-first) | `emit_audit(payload)` 가 `products` UPDATE **이전**에 ledger에 INSERT됨. self-describing payload (`before`/`after`).  |
| AD-3 (RLS)   | `bom_lines`의 RLS 정책이 카운트 쿼리를 자동으로 테넌트 스코프. 별도 WHERE 불필요.                                |
| AD-15        | 에러 envelope `{code:"PRODUCT_TYPE_HAS_REFERENCES", message_ko, details, trace_id}` (한국어 UI). |
| AD-18 (단일 정체성) | `products.id`만 PK. `code`는 항상 immutable (403). `product_type`은 **조건부** mutable (refs==0). |
| AD-11 (layering) | `packages/services/m1_baseline/product_references.py`에 pure helper 위치. UI 한국어 포맷팅은 handler(`apps/api/modules/m1_baseline/handlers.py`)에 위치. |
| AD-5 (engine purity) | `BOM_REFERENCE_QUERY` (SQL 상수) + `count_bom_references` / `count_ledger_references` / `total_references` / `hash_references`. 모두 stdlib-only. |
| AD-8 (money types) | 영향 없음. 본 스토리에서 금액 필드 변경 없음.                                                       |

---

## §9 Epic 5 ledger stub — 확장 지점

`packages/services/m1_baseline/product_references.py`:

```python
LEDGER_REFERENCE_QUERY_STUB: Final[str] = ""  # Epic 5 fold-in marker
def count_ledger_references() -> int: return 0
```

Epic 5 Story 5.x에서:

```python
LEDGER_REFERENCE_QUERY: Final[str] = (
    "SELECT COUNT(*) FROM inventory_movements "
    "WHERE tenant_id = :tenant_id AND product_id = :product_id"
)

def count_ledger_references(*, ledger_count: int) -> int:
    if ledger_count < 0:
        raise ValueError("ledger_count must be >= 0")
    return ledger_count
```

확장 시 service는 `_count_product_references` 안에 ledger SELECT COUNT를 한 줄 추가하고, `total_references(bom_count, ledger_count)`는 시그니처가 그대로 유지된다(파라미터 추가이지만 default 0). 호출부 변경 없음.

---

## §10 File list

### 신규
- `packages/services/m1_baseline/product_references.py` — pure helpers + SQL 상수
- `tests/services/test_product_references.py` — 28 pure-Python 단위 테스트
- `tests/api/test_product_type_change.py` — 14 service-level 단위 테스트 (mock session)
- `tests/integration/test_product_type_change_consistency.py` — 8 Python↔TS 와이어 정합성 테스트

### 변경
- `packages/services/m1_baseline/__init__.py` — re-export (`product_references`)
- `apps/api/modules/m1_baseline/schemas.py` — header docstring에 409 추가
- `apps/api/modules/m1_baseline/services/product_service.py` — type-change 가드 + 새 예외 클래스
- `apps/api/modules/m1_baseline/handlers.py` — 409 매핑 + `_format_type_references_message_ko` 헬퍼
- `apps/web/lib/api-client.ts` — `ProductUpdateRequest.product_type` 옵셔널 추가
- `apps/web/components/m1-baseline/products/ProductFormDialog.tsx` — type 라디오 그리드 edit 모드 활성 + 409 에러 분기

### 변경 없음
- Alembic 마이그레이션 — 스키마 변경 없음 (기존 `idx_bom_lines_parent_tenant` / `idx_bom_lines_child_tenant` 재사용)
- RLS 정책 — `bom_lines`은 Story 2.2에서 이미 테넌트 스코프
