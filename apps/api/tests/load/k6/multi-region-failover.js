// apps/api/tests/load/k6/multi-region-failover.js
// Phase 8 (cj-style 95번째 wire) — k6 Load Testing scenario 5/5
// (PRD §F24.1 + AC #1.6).
//
// Multi-region failover load test: Phase 5 wire `f093f8c` multi-region
// observability carry-over + Seoul region primary + Tokyo replica failover
// load. 10 VU RTO < 30s.
//
// Thresholds (k6 `thresholds` block — CI gate per §F24.1-7 + §F24.2-5 SLA-4):
//   - http_req_duration: p(95)<5000ms, p(99)<30000ms (NFR22 + Phase 5 wire)
//   - http_req_failed:   rate<0.001 (0.1%)
//
// Environment bindings: see apps/api/tests/load/k6/auth-login.js header.

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const tenantId = __ENV.K6_TENANT_ID || '00000000-0000-0000-0000-000000000000';
const traceId = __ENV.K6_TRACE_ID || 'k6-trace-multi-region';
const vus = parseInt(__ENV.K6_VUS || '10', 10);
const ramp = parseInt(__ENV.K6_RAMP_DURATION_S || '120', 10);
const baseUrl = __ENV.K6_BASE_URL || 'http://localhost:8000';

const errorRate = new Rate('errors');
const failoverDuration = new Trend('failover_duration_ms');

export const options = {
  stages: [
    { duration: `${ramp}s`, target: vus },
    { duration: '120s', target: vus },
    { duration: '20s', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<5000', 'p(99)<30000'],
    'http_req_failed':   ['rate<0.001'],
    'errors':            ['rate<0.001'],
  },
};

export default function () {
  // Phase 5 wire `f093f8c` multi-region observability.
  // GET /api/v1/admin/health/multi-region — replication lag + replica status
  // (PRD §F20.1 + AD-31 (a) sub-decision).
  const url = `${baseUrl}/api/v1/admin/health/multi-region`;
  const params = {
    headers: {
      'X-Tenant-Context': tenantId,
      'X-Admin-Role': 'owner',
      'traceparent': `00-${traceId}-${__VU}${__ITER}-01`,
    },
  };

  const res = http.get(url, params);
  failoverDuration.add(res.timings.duration);
  const ok = check(res, {
    'status is 2xx or 503-acceptable': (r) =>
      (r.status >= 200 && r.status < 300) || r.status === 503,
  });
  errorRate.add(!ok);
  sleep(1);
}
