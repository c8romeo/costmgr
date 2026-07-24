# Architecture Spine — Verifier Review

- **Spine under review:** `architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md`
- **Lens:** web-reality-check vs training-data assertion. Greenfield — no existing project/starter to lean on.
- **Run at:** 2026-07-24
- **Reviewer:** verifier lens

## Verdict

**needs-attention** — The structural design is sound and the hexagonal-core + modular-monolith combination is a recognized, well-named pattern. However, two binding ADs (AD-9 KR residency, AD-14 stack pin) contain claims that conflict with what web verification confirms, and most of the Stack table is "latest (2026-07)" placeholders that the spine itself flags as unverified. Until the Railway region is corrected and the pins are tightened, downstream epics/stories risk baking in a violation of AD-9 or building against versions that drift before commit.

## Findings

- **[critical]** **Railway region `asia-northeast3` (Seoul) is NOT an available Railway region as of 2026-07.** Web verification of Railway's public region list (2026) returns only US East (Virginia), US West (Oregon), Canada Central, EU West (Amsterdam), EU Central (Frankfurt), Asia East (Tokyo = `asia-northeast1`), and Southeast Asia (Singapore = `asia-southeast1`). There is no Seoul region. This contradicts AD-9 ("Railway backend `asia-northeast3` (Seoul)"), AD-14 (KR-residency binding), and PRD §13.3 ("Railway 백엔드"). The closest KR-respecting option is `asia-northeast1` (Tokyo). *Fix:* change spine to `asia-northeast1` (Tokyo) for Railway, OR swap the backend host to one with a Seoul region (AWS `ap-northeast-2`, GCP `asia-northeast3` direct, Naver Cloud, Kakao i Cloud). The spine must reconcile this with the "10만원/월 인프라 예산" PRD constraint — Tokyo adds negligible latency to Seoul tenants and keeps the budget; switching host is a bigger cost story.

- **[high]** **Supabase region `ap-northeast-2` (Seoul) is unverified and plausibly unavailable.** The Supabase public region list historically included only `ap-northeast-1` (Tokyo) and `ap-southeast-1` (Singapore) in Asia. The web search did not surface a clean confirmation either way for 2026-07. AD-9 binds Supabase to `ap-northeast-2`. If Seoul is not actually selectable in the Supabase project-creation dialog, AD-9 is silently broken. *Fix:* verify against the Supabase Dashboard region selector (live, not the docs page) before first commit. If unavailable, fall back to `ap-northeast-1` (Tokyo) on Supabase. Document the choice and the rationale in AD-9.

- **[high]** **Next.js pinned at 15.x while Next.js 16 is the current stable (released 2025-10-21).** Web-verified. Next 16 ships with Turbopack defaulting, React 19 alignment, Server Actions stable, and PPR available — all directly relevant to a greenfield App Router project. Starting on 15.x means a forced major upgrade mid-build. *Fix:* pin `Next.js: 16.x` and re-verify the App Router + RSC + i18n behavior under 16 before locking.

- **[high]** **Multiple stack pins are "latest (2026-07)" placeholders, not pins.** shadcn/ui, next-intl, Stripe (API version), Alembic, structlog, and uv are listed as `latest (2026-07)`. AD-14 explicitly states "Final pin requires web verification before first commit" — the spine acknowledges the gap, but the table itself does not commit to a number. This is acceptable as a *seed*, but every "latest" cell is an uncommitted decision. *Fix:* before committing the spine, replace each "latest" with the live version (or a `>=X.Y,<X+1` range) and a source URL. Concretely: uv is on a `0.x` cadence with frequent breaking minors — pin a minor, not just "latest".

- **[medium]** **PostgreSQL pinned at 15+ while 16 and 17 are GA and 15 is end-of-support window.** Supabase currently provisions PG 15 by default but exposes 17 in newer projects. *Fix:* pin `PostgreSQL 17+` (or at minimum `16+`) to align with Supabase's current default and to keep the 5-year support window through the SaaS's expected lifetime.

- **[medium]** **FastAPI pinned at `0.115+` (a lower-bound, not a pin).** A `+` suffix is a moving target. *Fix:* pin a specific minor (e.g., `0.116.x` or whatever the live latest is) and add uvicorn + starlette version pins — these are implicit dependencies the spine currently omits.

- **[medium]** **Claude model family stated as `claude-sonnet-4.5 family` — accurate but vague.** Web-verified: `claude-sonnet-4-5` exists with snapshot date 20250929 and is current. But Anthropic's most-recent flagship is Opus 4.7 (`claude-opus-4-7`). The PRD §13.2 says "Claude API (Vision 포함)" without specifying tier. *Fix:* state which Claude tier powers each M10 sub-capability (Vision extraction vs insight curation vs fixed/variable estimation). Sonnet is fine for most; Vision on Sonnet is acceptable; if any sub-capability needs higher reasoning, name Opus explicitly. Add a note that `claude-sonnet-4-5-20250929` is the snapshot date string.

- **[medium]** **OpenTelemetry pinned at `1.x` — under-specified.** OTel 1.x has been stable since 2024 and is now in 1.4x+ minors. The spine also defers the OTel *backend* choice. *Fix:* pin a 1.x minor; explicitly mark which signals (traces? metrics? logs?) are instrumented in 1차 vs deferred. The "exporter는 보류" defer is fine, but the instrumentation library pin should not be deferred.

- **[low]** **TanStack Table v8 — fine, but no minor pin.** v8 has been the major for several years; minor churn is unlikely to break the spine. *Fix:* pin a minor.

- **[low]** **Pydantic v2 / SQLAlchemy 2.x (async) / pytest 8.x — all plausible and current.** No change needed at this level of detail, but pytest is likely at 8.3+ or 9.x by 2026-07. *Fix:* confirm pytest minor and bump if needed.

- **[low]** **Node.js 22 LTS pinned.** As of 2026-07, Node 22 is in active LTS and Node 24 LTS may be available. *Fix:* confirm whether Node 24 LTS is GA before locking 22; if both are LTS, pick 22 for stability or 24 for the longer support runway and document the call.

- **[low]** **TypeScript pinned at "5.6+" — too loose for a 2026 build.** TS is well past 5.6 by mid-2026 (5.7, 5.8 likely GA). *Fix:* pin a specific minor.

- **[low]** **Recharts 2.x — plausible but worth a minor pin.** Recharts is at 2.12+ as of mid-2025; pin a minor.

- **[low]** **Hexagonal + Modular Monolith paradigm — confirmed recognized.** The combination (clean/hexagonal core inside a modular monolith) is a well-established pattern and aligns with the spine's intent (engine purity + single-operator simplicity). No structural issue.

## Confirmed (as of 2026-07, web-verified)

- React 19.x — current stable is 19.1.1 (released 2025-03-27). Spine pin acceptable.
- Tailwind CSS 4.x — current stable is in the 4.3.x line. Spine pin acceptable.
- Next.js 16 is current stable (released 2025-10-21) — spine is *behind* by one major; see finding above.
- Pydantic v2 — current major. Acceptable.
- SQLAlchemy 2.x async — current major. Acceptable.
- Anthropic `claude-sonnet-4-5` exists with snapshot `claude-sonnet-4-5-20250929`; current flagship is Opus 4.7.
- Hexagonal / ports-and-adapters / clean architecture is a recognized pattern. The spine's `ui → api → services → ports → engine ← adapters` dependency direction is conventional and correct.
- PostgreSQL append-only enforcement via `BEFORE UPDATE OR DELETE` row-level trigger raising `EXCEPTION` is a valid pattern.
- Supabase RLS with `tenant_id = (auth.jwt() ->> 'tenant_id')::uuid` is the canonical isolation pattern; spine implementation is correct.
- structlog JSON with `trace_id` propagation is a recognized logging pattern; no issue with the "latest (2026-07)" placeholder other than needing a real pin before commit.
- Vercel deployment model (managed edge + serverless for Next.js) is unchanged. Spine claim is fine.

## Cross-references

- The validation report (grade: Fair) flags "Downstream usability — thin" and the absence of Open Questions / Success Metrics / UJs in the PRD. From the verifier lens: the architecture spine is downstream-consumable today because UJ/SM exist in PRD §2.A/§2.B (added after the validation report), but the spine does not link each AD to a specific UJ or SM. This is a structural completeness issue, not a version issue — out of scope for the verifier lens but worth noting for the architecture review.
