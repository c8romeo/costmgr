# AD-15 Variance — `tenant_id`는 UUID v4 (Supabase Auth 호환)

> **상태:** Accepted (2026-07-28, Story 0.4 §1 §3)
> **관련 AD:** AD-15 (Cross-language Conventions), AD-3 (Multi-tenancy)
> **참조:** [conventions.md §3 Identity](../conventions.md#3-identity)

## Context

ARCHITECTURE-SPINE §AD-15는 "비즈니스 엔티티 ID는 UUID v7"로 명시한다. 시간 정렬 가능, 분산 ID 생성에 강하다.

그러나 `tenant_id`는 **Supabase Auth**의 `auth.users.id`를 직접 참조해야 한다. Supabase Auth는:
- v4 UUID만 발급한다 (`gen_random_uuid()` = `uuid_generate_v4`).
- Auth 사용자가 생성될 때 `auth.uid()` (UUID v4)를 반환한다.
- v7을 발급하는 옵션이 **없다** (2026-07 기준).

## Decision

`tenant_id`는 **UUID v4**로 고정한다.

| 엔티티 | ID 종류 | 근거 |
|---|---|---|
| `tenant_id` (모든 테이블 FK) | UUID v4 | Supabase Auth 호환 (필수) |
| `user_id` | UUID v4 | `auth.users.id` 직접 참조 |
| 비즈니스 엔티티 (products, BOM rows, …) | UUID v7 (또는 v4) | AD-15 기본 |
| Audit log (`audit_logs.id`) | UUID v4 | FK-less, 무관 |

## Consequences

**Positive:**
- Supabase Auth 통합이 깨지지 않는다 (RLS 정책이 `auth.uid()`로 직접 매칭).
- Story 0.2의 모든 RLS 정책이 추가 변환 없이 작동한다.

**Negative / Trade-offs:**
- `tenant_id`는 시간 정렬 불가 — 인덱스만으로 최신 tenant 정렬 불가.
- 마이그레이션 시 `tenant_id`는 항상 `gen_random_uuid()` (v4). v7 도입 시 DB 마이그레이션 필요.

**Mitigations:**
- 검색 패턴은 대부분 `tenant_id = :current` (equality). 정렬은 `created_at` 기준이므로 v4여도 무관.

## Notes

이 variance는 `conventions.md §3 Identity` 표에도 명시되어 있다. 새 코드를 작성할 때 `tenant_id` 자리에 v7을 쓰면 lint가 잡지는 못하지만, RLS가 동작하지 않으므로 CI 테스트가 잡는다 (`tests/rls`).