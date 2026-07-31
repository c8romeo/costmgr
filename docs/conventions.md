# costmgr Conventions — Canonical Rules

> 모든 언어·모든 레이어에서 따라야 할 단일 규칙 표. PR 머지 전 `make lint-conventions`가 통과해야 한다.
>
> 출처: ARCHITECTURE-SPINE §AD-1 (Modular Monolith), §AD-8 (Monetary Types), §AD-15 (Cross-language Conventions), §AD-23 (Tenant Settings Aggregate), §AD-24 (Period Keys), §AD-2 (Append-only Ledger).
>
> 위반 시 CI 단계가 명확한 메시지로 실패한다:
> `CONVENTION_VIOLATION: <file>:<line> uses <violation> which violates AD-<N>. Use <expected> instead.`

---

## §0 M0 도메인 enum (Story 1.1)

`tenant_settings.onboarding` JSONB 네임스페이스에 저장되는 값들의
단일 진실 공급원은 `packages/services/m0_onboarding/industry_menu.py`와
그 TypeScript 미러 `apps/web/lib/menu-config.ts`이다.

### §0.1 Industry (PRD §4.1 4지선다)

| enum value (snake_case) | 한글 라벨 | 비고 |
|---|---|---|
| `manufacturing` | ① 제조업 | 전통 개별원가 엔진 |
| `service` | ② 서비스업 | ABC 엔진 |
| `manufacturing_service` | ③ 제조+서비스 | 두 엔진 병행 |
| `manufacturing_service_other` | ④ 제조+서비스+기타 | 두 엔진 + 격리 버킷 |

### §0.2 Industry → MenuItem 매핑 (PRD §8.M0(a))

| Industry | 노출되는 MenuItem |
|---|---|
| `manufacturing` | PRODUCT, BOM, OPENING_INVENTORY, INVENTORY_LEDGER, ACCOUNT, DEPARTMENT, CUSTOMER, AI_EXTRACT, SIMULATION, BUDGET, REPORT, CLOSE, ACCOUNT_MGMT |
| `service` | COST_POOL, ACTIVITY, DRIVER, ACCOUNT, DEPARTMENT, CUSTOMER, AI_EXTRACT, SIMULATION, BUDGET, REPORT, CLOSE, ACCOUNT_MGMT |
| `manufacturing_service` | 위 13개 + SEGMENT_SPLIT (BOM·기초재고·수불부 + 원가풀·활동·동인 동시 노출) |
| `manufacturing_service_other` | `manufacturing_service`와 동일 |

### §0.3 규칙

- Industry **enum value는 snake_case** (AD-15). 한글 라벨은 별도 dict (`INDUSTRY_LABEL_KO`)에서 관리.
- MenuItem **enum value는 한글 UI 라벨** (그 자체가 화면에 렌더링됨). enum NAME은 PascalCase.
- `INDUSTRY_MENU_MAP`은 두 곳에 존재: Python (SSOT) + TypeScript (mirror). 드리프트는
  `tests/integration/test_menu_config_consistency.py`로 강제 차단.

### §0.4 Wizard 필드 포맷 (Story 1.2)

`tenant_settings.onboarding.*` 의 추가 필드는 Pydantic (Python) + JSON Schema (TS)에서 동일한 정규식으로 검증한다.

| 필드 | 포맷 | 검증 | 출처 |
|---|---|---|---|
| `fiscal_year_start` | `YYYY-MM` (월 ∈ 01..12) | `r"^\d{4}-(0[1-9]|1[0-2])$"` | A1, AD-24 — 회계연도 axiom, typed period-key prefix |
| `currency` | enum `KRW` \| `USD` | `Literal["KRW","USD"]` (Pydantic) + `enum` (TS) | A6, AD-8 — monetary type 선택 |
| `language` | enum `ko-KR` (MVP only) | `Literal["ko-KR"]` | NFR-18 — ko-KR MVP lock |
| `allocation_criteria.<key>.count` | `int >= 1` | `Field(ge=1)` | PRD §8.M0(b) — ≥1행 등록 시 완료 |

**Industry-conditional completion (PRD §8.M0(b))** — `direct_indirect` · `fixed_variable` 은 모든 업종에서 필수. `drivers` 는 `manufacturing` 업종에서만 건너뜀 (A11 — ABC engine 없음).

**A7 전진법 (lock)** — `fiscal_year_start` · `currency` 는 첫 계산 (`onboarding.last_calc_date` 세팅) 후 변경 불가. 7일 유예는 industry 와 동일 패턴 (Story 1.1).

자세한 도메인 의미는 `docs/onboarding-schema.md` + `docs/onboarding-flow.md`.

### §0.5 ProductType (PRD §8.M1 — Story 2.1)

`products.product_type` 컬럼의 단일 진실 공급원은
`packages/services/m1_baseline/schemas.py::ProductType` 와 그 TypeScript 미러
`apps/web/lib/menu-config.ts::PRODUCT_TYPE_VALUES` 이다.

| enum value (snake_case) | 한국어 라벨 | 코드 prefix | 비고 |
|---|---|---|---|
| `product` | ① 제품 | `PRD-` | 전통 개별원가 — BOM·수불부 기반 |
| `semi_product` | ② 반제품 | `SEM-` | BOM 중간 단계 |
| `material` | ③ 원자재 | `MAT-` | BOM 최하위 투입 요소 |
| `goods` | ④ 상품 | `GDS-` | 매매 대상 (제조 X) |
| `service` | ⑤ 서비스 | `SVC-` | ABC 원가 객체 |

**Industry-conditional subset (AC #6 / F-44)** — `service` 업종은 `material`/`semi_product` 등록
시 403 `INDUSTRY_NOT_SUPPORTED`로 거부된다. PRODUCT_MATERIAL capability 게이트.
세부 matrix: `docs/product-item-master.md#4-업종--유형-capability-gate-ac-6--f-44`.

**규칙:**
- `product_type` enum value는 snake_case (AD-15). 한글 라벨은 `PRODUCT_TYPE_LABEL_KO` dict.
- 코드 prefix는 enum value와 다르다 (snake_case → noisy prefix). 3글자 대문자.
- `code` 포맷: `^[A-Z]{3}-\d{4,}$`. 자동 생성은 `product_code.generate_next_code()` (pure).
- `code` / `product_type` 은 생성 후 immutable (AC #4 — BOM·수불부 FK 보존).
- TS mirror의 드리프트는 `tests/integration/test_product_type_consistency.py`로 강제 차단.

---

## §1 Naming

| 위치 | 규칙 | 예시 | 비고 |
|---|---|---|---|
| SQL (테이블·컬럼·인덱스) | `snake_case` | `tenant_settings`, `audit_logs` | Alembic 마이그레이션 포함 |
| Python (모듈·함수·변수) | `snake_case` | `format_krw`, `tenant_id` | Pydantic 모델 필드도 snake_case |
| Python (클래스·Pydantic 모델·타입 별칭) | `PascalCase` | `class AuditLog(BaseModel)` | NewType도 PascalCase |
| Next.js 라우트 (URL) | `kebab-case` | `/api/v1/cost-reports` | `app/<route>/page.tsx` |
| React/TS 컴포넌트 타입 (interface/type) | `PascalCase` | `interface MoneyFormatter` | ESLint `naming-convention`이 강제 |
| TS 변수·함수 | `camelCase` | `formatKRW`, `tenantId` | `formatKRW`처럼 약어는 모두 대문자 |
| TS boolean 변수 | `is/has/can/should` 접두 | `isLoading`, `hasPermission` | |

### 위반 예시

```python
# ❌ AD-15 violation: camelCase 컬럼
op.add_column("users", sa.Column("firstName", sa.Text))

# ✅ AD-15 compliant: snake_case
op.add_column("users", sa.Column("first_name", sa.Text))
```

```typescript
// ❌ AD-15 violation: snake_case 인터페이스
interface money_formatter { format(krw: KRW): string }

// ✅ AD-15 compliant: PascalCase 인터페이스
interface MoneyFormatter { format(krw: KRW): string }
```

---

## §2 Time

| 위치 | 규칙 | 비고 |
|---|---|---|
| DB (TIMESTAMPTZ) | UTC, ISO-8601 | `TIMESTAMPTZ NOT NULL DEFAULT now()` |
| Python (datetime) | `datetime` aware, UTC | `datetime.now(UTC)` 사용 |
| TS 표시 | KST, `next-intl` `ko-KR` | UI에 표시될 때만 KST 변환 |
| API 응답 | ISO-8601 UTC 문자열 | `"2026-07-25T14:32:11.523Z"` |
| 마이크로초 정밀도 | 옵션, 필요 시 `TIMESTAMPTZ(6)` | audit 로그 등 |

### 위반 예시

```typescript
// ❌ AD-15 violation: time/datetime import
import time from "time";
import { Datetime } from "datetime";

// ✅ AD-15 compliant: ISO-8601 string or Temporal
const now = new Date().toISOString();
```

---

## §3 Identity

| 엔티티 | 규칙 | 비고 |
|---|---|---|
| 비즈니스 엔티티 (products, BOM rows, …) | UUID v7 | 시간 정렬 가능, 분산 환경 친화 |
| `tenant_id` | **UUID v4** | **AD-15 variance** — Supabase Auth 호환 (자세한 결정은 [`AD-15-tenant-id-variance.md`](./architecture-decisions/AD-15-tenant-id-variance.md)) |
| `user_id` | UUID v4 | Supabase Auth `auth.users.id` |
| 마이그레이션 revision | `NNNN_descriptive_slug` | `0001_tenants_users_memberships_settings` |

### ID 생성

- Python: `uuid.uuid7()` (Python 3.14+, 현재 미도입) → 현 타겟 3.12에서는 `uuid.uuid4()` (또는 `uuid6/7` backport 라이브러리). **`tenant_id`/`user_id`는 v4 고정** (AD-15 variance참조).
- DB: `gen_random_uuid()` (pgcrypto) — 현재 일관되게 v4. v7 도입 시 마이그레이션 추가
- TS: `crypto.randomUUID()` (브라우저/Node 19+)

---

## §4 Errors

모든 에러 응답은 다음 구조를 따른다 (AD-2 audit, AD-15):

```python
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    code: str              # 안정된 머신 코드: "TENANT_NOT_FOUND", "RLS_DENIED"
    message_ko: str        # 한국어 사용자 메시지 (UX locked: ko-KR)
    details: dict          # 추가 컨텍스트 (선택)
    trace_id: str          # OpenTelemetry / structlog 추적 ID
```

| 규칙 | 설명 |
|---|---|
| `code` | 대문자 스네이크, 변경 시 deprecation |
| `message_ko` | 사용자에게 그대로 노출 — UX 팀이 승인한 한국어만 |
| `trace_id` | structlog 컨텍스트의 `trace_id`와 동일 |
| `details` | PII 금지 (tenant_id, user_id 정도만 허용) |

### 로그

- Python: `structlog` JSON 출력 (KR: `code`, `message_ko`, `trace_id`)
- TS: `pino` JSON 출력 (client-side은 `pino/browser`)

---

## §5 Money (AD-8 — 매우 엄격)

### 저장

| 통화 | DB 타입 | 예시 |
|---|---|---|
| KRW | `BIGINT` (1원 정밀도) | `unit_cost_krw BIGINT NOT NULL` |
| USD | `NUMERIC(18,2)` | `unit_cost_usd NUMERIC(18,2) NOT NULL` |

### 코드

| 언어 | KRW | USD |
|---|---|---|
| Python | `int` (`NewType("KRW", int)`) | `Decimal` (`NewType("USD", Decimal)`) |
| TypeScript | `bigint` (`type KRW = bigint`) | `string` (decimal.js serialized) |

**절대 금지:**
- Python: `float` (cost path에서) — `Decimal` 또는 `int`만
- TS: `number` (display code에서) — `bigint` 또는 `string`만
- 마이그레이션: `sa.Float` (money 컬럼) — `BigInteger` 또는 `Numeric(18,2)`

### 변환

```python
from apps.api.core.money import KRW, USD, to_krw, to_usd

krw: KRW = to_krw(1_500_000)         # KRW(1500000)
usd: USD = to_usd(Decimal("1234.5"))  # USD('1234.50')
```

```typescript
import { type KRW, type USD, toKRW, toUSD, formatKRW } from "@/lib/money";

const krw: KRW = toKRW(1_500_000);          // 1500000n
const usd: USD = toUSD("1234.5");            // "1234.50"
formatKRW(krw);                              // "1,500,000원"
```

자세한 결정 근거는 [`AD-8-money-types-decision.md`](./architecture-decisions/AD-8-money-types-decision.md).

### 사용처 — `products` 테이블 (Story 2.1, PRD §8.M1)

| 컬럼 | 통화 | DB 타입 | Python | TS wire |
|---|---|---|---|---|
| `products.unit_cost_krw` | KRW | `BIGINT NULL` (CHECK `>= 0`) | `int \| None` | `string \| null` |
| `products.unit_cost_usd` | USD | `NUMERIC(18,2) NULL` (CHECK `>= 0`) | `Decimal \| None` | `string \| null` |

- **NULL 허용** — 한 통화만 등록된 테넌트 (KRW만 또는 USD만). `tenant_settings.onboarding.currency` 와 무관하게 두 컬럼 모두 보유 (A2 회계 단위 일치).
- **CHECK `>= 0`** — 음수 단가 거부. 0은 허용 (무료 원자재 / 시식용 반제품).
- **TS wire shape** — JSON.stringify가 BigInt를 직접 직렬화하지 못해 `string`으로 보낸다. 클라이언트는 `BigInt(value)` 로 복원.
- 자세한 사용 예시: `docs/product-item-master.md`.

---

## §6 Period Keys (AD-24)

| 종류 | 형식 | 예시 |
|---|---|---|
| Real (실측 월) | `YYYY-MM` | `2026-07` |
| Virtual (예산 시뮬레이션) | `YYYY-MM#B<n>` | `2026-07#B1`, `2026-07#B2` |

- `#B<n>`은 같은 real 월 안에서 여러 가상 예산을 구분할 때 사용 (Story 8.1).
- 비교 시 `period_key` 전체를 문자열로 비교.

---

## §7 Money Formatting (Display only)

| 헬퍼 | 입력 | 출력 |
|---|---|---|
| `format_krw(KRW(1_000_000))` | Python `int` | `"1,000,000원"` |
| `format_usd(USD("1000.5"))` | Python `Decimal` | `"$1,000.50"` |
| `formatKRW(1_000_000n)` | TS `bigint` | `"1,000,000원"` |
| `formatUSD("1000.5")` | TS `string` | `"$1,000.50"` |

**규칙:**
- display 로직에서는 `Intl.NumberFormat` 인라인 사용 금지 — `formatKRW`/`formatUSD`를 통해서만 (locale 변경 시 단일 진입점).
- TS는 `BigInt` 산술을 사용 (Number 오버플로 방지).

---

## §8 Forbidden Patterns (요약)

| 패턴 | 금지 이유 |
|---|---|
| `float` (Python cost path) | IEEE 754 정밀도 손실 |
| `number` (TS money) | `2^53 - 1` 오버플로, 반올림 손실 |
| `import time` / `from datetime import datetime as Datetime` (TS) | AD-15 시간 규칙 위반 |
| `camelCase` SQL 컬럼 | AD-15 명명 위반 |
| `sa.Float` (money column) | AD-8 위반 — `BigInteger`/`Numeric` 사용 |
| `Intl.NumberFormat` 인라인 (display) | §7 위반 — `formatKRW`/`formatUSD` 사용 |
| Pydantic in `packages/cost_engine/core/` | AD-1 위반 — 순수 Python stdlib only |
| `import-linter` 회피 (예: `cost_engine`이 `apps.api` import) | AD-11 위반 |

---

## §9 Enforcement

| 검사 | 위치 | 실행 |
|---|---|---|
| Python 명명/import/style | `ruff` (root `pyproject.toml`) | `uv run ruff check` |
| Python `float` money (engine) | `scripts/check_money_types.py` | `make lint-conventions` |
| 마이그레이션 `camelCase` | `scripts/check_migration_naming.py` | `make lint-conventions` |
| 마이그레이션 `Float` (money) | `scripts/check_migration_money.py` | `make lint-conventions` |
| TS 명명/restricted types | ESLint (root `.eslint.config.mjs`, flat config) | `pnpm lint:conventions` |
| TS `number` (money) | ESLint `no-restricted-types` (apps/web override) | `pnpm lint:conventions` |

**PR 머지 차단:** `lint-conventions` 잡 실패 → merge 차단 (Story 0.4 §8).