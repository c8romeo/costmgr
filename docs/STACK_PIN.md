# Stack Pin Policy (AD-14)

> Single source of truth: [`STACK_PIN.yaml`](./STACK_PIN.yaml)
> Regenerated from `ARCHITECTURE-SPINE.md §Stack` by
> `scripts/regenerate_stack_pin.py`.

---

## Why a stack pin?

The architecture spine commits to a **cold-start pin** of every dependency
that affects AD-1 (modular monolith), AD-8 (monetary types — `Decimal` +
`bigint`), or AD-15 (cross-language conventions). Drift in these versions is
**silent breakage**: a patch bump of `pydantic-core` once cost us a working
test suite, and a `sqlalchemy` minor jump changed event-listener signatures
without a deprecation cycle.

Pin the version. Lock the resolution. Bump deliberately. CI fails the build
on any unauthorized drift.

---

## Bump policy

1. **Routine dep work** (patch updates, new transitive): free, no tag.
2. **Pinned-version bump** (anything in `STACK_PIN.yaml`): requires the
   `[STACK BUMP]` commit tag **and** CODEOWNER approval (`platform-team`).
3. **CI gate**: `stack-pin-check` job in `.github/workflows/ci.yml` runs
   `pnpm dep:check` and `uv run check-stack-pin`. Drift + no tag = build
   fails with `STACK_PIN_VIOLATION`.
4. **Dependabot** opens weekly PRs for `npm` + `pip`. PRs touching pinned
   packages get the `stack-pin` label and require CODEOWNER approval.

### How to bump

```bash
# 1. Edit docs/STACK_PIN.yaml (the only file you should hand-edit).
#    Update both `stack_pin` and the matching `notes` entry.

# 2. Run the helper — it updates package.json, pyproject.toml, and Dockerfile,
#    then commits with the [STACK BUMP] tag.
./scripts/bump_stack_pin.sh next 16.2.11

# 3. Push. CI guard will accept the bump because the tag is present.
git push origin bump/next-16.2.11
```

### V8 regression gate

**Any pinned-version bump requires running the V8 regression suite**
(`packages/cost_engine/tests/regression_v8/`) before merge. V8 fixtures
encode 1원 reconciliation contracts; a cost-engine version bump without a
clean V8 run is grounds for rollback.

Setup of the full V8 suite is Story 4.4. Until then, this story documents
the policy. To opt into early V8 checks during a bump:

```bash
uv run pytest packages/cost_engine/tests/regression_v8 -v
```

(Will return `no tests ran` until Story 4.4 ships the fixtures.)

---

## Files enforced by the pin

| File                          | What it pins                       |
| ----------------------------- | ---------------------------------- |
| `.nvmrc`                      | Node version                       |
| `.python-version`             | Python version                     |
| `package.json`                | engines.node, packageManager       |
| `apps/web/package.json`       | next, react, typescript            |
| `apps/api/pyproject.toml`     | fastapi, sqlalchemy, alembic, ...  |
| `packages/cost_engine/pyproject.toml` | numpy, pytest              |
| `Dockerfile`                  | base image tags (+ digests)        |
| `pnpm-lock.yaml`              | exact resolution of npm tree       |
| `uv.lock`                     | exact resolution of pip tree       |

---

## CLI

| Command                            | Purpose                                          |
| ---------------------------------- | ------------------------------------------------ |
| `pnpm dep:check`                   | Quick local Node check (mirrors CI guard)        |
| `pnpm dep:check:verbose`           | Show all expected vs actual, even if matching    |
| `uv run check-stack-pin`           | Python check (same output)                       |
| `./scripts/bump_stack_pin.sh <pkg> <ver>` | Bump a single pin with auto `[STACK BUMP]` tag |
| `python scripts/regenerate_stack_pin.py` | Re-derive `STACK_PIN.yaml` from ARCHITECTURE-SPINE.md |

---

## Anti-patterns

- ❌ `^` or `~` in `package.json` for any pinned package.
- ❌ `latest` in Docker base images — use digest (`@sha256:...`).
- ❌ Silent bump in lockfile without `STACK_PIN.yaml` update first.
- ❌ Dependabot auto-merge on `stack-pin`-labelled PR.
- ❌ `pnpm install` in CI (always `--frozen-lockfile`).
- ❌ Bumping `pydantic-core` to anything newer than the last known-good wheel
  until Pydantic's wheel pipeline is verified (see `notes.pydantic` in yaml).