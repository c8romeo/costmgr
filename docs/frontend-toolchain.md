# Frontend Toolchain (Story 0.5)

> Single source of truth for the Next.js frontend toolchain stack. Closed
> by Story 0.5 (Epic 4 close-out retro §7 A6 follow-through).

## §1 Stack Pin (AD-14 — exact versions, no `^` or `~`)

| Layer | Tool | Version |
|---|---|---|
| Runtime | Node | 24.18 LTS (24.15.0 accepted as minor drift) |
| Package manager | pnpm | 9.15.4 (corepack-managed) |
| Framework | Next.js | 15.5.4 (STACK_PIN aspirational 16.2.11 deferred) |
| UI | React | 19.1.1 |
| Styling | Tailwind CSS | 4.3.3 + `@tailwindcss/postcss@4.3.3` |
| Components | shadcn/ui (manual, CLI-equivalent) | Tabs/Tooltip/Dialog primitives |
| Toast | sonner | 2.0.7 |
| Icons | lucide-react | 0.460.0 |
| Linter | ESLint | 9.32.0 (flat config) |
| TypeScript | TS | 5.9.3 |
| Unit tests | vitest | 4.1.10 |
| Component tests | @testing-library/react | 16.3.2 |
| HTTP mocking | msw | 2.15.0 |
| E2E | @playwright/test | 1.62.1 |
| i18n | next-intl | 4.13.5 |
| Font | Pretendard Variable | via next/font/local (woff2 bundled in `apps/web/public/fonts/`) |

`apps/web/package.json` declares `"engines": { "node": ">=24.18.0 <25" }` —
Story 0.5 closes Story 0.3 TYPES-1 deferral.

## §2 Tailwind 4 Config

Tailwind 4 is CSS-first. Configuration lives in `apps/web/app/globals.css`:

- `@import "tailwindcss"` — required entry
- `@layer base { :root { ... } }` — CSS variables for shadcn design tokens
  (slate light theme baseline)
- `@theme inline { --color-background, --color-primary, --color-ring, --radius-* }`
  — exposes tokens as Tailwind utilities (`bg-background`, `text-primary`, etc.)
- `dark:` variant via `.dark` class (toggle deferred to theme story)

`apps/web/postcss.config.mjs` registers `@tailwindcss/postcss` + `autoprefixer`.
`apps/web/tailwind.config.ts` declares `content` paths only (Tailwind 4
auto-scans via `@tailwindcss/postcss`; the config exists for IDE IntelliSense).

## §3 shadcn/ui Setup

Manual authoring (CLI skipped for offline determinism — pattern parity):

- `apps/web/components.json` — shadcn registry config
- `apps/web/lib/utils.ts` — `cn(...inputs)` helper (clsx + tailwind-merge)
- `apps/web/components/ui/tabs.tsx` — Radix Tabs wrapper
- `apps/web/components/ui/tooltip.tsx` — Radix Tooltip wrapper
- `apps/web/components/ui/dialog.tsx` — Radix Dialog wrapper
- `apps/web/components/ui/sonner.tsx` — sonner Toaster wrapper

`cn()` is the canonical way to compose classNames. Never concatenate classes
manually — pass them through `cn()` to resolve Tailwind conflicts.

## §4 sonner Toast Usage

`<Toaster />` is wired in `apps/web/app/layout.tsx` after `{children}`,
inside `<body>`. Use `toast.warning()`, `toast.error()`, `toast.success()`,
`toast.info()` from any client component:

```tsx
"use client";
import { toast } from "sonner";

toast.warning("BOM 비중 합 100% 필요 (현재 95.00%)");
```

Server components cannot use `toast()` — must be inside a `"use client"`
boundary. The pattern: trigger the toast from a `useEffect` that watches
the relevant state (avoids toast spam on every render).

## §5 vitest Setup

- `apps/web/vitest.config.ts` — jsdom env + setup files + @vitejs/plugin-react
- `apps/web/test/setup.ts` — extends `expect` with `@testing-library/jest-dom`
  matchers + MSW server lifecycle (`beforeAll start / afterEach reset / afterAll close`)
- `apps/web/mocks/handlers.ts` — initial MSW handlers
  (`/api/v1/tenants/me`, `/api/v1/tenants/me/industry`)
- `apps/web/mocks/server.ts` — `setupServer(...handlers)` export

Run via `pnpm test` (vitest run), `pnpm test:watch` (vitest --watch),
`pnpm test:ui` (vitest --ui), `pnpm test:coverage` (v8 reporter).

`globals: true` is enabled so `describe`/`it`/`expect`/`vi` work without
import. ESLint config exposes these as globals too.

## §6 Playwright Setup

- `apps/web/playwright.config.ts` — baseURL `http://localhost:3000`,
  projects (chromium/firefox/webkit), webServer `pnpm dev` with
  `reuseExistingServer: !process.env.CI`, 30s timeout, 2 retries on CI
- `apps/web/e2e/fixtures/supabase-test.ts` — `rlsDb` fixture for tenant-scoped
  E2E tests (Story 1.1 F-30 close)
- `apps/web/e2e/onboarding.spec.ts` — 4 onboarding scenarios

Run via `pnpm playwright test` (full matrix), `pnpm playwright test --project=chromium`
(smoke subset — CI runs this only), `pnpm playwright install --with-deps chromium`
(initial browser install), `pnpm playwright codegen` (record).

## §7 next-intl Routing

- `apps/web/i18n.ts` — `getRequestConfig` (locale='ko-KR' default, timeZone='Asia/Seoul')
- `apps/web/middleware.ts` — `createMiddleware` matching `/[locale]/...`
- `apps/web/messages/ko-KR.json` — ko-KR translations (namespaces: industry, bom, settings, common, errors)
- `apps/web/next.config.ts` — wrapped with `createNextIntlPlugin('./i18n.ts')`

In client components:

```tsx
"use client";
import { useTranslations } from "next-intl";

export function IndustryCard() {
  const t = useTranslations("industry");
  return <h3>{t("manufacturing")}</h3>;
}
```

`localePrefix: "as-needed"` — `/ko-KR/onboarding/industry` is the explicit
form; bare `/onboarding/industry` also works (middleware injects default
locale). All test assertions use the explicit form to avoid locale-inference
ambiguity.

## §8 INDUSTRY_ICON Contract

The per-industry icon set lives in TWO places (cross-language drift guarded):

- `apps/web/lib/menu-config.ts::INDUSTRY_ICON` — `Record<Industry, string>`
  (TS source of truth — consumed by `IndustryCard.tsx` via lucide-react)
- `packages/services/m0_onboarding/industry_menu.py::INDUSTRY_ICON`
  — `dict[Industry, str]` (Python mirror; stores icon name only)

| Industry | Icon |
|---|---|
| manufacturing | `Factory` |
| service | `Briefcase` |
| manufacturing_service | `Layers` |
| manufacturing_service_other | `Boxes` |

Drift detector: `tests/integration/test_menu_config_consistency.py::test_industry_icon_parity_ts_matches_python`
asserts each industry key matches between TS and Python. Pattern matches
the A5 forward-lock drift detector — drift = A5 forward-lock fail.

Adding a new industry:

1. Add to `Industry` enum in BOTH TS and Python
2. Add icon name to `INDUSTRY_ICON` in BOTH TS and Python
3. Run `pnpm test` + `uv run pytest tests/integration/test_menu_config_consistency.py`
4. Both must pass; if either fails, drift detector has your back

## References

- Story 0.5 spec: `_bmad-output/implementation-artifacts/0-5-frontend-plumbing-shadcn-sonner-vitest-playwright.md`
- Epic 4 close-out retro §7 A6: `_bmad-output/implementation-artifacts/epic-4-retro-close-out-2026-08-03.md`
- Architecture spine AD-1, AD-14, AD-15: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md`
