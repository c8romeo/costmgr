# apps/api — bizup/costmgr FastAPI monolith

Story 0.1 stub: single `/health` route. Story 0.2 wires DB + JWT + RLS.
Domain endpoints land in Epic 1+.

AD-1, AD-11 compliance:
- Imports only stdlib + FastAPI/uvicorn
- Does NOT import `packages.cost_engine.core` directly
- Imports `packages.cost_engine.ports` via `apps.api.core.ports_bridge` (later stories)

Run locally:

```bash
uv sync --all-extras
cp .env.example .env   # fill in DATABASE_URL
uv run fastapi dev apps/api/main.py
```

Tests:

```bash
uv run pytest tests/rls/test_service_role_audit.py -v   # unit (no DB)
uv run pytest tests/rls -v                                # CI-only (Postgres on 54322)
```

See `supabase/README.md` for the Supabase local stack + RLS policy apply order.
