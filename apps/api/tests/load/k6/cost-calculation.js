// apps/api/tests/load/k6/cost-calculation.js
// Phase 8 (cj-style 95번째 wire) — k6 Load Testing scenario 2/5
// (PRD §F24.1 + AC #1.3).
//
// Cost calculation load test: Epic 9 ABC/TDABC + Epic 7 Story 7-2 next-month
// projection + Epic 8 AI extraction combined load. 50 VU 95p curl <5s.
//
// Thresholds (k6 `thresholds` block — CI gate per §F24.1-7 + §F24.2-2 SLA-1):
//   - http_req_duration: p(95)<2000ms, p(99)<5000ms (NFR22 latency budget)
//   - http_req_failed:   rate<0.01 (1%)
//
// Environment bindings: see apps/api/tests/load/k6/auth-login.js header.

import http from 'k6/http';
import { check } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const tenantId = __ENV.K6_TENANT_ID || '00000000-0000-0000-0000-000000000000';
const traceId = __ENV.K6_TRACE_ID || 'k6-trace-cost-calc';
const vus = parseInt(__ENV.K6_VUS || '50', 10);
const ramp = parseInt(__ENV.K6_RAMP_DURATION_S || '60', 10);
const baseUrl = __ENV.K6_BASE_URL || 'http://localhost:8000';

const errorRate = new Rate('errors');
const costCalcDuration = new Trend('cost_calc_duration_ms');

export const options = {
  stages: [
    { duration: `${ramp}s`, target: vus },
    { duration: '60s', target: vus },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'],
    'http_req_failed':   ['rate<0.01'],
    'errors':            ['rate<0.01'],
  },
};

export default function () {
  // Epic 9 + Phase 7 wire `59b56cd` Prometheus histogram baseline carry-over.
  // POST /api/v1/cost-engine/compute — periodic cost calculation endpoint
  // (Epic 9 m3_calculate + Epic 9 m9_abc dual-route per AD-19).
  const url = `${baseUrl}/api/v1/cost-engine/compute`;
  const payload = JSON.stringify({
    tenant_id: tenantId,
    period_key: '2026-08',
    industry: 'manufacturing_service',
  });
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-Context': tenantId,
      'traceparent': `00-${traceId}-${__VU}${__ITER}-01`,
    },
  };

  const res = http.post(url, payload, params);
  costCalcDuration.add(res.timings.duration);
  const ok = check(res, {
    'status is 2xx or 4xx-expected': (r) =>
      (r.status >= 200 && r.status < 300) || r.status === 409 || r.status === 422,
  });
  errorRate.add(!ok);
}
