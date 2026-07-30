# Dependabot Policy

> Weekly gated updates for stack-pinned packages.
> Source of truth: [`.github/dependabot.yml`](../.github/dependabot.yml)

---

## Schedule

| Ecosystem | Day      | Time (KST) | Labels                |
| --------- | -------- | ---------- | --------------------- |
| `npm`     | Monday   | 09:00      | `stack-pin`, `dependencies` |
| `pip`     | Tuesday  | 09:00      | `stack-pin`, `dependencies` |
| `docker`  | Wednesday| 09:00      | `stack-pin`, `docker`      |

Schedule is **business hours only** — the operator is solo, no weekend coverage.
PRs land during work hours so triage happens the same day.

---

## Grouping

Updates are split into two groups per ecosystem:

- **`pinned-dependencies`** — packages listed in `docs/STACK_PIN.yaml`.
  All updates to this group land in **one PR per week**. Easier review
  (one CI run, one approval) than N parallel PRs.
- **`non-pinned-dependencies`** — everything else. Also grouped into one PR.
  These are safe to auto-merge after CI passes.

---

## Approval flow for pinned-dependencies PRs

1. Dependabot opens a PR labelled `stack-pin`.
2. CI runs `stack-pin-check` (`.github/workflows/ci.yml`). It will fail
   because the version drifted from `STACK_PIN.yaml`.
3. Reviewer (CODEOWNER = platform-team) does one of:
   - **Approve** the bump → edit the PR description with `[STACK BUMP] bump
     <pkg> <old> → <new>`. Squash-merge so the [STACK BUMP] tag is in HEAD.
     Update `docs/STACK_PIN.yaml` to the new version as part of the PR.
   - **Reject** the bump → close the PR. The pin stays.
4. After merge, run the V8 regression gate:
   ```bash
   uv run pytest packages/cost_engine/tests/regression_v8 -v
   ```

---

## Approval flow for non-pinned-dependencies PRs

- CI passes (no drift because the package isn't pinned).
- Auto-merge after CI green + 1 approval.
- No `[STACK BUMP]` tag needed.

---

## Branch protection (recommended)

In **Settings → Branches → Branch protection rules → main**:

- [x] Require a pull request before merging
- [x] Require approvals: **1**
- [x] Require review from Code Owners
- [x] Require status checks to pass before merging:
  - `stack-pin-check`
  - `lint-deps`
  - `lint-imports`
  - `test-architecture`
  - `rls-tests` (on changes to `supabase/`, `apps/api/core/`, `tests/rls/`)
- [x] Do not allow bypassing the above settings

---

## What NOT to do

- ❌ Auto-merge `stack-pin`-labelled PRs without CODEOWNER review.
- ❌ Edit the Dependabot commit to add `[STACK BUMP]` retroactively without
  also updating `STACK_PIN.yaml`. The CI guard checks both.
- ❌ Pin a new package directly in `package.json` without first adding it to
  `STACK_PIN.yaml` (the regen script will overwrite your pin on next run).
- ❌ Disable Dependabot for the pinned group — silent drift is the failure mode
  this story was written to prevent.