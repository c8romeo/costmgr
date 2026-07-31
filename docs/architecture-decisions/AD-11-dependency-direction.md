# AD-11 Dependency Direction — `ui → api → services → ports → engine`

> **상태:** Accepted (2026-07-28, Story 0.4 §1 §5) + Money-types Exception (2026-07-31, Story 0.4 close-out)
> **관련 AD:** AD-1 (Modular Monolith), AD-8 (Money Types), AD-13 (MonthInputAdapter)
> **참조:** [conventions.md §11 Dependency Direction](../conventions.md)

## Context

Hexagonal core(`packages/cost_engine/`)는 순수 도메인 로직만 보관한다 (AD-1). 외부 어댑터 — DB, HTTP, settings, AI — 가 이 코어를 호출하는 단방향 흐름이 없으면:

- 코어 내부에 `httpx`/`sqlalchemy`/`fastapi` 의존이 새어 들어오면, `f(inputs: dataclass) -> dataclass` 순수성 (AD-5)이 깨진다.
- 동일 코어를 API·CLI·배치 등 다중 채널에서 재사용할 수 없다.
- 테스트가 DB/HTTP/시계에 종속되어 v8 회귀 fixture (Story 4.4)가 결정성을 잃는다.

## Decision

의존성 방향은 **한 방향, 강제**:

```
ui (apps/web)        →  api (apps/api)        →  services (packages/services)  →  ports (packages/ports)  →  engine (packages/cost_engine)
                                            ↘                                                       ↗
                                             adapters (alembic, scheduler, ai clients)
```

- **ui** 는 **api** 만 호출. **services**/engine 직접 import 금지.
- **api** 는 **services** 만 호출. **engine**/ports 직접 import 금지 (단, 아래 *예외* 참조).
- **services** 는 **ports** (인터페이스) 만 호출. **engine** 직접 호출은 **adapters** 레이어만 허용.
- **ports** 는 **engine** 만 호출. **api**/services 역방향 호출 금지.
- **engine** 는 어떤 다른 레이어도 import 금지 (AD-1, AD-5 purity).

검사는 `import-linter` contracts (`.importlinter` 또는 동등한 설정) — CI `lint-imports` job (`.github/workflows/ci.yml`).

## Consequences

**Positive:**
- 코어 순수성 보장 → 결정성 있는 v8 회귀 fixture (Story 4.4) 가능.
- 코어 교체/리팩터 시 어댑터만 영향.
- mock 주입이 깔끔 → 테스트가 빨라짐 (mock 없이도 services→ports 인터페이스 stub만으로 충분).

**Negative / Trade-offs:**
- 새 모듈을 만들 때 "어느 레이어에 둘지" 결정 비용.
- Strict 환경에서 가벼운 "한 줄" 도메인 호출도 services 거치게 됨.

**Mitigations:**
- 포트 인터페이스 (Story 4.1 calc_port 등) 도입으로 services 레이어 boilerplate 최소화.
- 의존성 위반은 PR review에서 `architecture/test_api_calls_only_ports.py`로 자동 차단.

## Exceptions

### Exception 1 — Money Types (2026-07-31, Story 0.4 close-out)

**Scope:** `packages.cost_engine/core/money.py` (KRW, USD, `Money`, `to_krw`, `to_usd`, `format_krw`, `format_usd`).

**Rationale:** Money types (AD-8)는 본질적으로 cross-cutting primitive이다. API 엔드포인트 응답 직렬화, settings 입력 검증, 코어 계산 — 모든 레이어가 동일 타입 정체성(`isinstance`/`NewType` semantics)을 공유해야 `Decimal ↔ int ↔ NUMERIC ↔ BIGINT` 변환 손실이 없다. 어댑터 (`apps/api/core/money.py`) 가 동일한 모듈을 re-export 하는 패턴은 **타입 ID 보존** 차원에서 불가결하다.

**Constraint:** 이 예외는 **`packages/cost_engine/core/money.py`** 단일 모듈에만 적용. 다른 engine 모듈 (calc_port, ccr_port, reversal_port, core/__init__ 등) 에 대한 api→engine direct import는 금지.

**Detection:** `scripts/check_money_types.py` + `tests/integration/test_money_types.py` 가 api→engine direct import 가 money 모듈에 한해서만 발생함을 검증. 다른 module에서 direct import 검출 시 CI `lint-conventions` job 실패.

**Future exceptions:** 동일 패턴 (cross-cutting primitive 모듈) 가 필요 시, 이 섹션에 새로운 예외 항목을 추가하고 PR review에서 architecture 권한자 승인을 받을 것.

### (Reserved) Exception N — TBD

향후 cross-cutting primitive 가 등장하면 동일한 template으로 등록.

## Alternatives Considered

| 후보 | 기각 이유 |
|---|---|
| 자유 의존 (no constraint) | v8 회귀 fixture 깨짐 + 코어 순수성 손실 |
| bi-directional (어댑터 ↔ 코어) | 코어가 어댑터 변경에 취약 + 순환 의존 위험 |
| 두 단계 (services 직접 호출 가능) | services 레이어가 작은 프로젝트에서 noise 만 증가 |
| imports 레이어 표시 (예: `*_service.py` suffix) | type-checker·lint 둘 다 통과 못함; 명시적 레이어 분리보다 약함 |

## Notes

- `apps/api/core/money.py` 는 실제로 `packages/cost_engine/core/money.py` 를 re-export 한다. 이 파일은 **adapter** 의 성격을 가지며 api 레이어에 머무는 것이 옳다. 코어 자체는 항상 순수.
- Story 6.2 (KRW/USD dual display) 가 추가될 때 환율 변환 어댑터 (services 레이어) 를 거쳐야 한다 — money 모듈 재사용은 가능, 단 직접 호출은 services 를 통해서만.
- `tests/architecture/test_api_calls_only_ports.py` 의 allowlist: 현재 `services.m0_onboarding.industry_menu`, `services.m0_onboarding.settings_completion` (pure function) 항목. pure 함수 services 모듈은 adapters 가 아니라 services 로 분류.
