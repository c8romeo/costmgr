// apps/api/tests/load/k6/audit-log-query.js
// Phase 8 (cj-style 95번째 wire) — k6 Load Testing scenario 4/5
// (PRD §F24.1 + AC #1.5).
//
// Audit log query load test: Epic 17 wire `2ada2ec` audit_log_query +
// Epic 12 2FA + Phase 6 wire `24e1cd7` retention combined load. 20 VU.
//
// Thresholds (k6 `thresholds` block — CI gate per §F24.1-7 + §F24.2-3 SLA-2):
//   - http_req_duration: p(95)<1000ms, p(99)<2000ms (Epic 17 carry-over)
//   - http_req_failed:   rate<0.01 (1%)
//
// Environment bindings: see apps/api/tests/load/k6/auth-login.js header.

import http from 'k6/http';
import { check } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const tenantId = __ENV.K6_TENANT_ID || '00000000-0000-0000-0000-000000000000';
const traceId = __ENV.K6_TRACE_ID || 'k6-trace-audit-log';
const vus = parseInt(__ENV.K6_VUS || '20', 10);
const ramp = parseInt(__ENV.K6_RAMP_DURATION_S || '30', 10);
const baseUrl = __ENV.K6_BASE_URL || 'http://localhost:8000';

const errorRate = new Rate('errors');
const auditLogDuration = new Trend('audit_log_duration_ms');

export const options = {
  stages: [
    { duration: `${ramp}s`, target: vus },
    { duration: '60s', target: vus },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000', 'p(99)<2000'],
    'http_req_failed':   ['rate<0.01'],
    'errors':            ['rate<0.01'],
  },
};

export default function () {
  // Epic 17 wire `2ada2ec` audit_log_query endpoint. Activity stream is
  // intentionally NOT gated (PRD §F21.3 verbatim — broad access).
  // GET /api/v1/audit-log?from=2026-08-01&to=2026-08-31 — paginated log query.
  const url = `${baseUrl}/api/v1/audit-log?from=2026-08-01&to=2026-08-31&page=1&page_size=50`;
  const params = {
    headers: {
      'X-Tenant-Context': tenantId,
      'traceparent': `00-${traceId}-${__VU}${__ITER}-01`,
    },
  };

  const res = http.get(url, params);
  auditLogDuration.add(res.timings.duration);
  const ok = check(res, {
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
  });
  errorRate.add(!ok);
}
