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

### §0.5 Verification rule purity gate (Story 4.3)

AD-5 purity invariant은 engine (`packages/cost_engine/core/`) 뿐 아니라 **verification rule kernels** (`apps/api/modules/m3_calculate/services/rules/*.py`) 에도 동일하게 적용된다. 4 rule kernels (V1 / V4 / V7 / V8) + `protocol.py` + `verification_runner.py` 모두 다음 3중 게이트를 통과해야 한다:

1. **`ruff`** (root `pyproject.toml`) — 코드 스타일 + `[tool.ruff.lint]` 규칙
   - `apps/api/modules/m3_calculate/services/rules/*.py`: `ARG002`, `A002` 명시적 ignore (Protocol 시그니처 보존 — `applies_to(*, industry: str)` + `check(self, input: RuleInput)`)
2. **`import-linter`** (root `pyproject.toml`) — `apps/api/**/*.py` 화이트리스트 외의 core import 차단
   - `tests/architecture/test_api_calls_only_ports.py` `CORE_IMPORT_ALLOWLIST`에 5개 rules 파일 + verification_runner 추가됨
3. **AST 가드** (`tests/cost_engine/test_verification_rules.py`) — `forbidden_imports` (sqlalchemy · psycopg · asyncpg · fastapi · starlette · httpx · time · datetime.now · random · secrets) 가 rule kernel 소스에 등장하면 즉시 fail

**드리프트 강제:** `tests/web/test_m3_verdict_parity.py` (20 cross-lang cases) — `apps/web/lib/m3-verdict.ts` TS mirror의 enum members / industry firing matrix / top_failure invariant / UI failure code 매핑을 Python canonical schema와 대조. Story 4.4 Industry canonical names parity 추가 (`manufacturing_service`, `manufacturing_service_other`).

**Story 4.4 V8 byte-identical CI gate (mandatory, no skip):**
`tests/regression_v8/test_regression_v8_fixtures.py` 는 `@pytest.mark.engine` + `@pytest.mark.v8_regression` 둘 다 marking. 12 fixture 매트릭스 (4 industries × 3 baseline shapes = b-small/b-standard/b-complex) 의 byte-identical 골든 vs engine 비교를 강제한다. CI / dev `pytest` 기본 호출이 자동 포함 (`--ignore`/`--deselect` 금지). `STORY_4_4_FILL_POINT` marker (`packages/cost_engine/tests/regression_v8/__init__.py::V8_FIXTURE_COUNT == 12`) 가 0 → 12 로 lock 되어야 한다.

- `verify_v8_golden_match` audit action (Story 4.4 forward-lock) — `verification_log` table 의 `action` column literal 에 추가됨. CR 1.1 audit-first 원칙 유지.

위반 시 CI 단계가 명확한 메시지로 실패한다:

```
CONVENTION_VIOLATION: <file>:<line> violates AD-5 purity gate.
  Rule kernel MUST NOT import DB / web / clock / random layers.
```

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

### §0.6 BOM Parent/Child Type Rules (PRD §6.1 — Story 2.2)

BOM 행렬은 `packages/services/m1_baseline/schemas.py::BOMParentType` /
`BOMChildType` frozenset (단일 진실 공급원) 으로 강제된다. TS mirror는
`apps/web/lib/bom-validation.ts::BOMParentTypes` / `BOMChildTypes`. 두 곳 모두
정적 const set 이라 변경하면 빌드 단계에서 컴파일 에러로 드러난다.

| 역할 | 허용 `product_type` | 비고 |
|---|---|---|
| BOM parent (모품목) | `product`, `semi_product` | 최종 제품 / BOM 중간 단계만. `material`/`goods`/`service` 는 422 `BOM_INVALID_PARENT_TYPE` |
| BOM child (자품목) | `material`, `semi_product` | BOM 의 최하위 투입 요소 / 중간 단계. `product`/`goods`/`service` 는 422 `BOM_INVALID_CHILD_TYPE` |

`BOMParentType` / `BOMChildType` frozenset 자체에는 derived 검사만 포함된다.
**TS mirror의 드리프트는 `tests/integration/test_bom_validation_consistency.py` 로 강제 차단**
(13 tests — Story 2.2 T6.5).

자세한 도메인 의미: `docs/bom-matrix.md`.

### §0.7 AD-20 State Machine — Calc State Transition (PRD §11, Story 4.3)

`POST /api/v1/calc` 의 state 전이는 **AD-20 invariant** 으로 강제된다. `verification_status` 와 `state` 의 매핑:

| `state` | 진입 조건 | 진입 후속 처리 | 비고 |
|---|---|---|---|
| `draft` | engine `compute_period_cost` 의 return | service layer 가 받음 (Story 4.2) | engine returns ONLY `draft` (AD-22) |
| `verified` | `verdict.verification_status == 'passed'` AND 모든 fired rule `status == 'passed'` | `INSERT INTO fiscal_period_snapshots (state='verified')` + `calc_log(action='compute')` + `verification_log(action='verification_passed')` | service-only transition |
| `committed` | Epic 11 M11 reversal-pending → 전표 확정 | M11 owner | **본 스토리 범위 외** — Epic 11 |
| `reversed` | M11 reversal | M11 owner | **본 스토리 범위 외** — Epic 11 |

**AD-20 외부 응답 invariant** — `verification_status` 는 외부에 `Literal["passed", "failed"]` 만 노출. `'pending'` 은 **calc 내부 transient** 으로만 존재 (engine draft → verification runner → state transition 의 중간 상태). Pydantic Literal type + TS `VerificationStatus` mirror 모두 `'pending'` 부재 검증 (`tests/web/test_m3_verdict_parity.py::test_pending_status_rejected_in_python` + `test_pending_status_rejected_in_ts`).

**AD-12 ordering invariant** — VerificationRunner가 `_VERIFICATION_RULES` tuple을 V1 → V4 → V7 → V8 순서로 iterate. `item.status == 'failed'` 시 `break` (후속 검증 abort). `verifications[]` 응답에는 발동된 rule만 포함 (applies_to=False → silent skip → array 미포함).

**드리프트 강제:** `tests/integration/test_verification_order.py` (12 cases) + `tests/cost_engine/test_verification_rules.py` (22 cases) + `tests/web/test_m3_verdict_parity.py` (20 cases).

자세한 도메인 의미는 `docs/cost-engine.md#verification-envelope-v1v4v7v8`.

### §0.8 품목 유형 변경 — 참조 검증 (PRD §6.1 — Story 2.3)

`product_type`은 변경 가능하지만 **조건부**: BOM + 수불 참조 0건일 때만 허용. 참조가 1건이라도 있으면
PATCH는 409 PRODUCT_TYPE_HAS_REFERENCES로 거부된다 (RFC 7231 §6.5.8 — state conflict).

**엄격한 의미의 immutable**: `code`만. (AD-18 `ProductImmutableFieldError` → 403 PRODUCT_IMMUTABLE_FIELD)

**조건부 가변**: `product_type`. 검증은 service 레이어에서:

```python
bom_count = (SELECT COUNT(*) FROM bom_lines
              WHERE tenant_id = :tenant_id
                AND (parent_product_id = :product_id OR child_product_id = :product_id))
ledger_count = 0  # Epic 5 stub — packages.services.m1_baseline.product_references.LEDGER_REFERENCE_QUERY_STUB
if (bom_count + ledger_count) > 0:
    raise ProductTypeHasReferencesError(...)  # 409 envelope w/ counts in details
```

pure helper는 `packages/services/m1_baseline/product_references.py`에 위치
(AD-5 stdlib-only). 단일 진실 공급원:
- `BOM_REFERENCE_QUERY: Final[str]` (bind-param SQL)
- `LEDGER_REFERENCE_QUERY_STUB: Final[str] = ""` (Epic 5 fold-in marker)
- `count_bom_references` / `count_ledger_references` / `total_references` / `hash_references`

TS 와이어 형식 (`apps/web/lib/api-client.ts::ProductUpdateRequest`)도 `product_type?` 옵셔널
필드를 노출해 PATCH body에 포함시킬 수 있도록 한다 — 핸들러가 가드.

드리프트 차단 (Story 2.3 T4.1): `tests/integration/test_product_type_change_consistency.py`
(8 tests) — handlers.py가 409 emit, TS `ProductUpdateRequest`가 `product_type?` 노출,
schema stable field set을 핀 고정.

자세한 도메인 의미: `docs/item-type-change.md`.

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

### §5.1 Ratio (AD-8 확장 — Story 2.2)

BOM 행의 `ratio` (비중 %) 는 money 가 아니지만 **Money 와 동일한 정밀도 보장**이 필요하다
(계산 시 합 100.0000 invariant). 따라서 `NUMERIC(7,4)` + `ROUND_HALF_EVEN`과 동일한
규약을 따른다.

| 항목 | 값 |
|---|---|
| DB 타입 | `NUMERIC(7,4)` (확장 고려: 8,4) |
| DB CHECK | `0 < ratio <= 100` |
| Python | `Decimal` (NewType 권장: `NewType("Ratio", Decimal)`) |
| TypeScript | `string` (decimal.js serialized) |
| Wire 정규식 | `^\d{1,3}\.\d{4}$` 또는 `^\d{1,3}$` (소수점 0~4자리) |
| TS mirror | `apps/web/lib/bom-validation.ts` — `quantizeRatio` 가 `Decimal.ROUND_HALF_EVEN` 으로 4자리 truncation |

**절대 금지:**
- Python: `float` (TS-side) — `Decimal` 만
- TS: `number` — `string` 만 (JSON 직렬화 보존)
- 마이그레이션: `sa.Float` — `Numeric(7,4)` 사용

**드리프트 강제:** `tests/integration/test_bom_validation_consistency.py` 의
`test_sum_ratios_python_matches_ts_quantization` 등이 Python의 `ROUND_HALF_EVEN`과
TS의 `Decimal.ROUND_HALF_EVEN`이 동일 결과 (`33.33335 → 33.3334`) 임을 검증.

자세한 도메인 의미: `docs/bom-matrix.md#3-100-불변식-a6-axiom-derived-at-read-time`.

---

## §6 Period Keys (AD-24)

### §6.1 `POST /api/v1/calc` period_key validation (Story 4.2)

The `CalcRequest.period_key` field validates against a strict regex:

- Pattern: `^\d{4}-(0[1-9]|1[0-2])$`
- Real fiscal periods ONLY — virtual `YYYY-MM#B<n>` keys are NOT
  accepted by the calc endpoint in Story 4.2 (virtual keys land in
  Story 8.1 with the simulation feature).
- Pydantic v2 `pattern=` parameter enforces at request body level
  → 422 INVALID_PAYLOAD on mismatch.
- Same regex mirrored in `packages.cost_engine.core.period_cost`
  (`_PERIOD_KEY_PATTERN`) for engine defense-in-depth.

### §6.2 Engine period_key validation

The engine also validates `period_key` on `MonthlyInput` and
`Baseline.fiscal_period` — engine-side guard raises `ValueError`
which the orchestrator catches → 500 INTERNAL_ERROR via
`CalcServiceError` wrapper (handler-level typed envelope).

---

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
| engine 이 `state="verified"` / `"committed"` / `"reversed"` 반환 | AD-22 위반 — engine 은 `state="draft"` ONLY (service layer 가 transition 소유) |
| engine 에 `sqlalchemy` / DB driver import | AD-22 / AD-5 위반 — engine NEVER writes to DB |

---

## §9 Enforcement

| 검사 | 위치 | 실행 |
|---|---|---|
| Python 명명/import/style | `ruff` (root `pyproject.toml`) | `uv run ruff check` |
| Python `float` money (engine) | `scripts/check_money_types.py` | `make lint-conventions` |
| 마이그레이션 `camelCase` | `scripts/check_migration_naming.py` | `make lint-conventions` |
| 마이그레이션 `Float` (money) | `scripts/check_migration_money.py` | `make lint-conventions` |
| Engine IO/DB/clock import (AD-5) | `tests/cost_engine/test_no_io_imports.py` AST guard | `uv run pytest tests/cost_engine/` |
| Engine AD-22 boundary (state, sqlalchemy, reversal) | `tests/cost_engine/test_no_io_imports.py` (4 cases) | `uv run pytest tests/cost_engine/` |
| Engine ↔ Adapter import-linter | `import-linter` (root `pyproject.toml`) | `uv run lint-imports` |
| Capability matrix drift | `tests/integration/test_capability_consistency.py` | `uv run pytest tests/integration/` |
| V8 regression contract (placeholder) | `tests/cost_engine/test_regression_v8_placeholder.py` | `uv run pytest tests/cost_engine/` |
| V8 골든 byte-identical CI gate | `tests/regression_v8/test_regression_v8_fixtures.py` (`@pytest.mark.v8_regression` — mandatory, no skip) | `uv run pytest tests/regression_v8/` |
| TS 명명/restricted types | ESLint (root `.eslint.config.mjs`, flat config) | `pnpm lint:conventions` |
| TS `number` (money) | ESLint `no-restricted-types` (apps/web override) | `pnpm lint:conventions` |

**PR 머지 차단:** `lint-conventions` 잡 실패 → merge 차단 (Story 0.4 §8).

---

## §10 Audit Actions (A5 — 단일 진실 공급원)

CR 1.1 lesson (Epic 1·2·3·4 4번째 epic 연속 재발) — audit log의 `action` 필드가 free-form string literal로 모듈 곳곳에 분산되어 4번 연속 drift 발생. A5 pin-point에서 `apps/api/core/audit_action.py`가 **단일 진실 공급원 (SSOT)** 으로 강제된다.

### §10.1 ActionClass / AuditAction

| ActionClass | 대상 (target_table) | AuditAction Literal | 비고 |
|---|---|---|---|
| `TENANT_SETTINGS` | `tenant_settings` | `industry_selected`, `industry_change_initial`, `onboarding_field_saved`, `allocation_criterion_saved`, `company_subblock_promoted` | F-36 inversion lesson (Story 1.1) |
| `SERVICE_ROLE` | `service_role` (audit_logs) | `service_role_bypass` | AD-2 audit-first |
| `UPLOADED_DOCUMENT` | `uploaded_documents` | `document_uploaded`, `document_reprocess_requested`, `document_retention_soft_deleted` | Story 1.3 |
| `INPUT_DRAFT` | `input_drafts` | `input_draft_confirm`, `input_draft_reject` | f-string interpolation → typed Literal 분리 |
| `PRODUCT` | `products` | `product_created`, `product_updated`, `product_type_changed`, `product_soft_deleted`, `product_reactivated` | conditional ternary (Story 2.3) |
| `BOM_LINE` | `bom_lines` | `bom_set`, `bom_cleared` | bulk replace (Story 2.2) |
| `MONTHLY_INPUT_ROW` | `monthly_input_rows` | `monthly_input_row_created`, `monthly_input_row_updated`, `monthly_input_row_deleted` | save_row + update_row PATCH 동일 action |
| `MONTHLY_INPUT_PERIOD` | `monthly_input_periods` | `monthly_input_mode_changed` | 다른 테이블 (per-row 아님) |
| `CALC_LOG` | `calc_log` (별도 테이블) | `compute`, `idempotent_skip`, `rollback` | DB CHECK 1st (0012) |
| `VERIFICATION_LOG` | `verification_log` (별도 테이블) | `verification_passed`, `verification_failed`, `verification_skipped`, `verify_v8_golden_match` | DB CHECK 2nd (0013) + Story 4.4 forward-lock |
| `INVENTORY_LEDGER` | `inventory_ledger` (Epic 5) | `inventory_ledger_event_appended`, `inventory_ledger_event_rejected`, `inventory_ledger_reversal_requested`, `inventory_ledger_reversal_logged`, `inventory_ledger_reversal_rejected`, `inventory_ledger_reprojection_triggered` | Story 5.2 — append-only invariant + 3중 방어 + Epic 11 forward-fill |
| `REVERSAL_LOG` | `reversal_log` (Epic 11) | (Epic 11 spec 진입 시 확정) | placeholder slot |

### §10.2 규칙

- **모든 audit log write는 `emit_audit_typed()` 또는 typed service-layer writer** (`CalcOrchestrator._write_calc_log`, `_write_verification_log`) 를 통해 호출. legacy `emit_audit()` 직접 호출 **금지**.
- **ActionClass는 호출 시점에 명시** — `target_table` 파라미터로 target_table을 추론하는 패턴 금지. registry가 라우팅 단일 결정.
- **tuple `(ActionClass, action)` → `AuditLogType` 1:1 매핑** — 변경 시 `_ActionRegistry._REGISTRY` 에서 단일 edit. 분기 로직 복수 정의 금지.
- **payload 내 `reason` field는 action literal과 분리** — compound discriminator 역할 (예: `industry_selected_initial` / `industry_change_within_grace`). action은 high-level verb.
- **DB CHECK constraint = production gate** — 신규 ledger (verification_log, inventory_ledger, reversal_log) 추가 시 Alembic에서 `CHECK (action IN (...))` 강제. registry와 동등성 유지 (Phase 4 3-way drift detector).
- **m4_inventory / m11_reversal service-layer writer** — `emit_audit_typed()`는 `audit_logs`만 라우팅. inventory_ledger / reversal_log는 각 service가 직접 typed writer 소유 (orchestrator 책임 분리).

### §10.3 위반 시

- `tests/services/test_audit_action_centralization.py` (AST-grep `emit_audit(` hitcount = 0) — **CI 게이트** (mandatory, no skip).
- `tests/integration/test_audit_action_consistency.py` (3-way drift detector: registry vs DB CHECK vs call sites) — Alembic 0013+ DB CHECK constraint 변경 시 자동 검증.
- 위반 시: `legacy emit_audit( call detected — migrate to emit_audit_typed() (apps/api/core/audit_action.py)`.

### §10.4 lint

| 검사 | 위치 | 실행 |
|---|---|---|
| `emit_audit(` legacy call site 0 | `tests/services/test_audit_action_centralization.py` AST-grep | `uv run pytest tests/services/test_audit_action_centralization.py` |
| Registry ↔ DB CHECK ↔ call sites 3-way | `tests/integration/test_audit_action_consistency.py` | `uv run pytest tests/integration/` |

### §10.5 Opening Auto-Carry Policy (Story 5.1)

PRD §F4.1: 기초재고는 자동 이월되며, 매달 다시 입력하지 않아도 된다.

**Chain limit**: 12-period (1년). `INVENTORY_PERIOD_CHAIN_LIMIT`
상수는 `packages/services/m2_input/opening_carry.py` SSOT. 자동
체인이 이 한도를 넘으면 silent no-op; 수동 trigger 도 422
`MONTHLY_INPUT_CARRY_CHAIN_LIMIT` 으로 거부. 운영자가 period 별로
수동 호출해 점진적 확장.

**Lock marker**: `_locked=True, _lock_reason_ko="전월 기말 자동 이월"`
JSONB sub-key 로 첫 row INSERT 후 추가. 이후 `stream='opening_inventory'`
POST 는 400 `MONTHLY_INPUT_OPENING_MANUAL_EDIT` 으로 reject.
_lock 해제는 Epic 11 reversal entrypoint (별도 story).

**Audit actions**: `monthly_input_period_opening_carried` +
`monthly_input_period_opening_locked` 두 액션. ActionClass
`MONTHLY_INPUT_PERIOD` 으로 라우팅 (Story 5.2 에서 inventory_ledger
도입 후 분리 가능).

**Stale value 정책**: prev period projection 과 current opening 이
불일치 시 silently overwrite (cj-style default). Audit log 의
before/after 스냅샷에 prev_old 값 캡처 (CR 1.1 lesson).

**3-way consistency pin**: pure kernel 의
`INVENTORY_PERIOD_CHAIN_LIMIT=12` 와 TS mirror 의
`OPENING_CARRY_CHAIN_LIMIT=12` 가 일치해야 함
(Story 5.3 frontend toast 시점). `tests/integration/test_opening_carry_label_consistency.py`
에서 검증.

**Capability gate**: `Capability.OPENING_INVENTORY` 는 manufacturing-kind
industry 에만 wired. Service industry 는 자동 no-op (carry chain
returns empty decisions — inventory-bearing products 없음).

- §10.5 갱신 (Story 5.3, 2026-08-06): "M14 TS mirror wire + L8 SQL CHECK + 5-3 frontend manual edit reject UI = 3중 defense-in-depth 보존."

### §10.6 Inventory Ledger Append-Only Policy (Story 5.2)

PRD §F4.2: 모든 재고 변동(inbound / outbound / carry / adjustment) 은
append-only 재고 원장에 기록되며, UPDATE/DELETE 가 차단된다.

**Append-only 3중 방어 (AD-2 / AC #3)**:
1. **DB trigger** (`Alembic 0015 inventory_ledger_append_only`) —
   PostgreSQL `BEFORE UPDATE OR DELETE` row-level trigger 가
   `SQLSTATE P0001` 으로 raise. Production gate.
2. **Service-layer AST guard** (`LedgerService._assert_not_modifying`) —
   UPDATE/DELETE/TRUNCATE/DROP TABLE 키워드 4종을 입력 SQL 텍스트에서
   감지. Early fail + raise `AppendOnlyLedgerViolationError`
   (500 APPEND_ONLY_LEDGER_VIOLATION).
3. **Audit log** — 모든 rejection 은 `inventory_ledger_event_rejected`
   audit 행으로 emit (관측성).

**11-value event_type enum (AC #2)** — opening_carried /
opening_carried_stale_overwrite / purchase_inbound / sales_outbound /
production_output_inbound / production_material_consumption /
adjustment_positive / adjustment_negative / reversal_negating /
reversal_corrected / closing_snapshot. Drift detector:
`tests/integration/test_inventory_ledger_event_type_drift.py`
(registry vs DB CHECK vs call sites 3-way).

**Period key AD-24 typed pattern**: `^\d{4}-(0[1-9]|1[0-2])$` —
예: `2026-07`. M8 virtual budget keys (`2026-07#B1`) 는 Epic 8 scope
으로 명시적으로 제외. Pydantic 필드 validator + service-layer
re-validation + pure kernel + DB CHECK 4중 검증.

**QTY_QUANTUM**: NUMERIC(18,4) — banker's rounding (ROUND_HALF_EVEN).
Python kernel `Decimal` ↔ PostgreSQL `NUMERIC(18,4)` parity (CR 0-4
lesson). `INVENTORY_LEDGER_QTY_QUANTUM = Decimal("0.0001")` SSOT.

**Capability gate**: `Capability.INVENTORY_LEDGER` 는 manufacturing-kind
3종 (manufacturing / manufacturing_service /
manufacturing_service_other) 에 wired. Service-only 는 403
INDUSTRY_NOT_SUPPORTED (BOM 없음 → 원장 의미 없음). Drift detector:
`tests/integration/test_inventory_ledger_capability.py` (T9.2).

**AD-22 reversal entrypoint forward-fill (AC #6)**: M4 entrypoint
`request_reversal(event_id, reason)` 은 audit marker emit +
501 `INVENTORY_LEDGER_REVERSAL_NOT_YET_WIRED` raise. Epic 11 M11
모듈 authority 가 실제 reversal sequence INSERT (`reversal_negating`
+ `reversal_corrected` 두 행) 를 담당. Epic 11 wire 시점에 501 →
200 + reversal sequence 반환으로 변경.

**Audit-first wire (A5 forward-lock)**: 모든 state-changing operation
은 `_write_inventory_ledger_audit` 를 **먼저** 호출. Drift detector:
`tests/integration/test_audit_action_consistency.py` (ActionClass
INVENTORY_LEDGER ↔ DB CHECK ↔ call sites 3-way gate).

**Epic 3.3 inline projection swap (AC #5)**: `MonthlyInputService` 가
`build_inventory_projection` 직접 호출 대신 `LedgerService.
query_period_closing_all(period_key=...)` 를 canonical source 로 사용.
`TODO(epic-5-5-2) CLOSED` marker 가
`packages/services/m2_input/inventory_projection.py` 에 남아 있음
(Epic 6 close-out retro 까지). Drift detector:
`tests/integration/test_inventory_projection_ledger_swap.py` (T9.5).

**TS mirror (deferred to Story 5.3)**: 5-3 frontend 진입 시점에
`apps/web/lib/l2-inventory-ledger.ts` 추가. `tests/integration/
test_inventory_ledger_label_consistency.py` 가 snake_case Python ↔
camelCase TS parity 검증 (CR 4-3 lesson — drift detector
placeholder).

### §10.7 Closing Guard Invariant Policy (Story 5.3)

closing ≥ 0 invariant = AD-2 ledger read-only aggregate + AD-4 atomicity close-time hook + AD-12 V3 verification ordering. 입력 시 경고 (Story 3.3 inline + 5-3 ledger aggregate) + 마감 시 차단 (5-3 closing_guard_service + 4-2 close-time hook) 2-layer. V3 fail 시 4-3 verdict envelope + 4-2 close-time block_reason 동등 발동. 5-3 spec에서 3중 게이트 와이어됨.

### §10.8 Monthly Closing Report Audit Policy (Story 6.2)

`MONTHLY_CLOSING_REPORT` capability (manufacturing 3종 ✅ / service-only ❌)
audit-first wire = AD-2 ledger read-only join + AD-4 atomicity read-only
aggregate + AD-12 V4 verification ordering. **Closing report view mode
classifier (READY / PARTIAL / EMPTY 3-state)** + **V4 closing-period
consistency 4-source verification** (`ledger_aggregate` +
`closing_snapshot_aggregate` + `fiscal_period_snapshot_aggregate` +
`product_whitelist`). 6-2 spec에서 3중 게이트 와이어됨.

| Trigger | audit action | ActionClass | enforcement |
|---|---|---|---|
| Closing report GET | `monthly_closing_report_viewed` | `ActionClass.MONTHLY_CLOSING_REPORT` | idempotent no-op skip on re-view (CR 1.1) |
| V4 verification dispatch | `verify_v4_closing_period_consistency` | `ActionClass.VERIFICATION` | service-layer dispatch (CR 1.1 audit-first) |
| KRW/USD dual display 환율 누락 | `monthly_closing_report_krw_usd_rate_missing` | `ActionClass.CLOSING_PERIOD` | 422 typed envelope |
| Closing report empty (3 sources 모두 0) | `monthly_closing_report_empty` | `ActionClass.CLOSING_PERIOD` | 409 typed envelope |

Drift protection: `tests/integration/test_monthly_closing_report_label_consistency.py`
(9 cases) + `tests/api/m4_inventory/test_monthly_closing_report_service.py`
(12 cases) + `tests/integration/test_monthly_closing_report_v4_verdict.py`
(4 cases).

---

## §11 Frontend Tooling (Story 0.5)

Frontend toolchain stack pin + 디자인 토큰 + drift detector의 SSOT는
[`docs/frontend-toolchain.md`](./frontend-toolchain.md) 이다. 본 절은
`docs/conventions.md` 의 다른 절과의 cross-reference 만을 다룬다.

### §11.1 적용 범위

`apps/web/**` (Next.js 15.5.4 + React 19.1.1 + Tailwind 4). 다른
package (모놀리식 frontend 가 없는 backend 서비스)에는 미적용.

### §11.2 Cross-reference

| 토픽 | 본 파일 anchor | frontend-toolchain.md anchor |
|---|---|---|
| Tailwind 4 디자인 토큰 (CSS variables) | §11.3 (이 절) | §2 Tailwind 4 Config |
| `cn()` helper | §11.4 (이 절) | §3 shadcn/ui Setup |
| sonner toast wire | §11.5 (이 절) | §4 sonner Toast Usage |
| vitest + MSW | §11.6 (이 절) | §5 vitest Setup |
| Playwright + rls_db fixture | §11.7 (이 절) | §6 Playwright Setup |
| next-intl ko-KR | §11.8 (이 절) | §7 next-intl Routing |
| INDUSTRY_ICON cross-language contract | §11.9 (이 절) | §8 INDUSTRY_ICON Contract |
| **Monthly closing report cross-language parity** | **§11.10 (이 절)** | **`monthly-closing-report.ts` + `monthly-closing-report-parity.ts`** |

### §11.3 Tailwind 4 디자인 토큰 (CSS variables)

Tailwind 4 디자인 토큰 (background / foreground / primary / ring / radius)
은 `apps/web/app/globals.css` `@theme inline` 블록에서 SSOT. 클래스명은
`bg-background`, `text-primary`, `ring-ring`, `rounded-lg` 등이며
utility-first 직접 사용을 권장. 임의 색상 (예: `bg-blue-500`)은
**금지** — 토큰을 확장하여 사용 (`bg-primary` 등).

### §11.4 `cn()` helper

```typescript
import { cn } from "@/lib/utils";

className={cn("px-4 py-2", isActive && "bg-primary", className)}
```

수동 className concatenation (`"px-4 " + (isActive ? "bg-primary" : "")`)
**금지** — tailwind-merge 로 충돌 resolved 보장.

### §11.5 sonner toast wire

```typescript
"use client";
import { toast } from "sonner";

useEffect(() => {
  if (!isComplete && ratioSum < 100) {
    toast.warning(`BOM 비중 합 100% 필요 (현재 ${ratioSum.toFixed(2)}%)`);
  }
}, [isComplete, ratioSum]);
```

- `<Toaster />` 는 `apps/web/app/layout.tsx` 에서 1회 wire. 페이지마다
  호출 금지.
- `useEffect` 안에서 trigger (render-time fire 금지 — spam 방지).
- server component 에서 직접 `toast()` 호출 **금지** — client component
  경계 안에서만.

### §11.6 vitest + MSW

- `apps/web/__tests__/**/*.test.tsx` - component / hook test
- `apps/web/test/setup.ts` - extend expect + MSW server lifecycle
- `apps/web/mocks/handlers.ts` - HTTP mock 추가 시 핸들러 1곳 SSOT

테스트 작성 시:
- `describe`/`it`/`expect`/`vi` 는 globals (import 불요)
- `<input>` 변경은 `userEvent.setup()` + `user.click()` / `user.type()`
  (fireEvent 사용 시 Radix 미작동)
- `next/navigation` 모킹 시 `useParams: vi.fn(() => ({ locale: "ko-KR" }))`
  명시 (default undefined 시 test fail)

### §11.7 Playwright + rls_db fixture

- `apps/web/e2e/**/*.spec.ts` - E2E test
- `apps/web/e2e/fixtures/supabase-test.ts` - tenant-scoped E2E fixture
  (Story 1.1 F-30 close)

`rlsDb` fixture 사용:

```typescript
import { test } from "./fixtures/supabase-test";

test("tenant-scoped inquiry", async ({ rlsDb }) => {
  // rlsDb.tenantId, rlsDb.tenantToken 자동 주입
});
```

### §11.8 next-intl ko-KR

- `apps/web/messages/ko-KR.json` - 번역 SSOT (namespaces: industry,
  bom, settings, common, errors)
- 모든 UI 텍스트는 `useTranslations("namespace")` 경유. ko-KR 인라인
  string **금지** (UX v1.0 ko-KR lock).

```typescript
"use client";
import { useTranslations } from "next-intl";

const t = useTranslations("industry");
return <h1>{t("manufacturing")}</h1>;
```

### §11.9 INDUSTRY_ICON cross-language contract

TS 와 Python 양쪽에 `INDUSTRY_ICON: Record<Industry, string>` /
`INDUSTRY_ICON: dict[Industry, str]` 가 존재. Drift detector:
`tests/integration/test_menu_config_consistency.py::test_industry_icon_parity_ts_matches_python`.
**새 industry 추가 시 Python + TS + detector 3중 일관성 필수** (AD-15
cross-language hygiene).

### §11.10 Lint — frontend toolchain

| 검사 | 위치 | 실행 |
|---|---|---|
| TS 명명/restricted types | ESLint (root `.eslint.config.mjs`) | `pnpm lint:conventions` |
| TS `number` (money) | ESLint `no-restricted-types` | `pnpm lint:conventions` |
| TS 타입 체크 | `tsc --noEmit` | `pnpm lint:tsc` |
| Vitest | `vitest` | `pnpm test` |
| Playwright (chromium smoke) | `playwright test --project=chromium` | `pnpm playwright:test` |
| Drift detector (TS ↔ Python INDUSTRY_ICON) | `tests/integration/test_menu_config_consistency.py` | `uv run pytest tests/integration/` |

Frontend 도구 세부 설치 / wire 절차는
[`docs/frontend-toolchain.md`](./frontend-toolchain.md) 참조.

### §11.11 Monthly Closing Report Cross-Language Parity (Story 6.2)

PRD §F5 / §F5.2 + AD-15 §11 cross-language parity. 6-2 wire 는
Python pure kernel + TS mirror + parity helper 3중 wire.

| Constant / helper | Python SSOT | TS mirror | parity file |
|---|---|---|---|
| `MONTHLY_CLOSING_REPORT_TITLE_KO` | `"월 마감 보고서"` | `"월 마감 보고서"` | `monthly-closing-report.ts` |
| `MONTHLY_CLOSING_REPORT_EMPTY_KO` | `"마감 데이터 없음"` | `"마감 데이터 없음"` | `monthly-closing-report.ts` |
| `REPORT_VIEW_MODE_READY` | `"READY"` | `"READY"` | `monthly-closing-report.ts` |
| `REPORT_VIEW_MODE_PARTIAL` | `"PARTIAL"` | `"PARTIAL"` | `monthly-closing-report.ts` |
| `REPORT_VIEW_MODE_EMPTY` | `"EMPTY"` | `"EMPTY"` | `monthly-closing-report.ts` |
| `USD_QUANTUM` | `Decimal("0.01")` (NUMERIC(18,2) AD-8) | `"0.01"` | `monthly-closing-report-parity.ts` |
| `QTY_QUANTUM` (parity helper) | `Decimal("0.0001")` (from `inventory_projection`) | `"0.0001"` | `monthly-closing-report-parity.ts` |
| `parityComputeUsdFromKrw` | `compute_usd_from_krw` (ROUND_HALF_EVEN) | `parityComputeUsdFromKrw` | `monthly-closing-report-parity.ts` |
| `parityFormatPeriodClosingKrwUsd` | `format_period_closing_krw_usd` | `parityFormatPeriodClosingKrwUsd` | `monthly-closing-report-parity.ts` |

Drift detector: `tests/integration/test_monthly_closing_report_label_consistency.py`
(9 cases, T9.7). **Drift caught here blocks 6-2 wire from shipping.**

Banker's rounding (CR 0-4 lesson) — TS parity helper imports
`Decimal.js` and sets `Decimal.set({ rounding: Decimal.ROUND_HALF_EVEN })`
on module load. Python uses `decimal.Decimal.quantize(USD_QUANTUM, rounding=ROUND_HALF_EVEN)`.
Parity invariant: TS `parityQuantizeUSD("1005")` = Python
`Decimal("1005").quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)` =
`Decimal("1.00")` (USD 1.005 → 1.00 ROUND_HALF_EVEN).