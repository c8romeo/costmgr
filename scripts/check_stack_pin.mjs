#!/usr/bin/env node
// scripts/check_stack_pin.mjs — Stack pin check (Story 0.3)
// Reads docs/STACK_PIN.yaml and verifies the actual repo state matches.
// Exits 0 if all match, 1 if any drift (unless [STACK BUMP] tag is present).
//
// Usage:
//   node scripts/check_stack_pin.mjs                 # default: enforced
//   VERBOSE=1 node scripts/check_stack_pin.mjs       # show all expected vs actual
//   STACK_BUMP=1 node scripts/check_stack_pin.mjs    # authorize drift (CI uses
//                                                     commit-message tag; this
//                                                     is for local testing)
//   STACK_BUMP_PR_HEAD_SHA=<sha>                     # PR head commit for tag check
//
// The drift authorization is also recognized via the most recent commit
// message (git log -1 --format=%s) containing the literal "[STACK BUMP]".

import { readFileSync, existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { exit } from 'node:process';
import yaml from 'js-yaml';

// CASCADE-1 (CR 2026-07-25): js-yaml handles BOM, anchors, escaped quotes,
// folded scalars — replaces the hand-rolled parseYamlSimple.

const ROOT = process.cwd();
const VERBOSE = process.env.VERBOSE === '1' || process.env.VERBOSE === 'true';

function read(path) {
  const full = `${ROOT}/${path}`;
  if (!existsSync(full)) throw new Error(`missing: ${path}`);
  // utf-8 BOM tolerance: js-yaml handles BOM-prefixed YAML transparently
  return readFileSync(full, 'utf8');
}

function readJson(path) {
  return JSON.parse(read(path));
}

function hasCommitTag(tag, prHeadSha) {
  // MSG-2 (CR 2026-07-25): case-insensitive + use PR head commit when set
  const target = prHeadSha || 'HEAD';
  try {
    const msg = execSync(`git log -1 --format=%s ${target}`, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    });
    return msg.toLowerCase().includes(tag.toLowerCase());
  } catch {
    return false;
  }
}

// ── Load pin table ─────────────────────────────────────────────────────────

if (!existsSync(`${ROOT}/docs/STACK_PIN.yaml`)) {
  // STYLE-1 (CR 2026-07-25): ASCII markers for cp949-safe output
  console.error('[ERROR] docs/STACK_PIN.yaml not found');
  exit(2);
}
const pinDoc = yaml.load(read('docs/STACK_PIN.yaml')) || {};
const PIN = pinDoc.stack_pin || {};
const EXCEPTIONS = pinDoc.exceptions || {};

// Empty pin table → nothing to verify, exit 0
if (Object.keys(PIN).length === 0) {
  console.log('[STACK_PIN] OK empty STACK_PIN.yaml — nothing to verify');
  process.exit(0);
}

const prHeadSha = process.env.STACK_BUMP_PR_HEAD_SHA || null;
const bumpFromCommit = hasCommitTag('[STACK BUMP]', prHeadSha);
const bumpFromEnv = process.env.STACK_BUMP === '1';
const BUMP_OK = bumpFromCommit || bumpFromEnv;

if (bumpFromCommit) {
  console.log('[STACK_PIN] [STACK BUMP] tag present in commit — drift authorized');
} else if (bumpFromEnv) {
  console.log('[STACK_PIN] STACK_BUMP=1 — drift authorized (local override)');
}

// ── Checks ─────────────────────────────────────────────────────────────────

const drifts = [];

function check(label, expected, actual) {
  if (expected === undefined || expected === null) return; // not pinned
  if (actual === expected) {
    if (VERBOSE) console.log(`  OK  ${label}: ${actual}`);
    return;
  }
  drifts.push({ label, expected, actual });
  // MSG-1 (CR 2026-07-25): standardized format
  console.log(`  XX  ${label}: expected=${JSON.stringify(expected)} actual=${JSON.stringify(actual)}`);
}

// .nvmrc — canonical exact pin
try {
  const node = read('.nvmrc').trim();
  check('node (.nvmrc)', PIN.node, node);
} catch {
  drifts.push({ label: 'node', expected: PIN.node, actual: null });
  console.log(`  XX  node (.nvmrc): missing file`);
}

// .python-version
try {
  const py = read('.python-version').trim();
  check('python (.python-version)', PIN.python, py);
} catch {
  drifts.push({ label: 'python', expected: PIN.python, actual: null });
  console.log(`  XX  python (.python-version): missing file`);
}

// package.json — engines.node is semver `>=24.18.0 <25` (DOCKER-6)
try {
  const rootPkg = readJson('package.json');
  const enginesNode = rootPkg.engines?.node ?? '';
  // engines.node is a semver range; .nvmrc enforces the exact pin (already
  // checked above). Only report if engines.node is NOT a range.
  if (enginesNode && !enginesNode.startsWith('>=') && !enginesNode.startsWith('^')) {
    check('node (package.json engines.node)', PIN.node, enginesNode);
  }
  check('pnpm (package.json packageManager)', `pnpm@${PIN.pnpm}`, rootPkg.packageManager);
  check('pnpm (package.json engines.pnpm)', PIN.pnpm, rootPkg.engines?.pnpm);
} catch (e) {
  console.warn(`  [WARN] package.json: ${e.message}`);
}

// apps/web/package.json
try {
  const webPkg = readJson('apps/web/package.json');
  check('next (apps/web/package.json)', PIN.next, webPkg.dependencies?.next);
  check('react (apps/web/package.json)', PIN.react, webPkg.dependencies?.react);
  check('react-dom (apps/web/package.json)', PIN.react_dom, webPkg.dependencies?.['react-dom']);
  check('typescript (apps/web/package.json)', PIN.typescript, webPkg.devDependencies?.typescript);
  // TYPECHECK-1 (CR 2026-07-25): @types/* dev pins
  if (PIN['@types/react']) {
    check('@types/react (apps/web/package.json)', PIN['@types/react'], webPkg.devDependencies?.['@types/react']);
  }
  if (PIN['@types/node']) {
    check('@types/node (apps/web/package.json)', PIN['@types/node'], webPkg.devDependencies?.['@types/node']);
  }
} catch (e) {
  console.warn(`  [WARN] apps/web/package.json: ${e.message}`);
}

// apps/api/pyproject.toml — simple regex parser (matches check_stack_pin.py)
try {
  const apiToml = read('apps/api/pyproject.toml');
  function pinOf(name) {
    // Match `name==version` in any deps list
    const m = apiToml.match(new RegExp(`"${name}==([^"]+)"`));
    return m ? m[1] : null;
  }
  for (const pkg of ['sqlalchemy', 'alembic', 'asyncpg', 'pyjwt', 'supabase', 'pydantic-settings', 'fastapi', 'uvicorn', 'httpx']) {
    if (PIN[pkg === 'pydantic-settings' ? 'pydantic_settings' : pkg]) {
      check(`${pkg} (apps/api/pyproject.toml)`, PIN[pkg === 'pydantic-settings' ? 'pydantic_settings' : pkg], pinOf(pkg));
    }
  }
  if (PIN.pydantic_core) {
    check('pydantic-core (apps/api/pyproject.toml)', PIN.pydantic_core, pinOf('pydantic-core'));
  }
  if (PIN.pydantic) {
    // Pydantic is now strict-equal pinned (RANGE-1)
    const pMatch = apiToml.match(/"pydantic==([^"]+)"/);
    check('pydantic (apps/api/pyproject.toml)', PIN.pydantic, pMatch ? pMatch[1] : null);
  }
} catch (e) {
  console.warn(`  [WARN] apps/api/pyproject.toml: ${e.message}`);
}

// packages/cost_engine/pyproject.toml
try {
  const ceToml = read('packages/cost_engine/pyproject.toml');
  const npMatch = ceToml.match(/"numpy==([^"]+)"/);
  if (PIN.numpy && npMatch) {
    check('numpy (packages/cost_engine)', PIN.numpy, npMatch[1]);
  }
  const ptMatch = ceToml.match(/"pytest==([^"]+)"/);
  if (PIN.pytest && ptMatch) {
    check('pytest (packages/cost_engine)', PIN.pytest, ptMatch[1]);
  }
} catch (e) {
  console.warn(`  [WARN] packages/cost_engine/pyproject.toml: ${e.message}`);
}

// root pyproject.toml — dev deps + build-system.requires
try {
  const rootToml = read('pyproject.toml');
  for (const pkg of ['import-linter', 'pytest', 'ruff']) {
    const m = rootToml.match(new RegExp(`"${pkg}==([^"]+)"`));
    if (m && PIN[pkg === 'import-linter' ? 'import_linter' : pkg]) {
      check(`${pkg} (pyproject.toml dev)`, PIN[pkg === 'import-linter' ? 'import_linter' : pkg], m[1]);
    }
  }
  // HATCH-1: hatchling pinned in [build-system].requires
  if (PIN.hatchling) {
    const hatchMatch = rootToml.match(/requires\s*=\s*\["hatchling==([^"]+)"\]/);
    if (hatchMatch) {
      check('hatchling (root [build-system])', PIN.hatchling, hatchMatch[1]);
    }
  }
  // Also check apps/api/pyproject.toml for hatchling
  try {
    const apiToml = read('apps/api/pyproject.toml');
    const hatchMatch = apiToml.match(/requires\s*=\s*\["hatchling==([^"]+)"\]/);
    if (hatchMatch && PIN.hatchling) {
      check('hatchling (apps/api [build-system])', PIN.hatchling, hatchMatch[1]);
    }
  } catch {}
} catch (e) {
  console.warn(`  [WARN] pyproject.toml: ${e.message}`);
}

// CHECK-1 (CR 2026-07-25): pnpm-lock.yaml — verify resolved versions exist
if (existsSync(`${ROOT}/pnpm-lock.yaml`)) {
  try {
    const pnpmLock = yaml.load(read('pnpm-lock.yaml')) || {};
    const packages = pnpmLock.packages || {};
    for (const pkgName of ['next', 'react', 'react-dom', 'typescript']) {
      if (PIN[pkgName]) {
        const expected = PIN[pkgName];
        // Look for `<name>@<expected>` or `/<name>@<expected>` in keys
        let found = false;
        for (const k of Object.keys(packages)) {
          if (k === `${pkgName}@${expected}` || k.endsWith(`/${pkgName}@${expected}`)) {
            found = true;
            break;
          }
        }
        if (!found && VERBOSE) {
          console.log(`  [INFO] ${pkgName}@${expected} not resolved in pnpm-lock.yaml`);
        }
      }
    }
  } catch (e) {
    console.warn(`  [WARN] pnpm-lock.yaml: ${e.message}`);
  }
}

// DOCKER-2 (CR 2026-07-25): scan CI workflow for postgres image digest
const ciYmlPath = `${ROOT}/.github/workflows/ci.yml`;
if (existsSync(ciYmlPath)) {
  try {
    const ciText = read('.github/workflows/ci.yml');
    const re = /image:\s*(postgres[^@\s]*)@sha256:([a-f0-9]+)/gm;
    const m = re.exec(ciText);
    if (m && PIN.postgresql_digest) {
      check('postgres CI service image digest', PIN.postgresql_digest, `sha256:${m[2]}`);
    }
  } catch (e) {
    console.warn(`  [WARN] ci.yml: ${e.message}`);
  }
}

// Dockerfile — base image tags + digests
try {
  const dockerfile = read('Dockerfile');
  const fromLines = dockerfile.match(/^FROM\s+([^\s@]+)(@sha256:[a-f0-9]+)?/gm) || [];
  const images = fromLines.map(l => {
    const m = l.match(/^FROM\s+([^\s@]+)/);
    if (!m) return null;
    // Strip leading `@` from digest for comparison with STACK_PIN.yaml
    const digestMatch = l.match(/@sha256:[a-f0-9]+/);
    const digest = digestMatch ? digestMatch[0].slice(1) : null;
    return { name: m[1], digest };
  }).filter(Boolean);

  if (PIN.python_slim) {
    const found = images.find(i => i.name.startsWith('python:'));
    check('python (Dockerfile base image)', `python:${PIN.python_slim}`, found?.name);
    if (PIN.python_slim_digest) {
      check('python (Dockerfile digest)', PIN.python_slim_digest, found?.digest);
    }
  }
  if (PIN.node_alpine) {
    const found = images.find(i => i.name.startsWith('node:'));
    check('node (Dockerfile base image)', `node:${PIN.node_alpine}`, found?.name);
    if (PIN.node_alpine_digest) {
      check('node (Dockerfile digest)', PIN.node_alpine_digest, found?.digest);
    }
  }
  if (PIN.nginx_alpine) {
    const found = images.find(i => i.name.startsWith('nginx:'));
    check('nginx (Dockerfile base image)', `nginx:${PIN.nginx_alpine}`, found?.name);
    if (PIN.nginx_alpine_digest) {
      check('nginx (Dockerfile digest)', PIN.nginx_alpine_digest, found?.digest);
    }
  }
} catch (e) {
  console.warn(`  [WARN] Dockerfile: ${e.message}`);
}

// ── Verdict ────────────────────────────────────────────────────────────────

if (drifts.length === 0) {
  console.log(`[STACK_PIN] OK all ${Object.keys(PIN).length} pins match`);
  exit(0);
}

if (BUMP_OK) {
  console.warn(`[STACK_PIN] WARN ${drifts.length} drift(s) detected but [STACK BUMP] authorized -- pass:`);
  for (const d of drifts) {
    console.warn(`  - ${d.label}: ${d.expected} -> ${d.actual}`);
  }
  exit(0);
}

// MSG-1: standardized violation message
console.error(`[STACK_PIN] FAIL ${drifts.length} drift(s) detected:`);
for (const d of drifts) {
  console.error(`  STACK_PIN_VIOLATION: ${d.label} drifted from ${d.expected} to ${d.actual}. Use [STACK BUMP] commit tag to bypass.`);
}
exit(1);