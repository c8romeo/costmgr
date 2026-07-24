# Reviewer Gate Verification — ARCHITECTURE-SPINE

- **대상:** `ARCHITECTURE-SPINE.md` (AD-9, AD-14, Stack, 배포 다이어그램)
- **검토일:** 2026-07-24
- **검토 방식:** 스파인을 수정하지 않고, Railway/Supabase/Node.js/Next.js/Vercel/SQLAlchemy 공식 문서와 npm/PyPI 레지스트리를 독립 조회했다. 레지스트리 조회는 정확한 버전 endpoint(예: `registry.npmjs.org/<package>/<version>`, `pypi.org/pypi/<package>/<version>/json`)로 재확인했다.

## Verdict

**CONDITIONAL FAIL — 2 High, 2 Medium, 0 Critical.**

버전 존재성 자체는 통과했지만, AD-9의 데이터 경계와 배포 다이어그램의 Vercel 정적 전용 가정이 공식 동작과 충돌할 수 있다. 이 두 High finding을 해소하고 lockfile/배포 검증을 추가하기 전에는 “web-verified stack pin”과 파일의 데이터 거주성 보장을 승인할 수 없다.

## 독립 검증 결과

### 1. Railway / Supabase 지역

- Railway 공식 [deployment regions](https://docs.railway.com/reference/deployment-regions)는 `Southeast Asia Metal | Singapore | asia-southeast1-eqsg3a`를 실제 region identifier로 열거한다. 따라서 AD-9의 Railway region 표기는 **존재성 통과**다.
- Supabase 공식 [available regions](https://supabase.com/docs/guides/platform/regions)는 `Northeast Asia (Seoul), ap-northeast-2`를 specific AWS project region으로 열거한다. 따라서 AD-9의 Supabase project region 표기는 **존재성 통과**다.
- 두 region이 서로 다른 사업자/region인 것은 검증되지만, 이 사실만으로 Auth, Storage, backup 복사본이 모두 Seoul에 있다는 보장은 되지 않는다. 아래 High-2를 참조한다.

### 2. Node / Next / React / TypeScript / UI 핀

정확한 npm registry version endpoint에서 다음 버전이 모두 반환되었다.

| 패키지 | 핀 | 결과 | 공식 호환성 확인 |
|---|---:|---|---|
| Node.js | 24.18.0 | [Node release page](https://nodejs.org/en/about/previous-releases)에 존재, Latest LTS | Next 16 package engine `>=20.9.0` 및 shadcn engine `>=20.18.1`을 만족 |
| next | 16.2.11 | npm에 존재 | package engine `>=20.9.0`; React/React DOM `^19.0.0` 허용 |
| react / react-dom | 19.2.8 | npm에 존재 | `react-dom@19.2.8` peer가 `react ^19.2.8`; 일치 |
| typescript | 7.0.2 | npm에 존재 | Next 공식 [installation](https://nextjs.org/docs/app/getting-started/installation)은 최소 TS 5.1만 명시; 7.0.2를 금지하는 peer는 확인되지 않았으므로 존재/최소요건은 통과하나 CI build 검증은 필요 |
| tailwindcss | 4.3.3 | npm에 존재 | shadcn 공식 [manual installation](https://ui.shadcn.com/docs/installation/manual)은 Tailwind v4 경로를 사용; `@tailwindcss/postcss@4.3.3`도 존재 |
| shadcn | 4.14.1 | npm에 존재 | engine `>=20.18.1`; Node 24.18.0과 호환 |
| @tanstack/react-table | 8.21.3 | npm에 존재 | peer React/React DOM `>=16.8`; 호환 |
| next-intl | 4.13.4 | npm에 존재 | peer Next `^16.0.0`, React `^19.0.0`; Next 16.2.11/React 19.2.8과 호환 |
| recharts | 3.10.0 | npm에 존재 | engine `>=18`, React 19 peer 허용 |

**판정:** 요청된 프런트엔드 핀은 모두 레지스트리 존재성과 선언된 engine/peer 범위에서 상호 호환된다. 다만 TS 7과 Next의 실제 typecheck/build 조합은 lockfile CI에서 확인해야 한다.

### 3. Python 핀

정확한 PyPI JSON endpoint에서 다음 버전이 모두 반환되었다. Python `3.12.x`와의 `Requires-Python` 충돌은 확인되지 않았다.

| 패키지 | 핀 | PyPI 결과 | `Requires-Python` |
|---|---:|---|---|
| FastAPI | 0.139.2 | 존재 | `>=3.10` |
| Pydantic | 2.13.4 | 존재 | `>=3.9` |
| SQLAlchemy | 2.0.51 | 존재 | `>=3.7` |
| Alembic | 1.18.5 | 존재 | `>=3.10` |
| pytest | 9.1.1 | 존재 | `>=3.10` |
| structlog | 26.1.0 | 존재 | `>=3.10` |
| uv | 0.11.32 | 존재 | `>=3.8` |
| opentelemetry-api | 1.44.0 | 존재 | `>=3.10` |

FastAPI의 PyPI metadata는 Pydantic `>=2.9.0`을 허용하므로 Pydantic 2.13.4와 맞는다. SQLAlchemy 2.0.51과 Alembic 1.18.5의 최소 Python 범위도 Python 3.12와 맞는다.

### 4. Stripe / PostgreSQL

- Stripe 공식 [API versioning](https://docs.stripe.com/api/versioning)은 현재 버전 형식과 `2026-06-24.dahlia`를 명시한다. Stack pin은 **존재성 통과**다.
- Supabase 공식 upgrade 문서의 Postgres 17 upgrade notes에서 Postgres 17 target이 확인되어 `PostgreSQL 17 on Supabase`는 **현재 문서상 가능**하다. 다만 실제 project plan/cluster에서 17을 provisioning하는 CI smoke test는 별도 필요하다.

## Findings

### HIGH-1 — Vercel을 “static assets only”로 그렸지만 Next App Router는 기본적으로 서버 실행 경로를 만든다

- **위치:** AD-9 line 87; Design Paradigm line 21; Container view lines 299–315; Deployment and environments lines 343–359.
- **증거:** Next 공식 [Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)는 `app`의 layouts/pages가 기본적으로 Server Components이고 서버에서 data/API fetch 및 render한다고 명시한다. Vercel 공식 [Next.js on Vercel](https://vercel.com/docs/frameworks/full-stack/nextjs)은 SSR을 Vercel Functions로 실행하고, App Router의 Route Handlers/React Server Components/ISR/PPR을 Vercel 런타임과 CDN에 배치할 수 있다고 명시한다. 반대로 Next 공식 [static export](https://nextjs.org/docs/app/guides/static-exports)는 `output: 'export'`를 별도로 켜야 하며, Cookies, Server Actions, Request 기반 Route Handlers, ISR 등은 static export에서 지원하지 않는다고 열거한다.
- **실패 시나리오:** 현재 구조대로 인증 dashboard가 App Router Server Component, cookies, Server Action 또는 Route Handler 하나라도 사용하면 Vercel Function이 tenant JWT/응답/데이터를 처리한다. 이는 “Vercel may cache static assets globally but never tenant data” 및 AD-9의 “tenant payload는 Railway에서만 transient processing”을 보장하지 못한다. 또한 Vercel 문서상 ISR 생성물은 CDN 및 durable storage에 캐시/보존될 수 있어 static-only라는 라벨만으로는 차단되지 않는다.
- **수정 요구:** 다음 중 하나를 명시하고 CI에서 강제해야 한다.
  1. `output: 'export'` 기반의 진짜 static/SPA 프런트로 제한하고, 모든 tenant API/Auth 데이터는 브라우저에서 Railway API로만 호출한다. dynamic API, cookies, Server Actions, ISR/PPR, Vercel Middleware 등 금지 검사를 둔다.
  2. Vercel의 Server Components/Functions를 허용한다면 AD-9를 재작성하여 Vercel 실행/캐시 region, 로그/보존, tenant-data 처리 여부를 명시하고 PIPA 처리자 검토에 포함한다.
  3. 동적 Next 서버를 Railway로 옮기고 Vercel은 명시적으로 정적 산출물 CDN만 담당하게 한다.

### HIGH-2 — `Supabase Seoul` project region 확인만으로 Auth/Storage/backups의 Seoul 거주성을 입증하지 못한다

- **위치:** AD-9 line 87; Stack lines 224–228; Container view lines 305–309; Deployment diagram lines 344–356; Operational envelope line 359.
- **증거:** Supabase 공식 [available regions](https://supabase.com/docs/guides/platform/regions)는 `ap-northeast-2`를 **project의 specific AWS region**으로 확인하지만, 해당 페이지는 Auth/Storage/backup 각각의 서비스별 region, 복제, CDN/backup 복사본의 데이터 거주성을 보장하는 계약 문구로 세분화하지 않는다. Supabase 공식 [Storage](https://supabase.com/docs/guides/storage)는 Storage가 S3-compatible이고 global CDN으로 파일을 제공할 수 있음을 설명한다. Supabase [backups](https://supabase.com/docs/guides/platform/backups)는 자동 backup/복원 기능을 설명하지만, 검토 시 확인 가능한 문구만으로는 이 아키텍처가 사용하는 모든 backup/PITR/restore 복사본과 Storage object가 Seoul에 고정되었음을 입증하지 못한다. 따라서 Stack의 한 region 표기에서 “tenant data at rest, Auth, Storage, and backups live in Seoul”까지 도약한 것은 web-verification 증거가 부족하다.
- **실패 시나리오:** project database만 `ap-northeast-2`에 두고 Storage bucket, Auth 처리/로그, PITR/backup, restore 대상 또는 CDN origin을 다른 지원 region/공급자 기본값으로 생성하면 tenant PII/파일이 Seoul 밖에 저장된다. AD-9의 PIPA cross-border notice/consent 및 “no tenant data outside Supabase Seoul” 운영 문장이 거짓이 된다. 특히 Storage는 S3/CDN 경로가 별도이므로 bucket region을 명시하지 않는 한 region pin이 검증되지 않는다.
- **수정 요구:** Supabase 계약/지원 문서와 실제 project를 통해 (a) Auth metadata/session/로그, (b) 각 Storage bucket의 실제 object region과 public/private CDN 동작, (c) daily backup, PITR/WAL, restore artifact의 region/복제, (d) 삭제/보존 기간을 항목별로 확인하고 증거를 보관한다. `ap-northeast-2`가 Storage 또는 필요한 backup tier에 지원되지 않으면 “Seoul all data” 설계를 유지할 수 없으므로 Storage를 별도 Seoul-resident provider로 고정하거나 AD-9의 보장 범위를 수정해야 한다. 배포 전 실제 region API/console assertion과 cross-region egress 테스트를 CI/운영 체크리스트에 넣는다.

### MEDIUM-1 — `SQLAlchemy 2.0.51 async`는 버전만으로 재현 가능한 async 설치가 아니다

- **위치:** Stack line 221.
- **증거:** SQLAlchemy 공식 [asyncio extension](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)은 async extension이 `greenlet`에 의존하며, 필요한 경우 `pip install sqlalchemy[asyncio]`로 extra를 설치하라고 명시하고 PostgreSQL async dialect 예시로 `asyncpg`를 사용한다.
- **실패 시나리오:** lockfile/pyproject가 `SQLAlchemy==2.0.51`만 고정하고 `[asyncio]` extra 및 `asyncpg`/`psycopg` async driver를 고정하지 않으면 이미지/플랫폼에 따라 `greenlet` 또는 driver가 빠져 API cold start/DB connection이 실패한다.
- **수정 요구:** `sqlalchemy[asyncio]==2.0.51` 또는 명시적 `greenlet`과 정확한 async PostgreSQL driver를 lockfile에 포함하고, Python 3.12 Linux Railway 이미지에서 `create_async_engine` smoke test를 실행한다.

### MEDIUM-2 — “Supabase supplies daily backups”는 plan/retention/PITR가 고정되지 않았다

- **위치:** Operational envelope line 359; AD-9 line 87; Stack line 225.
- **증거:** Supabase 공식 [Database Backups](https://supabase.com/docs/guides/platform/backups)는 plan별 자동 backup과 PITR/복원 기능을 구분한다. Stack에는 Supabase plan, retention, PITR 사용 여부, restore target region이 없다.
- **실패 시나리오:** staging/production이 서로 다른 plan으로 생성되거나 PITR을 사용하지 않는 plan에 배치되면 “daily backups” 또는 목표 RPO가 실제로 제공되지 않는다. 복원 테스트가 다른 region으로 project를 만들면 AD-9의 Seoul-only 조건도 깨질 수 있다.
- **수정 요구:** production/staging plan, daily backup retention, PITR 여부, backup/restore region, 삭제 시 보존·파기 정책을 Stack/운영 runbook에 명시하고 분기별 Seoul restore drill을 V8/배포 gate에 포함한다.

## 최종 판정 근거

### 통과

- Railway `asia-southeast1-eqsg3a`: 공식 region 목록에 존재.
- Supabase `ap-northeast-2`: 공식 project region 목록에 존재.
- Next.js 16.2.11, React/React DOM 19.2.8, TypeScript 7.0.2, Tailwind 4.3.3, shadcn 4.14.1, TanStack Table 8.21.3, next-intl 4.13.4, Recharts 3.10.0: npm registry에 정확한 버전 존재.
- FastAPI 0.139.2, Pydantic 2.13.4, SQLAlchemy 2.0.51, Alembic 1.18.5, pytest 9.1.1, structlog 26.1.0, uv 0.11.32, opentelemetry-api 1.44.0: PyPI에 정확한 버전 존재.
- Node 24.18.0은 Node 공식 release page에서 LTS이며 Next/shadcn engine 범위를 만족.
- React/Next/next-intl/Recharts/TanStack의 registry peer 범위는 서로 호환.

### 차단

1. Vercel의 실제 Next App Router 실행 모델과 “static assets only / no tenant data” 주장을 일치시킬 실행 모드와 CI enforcement가 없다.
2. Supabase project region과 Auth/Storage/backup 각 artifact의 Seoul 거주성을 잇는 공식/운영 증거가 없다.

**권고:** HIGH-1, HIGH-2 해소 후 재검토한다. 스파인은 수정하지 않았다.
