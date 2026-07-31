# costmgr Product / Item Master (M1 — Story 2.1)

> **소속**: Epic 2 / Story 2.1
> **최종 갱신**: 2026-07-31
> **PRD 참조**: §8.M1 (기준정보/품목) · §3.A2 (회계 단위 일치) · §4.1 (업종 4지선다)
> **UX locked-decisions**: Dark MVP · WCAG AA · Professional 톤 · ko-KR (NFR-18)

우리 회사 카탈로그(제품·반제품·원자재·상품·서비스)를 한 화면에서 등록·조회·수정·비활성화하는 화면과 API.
각 유형은 다른 색 배지로 구분되며, 코드는 **테넌트당·유형당 독립적인 시퀀스**로 자동 생성된다.

---

## 1. 데이터 모델 — `products` 테이블 (PRD §8.M1)

`products`는 `tenant_settings.onboarding` 같은 JSONB 네임스페이스가 **아니다**.
많은 행을 가지며, BOM(Story 2.2)·수불부(Epic 5)·계산(Epic 4)에서 FK 참조되므로
독립 테이블로 분리한다 (AD-23: 카디널리티가 낮고 단일 키로 자주 조회되는 설정만 JSONB로).

| 컬럼              | 타입            | 제약 / 비고                                                  |
|------------------|----------------|-------------------------------------------------------------|
| `id`             | UUID PK        | UUID v7 (default `packages.common.uuid7.uuid7()`)           |
| `tenant_id`      | UUID NOT NULL  | UUID v4 — `tenants(id)` ON DELETE CASCADE                  |
| `product_type`   | TEXT NOT NULL  | CHECK in `('product','semi_product','material','goods','service')` |
| `code`           | TEXT NOT NULL  | UNIQUE (`tenant_id`, `code`) — 같은 테넌트 안에서만 유일      |
| `name`           | TEXT NOT NULL  | CHECK 1 ≤ length ≤ 200                                       |
| `unit`           | TEXT NULL      | CHECK length ≤ 20 (예: `EA`, `KG`, `BOX`)                   |
| `unit_cost_krw`  | BIGINT NULL    | AD-8 — 1원 단위 정수                                          |
| `unit_cost_usd`  | NUMERIC(18,2) NULL | AD-8 — 소수점 2자리 (Python `Decimal`, TS `decimal.js`)    |
| `description`    | TEXT NULL      | CHECK length ≤ 2000                                          |
| `is_active`      | BOOLEAN        | DEFAULT true — soft-delete 토글 (AD-2)                       |
| `created_at`     | TIMESTAMPTZ    | DEFAULT now()                                                |
| `updated_at`     | TIMESTAMPTZ    | DEFAULT now()                                                |

인덱스:
- `uq_products_tenant_code` UNIQUE (tenant_id, code) — **AC #3** code uniqueness
- `idx_products_tenant_created_at` (tenant_id, created_at DESC) — list query
- `idx_products_tenant_type_active` (tenant_id, product_type, is_active) — Epic 3 M2 input filter

---

## 2. 유형 × 색 × 라벨 × 코드 prefix (PRD §8.M1)

PRD §8.M1이 명시한 5가지 유형. 색상 매핑은 WCAG 2.1 AA contrast (≥ 4.5:1) 기준을 만족한다.

| 유형 (`product_type`) | 한국어 라벨 | 코드 prefix | 배지 색 (light)             | 사용처                                        |
|-----------------------|------------|------------|----------------------------|----------------------------------------------|
| `product`             | 제품       | `PRD-`     | green  (`#f0fdf4`/`#15803d`)| 전통 개별원가 — BOM·수불부 기반 최종 제품     |
| `semi_product`        | 반제품     | `SEM-`     | purple (`#faf5ff`/`#7e22ce`)| BOM 중간 단계 — 다음 제품의 투입 요소         |
| `material`            | 원자재     | `MAT-`     | blue   (`#eff6ff`/`#1d4ed8`)| BOM 최하위 투입 요소                          |
| `goods`               | 상품       | `GDS-`     | orange (`#fff7ed`/`#c2410c`)| 매매 대상 (제조 X) — 제조+서비스 업종 카탈로그 |
| `service`             | 서비스     | `SVC-`     | gray   (`#f3f4f6`/`#374151`)| ABC 원가 객체 — 서비스 업종의 주력 카탈로그    |

TS 색 매핑은 `apps/web/lib/menu-config.ts::PRODUCT_TYPE_COLOR_VAR` (Story 2.1 T2.3).
Python 색 매핑은 직접 색상 코드를 사용하지 않고 의미 변수(이름)만 노출한다 — 색상 결정은 UI 책임.

---

## 3. 코드 자동 생성 알고리즘

**Per-tenant per-type sequence** — DB-driven, no global state.

```sql
-- 자동 생성 (code 미지정 시)
SELECT COALESCE(MAX(CAST(SUBSTRING(code FROM 5) AS INTEGER)), 0) + 1
  FROM products
 WHERE tenant_id = :tenant_id
   AND product_type = :product_type
   AND code ~ ('^' || :prefix || '-[0-9]+$');  -- 안전망: 잘못된 형식은 무시
```

> **M10 / 오버플로 경고**: `CAST(... AS INTEGER)`는 PostgreSQL 4-byte int 범위(`-2^31..2^31-1`, 즉 ±21억) 내에서만 안전합니다. 시퀀스가 ~21억을 넘는 다중 테넌트 SaaS에서는 `CAST(... AS BIGINT)`로 변경해야 합니다. 현 시점(테넌트당 `product_type`별 1만 미만 가정)에서는 INTEGER가 충분하지만, 마이그레이션 계획(AD-8 footnote 참조)을 Story 4.4+ `cost_pool` 일괄 산정에서 다시 검토합니다.

레이스 컨디션: 동시 POST가 같은 시퀀스를 잡으면 한 건은 UNIQUE 인덱스에서 409를 받는다.
`ProductCodeDuplicateError` (AC #3) 가 그 경우를 흡수한다 — 자동 생성은 fast-path 최적화일 뿐,
유일성은 DB 인덱스가 진실의 원천이다.

### 코드 형식

```
^[A-Z]{3}-\d{4,}$
```

- prefix: 3글자 대문자 (PRD §8.M1 "코드")
- suffix: 4자리 zero-pad (`MAT-0001`), 9999 초과 시 5자리+ 허용 (`MAT-10000`)
- `packages.services.m1_baseline.product_code.generate_next_code` / `parse_code` (순수 함수)
  가 DB / clock / I/O 없이 동작한다 (AD-5 engine purity).

### 수동 입력

`code` 필드를 직접 입력할 수 있다 (재정렬·마이그레이션 용도). 형식이 잘못되면
`InvalidProductCodeError` → 422 `INVALID_PRODUCT_CODE` (AC #1).

---

## 4. 업종 × 유형 capability gate (AC #6 / F-44)

Defense in depth — 메뉴 UI가 유형을 숨겨도 백엔드는 거부한다.

| 업종 (Industry)        | PRODUCT | PRODUCT_MATERIAL | 등록 가능한 유형                  |
|------------------------|---------|------------------|----------------------------------|
| `manufacturing` (①)    | ✓       | ✓                | 5종 모두                         |
| `service` (②)          | ✓       | ✗                | `service`만 (또는 product/goods) |
| `manufacturing_service` (③) | ✓ | ✓              | 5종 모두                         |
| `manufacturing_service_other` (④) | ✓ | ✓        | 5종 모두                         |

- **PRODUCT_MATERIAL** 가 거부되면 `material`/`semi_product` 등록은 403
  `INDUSTRY_NOT_SUPPORTED`로 거부된다 (`ProductCapabilityError`).
- `product`/`goods`/`service`는 PRODUCT_MATERIAL 없이도 등록 가능 — 서비스 업종의 ABC 카탈로그
  또는 제조+서비스 카탈로그 폭넓게 지원용.

자세한 capability matrix: `apps/api/core/capability.py::_INDUSTRY_CAPABILITIES` (Story 2.1 T2.1).

---

## 5. AC 워크스루 — 요청/응답 예시

### AC #1 — `POST /api/v1/baseline/products` (자동 코드 생성)

```http
POST /api/v1/baseline/products
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "product_type": "material",
  "name": "스테인리스 SUS304 1mm",
  "unit": "KG",
  "unit_cost_krw": "12000"
}
```

```http
HTTP/1.1 201 Created
X-Trace-Id: 7d2f-...

{
  "id": "01920b8a-...-v7",
  "tenant_id": "...",
  "product_type": "material",
  "code": "MAT-0001",
  "name": "스테인리스 SUS304 1mm",
  "unit": "KG",
  "unit_cost_krw": "12000",
  "unit_cost_usd": null,
  "description": null,
  "is_active": true,
  "created_at": "2026-07-31T08:00:00.000000+00:00",
  "updated_at": "2026-07-31T08:00:00.000000+00:00"
}
```

`audit_logs`에 `action='product_created'`가 INSERT보다 먼저 기록된다 (AD-2 audit-first).

### AC #3 — 409 PRODUCT_CODE_DUPLICATE

```http
POST /api/v1/baseline/products
{ "product_type": "material", "name": "다른 이름", "code": "MAT-0001" }
```

```http
HTTP/1.1 409 Conflict

{
  "code": "PRODUCT_CODE_DUPLICATE",
  "message_ko": "이미 존재하는 코드입니다",
  "details": { "code": "MAT-0001", "product_id": "01920b8a-..." },
  "trace_id": "7d2f-..."
}
```

UI: 토스트 "이미 존재하는 코드입니다" (AC #3 마지막 bullet).

### AC #4 — `PATCH /api/v1/baseline/products/{id}` 부분 수정

```http
PATCH /api/v1/baseline/products/01920b8a-...
{ "unit_cost_krw": "13000" }
```

`code` / `product_type`을 PATCH 하려고 하면 403 `PRODUCT_IMMUTABLE_FIELD`.

### AC #5 — soft-delete toggle

```http
PATCH /api/v1/baseline/products/01920b8a-...
{ "is_active": false }
```

- 행은 삭제되지 않음 — BOM·수불부 FK 보존 (AD-2)
- 기본 목록(`is_active=true` 필터)에서는 제외됨
- BOM 히스토리(Story 2.2)에는 표시됨
- 비활성 배지: 회색 + 취소선 + "(비활성)" 라벨

### AC #6 — service 업종이 `material` 등록 시도

```http
POST /api/v1/baseline/products
{ "product_type": "material", "name": "..." }
```

```http
HTTP/1.1 403 Forbidden

{
  "code": "INDUSTRY_NOT_SUPPORTED",
  "message_ko": "제조업 업종에서만 등록 가능한 유형입니다",
  "details": {
    "current_industry": "service",
    "requested_type": "material"
  },
  "trace_id": "..."
}
```

---

## 6. AD 크로스레퍼런스

- **AD-1** Modular Monolith + Hexagonal Core — `m1_baseline` 모듈이 `products` 소유.
- **AD-2** Append-only ledger-leaning — `audit_logs` row INSERT BEFORE `products` write;
  soft-delete only.
- **AD-3** Multi-tenant RLS — `tenant_id` from JWT (request body 무시). RLS policy는
  `supabase/policies/0006_products_rls.sql`.
- **AD-5** Cost-engine purity — `product_code.py`는 순수 함수 (no DB / clock / I/O).
- **AD-8** Monetary types — `unit_cost_krw` BIGINT (Python `int`), `unit_cost_usd`
  NUMERIC(18,2) (Python `Decimal`, TS `decimal.js`). `ROUND_HALF_EVEN` (Story 0.4 chunk-B).
- **AD-11** Dependency direction — `apps/api` → `packages/services` → engine.
  `product_code.py`는 `packages/services/m1_baseline/`에 위치.
- **AD-15** Cross-language conventions — DB/Python `snake_case`, TS 변수 `camelCase`,
  PascalCase types, UUID v7 business (`products.id`), UUID v4 tenant (`tenant_id`).
- **AD-18** Single product identity — `products.id` is sole key (BOM·수불부·보고서 공통 참조).
- **AD-23** Tenant settings aggregate — `products`는 별도 테이블 (JSONB 네임스페이스 아님,
  카디널리티가 높고 FK 참조가 잦음).

---

## 7. 변경된 파일

### Backend

- `apps/api/alembic/versions/0006_products_item_master.py` — products 테이블 + 인덱스 3개
- `apps/api/core/db_models.py` — Product ORM 추가
- `apps/api/core/capability.py` — PRODUCT + PRODUCT_MATERIAL enum 추가
- `apps/api/modules/m1_baseline/schemas.py` — ProductCreate/Update/List/Response
- `apps/api/modules/m1_baseline/services/product_service.py` — CRUD + audit-first
- `apps/api/modules/m1_baseline/handlers.py` — 4 routes 추가

### Database / RLS

- `supabase/policies/0006_products_rls.sql` — SELECT (모든 역할) + INSERT/UPDATE (owner only)
  - **AD-10 / T4.2**: 백엔드는 `apps/api/core/capability.py::require_role("owner")` 의존성으로 동일 규칙을 강제 (RLS만으로는 토큰 변조 우회 시 방어선 부족)

### Frontend

- `apps/web/lib/server-api.ts` — `fetchProductsServerSide`
- `apps/web/lib/api-client.ts` — `fetchProducts`/`getProduct`/`createProduct`/`updateProduct`
- `apps/web/lib/menu-config.ts` — ProductType/PREFIX/LABEL_KO/COLOR_VAR/INDUSTRY_ALLOWED
- `apps/web/hooks/useProducts.ts` — list + mutations
- `apps/web/components/m1-baseline/products/ProductTypeBadge.tsx` — colored badge
- `apps/web/components/m1-baseline/products/ProductFormDialog.tsx` — create/edit dialog
- `apps/web/components/m1-baseline/products/ProductListClient.tsx` — table + filter chips
- `apps/web/app/[locale]/(dashboard)/m1-baseline/products/page.tsx` — Server Component entry

### Pure helpers / packages

- `packages/services/m1_baseline/__init__.py` — re-exports
- `packages/services/m1_baseline/schemas.py` — `ProductType` enum + prefix/label maps
- `packages/services/m1_baseline/product_code.py` — pure code generation

### Tests

- `tests/services/test_product_code.py` — 23 pure-function tests
- `tests/api/test_products.py` — 23 typed-exception contract tests
- `tests/api/test_product_capability.py` — 22 capability matrix parametrize
- `tests/integration/test_product_type_consistency.py` — 7 TS↔Python drift
- `tests/rls/test_products_isolation.py` — 6 RLS isolation tests (CI-only)

---

## 8. 후속 스토리 (참조)

- **Story 2.2** BOM Matrix — `product_type IN ('material','semi_product')` 행을 BOM 자식으로 투입.
  `products.id` (UUID v7) 로 FK. 코드 변경 불가 (AC #4) 가 BOM referential drift를 차단.
- **Story 2.3** Item Type Change Integrity Guard — `product_type` 변경 시 BOM / 수불부
  / 비용 계산 참조 일관성 검사. 현재는 403 PRODUCT_IMMUTABLE_FIELD로 차단.
- **Story 3.x** Epic 3 M2 Input — `is_active=true` AND `product_type IN ('material','semi_product','product')`
  행을 계산 입력 드롭다운에 노출 (F-44 / A11 CCR).
- **Story 6.1** Report Library — `products.id` 가 보고서 dimension으로 등장.
