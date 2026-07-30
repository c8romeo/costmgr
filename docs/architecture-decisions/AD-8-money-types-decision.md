# AD-8 Money Types — Decimal (Python) + decimal.js (TS)

> **상태:** Accepted (2026-07-28, Story 0.4 §1 §5)
> **관련 AD:** AD-8 (Monetary Types), AD-1 (Modular Monolith), AD-2 (Append-only Ledger)
> **참조:** [conventions.md §5 Money](../conventions.md#5-money-ad-8--매우-엄격)

## Context

원가/예산/매출은 절대 정밀도를 가져야 한다. `float` (IEEE 754)은:
- `0.1 + 0.2 ≠ 0.3` 같은 비교 실패
- `1_000_000_000 + 0.01`에서 소수부 손실
- 합계·환산 누적 시 "왜 1원이 모자르지?" 디버깅 불가

KRW는 정수 통화(1원 단위)이므로 `int`로 충분하다. USD는 센트 단위(2자리)이므로 `Decimal`/`Numeric`이 필수.

## Decision

| 통화 | DB | Python | TypeScript |
|---|---|---|---|
| KRW | `BIGINT` (1원 단위 정수) | `int` (`NewType("KRW", int)`) | `bigint` (`type KRW = bigint`) |
| USD | `NUMERIC(18,2)` | `Decimal` (`NewType("USD", Decimal)`) | `string` (decimal.js serialized) |

### 라이브러리 선택

| 언어 | 라이브러리 | 근거 |
|---|---|---|
| Python | **`decimal.Decimal` (stdlib)** | Python 3.12+ 표준, 의존성 0, Psycopg가 asyncpg를 통해 자동으로 `Numeric` ↔ `Decimal` 매핑. `Decimal`의 `quantize(Decimal("0.01"))`로 USD 반올림 결정성 보장. |
| TypeScript | **`decimal.js` (10.x)** | 브라우저+Node 호환, `toFixed(2)`로 결정성 있는 직렬화, IEEE 754 회피. 대안 `big.js`는 1.0/2.0 정수만 정밀 (소수 3자리부터 손실). `bignumber.js`는 너무 무거움. |

### 왜 `float` 금지인가

```python
>>> 0.1 + 0.2
0.30000000000000004

>>> Decimal("0.1") + Decimal("0.2")
Decimal('0.3')

>>> sum([0.01] * 100)
9.999999999999831

>>> sum([Decimal("0.01")] * 100)
Decimal('1.00')
```

원가 계산은 같은 금액을 수천 번 합산한다 (Epic 4 §4.1 pure cost engine). `float` 누적 오차는 **반복 계산의 deterministic regression fixture** (Story 4.4 §v8)를 깨뜨린다.

### 왜 TS는 `bigint` + `string`인가

- `number`는 IEEE 754 double — 2^53 - 1 ≈ 9,007,199,254,740,991까지 정확.
  - KRW 1조 = 10^12. 9000조까지 안전하지만, 더 큰 금액이나 환율 변환에서 위험.
  - 환율 변환 × 합산 = `Number.MAX_SAFE_INTEGER` 초과 쉬움.
- `bigint`는 정수 정밀, 임의 크기.
- USD는 2자리 소수 — TS native에 없음. `decimal.js`의 `toFixed(2)`가 결정성 있는 문자열 직렬화.

## Consequences

**Positive:**
- 결정성 있는 계산 → `v8_regression` (Story 4.4) 안정.
- DB ↔ Python ↔ TS 간 직렬화 손실 없음.
- Display용 locale formatter를 단일 진입점 (`format_krw`/`formatKRW`)으로 관리 가능.

**Negative / Trade-offs:**
- TS `bigint`은 `JSON.stringify`가 그대로 직렬화 불가 → API 응답 시 `string` 변환 필요 (`toKRWString(krw)`).
- `decimal.js`는 `~30KB` gzipped — 프론트엔드 번들 사이즈 약간 증가 (허용 범위).

**Mitigations:**
- API 응답은 ISO-8601 + KRW/USD 문자열로 통일. 클라이언트는 `BigInt(krwString)`로 받으면 됨.

## Alternatives Considered

| 후보 | 기각 이유 |
|---|---|
| Python `numpy.float64` | numpy는 cost_engine 의존 아님 + float 위험 재현 |
| TS `bignumber.js` | `decimal.js` 대비 무거움 + API 유사 |
| TS `number` (KST 정수만) | 환율 변환 시 오버플로 + USD 정밀도 0 |
| DB `NUMERIC` for KRW | `BIGINT` 대비 16바이트 → row size 증가, 정수 연산 느림 |

## Notes

`packages/cost_engine/core/money.py`는 **순수 Python stdlib only** (AD-1 hexagonal core purity). Pydantic/FastAPI 의존 없음. `apps/api/core/money.py`는 동일 타입을 re-export + FastAPI 의존성 가능.