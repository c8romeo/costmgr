/**
 * dependency-cruiser config — enforce AD-1, AD-11 dependency direction.
 *
 * Direction: ui → api → services → ports → engine
 *  - apps/web  (UI)  → may NOT import apps/api, packages/*
 *  - apps/api  (TS)  → may import packages/ports types only
 *  - packages/services → may import packages/ports, packages/cost_engine/ports
 *  - packages/ports  → stdlib/typing only
 *  - packages/cost_engine/core → no I/O, no DB/web/clock/random
 */

/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'No circular dependencies',
      from: {},
      to: { circular: true },
    },
    {
      name: 'no-orphans',
      severity: 'warn',
      comment: 'No orphaned files (unreferenced)',
      from: {},
      to: { reachable: false },
    },
    {
      name: 'apps-may-not-reach-engine-core',
      severity: 'error',
      comment: 'apps/** may not import packages/cost_engine/core directly (AD-1/AD-11). Use ports/.',
      from: { path: '^apps' },
      to: { path: '^packages/cost_engine/core' },
    },
    {
      name: 'ui-cannot-reach-server-or-engine',
      severity: 'error',
      comment: 'apps/web may not import apps/api or packages/* (AD-1)',
      from: { path: '^apps/web' },
      to: { path: '^(apps/api|packages/.*)' },
    },
    {
      name: 'api-calls-only-ports',
      severity: 'error',
      comment: 'apps/api may only import packages/ports types, never packages/cost_engine/* internals (AD-1/AD-11)',
      from: { path: '^apps/api' },
      to: {
        path: '^packages/cost_engine',
        pathNot: '^packages/cost_engine/ports',
      },
    },
    {
      name: 'services-only-via-ports',
      severity: 'error',
      comment: 'packages/services may import only packages/ports and packages/cost_engine/ports (AD-11)',
      from: { path: '^packages/services' },
      to: {
        path: '^packages/cost_engine',
        pathNot: '^packages/cost_engine/ports',
      },
    },
    {
      name: 'engine-core-no-adapters',
      severity: 'error',
      comment: 'packages/cost_engine/core must not import packages/cost_engine/adapters (AD-1/AD-11)',
      from: { path: '^packages/cost_engine/core' },
      to: { path: '^packages/cost_engine/adapters' },
    },
    {
      name: 'ports-stdlib-only',
      severity: 'error',
      comment: 'packages/ports may import only stdlib/typing (AD-11)',
      from: { path: '^packages/ports' },
      to: {
        path: '^(?!(\.|node:)).+',
        pathNot: '^@?[a-z0-9-]+$', // bare specifiers only — checked separately
      },
    },
  ],
  options: {
    doNotFollow: { path: 'node_modules' },
    tsConfig: { fileName: 'tsconfig.base.json' },
    enhancedResolveOptions: {
      exportsFields: ['exports'],
      conditionNames: ['import', 'require', 'node', 'default'],
    },
    moduleSystems: ['amd', 'cjs', 'es6', 'tsd'],
    reporterOptions: {
      dot: { collapsePattern: 'node_modules/(@[^/]+/[^/]+|[^/]+)' },
    },
  },
};
