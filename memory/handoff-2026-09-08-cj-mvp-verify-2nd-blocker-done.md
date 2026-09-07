---
name: handoff-2026-09-08-cj-mvp-verify-2nd-blocker-done
description: "cj-305 self-host MVP verify Phase 2 (38분) — Docker ready ✅ + Postgres healthy ✅ + alembic FAIL `role \"anon\" does not exist` (2nd BLOCKER). 다음 세션 옵션 4개 결정 보류. CR 11-3 honest-DEFER 257번째."
metadata:
  node_type: memory
  type: project
  originSessionId: cj-mvp-verify-walkthrough-2026-09-08
  modified: 2026-09-08T07:25:00.000Z
---

# cj-305 Self-Host MVP Verify Phase 2 — 2nd BLOCKER 발견 (2026-09-08 KST)

**일자**: 2026-09-08 (KST, 38분 세션)
**territory**: Phase 31 Self-Host MVP Verification → verify phase Phase 2
**session elapsed**: ~38분 (사용자 40분 제약 도달 임박)
**CR 11-3 honest-DEFER 257번째** — cj-305 verify walkthrough Phase 1 (256번째) 에 이어 Phase 2 BLOCKER 결정 진입

---

## §1 Phase 1 → Phase 2 진척

### ✅ User action: Docker Desktop 시작

사용자 = A 옵션 선택 → 본 세션 안에서 Docker daemon 시작 → ~10s 후 `docker ps` ready.

### ✅ Postgres container 부팅 healthy

`docker compose up postgres -d` → `costmgr-postgres` container `Up 13 seconds (healthy)` (port 54322→5432 mapping). 3주된 pre-existing image 그대로 사용 (volume 보존).

### ⚠️ alembic migrate FAIL — `role "anon" does not exist`

**Error**:
```
sqlalchemy.exc.ProgrammingError: <class 'asyncpg.exceptions.UndefinedObjectError'>:
role "anon" does not exist
[SQL: CREATE POLICY external_identities_anon_block ON public.external_identities
FOR ALL TO anon USING (false) WITH CHECK (false)]
```

**Root cause**: cj-305 wire 의 RLS policies 가 **Supabase 전용 role 3종** (`anon`, `authenticated`, `service_role`) 가정. vanilla postgres:15 image 는 해당 role 부재.

**참조**: `docker-compose.yml` 주석 직접 언급 — 
> "RLS policies live in: supabase/policies/0001_rls_policies.sql (applied AFTER alembic upgrade)"

즉, 원래 의도 = **alembic (base schema) + 별도 supabase RLS policies 분리 적용**. 현 self-host verify pipeline 은 Supabase role 없이 alembic 의 anon-policy 까지 실행 → FAIL.

---

## §2 해결 옵션 4개 (다음 세션 결정 보류)

| # | 옵션 | 작업량 | 위험 |
|---|------|--------|------|
| **(A)** | psql 접속하여 `anon`/`authenticated`/`service_role` 3개 role 생성 후 migration 재시도 | 5분 | RLS 가 실제로 enforce 안 될 위험 (Supabase 의 JWT context 미주입) |
| **(B)** ★ RECOMMENDED | alembic 의 anon-related migration 만 skip 후 나머지 적용, 별도 SQL dump 후 `role if not exists` wrap | 30분 | 가장 적은 변경. RLS 정책 효과 무시되지만 schema OK |
| (C) | Supabase CLI 로 local full stack (postgres + GoTrue + PostgREST + Studio) setup | 30분+ | setup 시간 과다, MVP verify scope 초과 |
| (D) | 해당 migration class 만 `if not exists` wrap 한 source patch PR (cj-style sprint 진입) | 2-3h | cj-305 결정 wire 범위 외 (변경 발생) |

**추천**: **(B) alembic skip + Supabase role 분기 적용** — 다음 세션 30분 내 가능.

---

## §3 현재 안전 저장 상태

- ✅ Commit `c29d606`: walkthrough scaffold + 1st handoff memory
- ✅ Postgres container healthy (54322 port)
- ✅ alembic.ini 복구 완료 (script_location 원본 그대로)
- ✅ walkthrough report 보강 (§2.5b + §2.6 NEW BLOCKER 섹션)

**다음 세션 resume command (Option B 적용 시)**:
```bash
# Postgres 는 이미 healthy 상태 (재시작 불필요)
docker compose ps | grep postgres
# Supabase role 3개 생성 (DDL)
docker exec costmgr-postgres psql -U postgres -d postgres -c "
  CREATE ROLE anon NOLOGIN;
  CREATE ROLE authenticated NOLOGIN;
  CREATE ROLE service_role NOLOGIN BYPASSRLS;
"
# alembic 의 anon-policy 는 skip 후 나머지 적용 (수동 SQL dump)
cd "C:/Users/c8rom/desktop/a/costmgr"
uv run alembic -c apps/api/alembic.ini upgrade head --sql > /tmp/alembic.sql
# anon-related lines 만 grep -v 로 skip 후 psql exec
grep -v "TO anon\|TO authenticated\|TO service_role" /tmp/alembic.sql | \
  docker exec -i costmgr-postgres psql -U postgres -d postgres
# 이후 dev_seed + uvicorn + smoke
uv run python scripts/dev_seed.py
cd apps/api && uv run uvicorn apps.api.main:app --reload --port 8000 &
# 별도 terminal:
uv run python scripts/self_host_smoke_test.py
```

---

## §4 DoD 진행률 갱신

- [x] **stack pin 37 pins match** ✅ (1/4 = 25%)
- [x] **Postgres container healthy** ✅ (NEW, 2/4 = 50%)
- [ ] **alembic schema applied** ⚠️ BLOCKED — anon role (3rd BLOCKER)
- [ ] **uvicorn boot + 8 auto smoke + 4 P1 manual + audit_logs 5 actions** 보류

---

## §5 결정 wire 보존 (이번 세션 변경 0건)

cj-305 결정 wire 그대로 보존. vanilla postgres Supabase role 부재는 self-host verify 의 **env mismatch** 이지 source 변경 아님.

---

## §6 결정 보류 (운전자) — 다음 세션 진입 시

| # | 옵션 | 우선순위 |
|---|------|----------|
| ① | **anon role 4 옵션 중 선택** (A/B/C/D) | ★★★ RECOMMENDED: (B) alembic skip + Supabase role 분기 |
| ② | cj-305 close-out retro | DoD 4/4 ✅ 후 |
| ③ | cj-303 carryover 4건 fix | 솔리드 MVP verified 후 |
| ④ | PRD v2 EXTENSION / Epic 29+ | pilot feedback 후 |

---

## §7 CR 11-3 honest-DEFER 257번째

cj-style chain:
- cj-282 (220번째) → ... → cj-305 wire (255번째) → cj-305 verify walkthrough Phase 1 (256번째) → **cj-305 verify walkthrough Phase 2 BLOCKER (257번째, 본 handoff)**

**37 sprints 정직 회복 결정 wire 진입**.

---

## §8 Why / How to apply

**Why**: Phase 1 의 cj-style 256번째 sprint 가 Docker daemon BLOCKER 를 발견 → 사용자 직접 Docker Desktop 시작으로 우회 성공 → Phase 2 진입 즉시 2nd BLOCKER (anon role) 발견. 이 env mismatch 는 self-host verify 의 Supabase role 가정이 vanilla postgres 와 양립 불가능하다는 결정 wire 의 **새로운 발견**.

**How to apply**:
- 다음 세션 첫 action: §3 의 Option B 명령어 실행 (anonymous role 분기 + 나머지 migration 적용)
- Option B 가 30분 내 성공 시 → dev_seed + uvicorn + smoke 가능 → DoD 4/4 ✅ 진입
- Option B 실패 시 → (A) 또는 (C) fallback (CJ 결정)

---

## Cross-references

- **이전 handoff**: `memory/handoff-2026-09-08-cj-mvp-verify-walkthrough-blocker-done.md`
- **Walkthrough report (갱신됨)**: `docs/walkthrough/cj-mvp-verify-2026-09-08.md` (2nd BLOCKER 추가)
- **Commit `c29d606`**: Phase 1 walkthrough scaffold + handoff 결정 wire
- **Phase 31 entry**: `_bmad-output/implementation-artifacts/phase-31-self-host-mvp-verification-entry-2026-09-07.md`
- **cj-305 wire handoff**: `memory/handoff-2026-09-07-cj-305-self-host-mvp-verification-wire-done.md`
